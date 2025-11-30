import webbrowser

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from constants import (
    BUTTON_SMALL_SIZE,
    TELEGRAM_URL,
)
from gui.todo_list_widget import TodoListWidget


class WorkTimerUI:
    def __init__(self, central_widget: QWidget) -> None:
        self.central_widget = central_widget
        self.layout = QVBoxLayout(central_widget)

        self.timer_label: QLabel
        self.start_button: QPushButton
        self.pause_button: QPushButton
        self.end_button: QPushButton
        self.title_label: QLabel
        self.verse_label: QLabel
        self.link_widget: QWidget
        self.todo_widget: TodoListWidget

        self._setup_ui()

    def _setup_ui(self) -> None:
        self._create_timer_label()
        self._create_buttons()
        self._create_link_widget()
        self._create_todo_widget()
        self._create_prayer_section()

    def _create_timer_label(self) -> None:
        self.timer_label = QLabel("")
        self.timer_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("margin: 20px; color: darkgreen;")
        self.layout.addWidget(self.timer_label)

    def _create_buttons(self) -> None:
        self.start_button = QPushButton("Начать рабочий день")
        self.start_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")

        self.pause_button = QPushButton("Обед (пауза)")
        self.pause_button.setEnabled(False)
        self.pause_button.setStyleSheet("QPushButton { background-color: #FF9800; color: white; }")

        self.end_button = QPushButton("Закончить день")
        self.end_button.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")

        self.layout.addWidget(self.start_button)
        self.layout.addWidget(self.pause_button)
        self.layout.addWidget(self.end_button)

    def _create_link_widget(self) -> None:
        link_container = QWidget()
        link_layout = QVBoxLayout(link_container)
        link_layout.setContentsMargins(0, 15, 0, 15)

        self.link_widget = QWidget()
        link_inner_layout = QHBoxLayout(self.link_widget)
        link_inner_layout.setContentsMargins(20, 0, 20, 0)
        link_inner_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        link_label = QLabel(TELEGRAM_URL)
        link_label.setStyleSheet("font-weight: bold; color: #0066cc;")
        link_inner_layout.addWidget(link_label)

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
        link_inner_layout.addWidget(copy_btn)

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
        link_inner_layout.addWidget(open_btn)

        link_layout.addWidget(self.link_widget)
        self.layout.addWidget(link_container)

    def _create_todo_widget(self) -> None:
        self.todo_widget = TodoListWidget()
        self.layout.addWidget(self.todo_widget)

    def _create_prayer_section(self) -> None:
        self.title_label = QLabel("Молитва Господа Нашего Иисуса Христа:")
        self.title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: red;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verse_label = QLabel()
        self.verse_label.setFont(QFont("Arial", 10))
        self.verse_label.setWordWrap(True)
        self.verse_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.verse_label.setStyleSheet("margin: 10px;")

        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.verse_label)

    def _copy_to_clipboard(self) -> None:
        clipboard = QApplication.clipboard()

        if clipboard is None:
            raise RuntimeError("Clipboard is None")

        clipboard.setText(TELEGRAM_URL)

    def _open_channel(self) -> None:
        webbrowser.open(TELEGRAM_URL)

    def update_timer_display(self, remaining: int, label: str) -> None:
        mins = remaining // 60
        secs = remaining % 60
        self.timer_label.setText(f"{label}: {mins:02d}:{secs:02d}")

    def set_verse_text(self, text: str) -> None:
        self.verse_label.setText(text)

    def hide_prayer_title(self) -> None:
        self.title_label.hide()

    def update_button_states(self, *, start_enabled: bool, pause_enabled: bool, end_enabled: bool) -> None:
        self.start_button.setEnabled(start_enabled)
        self.pause_button.setEnabled(pause_enabled)
        self.end_button.setEnabled(end_enabled)

    def set_start_button_text(self, text: str) -> None:
        self.start_button.setText(text)

    def set_timer_label_text(self, text: str) -> None:
        self.timer_label.setText(text)
