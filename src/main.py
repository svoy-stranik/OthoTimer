import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from constants import IS_STANDALONE, PLATFORM_SYSTEM
from gui.window import WorkTimerApp
from logger import logger, set_exception_hooks
from updater import Updater
from utils import reveal_project_version


def main() -> None:
    set_exception_hooks()
    logger.info("Staring %s on %s", reveal_project_version(), PLATFORM_SYSTEM)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    updater = Updater(Path(sys.executable).resolve())
    window = WorkTimerApp(updater)
    window.show()

    if IS_STANDALONE:
        updater.cleanup()
        window.check_for_updates()

    try:
        sys.exit(app.exec())
    except Exception:
        logger.critical("Global Critical Exception", exc_info=True)


if __name__ == "__main__":
    main()
