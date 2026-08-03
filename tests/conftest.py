"""Pytest configuration: make src/ importable and provide a Qt app."""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


@pytest.fixture(scope="session")
def qapp():
    """Offscreen QApplication for tests touching QObject signals or widgets.

    A QCoreApplication is not enough: constructing any widget under one aborts
    the process, and a session-scoped app is shared by every test that asks.
    """
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    return app
