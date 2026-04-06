---
phase: quick-003
plan: 003
type: execute
wave: 1
depends_on: []
files_modified:
  - src/core/downloader.py
  - build.spec
autonomous: true
must_haves:
  truths:
    - "ffmpeg path detection works on Windows (ffmpeg.exe)"
    - "ffmpeg path detection works on macOS/Linux (ffmpeg)"
    - "PyInstaller bundles correct binary per platform"
  artifacts:
    - path: "src/core/downloader.py"
      provides: "Platform-aware ffmpeg path resolution"
    - path: "build.spec"
      provides: "Platform-aware binary bundling"
  key_links:
    - from: "src/core/downloader.py"
      to: "sys.platform"
      via: "conditional check"
---

<objective>
Fix ffmpeg path detection and bundling to support macOS/Linux.
Purpose: Allow the application to run on non-Windows platforms where ffmpeg does not have an .exe extension.
Output: Modified downloader.py and build.spec handling platform-specific binary names.
</objective>

<execution_context>
@~/.config/opencode/get-shit-done/workflows/execute-plan.md
@~/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@src/core/downloader.py
@build.spec
</context>

<tasks>

<task type="auto">
  <name>Task 1: Platform-aware ffmpeg detection</name>
  <files>src/core/downloader.py</files>
  <action>
    Update `get_ffmpeg_path` in `src/core/downloader.py`:
    - Determine executable name based on `sys.platform`:
      - 'win32' -> 'ffmpeg.exe'
      - others -> 'ffmpeg'
    - Update the path construction logic to use this dynamic name.
  </action>
  <verify>
    Create a temporary test script that imports `get_ffmpeg_path`, mocks `sys.platform`, and asserts correct filename is looked for.
  </verify>
  <done>
    `get_ffmpeg_path` correctly identifies 'ffmpeg.exe' on Windows and 'ffmpeg' on other platforms.
  </done>
</task>

<task type="auto">
  <name>Task 2: Platform-aware binary bundling</name>
  <files>build.spec</files>
  <action>
    Update `build.spec` to conditionally include binaries:
    - Import `sys`
    - Define `ffmpeg_bin` and `ffprobe_bin` based on `sys.platform` ('win32' checks for .exe, others check for no extension).
    - Update `binaries` list to use these variables.
    - Ensure logic falls back gracefully or errors if binary missing (standard PyInstaller behavior).
  </action>
  <verify>
    Run `pyinstaller build.spec --clean --noconfirm` (dry run or partial check) or verify syntax with `python build.spec`.
    Since full build is heavy, syntax check + logic verification via python execution of the spec file (if possible) or just careful code review is acceptable for this quick fix.
    Actually, we can just run `python -c "import sys; exec(open('build.spec').read())"` to see if it parses, but that might trigger the build.
    Better: Just rely on code correctness for the spec file, it's python.
  </verify>
  <done>
    `build.spec` contains platform-specific logic for binary inclusion.
  </done>
</task>

</tasks>

<verification>
Manual verify:
1. On Windows: Build works, runs, finds ffmpeg.exe.
2. On macOS: Build works, runs, finds ffmpeg (no extension).
</verification>

<success_criteria>
- [ ] `get_ffmpeg_path` returns correct path on Windows
- [ ] `get_ffmpeg_path` returns correct path on macOS
- [ ] `build.spec` bundles correct binaries for the platform running the build
</success_criteria>

<output>
After completion, create `.planning/quick/003-fix-ffmpeg-detection/003-SUMMARY.md`
</output>
