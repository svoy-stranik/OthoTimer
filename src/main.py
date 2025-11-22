import sys

from PyQt6.QtWidgets import QApplication

from gui.window import WorkTimerApp


def main() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    window = WorkTimerApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
