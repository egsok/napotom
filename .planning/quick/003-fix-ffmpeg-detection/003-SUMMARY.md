---
phase: quick-003
plan: 003
subsystem: core
tags: [ffmpeg, cross-platform, build]
requires: []
provides: [platform-agnostic-ffmpeg]
affects: [build-system]
tech-stack:
  added: []
  patterns: [conditional-bundling]
key-files:
  created: []
  modified:
    - src/core/downloader.py
    - build.spec
metrics:
  duration: "5 mins"
  completed: "2026-02-01"
---

# Quick Task 003: Fix FFmpeg Detection Summary

Implemented platform-aware FFmpeg path detection and bundling to support macOS/Linux.

## Tasks Completed

| Task | Description | Status |
| :--- | :--- | :--- |
| **1** | **Platform-aware ffmpeg detection**<br>Updated `get_ffmpeg_path` to handle 'ffmpeg' vs 'ffmpeg.exe' based on `sys.platform`. Verified with mock tests. | ✅ Completed |
| **2** | **Platform-aware binary bundling**<br>Updated `build.spec` to conditionally include correct binary names. Verified with mock PyInstaller environment. | ✅ Completed |

## Deviations from Plan

None.

## Authentication Gates

None.

## Decisions Made

- **Runtime Detection**: Used `sys.platform` check at runtime to determine binary name.
- **Build-time Detection**: Used `sys.platform` in `build.spec` to determine which binaries to bundle.
