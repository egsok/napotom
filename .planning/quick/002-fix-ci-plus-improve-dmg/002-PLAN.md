---
phase: 002-fix-ci-plus-improve-dmg
plan: 002
type: execute
wave: 1
depends_on: []
files_modified: [.github/workflows/release.yml]
autonomous: true
user_setup: []

must_haves:
  truths:
    - "macOS CI installs sevenzip explicitly"
    - "DMG includes Applications shortcut (drag-to-install)"
    - "DMG has custom icon and layout"
  artifacts:
    - path: ".github/workflows/release.yml"
      contains: "brew install sevenzip create-dmg"
    - path: ".github/workflows/release.yml"
      contains: "create-dmg"
  key_links: []
---

<objective>
Stabilize macOS CI builds and upgrade DMG creation to a professional drag-and-drop installer.

Purpose: Fix potential CI failures due to missing tools and improve user installation experience on macOS.
Output: Updated release.yml workflow.
</objective>

<execution_context>
@~/.config/opencode/get-shit-done/workflows/execute-plan.md
@~/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.github/workflows/release.yml
@build_mac.spec
</context>

<tasks>

<task type="auto">
  <name>Task 1: Fix CI and Upgrade DMG</name>
  <files>.github/workflows/release.yml</files>
  <action>
    Update the `build-macos` job in `release.yml`:

    1.  **Install Dependencies:** Update "Install dependencies" or add a new step to install system tools:
        ```bash
        brew install sevenzip create-dmg
        ```
        (This ensures `7z` is available for ffmpeg extraction and `create-dmg` for installer creation)

    2.  **Upgrade DMG Creation:** Replace the existing `hdiutil` step with `create-dmg` to generate a professional installer with:
        -   Volume name "VideoDownloader2"
        -   Volume icon from `assets/icon.icns`
        -   Drag-and-drop link to `/Applications`
        -   Clean layout (window size 600x300)

        **Command to use:**
        ```bash
        create-dmg \
          --volname "VideoDownloader2" \
          --volicon "assets/icon.icns" \
          --window-pos 200 120 \
          --window-size 600 300 \
          --icon-size 100 \
          --icon "VideoDownloader2.app" 175 120 \
          --hide-extension "VideoDownloader2.app" \
          --app-drop-link 425 120 \
          "VideoDownloader2-macOS.dmg" \
          "dist/VideoDownloader2.app"
        ```

    3.  **Cleanup:** Ensure the step `Upload artifact` uploads the new `VideoDownloader2-macOS.dmg`.
  </action>
  <verify>
    Check file content implies:
    - `brew install` includes `sevenzip` and `create-dmg`
    - `hdiutil` command is replaced/augmented by `create-dmg`
  </verify>
  <done>
    CI workflow updated to use reliable tools and produce professional DMGs.
  </done>
</task>

</tasks>

<verification>
Manual run of GitHub Action (triggered by push) will confirm success.
</verification>

<success_criteria>
- CI workflow file updated
- macOS build step includes create-dmg
</success_criteria>

<output>
After completion, create `.planning/phases/002-fix-ci-plus-improve-dmg/002-002-SUMMARY.md`
</output>
