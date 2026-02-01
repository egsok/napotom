---
phase: quick
plan: 001
type: execute
wave: 1
depends_on: []
files_modified:
  - src/utils/i18n.py
  - src/utils/translations.py
  - src/utils/config.py
  - src/ui/settings_dialog.py
  - src/ui/main_window.py
  - src/ui/widgets/queue_item_widget.py
autonomous: true

must_haves:
  truths:
    - "User can switch between English and Russian in Settings"
    - "All UI text displays in the selected language"
    - "Settings dialog is larger and more spacious"
    - "Language preference persists after app restart"
  artifacts:
    - path: "src/utils/i18n.py"
      provides: "Translation function tr() and language switching"
    - path: "src/utils/translations.py"
      provides: "English and Russian translation dictionaries"
    - path: "src/ui/settings_dialog.py"
      provides: "Language selector and enlarged dialog"
  key_links:
    - from: "src/ui/*.py"
      to: "src/utils/i18n.py"
      via: "tr() function calls"
      pattern: "tr\\("
---

<objective>
Add Russian translation support with a language switcher in Settings, and improve the Settings dialog layout with a larger window and better spacing.

Purpose: Enable Russian-speaking users to use the app in their native language, and improve Settings UX as more options are added.
Output: Working bilingual UI (EN/RU) with improved Settings dialog layout.
</objective>

<execution_context>
@~/.config/Claude/get-shit-done/workflows/execute-plan.md
@~/.config/Claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@src/ui/main_window.py
@src/ui/settings_dialog.py
@src/ui/styles.py
@src/utils/config.py
@src/ui/widgets/queue_item_widget.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create i18n module with translations</name>
  <files>src/utils/i18n.py, src/utils/translations.py, src/utils/config.py</files>
  <action>
    1. Create `src/utils/translations.py` with translation dictionaries:
       - TRANSLATIONS dict with 'en' and 'ru' keys
       - Each language dict maps string keys to translated text
       - Cover ALL user-visible strings from: main_window.py, settings_dialog.py, queue_item_widget.py
       - Keys should be descriptive (e.g., "url_placeholder", "quality_best", "settings_title")
    
    2. Create `src/utils/i18n.py` with:
       - `get_current_language() -> str` - reads from config_manager
       - `set_language(lang: str)` - writes to config_manager
       - `tr(key: str) -> str` - returns translated string for current language
       - Fallback to English if key missing in current language
       - Fallback to key itself if missing in both languages (for debugging)
    
    3. Update `src/utils/config.py`:
       - Add `language: str = "en"` field to Config dataclass (after line 43)
    
    Translation strings to include (minimum):
    - Main window: "Video Downloader 2", "Paste video URL here...", "Quality:", "Save to:", "Change", "QUEUE", "Paste a video URL and click + to start downloading", "Open Folder", "Settings", "Invalid URL", "Please enter a valid URL"
    - Quality options: "Best", "1080p", "720p", "Audio only"
    - Settings dialog: "Settings", "Download Settings", "Download Path:", "Browse...", "Default Quality:", "Parallel Downloads:", "Preferences", "Enable notifications", "Enable sound", "Check for updates on startup", "yt-dlp", "Version:", "Check Now", "Cookies (for age-restricted videos)", "Required for age-restricted...", "Cookies file:", "No file selected", "How to export cookies?", "Browser:", "None", "Test Import", "Logging", "Log file:", "Not configured", "Open Folder", "Cancel", "Save"
    - Cookie help dialog: "How to Export Cookies", "Export Cookies from Chrome", all step text, "Open Extension Page", "Close"
    - Update messages: "Checking...", "Update Available", "Up to Date", "Update Complete", "Update Failed"
    - Queue item: status strings (Pending, Downloading, Complete, Error, Cancelled)
  </action>
  <verify>
    - `python -c "from src.utils.i18n import tr, get_current_language; print(tr('settings_title'))"` returns "Settings"
    - `python -c "from src.utils.translations import TRANSLATIONS; print(len(TRANSLATIONS['ru']))"` shows 40+ keys
  </verify>
  <done>i18n module exists with tr() function, translations.py has EN/RU dictionaries with all UI strings, config has language field</done>
