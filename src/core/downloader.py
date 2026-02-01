"""yt-dlp wrapper for video downloading."""

import logging
import os
import sys
from dataclasses import dataclass
from typing import Optional, Callable, List
from pathlib import Path

import yt_dlp
from yt_dlp.utils import DownloadError, ExtractorError

logger = logging.getLogger(__name__)


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
        # Running as bundled exe
        base_path = sys._MEIPASS
    else:
        # Running as script - check project root
        base_path = Path(__file__).parent.parent.parent

    ffmpeg = Path(base_path) / 'ffmpeg.exe'
    if ffmpeg.exists():
        return str(ffmpeg.parent)

    return None  # Let yt-dlp find it in PATH


class Downloader:
    """Video downloader using yt-dlp."""

    def __init__(self):
        self.ffmpeg_location = get_ffmpeg_path()

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
        }
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
            except Exception as e:
                logger.exception('Failed to get video info for %s', url[:50])
                raise DownloaderError(f"Failed to get video info: {e}")

    def download(
        self,
        url: str,
        output_path: str,
        quality: str = "best",
        progress_callback: Optional[Callable[[int, float, str], None]] = None,
    ) -> str:
        """
        Download video.

        Args:
            url: Video URL
            output_path: Directory to save to
            quality: Quality preset key
            progress_callback: Callback(percent, speed_mbps, status)

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

        def progress_hook(d):
            nonlocal downloaded_file, last_logged_milestone

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
        logger.info('Starting download: %s (quality: %s)', url[:80], quality)

        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                ydl.download([url])
                if progress_callback:
                    progress_callback(100, 0, 'completed')
                logger.info('Download completed: %s', downloaded_file or output_path)
                return downloaded_file or output_path
            except DownloadError as e:
                logger.error('Download error for %s: %s', url[:50], e)
                raise DownloaderError(self._translate_error(e))
            except Exception as e:
                logger.exception('Unexpected download error for %s', url[:50])
                raise DownloaderError(f"Download failed: {e}")

    def _translate_error(self, error: Exception) -> str:
        """Translate yt-dlp errors to user-friendly messages."""
        msg = str(error).lower()

        if 'video unavailable' in msg or 'private video' in msg:
            return "Video unavailable or private"
        elif 'sign in' in msg or 'age' in msg:
            return "Video requires age verification"
        elif 'geo' in msg or 'not available in your country' in msg:
            return "Video not available in your region"
        elif '403' in msg:
            return "Access denied to video"
        elif '404' in msg:
            return "Video not found"
        elif '429' in msg:
            return "Too many requests, try again later"
        elif 'ffmpeg' in msg:
            return "FFmpeg required but not found"
        else:
            return str(error)


class DownloaderError(Exception):
    """Custom exception for download errors."""
    pass
