# Architecture

**Analysis Date:** 2026-02-01

## Pattern Overview

**Overall:** Layered MVC with Qt Signals/Slots

**Key Characteristics:**
- Clean separation between UI (PyQt6), core logic, and utilities
- Event-driven communication via Qt signals/slots pattern
- Background processing via QThreadPool/QRunnable workers
- Global singletons for cross-cutting concerns (config, notifications)

## Layers

**UI Layer (`src/ui/`):**
- Purpose: User interface presentation and user interaction handling
- Location: `src/ui/`
- Contains: Main window, dialogs, widgets, stylesheet definitions
- Depends on: Core layer (queue, updater), Utils layer (config, helpers)
- Used by: Application entry point (`src/main.py`)

**Core Layer (`src/core/`):**
- Purpose: Business logic for downloading, queue management, and updates
- Location: `src/core/`
- Contains: Downloader (yt-dlp wrapper), DownloadQueue (queue management), Updater (yt-dlp updates)
- Depends on: Utils layer (config, notifications), external libs (yt-dlp)
- Used by: UI layer

**Utils Layer (`src/utils/`):**
- Purpose: Cross-cutting utilities and configuration management
- Location: `src/utils/`
- Contains: ConfigManager (JSON persistence), NotificationManager (toasts/sounds), helpers
- Depends on: Nothing (standalone utilities)
- Used by: Core layer, UI layer

**Entry Point:**
- Purpose: Application bootstrap and initialization
- Location: `src/main.py`
- Contains: QApplication setup, stylesheet application, main window creation, startup update check
- Depends on: All layers

## Data Flow

**Download Request Flow:**

1. User pastes URL in `MainWindow.url_input` and clicks add button
2. `MainWindow._on_add_clicked()` creates queue item via `DownloadQueue.add()`
3. `DownloadQueue` emits `item_added` signal, UI creates `QueueItemWidget`
4. `DownloadQueue._process_next()` starts `DownloadWorker` in thread pool
5. `DownloadWorker.run()` fetches video info, then downloads via `Downloader`
6. Worker emits progress/finished/error signals back to `DownloadQueue`
7. `DownloadQueue` emits `item_updated` signal, UI widget updates display
8. On completion, `NotificationManager` shows toast and plays sound

**Configuration Flow:**

1. User opens Settings dialog
2. `SettingsDialog._load_settings()` reads from `config_manager.get()`
3. User changes settings and clicks Save
4. `SettingsDialog._save_and_close()` calls `config_manager.set()` for each setting
5. `ConfigManager.save()` persists to JSON file at `%APPDATA%/VideoDownloader2/config.json`

**State Management:**
- Application state lives in `DownloadQueue.items` (list of `QueueItem`)
- Configuration state lives in `ConfigManager.config` (persisted to JSON)
- No global state store; each component owns its state
- Communication via Qt signals (not shared mutable state)

## Key Abstractions

**QueueItem (`src/core/queue.py`):**
- Purpose: Represents a single download task with all its state
- Examples: `src/core/queue.py` lines 24-37
- Pattern: Dataclass with status enum, progress tracking, video metadata

**Downloader (`src/core/downloader.py`):**
- Purpose: Wraps yt-dlp for video info extraction and downloading
- Examples: `src/core/downloader.py` lines 58-195
- Pattern: Facade pattern around yt-dlp, handles FFmpeg path resolution

**DownloadWorker (`src/core/queue.py`):**
- Purpose: Background task execution for downloads
- Examples: `src/core/queue.py` lines 47-95
- Pattern: QRunnable with WorkerSignals for thread-safe communication

**ConfigManager (`src/utils/config.py`):**
- Purpose: Centralized configuration with JSON persistence
- Examples: `src/utils/config.py` lines 44-79
- Pattern: Singleton with get/set interface, automatic save on set

## Entry Points

**Application Entry (`src/main.py`):**
- Location: `src/main.py`
- Triggers: `python src/main.py` or PyInstaller executable
- Responsibilities: Initialize QApplication, apply stylesheet, create MainWindow, check for updates

**PyInstaller Build (`build.spec`):**
- Location: `build.spec`
- Triggers: `pyinstaller build.spec`
- Responsibilities: Bundle application with FFmpeg binaries and assets

## Error Handling

**Strategy:** Exception translation with user-friendly messages

**Patterns:**
- `Downloader._translate_error()` converts yt-dlp exceptions to readable strings
- `DownloadWorker.run()` catches all exceptions and emits error signals
- UI layer displays errors via status labels and `QMessageBox` dialogs
- Failed downloads can be retried via `DownloadQueue.retry()`

## Cross-Cutting Concerns

**Logging:** Not implemented. Console output only (suppressed in production via PyInstaller console=False)

**Validation:** Minimal URL validation in `MainWindow._on_add_clicked()` (checks http/https prefix). Full validation delegated to yt-dlp.

**Authentication:** Not applicable. No user accounts. yt-dlp handles site-specific auth requirements.

**Threading:** QThreadPool manages download workers. Max parallel threads controlled by `config_manager.get('max_parallel_downloads')`. All cross-thread communication via Qt signals (thread-safe).

**Asset Resolution:** `get_asset_path()` in `src/main.py` and `get_assets_path()` in `src/utils/notifications.py` handle dev vs PyInstaller bundle paths.

---

*Architecture analysis: 2026-02-01*
