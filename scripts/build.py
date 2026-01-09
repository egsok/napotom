#!/usr/bin/env python
"""Build script for VideoDownloader2."""

import subprocess
import sys
import shutil
from pathlib import Path


def main():
    root = Path(__file__).parent.parent

    # Clean previous builds
    for folder in ['build', 'dist']:
        path = root / folder
        if path.exists():
            shutil.rmtree(path)

    # Run PyInstaller
    result = subprocess.run([
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        str(root / 'build.spec'),
    ], cwd=root)

    if result.returncode == 0:
        print("\n✓ Build successful!")
        print(f"  Output: {root / 'dist' / 'VideoDownloader2.exe'}")
    else:
        print("\n✗ Build failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()
