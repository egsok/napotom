"""yt-dlp wrapper for video downloading."""

import logging
import os
import re
import sys
from dataclasses import dataclass
from typing import Optional, Callable, List
from pathlib import Path

import yt_dlp
from yt_dlp.utils import DownloadError, ExtractorError, DownloadCancelled
from yt_dlp.postprocessor.common import PostProcessor

from utils.config import config_manager
from utils.i18n import tr

logger = logging.getLogger(__name__)


class FinalPathCollector(PostProcessor):
    """Captures the final file path at the 'after_move' stage.

    Progress hooks report per-stream intermediate files; only at
    'after_move' is info['filepath'] final for all cases (single file,
    video+audio merge, mp3 extraction).
    """

    filepath = None

    def run(self, info):
        try:
            self.filepath = info.get('filepath')
        except Exception:
            pass  # Never abort the download from a collector
        return [], info


# Error patterns ordered by specificity (most specific first).
# The second element is a translation key resolved through tr() at display time,
# so error messages follow the interface language.
ERROR_PATTERNS = [
    # Cookie extraction failures - actionable
    ('could not copy', 'err_cookie_copy'),
    ('dpapi', 'err_cookie_decrypt'),
    ('failed to decrypt', 'err_cookie_decrypt'),

    # Bot detection - actionable
    ('sign in to confirm you\'re not a bot', 'err_bot_check'),
    ('confirm you\'re not a bot', 'err_bot_check'),

    # Age restriction - actionable (cookies can help)
    ('sign in to confirm your age', 'err_age_verify'),
    ('age-restricted', 'err_age_restricted'),
    ('age gate', 'err_age_restricted'),

    # Login required - actionable (cookies can help)
    ('sign in to view', 'err_sign_in_required'),
    ('members only', 'err_members_only'),
    ('join this channel', 'err_members_only'),
    ('premium', 'err_premium_required'),

    # Availability - not actionable
    ('video unavailable', 'err_video_unavailable'),
    ('private video', 'err_video_private'),
    ('removed by', 'err_video_removed'),
    ('deleted video', 'err_video_deleted'),
    ('copyright', 'err_copyright'),

    # Geo-restriction - not actionable
    ('not available in your country', 'err_geo_region'),
    ('geo', 'err_geo_restricted'),
    ('blocked in your country', 'err_geo_blocked'),

    # Live content
    ('live event will begin', 'err_upcoming_live'),
    ('premieres in', 'err_premiere'),

    # HTTP errors
    ('401', 'err_unauthorized'),
    ('unauthorized', 'err_unauthorized'),
    ('403', 'err_forbidden'),
    ('404', 'err_not_found'),
    ('429', 'err_rate_limited'),
    ('503', 'err_service_unavailable'),

    # Network errors
    ('connection', 'err_connection'),
    ('timeout', 'err_timeout'),
    ('network', 'err_network'),
    ('ssl', 'err_ssl'),

    # Technical errors
    ('ffmpeg', 'err_ffmpeg'),
    ('postprocessing', 'err_postprocessing'),
    ('no video formats', 'err_no_formats'),
    ('unsupported url', 'err_unsupported_url'),

    # Format selection failures (usually auth-related or missing JS runtime)
    ('requested format is not available', 'err_no_formats_cookies'),
    # JS runtime missing — YouTube needs it for challenge solving
    ('no js runtime', 'err_no_js_runtime'),
    ('jsc', 'err_no_js_runtime'),
]


def check_js_runtime_available() -> bool:
    """Check if any JavaScript runtime is available for yt-dlp's YouTube solver."""
    import shutil
    for cmd in ('deno', 'node', 'bun', 'qjs'):
        if shutil.which(cmd):
            logger.debug('Found JS runtime: %s', cmd)
            return True
    logger.warning('No JavaScript runtime found (node/deno/bun/qjs). YouTube downloads may fail.')
    return False


