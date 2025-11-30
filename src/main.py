import sys
from pathlib import Path
from time import sleep

from constants import IS_STANDALONE
from updater import Updater
from utils import reveal_project_version


def update():
    if not IS_STANDALONE:
        return

    updater = Updater(Path(sys.executable).resolve())

    updater.cleanup()

    current_version = reveal_project_version()
    latest_version = updater.get_latest_version()

    if current_version >= latest_version:
        print("Up-to-date")
        return

    updater.update()


def main() -> None:
    sleep(5)
    print(sys.argv)

    update()
    print("RUN!!!")

    from PyQt6.QtWidgets import QApplication

    from gui.window import WorkTimerApp

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    window = WorkTimerApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
