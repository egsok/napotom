# Project State: Video Downloader 2

## Project Reference

**Core Value:** Downloads must work reliably — users paste a URL, it downloads.

**Current Focus:** Bug fix and stabilization milestone — fix 4 bugs, add logging, improve error UX, add cookie import.

**Key Files:**
- `src/core/downloader.py` — yt-dlp wrapper, error translation
- `src/core/queue.py` — Download queue and worker threads
- `src/core/updater.py` — yt-dlp version detection and updates
- `src/utils/config.py` — Configuration management
- `src/main.py` — App entry point
- `build.spec` — PyInstaller configuration

---

## Current Position

**Phase:** 1 of 3 — Logging Foundation
**Plan:** Not yet created
**Status:** Awaiting planning

```
[░░░░░░░░░░░░░░░░░░░░] 0% — Phase 1 not started
```

---

## Performance Metrics

| Metric | Value |
|--------|-------|
| Requirements (v1) | 7 |
| Completed | 0 |
| Phases | 3 |
| Current Phase | 1 |

---

## Accumulated Context

### Decisions Made

| Decision | Rationale | Date |
|----------|-----------|------|
| Logging first | Need visibility into errors before fixing them | 2026-02-01 |
| 3 phases for 7 requirements | Natural clustering: foundation → bugs → UX | 2026-02-01 |

### Architecture Notes

- Layered MVC: UI → Core → Utils
- Qt signals/slots for thread-safe communication
- QThreadPool for background downloads
- ConfigManager singleton for settings
- No logging currently — console output only (suppressed in production)

### Technical Debt

- No logging system (STAB-02 will fix)
- yt-dlp errors exposed raw to users (STAB-01 will fix)

### TODOs

_None yet — planning not started_

### Blockers

_None identified_

---

## Session Continuity

### Last Session

_New project — no previous sessions_

### Handoff Notes

Ready to start Phase 1 planning. Key considerations:
- Python logging module is the obvious choice
- Log location should be `%APPDATA%/VideoDownloader2/logs/`
- Need to decide on rotation strategy (size-based or time-based)
- Consider adding log level config option for power users

---

*State initialized: 2026-02-01*
*Last updated: 2026-02-01*
