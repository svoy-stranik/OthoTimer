import webbrowser

from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QWidget,
)

from constants import (
    BUTTON_SMALL_SIZE,
    TELEGRAM_URL,
)
from schema import DaySummary


class DaySummaryDialog(QMessageBox):
    def __init__(self, summary: DaySummary, parent: QWidget | None = None):
        super().__init__(parent)
        self.summary = summary
        self.setWindowTitle("Итоги дня")
        self.setIcon(QMessageBox.Icon.Information)
        self._setup_ui()

    def _setup_ui(self) -> None:
        lunch_periods_text = "\n".join(
            [f"  • {period.start_time} - {period.end_time}" for period in self.summary.lunch_periods if period.end_time]
        )

        result_text = (
            f"Итоги дня:\n\n"
            f"Работал: {self.summary.work_hours} ч {self.summary.work_minutes} мин\n"
            f"Коротких перерывов: {self.summary.break_count}\n"
            f"Обедов: {self.summary.lunch_count}\n"
        )

        if self.summary.lunch_periods:
            result_text += f"Время обедов:\n{lunch_periods_text}\n\n"
        else:
            result_text += "\n"

        result_text += "Сделано Странником.\nНадеюсь, вы нашли сегодня немного времени для молитвы!"
        self.setText(result_text)

        link_widget = QWidget()
        link_layout = QHBoxLayout(link_widget)
        link_layout.setContentsMargins(0, 10, 0, 0)

        link_label = QLabel(TELEGRAM_URL)
        link_label.setStyleSheet("font-weight: bold; color: #0066cc;")
        link_layout.addWidget(link_label)

        copy_btn = QPushButton("Copy")
        copy_btn.setFixedSize(*BUTTON_SMALL_SIZE)
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d; color: white;
                border: none; border-radius: 3px; font-size: 10px;
            }
            QPushButton:hover { background-color: #5a6268; }
        """)
        copy_btn.clicked.connect(self._copy_to_clipboard)
        link_layout.addWidget(copy_btn)

        open_btn = QPushButton("Open")
        open_btn.setFixedSize(*BUTTON_SMALL_SIZE)
        open_btn.setStyleSheet("""
            QPushButton {
                background-color: #0088cc; color: white;
                border: none; border-radius: 3px; font-size: 10px;
            }
            QPushButton:hover { background-color: #006699; }
        """)
        open_btn.clicked.connect(self._open_channel)
        link_layout.addWidget(open_btn)

        link_layout.addStretch()
        layout = self.layout()
        if layout is None:
            raise RuntimeError("No Layout!")

        layout.addWidget(link_widget, layout.rowCount(), 0, 1, layout.columnCount())  # pyright: ignore[reportCallIssue, reportAttributeAccessIssue]
        self.setStandardButtons(QMessageBox.StandardButton.Ok)

    def _copy_to_clipboard(self) -> None:
        clipboard = QApplication.clipboard()
        if clipboard is None:
            raise RuntimeError("No Clipboard")
        clipboard.setText(TELEGRAM_URL)

    def _open_channel(self) -> None:
        webbrowser.open(TELEGRAM_URL)
