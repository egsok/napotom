import sys
from PyQt6.QtWidgets import QApplication

from ui.styles import STYLESHEET
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
