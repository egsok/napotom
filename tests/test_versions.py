"""Tests for parse_version / get_ytdlp_version from core.updater."""

from core.updater import get_ytdlp_version, parse_version


def test_parse_simple_version():
    assert parse_version("2025.12.8") == (2025, 12, 8)


def test_zero_padded_equals_unpadded():
    # "2025.12.8" and "2025.12.08" are the same release
    assert parse_version("2025.12.8") == parse_version("2025.12.08")


def test_tuple_comparison_is_numeric_not_lexicographic():
    # String comparison would say "2025.12.9" > "2025.12.10"
    assert parse_version("2025.12.9") < parse_version("2025.12.10")


def test_invalid_strings_return_none():
    assert parse_version("garbage") is None
    assert parse_version("") is None
    assert parse_version("1.2.beta") is None
    assert parse_version(None) is None


def test_get_ytdlp_version_returns_installed_version():
    import yt_dlp.version
    assert get_ytdlp_version() == yt_dlp.version.__version__
