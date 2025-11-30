import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from constants import IS_STANDALONE
from gui.window import WorkTimerApp
from updater import Updater


def main() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    updater = Updater(Path(sys.executable).resolve())
    window = WorkTimerApp(updater)
    window.show()

    if IS_STANDALONE:
        updater.cleanup()
        window.check_for_updates()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
