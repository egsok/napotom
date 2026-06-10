"""Tests for Downloader._translate_error and ERROR_PATTERNS."""

import pytest

from core.downloader import Downloader, ERROR_PATTERNS


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
