from PyQt6.QtCore import QThread, pyqtSignal

from logger import logger


class TimerThread(QThread):
    timer_signal = pyqtSignal(int, str, bool)
    timer_finished = pyqtSignal(bool)

    def __init__(self, duration: int, label: str, *, is_break: bool = False) -> None:
        super().__init__()
        self.duration: int = duration
        self.label: str = label
        self.is_break: bool = is_break
        self._is_running: bool = True

    def run(self) -> None:
        remaining = self.duration
        while remaining > 0 and self._is_running:
            self.timer_signal.emit(remaining, self.label, self.is_break)
            self.sleep(1)
            remaining -= 1

        if remaining <= 0 and self._is_running:
            logger.debug("Emitting timer_finished signal")
            self.timer_finished.emit(self.is_break)

    def stop(self) -> None:
        self._is_running = False
        self.wait()