@dataclass
class VideoInfo:
    """Video metadata."""
    url: str
    title: str
    duration: int  # seconds
    thumbnail: Optional[str]
    uploader: Optional[str]
    extractor: str  # youtube, vimeo, etc.

    @property
    def duration_str(self) -> str:
        """Format duration as HH:MM:SS or MM:SS."""
        hours, remainder = divmod(self.duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"


# Quality presets mapping to yt-dlp format strings
QUALITY_PRESETS = {
    "best": "bestvideo+bestaudio/best",
    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "audio": "bestaudio/best",
}


def get_ffmpeg_path() -> Optional[str]:
    """Get FFmpeg path, handling PyInstaller bundling."""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = Path(__file__).parent.parent.parent

    # Platform-specific binary name
    binary_name = 'ffmpeg.exe' if sys.platform == 'win32' else 'ffmpeg'
    ffmpeg = Path(base_path) / binary_name
    
    if ffmpeg.exists():
        logger.debug('Found bundled ffmpeg at: %s', ffmpeg.parent)
        return str(ffmpeg.parent)

    logger.debug('Bundled ffmpeg not found, using system PATH')
    return None  # Let yt-dlp find it in PATH


class Downloader:
    """Video downloader using yt-dlp."""

    def __init__(self):
        self.ffmpeg_location = get_ffmpeg_path()
        self._cookie_file_missing = False  # Track for error messages
        self.js_runtime_available = check_js_runtime_available()

    def _get_base_opts(self) -> dict:
        """Get base yt-dlp options."""
        opts = {
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 30,
            'retries': 10,
            'fragment_retries': 10,
            'remote_components': ['ejs:github'],
            'concurrent_fragment_downloads': 4,
            'legacy_server_connect': True,  # Fix SSL issues on macOS
            # Enable all JS runtimes for YouTube POT/JSC challenge solving
            # Default yt-dlp only tries Deno — we want any available runtime
            'js_runtimes': {
                'deno': {},
                'node': {},
                'bun': {},
                'quickjs': {},
            },
            # Fix BUG-01: Sanitize filenames for Windows compatibility
            # Handles invalid chars (?*"<>|:/\), reserved names (CON, PRN), path limits
            'windowsfilenames': True,
        }
        
        # Add cookies if configured (FEAT-01)
        # Priority: cookie file (if exists) > browser extraction
        cookie_file = config_manager.get('cookie_file_path', '')
        cookie_browser = config_manager.get('cookie_browser', '')
        self._cookie_file_missing = False  # Track for better error messages
        
        # Only use cookie file if it actually exists
        if cookie_file and os.path.exists(cookie_file):
            logger.debug('Using cookie file: %s', cookie_file)
            opts['cookiefile'] = cookie_file
        elif cookie_browser:
            # Browser extraction as fallback or primary if no file
            logger.debug('Using browser cookies: %s', cookie_browser)
            opts['cookiesfrombrowser'] = (cookie_browser,)
        elif cookie_file:
            # Cookie file was configured but doesn't exist
            logger.warning('Cookie file not found: %s', cookie_file)
            self._cookie_file_missing = True
        
        if self.ffmpeg_location:
            opts['ffmpeg_location'] = self.ffmpeg_location
        return opts

    def get_info(self, url: str) -> VideoInfo:
        """Extract video information without downloading."""
        logger.info('Getting video info: %s', url[:80])
        opts = self._get_base_opts()

        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                info = ydl.sanitize_info(info)

                logger.info('Video info retrieved: %s (duration: %s)', info.get('title', 'Unknown')[:50], info.get('duration', 0))
                return VideoInfo(
                    url=url,
                    title=info.get('title', 'Unknown'),
                    duration=info.get('duration', 0) or 0,
                    thumbnail=info.get('thumbnail'),
                    uploader=info.get('uploader'),
                    extractor=info.get('extractor', 'unknown'),
                )
            except ExtractorError as e:
                logger.error('Extractor error for %s: %s', url[:50], e)
                raise DownloaderError(self._translate_error(e))
            except DownloadError as e:
                logger.error('Download error for %s: %s', url[:50], e)
                raise DownloaderError(self._translate_error(e))
            except Exception as e:
                logger.exception('Failed to get video info for %s', url[:50])
                raise DownloaderError(self._translate_error(e))

    def download(
        self,
        url: str,
        output_path: str,
        quality: str = "best",
        progress_callback: Optional[Callable[[int, float, str], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
        info_callback: Optional[Callable[[VideoInfo], None]] = None,
    ) -> str:
        """
        Download video.

        Args:
            url: Video URL
            output_path: Directory to save to
            quality: Quality preset key
            progress_callback: Callback(percent, speed_mbps, status)
            cancel_check: Returns True when the download should be aborted;
                raises DownloadCancelled out of this method
            info_callback: Called once with VideoInfo as soon as extraction
                completes (before the actual download starts)

        Returns:
            Path to downloaded file
        """
        opts = self._get_base_opts()
        opts['format'] = QUALITY_PRESETS.get(quality, QUALITY_PRESETS['best'])
        opts['overwrites'] = True

        # Filename template with quality
        if quality == 'audio':
            opts['outtmpl'] = os.path.join(output_path, '%(title)s [audio].%(ext)s')
            opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            opts['outtmpl'] = os.path.join(output_path, '%(title)s [%(height)sp].%(ext)s')
            opts['merge_output_format'] = 'mp4'

        downloaded_file = None
        last_logged_milestone = 0
        info_emitted = False

        def progress_hook(d):
            nonlocal downloaded_file, last_logged_milestone, info_emitted

            if cancel_check and cancel_check():
                raise DownloadCancelled('Cancelled by user')

            # First hook fires right after extraction — hooks run separately
            # for video and audio streams, so emit info only once
            if info_callback and not info_emitted:
                info_emitted = True
                info = d.get('info_dict') or {}
                info_callback(VideoInfo(
                    url=url,
                    title=info.get('title', 'Unknown'),
                    duration=info.get('duration', 0) or 0,
                    thumbnail=info.get('thumbnail'),
                    uploader=info.get('uploader'),
                    extractor=info.get('extractor', 'unknown'),
                ))

            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                speed = d.get('speed') or 0

                if total > 0:
                    percent = int(downloaded / total * 100)
                    speed_mbps = speed / 1_000_000  # Convert to MB/s
                    if progress_callback:
                        progress_callback(percent, speed_mbps, 'downloading')
                    
                    # Only log at milestones to avoid log spam
                    for milestone in (25, 50, 75, 100):
                        if percent >= milestone and last_logged_milestone < milestone:
                            logger.debug('Download progress: %d%% for %s', percent, url[:50])
                            last_logged_milestone = milestone
                            break

            elif d['status'] == 'finished':
                downloaded_file = d.get('filename')
                if progress_callback:
                    progress_callback(100, 0, 'processing')
                logger.debug('Download progress: 100%% for %s', url[:50])

        opts['progress_hooks'] = [progress_hook]

        if cancel_check:
            # match_filter runs after extraction, before the download starts —
            # covers the cancellation window during the extraction phase,
            # where progress hooks are not yet called
            def cancel_filter(info_dict, *, incomplete=False):
                if cancel_check():
                    raise DownloadCancelled('Cancelled by user')
                return None

            opts['match_filter'] = cancel_filter

        logger.info('Starting download: %s (quality: %s)', url[:80], quality)

        with yt_dlp.YoutubeDL(opts) as ydl:
            collector = FinalPathCollector(ydl)
            ydl.add_post_processor(collector, when='after_move')
            try:
                if cancel_check and cancel_check():
                    raise DownloadCancelled('Cancelled by user')
                ydl.download([url])
                if progress_callback:
                    progress_callback(100, 0, 'completed')
                final_path = collector.filepath or downloaded_file or output_path
                logger.info('Download completed: %s', final_path)
                return final_path
            except DownloadCancelled:
                logger.info('Download cancelled: %s', url[:50])
                raise
            except DownloadError as e:
                logger.error('Download error for %s: %s', url[:50], e)
                raise DownloaderError(self._translate_error(e))
            except Exception as e:
                logger.exception('Unexpected download error for %s', url[:50])
                raise DownloaderError(self._translate_error(e))

    def _translate_error(self, error: Exception) -> str:
        """Translate yt-dlp errors to user-friendly messages."""
        msg = str(error).lower()

        # Special case: format error when cookie file was configured but not found
        # This often happens when config.json has a path from a different OS
        if 'requested format is not available' in msg and getattr(self, '_cookie_file_missing', False):
            return tr('err_cookie_file_missing')

        # Special case: format error likely caused by missing JS runtime
        if 'requested format is not available' in msg and not getattr(self, 'js_runtime_available', True):
            return tr('err_no_js_runtime_install')

        # Special case: Vimeo revoked the anonymous API clients yt-dlp ships with,
        # so every anonymous extraction fails with 401 until yt-dlp is updated.
        # The 'macos'/'oauth token' wording is the yt-dlp API client name, not the OS.
        if 'vimeo' in msg and ('401' in msg or 'unauthorized' in msg or 'oauth token' in msg):
            return tr('err_vimeo_auth')

        # Check against known patterns
        for pattern, message_key in ERROR_PATTERNS:
            if pattern in msg:
                return tr(message_key)

        # Fallback: Clean up the original message
        return self._clean_error_message(str(error))
    
    def _clean_error_message(self, msg: str) -> str:
        """Remove technical details and wiki links from error message."""
        # Remove GitHub/wiki URLs
        msg = re.sub(r'https?://[^\s]+', '', msg)
        # Remove "ERROR:" prefixes
        msg = re.sub(r'^ERROR:\s*', '', msg, flags=re.IGNORECASE)
        # Remove yt-dlp technical prefixes
        msg = re.sub(r'\[[\w\.-]+\]\s*', '', msg)
        # Collapse whitespace
        msg = re.sub(r'\s+', ' ', msg).strip()
        # Truncate if too long
        if len(msg) > 200:
            msg = msg[:197] + '...'
        return msg if msg else tr('err_download_failed')


class DownloaderError(Exception):
    """Custom exception for download errors."""
    pass
