"""Pytest configuration: make src/ importable and provide a Qt core app."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


@pytest.fixture(scope="session")
def qapp():
    """Minimal QCoreApplication for tests touching QObject signals (no GUI)."""
    from PyQt6.QtCore import QCoreApplication
    app = QCoreApplication.instance() or QCoreApplication(sys.argv)
    return app
