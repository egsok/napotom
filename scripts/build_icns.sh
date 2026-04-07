#!/usr/bin/env bash
# Build macOS .icns icon from the existing .iconset directory.
#
# REQUIRES: macOS with iconutil (ships with Xcode Command Line Tools).
# The assets/icon.iconset/ directory must contain Apple-standard sizes:
#   icon_16x16.png, icon_16x16@2x.png, icon_32x32.png, icon_32x32@2x.png,
#   icon_128x128.png, icon_128x128@2x.png, icon_256x256.png, icon_256x256@2x.png,
#   icon_512x512.png, icon_512x512@2x.png
#
# Usage:
#   ./scripts/build_icns.sh
#
# Output:
#   assets/icon.icns

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

ICONSET_DIR="$REPO_ROOT/assets/icon.iconset"
OUTPUT_ICNS="$REPO_ROOT/assets/icon.icns"

if [[ "$(uname)" != "Darwin" ]]; then
    echo "ERROR: This script requires macOS (iconutil is not available on $(uname))." >&2
    exit 1
fi

if ! command -v iconutil &>/dev/null; then
    echo "ERROR: iconutil not found. Install Xcode Command Line Tools: xcode-select --install" >&2
    exit 1
fi

if [[ ! -d "$ICONSET_DIR" ]]; then
    echo "ERROR: Iconset directory not found: $ICONSET_DIR" >&2
    exit 1
fi

echo "Converting $ICONSET_DIR → $OUTPUT_ICNS"
iconutil --convert icns "$ICONSET_DIR" --output "$OUTPUT_ICNS"

FILE_SIZE=$(stat -f%z "$OUTPUT_ICNS" 2>/dev/null || stat --printf="%s" "$OUTPUT_ICNS" 2>/dev/null)
echo "Done: $OUTPUT_ICNS ($FILE_SIZE bytes)"
