# Codebase Structure

**Analysis Date:** 2026-02-01

## Directory Layout

```
video-downloader2/
├── src/                    # Application source code
│   ├── main.py            # Application entry point
│   ├── __init__.py        # Package marker
│   ├── core/              # Business logic layer
│   │   ├── __init__.py    # Package marker
│   │   ├── downloader.py  # yt-dlp wrapper
│   │   ├── queue.py       # Download queue management
│   │   └── updater.py     # yt-dlp update management
│   ├── ui/                # User interface layer
│   │   ├── __init__.py    # Package marker
│   │   ├── main_window.py # Main application window
│   │   ├── settings_dialog.py # Settings modal dialog
│   │   ├── styles.py      # Qt stylesheet and colors
│   │   └── widgets/       # Reusable UI components
│   │       ├── __init__.py
│   │       └── queue_item_widget.py # Download item display
│   └── utils/             # Utilities layer
│       ├── __init__.py    # Package marker
│       ├── config.py      # Configuration management
│       ├── notifications.py # Toast notifications & sounds
│       └── helpers.py     # Misc helper functions
├── assets/                # Static resources
│   ├── icon.ico          # Application icon
│   └── sounds/           # Audio files
│       └── complete.wav  # Download completion sound
├── scripts/              # Build and automation scripts
│   └── build.py         # PyInstaller build script
├── docs/                 # Documentation
│   └── plans/           # Planning documents
├── build/               # PyInstaller build artifacts (generated)
├── dist/                # Distribution output (generated)
├── .venv/               # Python virtual environment
├── .github/             # GitHub configuration
│   └── workflows/       # CI/CD workflows
├── .claude/             # Claude AI configuration
├── .planning/           # Project planning docs
│   └── codebase/        # Codebase analysis docs
├── build.spec           # PyInstaller configuration
├── requirements.txt     # Python dependencies
├── README.md           # Project documentation
└── .gitignore          # Git ignore rules
```

## Directory Purposes

**`src/`:**
- Purpose: All application source code
- Contains: Python modules organized by layer (core, ui, utils)
- Key files: `main.py` (entry point)

**`src/core/`:**
- Purpose: Business logic independent of UI framework
- Contains: Downloader, queue management, updater
- Key files: `downloader.py` (yt-dlp wrapper), `queue.py` (state management)

**`src/ui/`:**
- Purpose: PyQt6 user interface components
- Contains: Windows, dialogs, widgets, stylesheets
- Key files: `main_window.py`, `styles.py`

**`src/ui/widgets/`:**
- Purpose: Reusable UI components
- Contains: Custom Qt widgets for specific features
- Key files: `queue_item_widget.py`

**`src/utils/`:**
- Purpose: Cross-cutting utilities used by all layers
- Contains: Configuration, notifications, helpers
- Key files: `config.py`, `notifications.py`

**`assets/`:**
- Purpose: Static resources bundled with application
- Contains: Icons, sounds
- Key files: `icon.ico`, `sounds/complete.wav`

**`scripts/`:**
- Purpose: Automation and build scripts
- Contains: Build helpers
- Key files: `build.py`

## Key File Locations

**Entry Points:**
- `src/main.py`: Application main entry point
- `build.spec`: PyInstaller build configuration

**Configuration:**
- `requirements.txt`: Python package dependencies
- `build.spec`: PyInstaller bundling configuration
- `src/utils/config.py`: Runtime configuration management

**Core Logic:**
- `src/core/downloader.py`: Video downloading via yt-dlp
- `src/core/queue.py`: Download queue and worker management
- `src/core/updater.py`: yt-dlp version checking and updates

**UI Components:**
- `src/ui/main_window.py`: Primary application window
- `src/ui/settings_dialog.py`: Settings modal
- `src/ui/styles.py`: Color palette and Qt stylesheet
- `src/ui/widgets/queue_item_widget.py`: Download item display widget

**Utilities:**
- `src/utils/config.py`: JSON config persistence
- `src/utils/notifications.py`: System notifications and sounds
- `src/utils/helpers.py`: OS utilities (open folder)

**Testing:**
- No dedicated test files present

## Naming Conventions

**Files:**
- snake_case for all Python files: `main_window.py`, `queue_item_widget.py`
- Descriptive names matching primary class: `downloader.py` contains `Downloader` class

**Directories:**
- lowercase: `core/`, `ui/`, `utils/`, `widgets/`
- Layer-based organization at top level
- Feature-based for nested directories (e.g., `widgets/`)

**Classes:**
- PascalCase: `MainWindow`, `DownloadQueue`, `QueueItemWidget`
- Suffix conventions: `*Dialog` for modals, `*Widget` for Qt widgets, `*Worker` for QRunnable tasks

**Functions:**
- snake_case: `get_info()`, `_on_add_clicked()`, `_setup_ui()`
- Private methods prefixed with underscore: `_connect_signals()`, `_translate_error()`

**Constants:**
- SCREAMING_SNAKE_CASE: `QUALITY_PRESETS`, `COLORS`, `STYLESHEET`

## Where to Add New Code

**New Feature (e.g., playlist support):**
- Primary code: Add extractor logic to `src/core/downloader.py`
- Queue changes: Update `src/core/queue.py` with new item types
- UI changes: Update `src/ui/main_window.py` or create new widget in `src/ui/widgets/`

**New Component/Module:**
- Core business logic: `src/core/new_module.py`
- UI component: `src/ui/widgets/new_widget.py`
- Update relevant `__init__.py` if needed for exports

**New UI Dialog:**
- Implementation: `src/ui/new_dialog.py`
- Follow `settings_dialog.py` as template
- Import from `main_window.py` when needed

**New Utility:**
- Shared helpers: `src/utils/helpers.py` (add to existing)
- New utility module: `src/utils/new_utility.py`

**New Asset:**
- Icons: `assets/icon.ico` (update build.spec if new files)
- Sounds: `assets/sounds/`
- Update `build.spec` datas list for PyInstaller bundling

## Special Directories

**`.venv/`:**
- Purpose: Python virtual environment
- Generated: Yes (by `python -m venv .venv`)
- Committed: No

**`build/`:**
- Purpose: PyInstaller build artifacts
- Generated: Yes (by `pyinstaller build.spec`)
- Committed: No

**`dist/`:**
- Purpose: Final distribution binaries
- Generated: Yes (by `pyinstaller build.spec`)
- Committed: No

**`__pycache__/`:**
- Purpose: Python bytecode cache
- Generated: Yes (by Python interpreter)
- Committed: No

**`.planning/codebase/`:**
- Purpose: Codebase analysis documents for AI tooling
- Generated: No (manually maintained)
- Committed: Yes

---

*Structure analysis: 2026-02-01*
