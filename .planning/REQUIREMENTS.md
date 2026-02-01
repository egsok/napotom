# Requirements: Video Downloader 2

**Defined:** 2026-02-01
**Core Value:** Downloads must work reliably — users paste a URL, it downloads.

## v1 Requirements

Requirements for this bug fix and stabilization milestone.

### Bug Fixes

- [ ] **BUG-01**: Fix Errno 22: Invalid argument when getting video info
- [ ] **BUG-02**: Fix yt-dlp version detection showing "Not installed"
- [ ] **BUG-03**: Fix PyInstaller temp directory cleanup warning (MEI folder)
- [ ] **BUG-04**: Fix yt-dlp update loop — stops prompting after successful update

### Stability

- [ ] **STAB-01**: User sees friendly error messages instead of raw yt-dlp errors
- [x] **STAB-02**: App logs errors to file for debugging

### Features

- [ ] **FEAT-01**: User can import browser cookies for age-restricted videos

## v2 Requirements

Deferred to future release.

- **FEAT-02**: Auto-update yt-dlp in background
- **FEAT-03**: Download history with search
- **FEAT-04**: Playlist support with selective downloads

## Out of Scope

| Feature | Reason |
|---------|--------|
| New UI features | Focus on stability first |
| Linux/macOS fixes | Windows-only for now |
| Browser extension | Separate project |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| STAB-02 | Phase 1 | Complete |
| BUG-01 | Phase 2 | Pending |
| BUG-02 | Phase 2 | Pending |
| BUG-03 | Phase 2 | Pending |
| BUG-04 | Phase 2 | Pending |
| STAB-01 | Phase 3 | Pending |
| FEAT-01 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 7 total
- Mapped to phases: 7 ✓
- Unmapped: 0

---
*Requirements defined: 2026-02-01*
*Last updated: 2026-02-01 after initial definition*