</task>

<task type="auto">
  <name>Task 2: Integrate translations into UI and add language switcher</name>
  <files>src/ui/settings_dialog.py, src/ui/main_window.py, src/ui/widgets/queue_item_widget.py</files>
  <action>
    1. Update `src/ui/settings_dialog.py`:
       - Import: `from utils.i18n import tr, get_current_language, set_language`
       - Increase dialog size: change `setMinimumWidth(450)` to `setMinimumSize(550, 700)`
       - Add "Language" section as FIRST group box (before Download Settings):
         - QGroupBox with same styling as other groups
         - QComboBox with items: "English", "Russian" (display names)
         - Store language codes internally: 'en', 'ru'
         - Connect to handler that calls set_language() and shows restart hint
         - Add QLabel below: "Restart app to apply language change" (initially hidden, show when changed)
       - Replace ALL hardcoded strings with tr() calls:
         - Window title: `self.setWindowTitle(tr("settings_title"))`
         - Group titles: `QGroupBox(tr("download_settings"))`
         - Labels, buttons, tooltips, etc.
       - Increase spacing in download_layout: `setSpacing(16)` (was 12)
       - Increase group box margins: `setContentsMargins(20, 24, 20, 20)` (was 16, 20, 16, 16)
    
    2. Update `src/ui/main_window.py`:
       - Import: `from utils.i18n import tr`
       - Replace ALL hardcoded strings with tr() calls:
         - Window title, placeholder text, labels, buttons, messages
         - Quality combo items: use tr("quality_best"), tr("quality_1080p"), etc.
       - Update _get_quality_display and _get_quality_key to use translated strings
    
    3. Update `src/ui/widgets/queue_item_widget.py`:
       - Import: `from utils.i18n import tr`
       - Replace status display strings with tr() calls
       - Any button text or tooltips
  </action>
  <verify>
    - App launches without errors: `python -m src.main`
    - Settings dialog shows Language section at top
    - Changing language shows restart hint
    - All visible text in Settings uses tr() (grep should find tr( calls, not hardcoded strings)
  </verify>
  <done>All UI files use tr() for user-visible strings, Settings has language switcher, dialog is larger with better spacing</done>
</task>

<task type="auto">
  <name>Task 3: Test and verify translations work</name>
  <files>src/utils/config.py</files>
  <action>
    1. Manual verification steps (document in summary):
       - Launch app with default English
       - Open Settings, verify Language dropdown shows "English" selected
       - Verify Settings dialog is noticeably larger (~550x700 vs old ~450x600)
       - Verify spacing between elements is comfortable
       - Change language to Russian, verify restart hint appears
       - Close and reopen app
       - Verify all UI text is now in Russian
       - Verify Settings shows "Russian" selected
       - Open Settings -> all group titles, labels, buttons in Russian
       - Change back to English, restart, verify English restored
    
    2. Fix any missing translations discovered during testing:
       - Check console for any tr() key-not-found warnings
       - Add missing keys to translations.py
    
    3. Ensure config.json saves language preference:
       - Check %APPDATA%/VideoDownloader2/config.json contains "language": "ru" after switching
  </action>
  <verify>
    - `python -c "from src.utils.config import config_manager; config_manager.set('language', 'ru'); print(config_manager.get('language'))"` returns 'ru'
    - App runs in both languages without errors
  </verify>
  <done>Language switching works end-to-end, config persists preference, all UI text translates correctly in both EN and RU</done>
</task>

</tasks>

<verification>
1. App launches without import errors
2. Settings dialog is larger (550x700 minimum)
3. Language selector appears in Settings as first section
4. Switching language and restarting shows translated UI
5. All major UI strings have Russian translations
6. Language preference persists in config.json
</verification>

<success_criteria>
- [ ] tr() function works and returns correct translations
- [ ] Russian translations exist for all user-visible strings
- [ ] Settings dialog has Language section with EN/RU options
- [ ] Settings dialog is larger (550x700) with better spacing
- [ ] Language preference saved to config and persists across restarts
- [ ] UI displays correctly in both English and Russian
</success_criteria>

<output>
After completion, create `.planning/quick/001-localization-ui-improvements/001-SUMMARY.md`
</output>
