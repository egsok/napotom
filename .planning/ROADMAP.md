# Roadmap: Video Downloader 2 — Bug Fix & Stabilization

**Created:** 2026-02-01
**Depth:** Standard
**Phases:** 3

## Overview

This milestone fixes critical bugs breaking core download functionality and adds stability infrastructure. Phase 1 establishes logging for debugging. Phase 2 fixes the four core bugs affecting downloads and updates. Phase 3 improves error handling and adds cookie import for restricted content.

---

## Phase 1: Logging Foundation

**Goal:** App logs all operations and errors to file for debugging.

**Dependencies:** None

**Plans:** 2 plans

Plans:
- [x] 01-01-PLAN.md — Create logger module and initialize at startup
- [x] 01-02-PLAN.md — Add logging to download operations and Settings UI

**Requirements:**
- STAB-02: App logs errors to file for debugging

**Success Criteria:**
1. App writes log file to user's AppData directory on startup
2. All download operations (start, progress, complete, error) are logged with timestamps
3. User can find log file location from Settings or Help menu
4. Log file rotates or truncates to prevent unbounded growth

---

## Phase 2: Core Bug Fixes

**Goal:** Downloads and updates work without cryptic errors.

**Dependencies:** Phase 1 (logging helps debug these fixes)

**Plans:** 2 plans

Plans:
- [x] 02-01-PLAN.md — Fix Errno 22, version detection, and MEI cleanup (BUG-01, BUG-02, BUG-03)
- [x] 02-02-PLAN.md — Fix yt-dlp update loop (BUG-04)

**Requirements:**
- BUG-01: Fix Errno 22: Invalid argument when getting video info
- BUG-02: Fix yt-dlp version detection showing "Not installed"
- BUG-03: Fix PyInstaller temp directory cleanup warning (MEI folder)
- BUG-04: Fix yt-dlp update loop — stops prompting after successful update

**Success Criteria:**
1. User can paste any valid YouTube URL and see video info without "Errno 22" errors
2. Settings dialog shows correct yt-dlp version (e.g., "2025.12.8") not "Not installed"
3. App exits cleanly without "Failed to remove temporary directory" warnings
4. After updating yt-dlp, user is not prompted to update again until a new version exists

---

## Phase 3: Error UX & Cookie Import

**Goal:** Users understand errors and can access restricted content.

**Dependencies:** Phase 2 (bugs fixed first, then UX polish)

**Plans:** 2 plans

Plans:
- [ ] 03-01-PLAN.md — Expand error translation with friendly, actionable messages
- [ ] 03-02-PLAN.md — Add browser cookie import to Settings

**Requirements:**
- STAB-01: User sees friendly error messages instead of raw yt-dlp errors
- FEAT-01: User can import browser cookies for age-restricted videos

**Success Criteria:**
1. When download fails, user sees actionable message (not raw yt-dlp output or wiki links)
2. User can select browser (Chrome, Firefox, Edge) and import cookies from Settings
3. After importing cookies, age-restricted videos download successfully
4. If cookie import fails, user sees clear explanation of what went wrong

---

## Progress

| Phase | Status | Requirements | Completed |
|-------|--------|--------------|-----------|
| 1 - Logging Foundation | ✓ Complete | 1 | 1/1 |
| 2 - Core Bug Fixes | ✓ Complete | 4 | 4/4 |
| 3 - Error UX & Cookie Import | In Progress | 2 | 0/2 |

**Total:** 5/7 requirements complete (71%)

---

*Roadmap created: 2026-02-01*
