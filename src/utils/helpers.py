"""Helper utilities."""

import subprocess
import sys
import os


def open_folder(path: str) -> None:
    """Open folder in system file manager."""
    # Ensure path exists and get directory if it's a file
    if os.path.isfile(path):
        path = os.path.dirname(path)
    
    if not os.path.exists(path):
        return
    
    if sys.platform == 'darwin':  # macOS
        subprocess.run(['open', path])
    elif sys.platform == 'win32':  # Windows
        subprocess.run(['explorer', path])
    else:  # Linux
        subprocess.run(['xdg-open', path])
