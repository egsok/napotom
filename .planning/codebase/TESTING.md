# Testing Patterns

**Analysis Date:** 2026-02-01

## Test Framework

**Runner:**
- Not configured
- No pytest, unittest, or any test framework detected
- No test configuration files found

**Assertion Library:**
- Not applicable

**Run Commands:**
```bash
# No test commands available - testing not implemented
```

## Test File Organization

**Location:**
- No test files exist
- No `tests/` directory
- No `*_test.py` or `test_*.py` files

**Naming:**
- Not established

**Structure:**
- Not established

## Test Structure

**Suite Organization:**
- Not applicable - no tests exist

**Recommended Pattern (if adding tests):**
```python
# tests/test_downloader.py
import pytest
from core.downloader import Downloader, DownloaderError, VideoInfo

class TestDownloader:
    """Tests for Downloader class."""
    
    def test_get_info_returns_video_info(self, mock_yt_dlp):
        """Verify get_info returns VideoInfo dataclass."""
        downloader = Downloader()
        result = downloader.get_info("https://youtube.com/watch?v=test")
        
        assert isinstance(result, VideoInfo)
        assert result.title != ""
    
    def test_translate_error_handles_private_video(self):
        """Verify error translation for private videos."""
        downloader = Downloader()
        
        result = downloader._translate_error(Exception("private video"))
        
        assert result == "Video unavailable or private"
```

## Mocking

**Framework:** Not applicable

**Patterns:**
- Not established

**Recommended Mock Targets:**
- `yt_dlp.YoutubeDL` - external download library
- `subprocess.run` - for updater tests
- `QThreadPool` - for async operation tests
- `win10toast.ToastNotifier` - for notification tests
- File system operations via `pathlib.Path`

**What to Mock:**
- External API calls (yt-dlp, PyPI version check)
- File system operations
- System notifications
- Subprocess calls

**What NOT to Mock:**
- Dataclass creation and properties
- Pure functions like `_translate_error()`
- Signal/slot connections (test integration instead)

## Fixtures and Factories

**Test Data:**
- Not established

**Recommended Fixtures:**
```python
# conftest.py
import pytest
from core.downloader import VideoInfo

@pytest.fixture
def sample_video_info():
    """Create sample VideoInfo for testing."""
    return VideoInfo(
        url="https://youtube.com/watch?v=test",
        title="Test Video",
        duration=120,
        thumbnail="https://example.com/thumb.jpg",
        uploader="Test Channel",
        extractor="youtube",
    )

@pytest.fixture
def mock_yt_dlp(mocker):
    """Mock yt_dlp.YoutubeDL."""
    mock = mocker.patch('core.downloader.yt_dlp.YoutubeDL')
    mock.return_value.__enter__.return_value.extract_info.return_value = {
        'title': 'Test Video',
        'duration': 120,
        'thumbnail': 'https://example.com/thumb.jpg',
        'uploader': 'Test Channel',
        'extractor': 'youtube',
    }
    return mock
```

**Location:**
- Recommended: `tests/conftest.py` for shared fixtures

## Coverage

**Requirements:** Not enforced

**View Coverage:**
```bash
# Not configured - would be:
# pytest --cov=src --cov-report=html
```

## Test Types

**Unit Tests:**
- Not implemented
- Recommended scope: Individual functions/methods
- Focus on: `Downloader`, `ConfigManager`, error translation, dataclass properties

**Integration Tests:**
- Not implemented
- Recommended scope: Queue processing, signal/slot connections
- Focus on: `DownloadQueue` workflow, `Updater` workflow

**E2E Tests:**
- Not implemented
- Would require: PyQt testing library (pytest-qt)
- Focus on: Full download workflow via UI

## Common Patterns

**Async Testing (recommended):**
```python
# For Qt signal/slot testing with pytest-qt
def test_download_emits_progress(qtbot, download_queue):
    """Verify progress signals during download."""
    with qtbot.waitSignal(download_queue.item_updated, timeout=5000):
        download_queue.add("https://example.com/video", "best", "/tmp")
```

**Error Testing (recommended):**
```python
def test_invalid_url_raises_downloader_error():
    """Verify DownloaderError on invalid URL."""
    downloader = Downloader()
    
    with pytest.raises(DownloaderError) as exc_info:
        downloader.get_info("invalid-url")
    
    assert "Failed to get video info" in str(exc_info.value)
```

**Dataclass Testing:**
```python
def test_video_info_duration_str_hours():
    """Verify duration formatting with hours."""
    info = VideoInfo(
        url="", title="", duration=3661,
        thumbnail=None, uploader=None, extractor=""
    )
    
    assert info.duration_str == "1:01:01"
```

## Recommended Test Setup

**Install Test Dependencies:**
```bash
pip install pytest pytest-cov pytest-qt pytest-mock
```

**Create Test Structure:**
```
tests/
├── __init__.py
├── conftest.py           # Shared fixtures
├── core/
│   ├── __init__.py
│   ├── test_downloader.py
│   ├── test_queue.py
│   └── test_updater.py
├── utils/
│   ├── __init__.py
│   ├── test_config.py
│   └── test_helpers.py
└── ui/
    ├── __init__.py
    └── test_main_window.py
```

**pytest.ini Configuration:**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

## Priority Test Candidates

**High Priority (core logic):**
- `src/core/downloader.py`: `_translate_error()`, `VideoInfo.duration_str`
- `src/utils/config.py`: `ConfigManager` load/save
- `src/core/queue.py`: `QueueItem` dataclass, status transitions

**Medium Priority (error paths):**
- `DownloaderError` propagation
- Config file corruption handling
- Update failure handling

**Low Priority (UI-dependent):**
- Widget rendering
- Signal/slot integration
- Full download workflow

---

*Testing analysis: 2026-02-01*
