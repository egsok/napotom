#!/usr/bin/env python3
"""Rebuild assets/icon.ico with multi-size layers from the high-res source PNG.

Uses Pillow to generate a Windows ICO containing 7 standard sizes:
16, 24, 32, 48, 64, 128, 256 pixels — all derived from the 1024×1024 source.

Usage:
    python scripts/rebuild_icon.py
"""

import os
import sys
from pathlib import Path

from PIL import Image

# Resolve paths relative to repo root (parent of scripts/)
REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_PNG = REPO_ROOT / "assets" / "icon.iconset" / "icon_512x512@2x.png"
OUTPUT_ICO = REPO_ROOT / "assets" / "icon.ico"

# Standard Windows ICO sizes for crisp rendering at all display contexts
ICO_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def main() -> None:
    if not SOURCE_PNG.exists():
        print(f"ERROR: Source PNG not found: {SOURCE_PNG}", file=sys.stderr)
        sys.exit(1)

    src = Image.open(SOURCE_PNG)
    print(f"Source: {SOURCE_PNG.name} — {src.size[0]}×{src.size[1]} {src.mode}")

    # Ensure RGBA for proper transparency in ICO
    if src.mode != "RGBA":
        src = src.convert("RGBA")

    src.save(str(OUTPUT_ICO), format="ICO", sizes=ICO_SIZES)

    file_size = os.path.getsize(OUTPUT_ICO)
    print(f"Saved: {OUTPUT_ICO} — {file_size:,} bytes")
    print(f"Layers: {', '.join(f'{s[0]}px' for s in ICO_SIZES)}")


if __name__ == "__main__":
    main()
