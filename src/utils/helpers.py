"""Helper utilities."""

import subprocess
import sys
import os


def open_folder(path: str) -> None:
    """Open folder in system file manager."""
    if not path:
        return

    # Ensure path exists and get directory if it's a file
    if os.path.isfile(path):
        path = os.path.dirname(path)

    if not os.path.exists(path):
        return

    # Normalize path
    path = os.path.normpath(path)

    if sys.platform == 'darwin':  # macOS
        subprocess.run(['open', path])
    elif sys.platform == 'win32':  # Windows
        os.startfile(path)
    else:  # Linux
        subprocess.run(['xdg-open', path])
