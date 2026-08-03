"""Tests for Downloader._translate_error and ERROR_PATTERNS."""

import pytest

from core.downloader import Downloader, ERROR_PATTERNS
from utils.translations import TRANSLATIONS


@pytest.fixture(autouse=True)
def english_ui(monkeypatch):
    # Error messages are localized through tr(); pin the language so the
    # assertions below test the mapping, not the user's config
    monkeypatch.setattr('utils.i18n.get_current_language', lambda: 'en')


@pytest.fixture
def downloader():
    d = Downloader.__new__(Downloader)  # Skip __init__ (ffmpeg/JS runtime probes)
    d._cookie_file_missing = False
    d.js_runtime_available = True
    return d


def test_bot_detection_maps_to_cookie_hint(downloader):
    msg = downloader._translate_error(
        Exception("ERROR: Sign in to confirm you're not a bot")
    )
    assert msg == 'YouTube requires authentication. Set up cookies in Settings.'


def test_pattern_order_most_specific_first(downloader):
    # Message matching both a cookie pattern and an HTTP-code pattern must
    # resolve to the earlier (more specific) cookie message
    msg = downloader._translate_error(
        Exception("Could not copy Chrome cookie database; HTTP Error 403")
    )
    assert 'cookies' in msg.lower()
    assert 'Access denied' not in msg


def test_cookie_file_missing_special_case(downloader):
    downloader._cookie_file_missing = True
    msg = downloader._translate_error(Exception("Requested format is not available"))
    assert msg == 'Cookie file not found. Re-import your cookies.txt file in Settings.'


def test_no_js_runtime_special_case(downloader):
    downloader.js_runtime_available = False
    msg = downloader._translate_error(Exception("Requested format is not available"))
    assert 'JavaScript runtime' in msg


def test_format_error_without_special_cases_uses_pattern(downloader):
    msg = downloader._translate_error(Exception("Requested format is not available"))
    assert msg == 'No downloadable formats found. Try setting up cookies in Settings.'


def test_fallback_cleans_technical_noise(downloader):
    msg = downloader._translate_error(
        Exception("ERROR: [youtube] Something strange happened. See https://example.com/wiki")
    )
    assert msg == 'Something strange happened. See'


def test_fallback_empty_message_gets_default(downloader):
    msg = downloader._translate_error(Exception("https://example.com/only-a-url"))
    assert msg == 'Download failed. Please try again.'


def test_all_patterns_are_lowercase():
    # _translate_error lowercases the message, so patterns must be lowercase
    # or they can never match
    for pattern, _ in ERROR_PATTERNS:
        assert pattern == pattern.lower()


def test_vimeo_401_explains_itself(downloader):
    # The real yt-dlp message names its internal API client ("macos"), which
    # reads as an OS mismatch to the user — it must never reach the UI verbatim
    msg = downloader._translate_error(Exception(
        "ERROR: [vimeo] 1214343121: Unable to download macos API JSON: "
        "HTTP Error 401: Unauthorized (caused by <HTTPError 401: Unauthorized>)"
    ))
    assert 'macos' not in msg.lower()
    assert 'Vimeo' in msg
    assert 'yt-dlp' in msg


def test_vimeo_oauth_failure_maps_to_same_hint(downloader):
    msg = downloader._translate_error(Exception(
        "ERROR: [vimeo] 1214343121: Failed to fetch macos OAuth token: HTTP Error 401: Unauthorized"
    ))
    assert 'Vimeo' in msg


def test_non_vimeo_401_stays_generic(downloader):
    # A 401 from any other site must not blame Vimeo
    msg = downloader._translate_error(Exception("ERROR: [generic] HTTP Error 401: Unauthorized"))
    assert 'Vimeo' not in msg
    assert '401' in msg


def test_every_pattern_key_is_translated():
    # A missing key makes tr() return the key itself, e.g. "err_ssl" in the UI
    keys = {key for _, key in ERROR_PATTERNS}
    keys |= {'err_cookie_file_missing', 'err_no_js_runtime_install',
             'err_vimeo_auth', 'err_download_failed'}
    for lang, table in TRANSLATIONS.items():
        missing = sorted(keys - table.keys())
        assert not missing, f'{lang} is missing: {missing}'
