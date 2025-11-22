import json
import random
import sys
import webbrowser
from datetime import datetime
from typing import override

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QFont, QIcon
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from constants import (
    BIBLE_VERSES,
    BREAK_TIME,
    BUTTON_SMALL_SIZE,
    BUTTON_TINY_SIZE,
    COLOR_ACCENT_BROWN,
    COLOR_ACCENT_GOLD,
    COLOR_ACCENT_ORANGE,
    COLOR_DARK_BG,
    COLOR_DARKER_BG,
    COLOR_DARKEST_BG,
    COLOR_DELETE_HOVER,
    COLOR_DELETE_RED,
    COLOR_TEXT_LIGHT,
    COLOR_TEXT_MUTED,
    ICON_PATH,
    LAUNCH_FILE,
    OTCHE_NASH,
    PRAYER_REMINDER_INTERVAL,
    TASK_ITEM_HEIGHT,
    TELEGRAM_URL,
    USED_VERSES_FILE,
    VERSE_UPDATE_INTERVAL,
    WORK_TIME,
)
from schema import AppState, DaySummary, LunchPeriod
from utils import reveal_project_version


class TodoItemWidget(QWidget):
    delete_requested = pyqtSignal()

    def __init__(self, text: str = "", parent: QWidget | None = None, *, completed: bool = False):
        super().__init__(parent)
        self.text: str = text
        self.completed: bool = completed
        self.is_editing: bool = False
        self._widgets_initialized: bool = False  # Флаг инициализации

        self.setStyleSheet("QWidget { background: transparent; }")
        self._setup_ui()
        self._update_appearance()
        self._widgets_initialized = True  # Виджеты инициализированы

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(8)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.completed)
        self.checkbox.stateChanged.connect(self._on_checkbox_changed)
        self.checkbox.setStyleSheet(f"""
            QCheckBox {{ spacing: 8px; background: transparent; }}
            QCheckBox::indicator {{
                width: 16px; height: 16px;
                border: 2px solid {COLOR_ACCENT_GOLD};
                border-radius: 3px;
                background: {COLOR_DARKER_BG};
            }}
            QCheckBox::indicator:checked {{
                background: {COLOR_ACCENT_ORANGE};
                border: 2px solid {COLOR_ACCENT_ORANGE};
            }}
            QCheckBox::indicator:hover {{
                border: 2px solid #F4A460;
            }}
        """)
        layout.addWidget(self.checkbox)

        self.text_label = QLabel(self.text)
        self.text_label.setWordWrap(True)
        self.text_label.setMinimumHeight(30)
        layout.addWidget(self.text_label, 1)

        self.edit_input = QLineEdit(self.text)
        self.edit_input.setVisible(False)
        self.edit_input.setMinimumHeight(30)
        self.edit_input.setStyleSheet(f"""
            QLineEdit {{
                font-family: "Times New Roman"; font-size: 12px;
                color: white; padding: 5px;
                background: #606060;
                border: 2px solid {COLOR_ACCENT_ORANGE};
                border-radius: 3px;
            }}
        """)
        self.edit_input.returnPressed.connect(self._finish_editing)
        self.edit_input.focusOutEvent = self._on_edit_focus_out
        layout.addWidget(self.edit_input, 1)

        self.delete_btn = QPushButton("✕")
        self.delete_btn.setFixedSize(*BUTTON_TINY_SIZE)
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_DELETE_RED}; color: white;
                border: none; border-radius: 12px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {COLOR_DELETE_HOVER}; }}
        """)
        self.delete_btn.clicked.connect(self._request_delete)
        layout.addWidget(self.delete_btn)

    def _update_appearance(self) -> None:
        if not self._widgets_initialized:
            return

        if self.completed:
            self.text_label.setStyleSheet(f"""
                QLabel {{
                    font-family: "Times New Roman"; font-size: 12px;
                    color: {COLOR_TEXT_MUTED}; padding: 5px;
                    background: {COLOR_DARKEST_BG};
                    border: 1px solid #505050; border-radius: 3px;
                    text-decoration: line-through;
                }}
            """)
        else:
            self.text_label.setStyleSheet(f"""
                QLabel {{
                    font-family: "Times New Roman"; font-size: 12px;
                    color: {COLOR_TEXT_LIGHT}; padding: 5px;
                    background: #505050;
                    border: 1px solid #696969; border-radius: 3px;
                }}
            """)

    def _on_checkbox_changed(self, state: int) -> None:
        self.completed = state == Qt.CheckState.Checked.value
        self._update_appearance()

    def start_editing(self) -> None:
        if not self._widgets_initialized:
            return

        self.is_editing = True
        self.text_label.setVisible(False)
        self.edit_input.setVisible(True)
        self.edit_input.setText(self.text)
        self.edit_input.setFocus()
        self.edit_input.selectAll()

    def _finish_editing(self) -> None:
        if not self._widgets_initialized:
            return

        new_text = self.edit_input.text().strip()
        if new_text:
            self.text = new_text
            self.text_label.setText(new_text)
        self.is_editing = False
        self.edit_input.setVisible(False)
        self.text_label.setVisible(True)

    def _on_edit_focus_out(self, event) -> None:
        if self._widgets_initialized:
            self._finish_editing()
        super().focusOutEvent(event)

    def _request_delete(self) -> None:
        reply = QMessageBox.question(
            self,
            "Удаление задачи",
            f'Вы уверены, что хотите удалить задачу:\n"{self.text}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_requested.emit()


class TodoListWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.tasks: list = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(5)

        self.setStyleSheet(f"""
            QWidget {{
                background: {COLOR_DARK_BG};
                border-radius: 8px; margin: 5px;
            }}
        """)

        title = QLabel("Задачи")
        title.setFont(QFont("Times New Roman", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"QLabel {{ color: {COLOR_ACCENT_GOLD}; margin: 10px; background: transparent; }}")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.add_task_input = QLineEdit()
        self.add_task_input.setPlaceholderText("Добавить новую задачу...")
        self.add_task_input.setStyleSheet(f"""
            QLineEdit {{
                font-family: "Times New Roman"; font-size: 12px; padding: 8px;
                background: {COLOR_DARKER_BG}; color: white;
                border: 2px solid {COLOR_ACCENT_BROWN}; border-radius: 5px;
                margin: 0px 10px;
            }}
            QLineEdit::placeholder {{ color: #A0A0A0; }}
            QLineEdit:focus {{ border: 2px solid {COLOR_ACCENT_ORANGE}; }}
        """)
        self.add_task_input.returnPressed.connect(self._add_new_task)
        layout.addWidget(self.add_task_input)

        self.tasks_list = QListWidget()
        self.tasks_list.setStyleSheet(f"""
            QListWidget {{
                background: {COLOR_DARKER_BG};
                border: 2px solid {COLOR_ACCENT_BROWN}; border-radius: 5px;
                margin: 0px 10px; outline: none;
            }}
            QListWidget::item {{
                border-bottom: 1px solid #505050;
                height: {TASK_ITEM_HEIGHT}px;
                background: {COLOR_DARKER_BG};
            }}
            QListWidget::item:alternate {{ background: {COLOR_DARKEST_BG}; }}
            QListWidget::item:last {{ border-bottom: none; }}
            QListWidget::item:hover {{ background: #484848; }}
        """)
        self.tasks_list.setAlternatingRowColors(True)
        self.tasks_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        layout.addWidget(self.tasks_list)

    def _add_new_task(self) -> None:
        text = self.add_task_input.text().strip()
        if text:
            self._create_task_item(text)
            self.add_task_input.clear()

    def _create_task_item(self, text: str) -> None:
        item = QListWidgetItem()
        item_widget = TodoItemWidget(text, completed=False)
        item_widget.delete_requested.connect(lambda: self._delete_task_item(item))

        def start_edit():
            if item_widget._widgets_initialized and not item_widget.completed:
                item_widget.start_editing()

        self.tasks_list.addItem(item)
        self.tasks_list.setItemWidget(item, item_widget)

        def handle_double_click(clicked_item):
            if clicked_item == item:
                start_edit()

        self.tasks_list.itemDoubleClicked.connect(handle_double_click)

    def _delete_task_item(self, item: QListWidgetItem) -> None:
        row = self.tasks_list.row(item)
        self.tasks_list.takeItem(row)


class VerseManager:
    def __init__(self):
        self.used_verses: set[str] = set()
        self.available_verses: list[str] = list(BIBLE_VERSES)
        self._load_used_verses()

    def _load_used_verses(self) -> None:
        if USED_VERSES_FILE.exists():
            try:
                with USED_VERSES_FILE.open(encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("date") == datetime.now().strftime("%Y-%m-%d"):
                        self.used_verses = set(data.get("used_verses", []))
            except (json.JSONDecodeError, KeyError):
                self.used_verses = set()

    def _save_used_verses(self) -> None:
        data = {"date": datetime.now().strftime("%Y-%m-%d"), "used_verses": list(self.used_verses)}
        with USED_VERSES_FILE.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_random_verse(self) -> str:
        if not self.available_verses:
            self.available_verses = list(BIBLE_VERSES)
            self.used_verses.clear()

        available_verses = [v for v in self.available_verses if v not in self.used_verses]

        if not available_verses:
            self.available_verses = list(BIBLE_VERSES)
            self.used_verses.clear()
            available_verses = self.available_verses

        verse = random.choice(available_verses)
        self.used_verses.add(verse)
        self._save_used_verses()
        return verse

    def reset_daily_verses(self) -> None:
        self.used_verses.clear()
        self.available_verses = list(BIBLE_VERSES)
        if USED_VERSES_FILE.exists():
            USED_VERSES_FILE.unlink()


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
        self.layout().addWidget(link_widget, self.layout().rowCount(), 0, 1, self.layout().columnCount())
        self.setStandardButtons(QMessageBox.StandardButton.Ok)

    def _copy_to_clipboard(self) -> None:
        clipboard = QApplication.clipboard()
        clipboard.setText(TELEGRAM_URL)

    def _open_channel(self) -> None:
        webbrowser.open(TELEGRAM_URL)


class TimerThread(QThread):
    timer_signal = pyqtSignal(int, str, bool)
    timer_finished = pyqtSignal(str, bool)

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
            self.timer_finished.emit(self.label, self.is_break)

    def stop(self) -> None:
        self._is_running = False
        self.wait()


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
        self.title_label.setStyleSheet("color: darkblue;")
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


class SystemTrayManager:
    def __init__(self, main_window: WorkTimerApp) -> None:
        self.main_window = main_window
        self.tray_icon: QSystemTrayIcon | None = None
        self.notifier: QSystemTrayIcon | None = None
        self._setup_tray()

    def _setup_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        self.tray_icon = QSystemTrayIcon(self.main_window)
        self.tray_icon.setIcon(QIcon(str(ICON_PATH)))

        tray_menu = QMenu()
        show_action = QAction("Показать", self.main_window)
        show_action.triggered.connect(self.main_window.show)
        tray_menu.addAction(show_action)

        quit_action = QAction("Выход", self.main_window)
        quit_action.triggered.connect(self._quit_from_tray)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_icon_activated)
        self.tray_icon.show()
        self.notifier = self.tray_icon

    def _quit_from_tray(self) -> None:
        self.main_window.quit_application()

    def _on_tray_icon_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.main_window.show()
            self.main_window.activateWindow()

    def show_notification(self, title: str, message: str) -> None:
        if self.notifier:
            self.notifier.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 5000)


class WorkTimerApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._app_state = AppState()
        self.current_timer: TimerThread | None = None
        self._show_tray_notification: bool = True
        self.verse_manager = VerseManager()
        self._last_timer_type: str = ""

        self._init_ui()
        self.tray_manager = SystemTrayManager(self)
        self._init_timers()
        self._check_first_launch()

    def _init_ui(self) -> None:
        self.setWindowTitle(f"Рабочий таймер от Странника v{reveal_project_version()}")
        self.setFixedSize(400, 650)
        self.setWindowIcon(QIcon(str(ICON_PATH)))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.ui = WorkTimerUI(central_widget)
        self._connect_ui_signals()

    def _connect_ui_signals(self) -> None:
        self.ui.start_button.clicked.connect(self.start_day)
        self.ui.pause_button.clicked.connect(self.pause_day)
        self.ui.end_button.clicked.connect(self.end_day)

    def _init_timers(self) -> None:
        self.prayer_timer = QTimer()
        self.prayer_timer.timeout.connect(self.prayer_reminder)
        self.prayer_timer.start(PRAYER_REMINDER_INTERVAL * 1000)

        self.verse_timer = QTimer()
        self.verse_timer.timeout.connect(self.update_verse)

    def _check_first_launch(self) -> None:
        today = datetime.now().strftime("%Y-%m-%d")
        last_launch = ""

        if LAUNCH_FILE.exists():
            last_launch = LAUNCH_FILE.read_text(encoding="utf-8")

        if last_launch != today:
            self.verse_manager.reset_daily_verses()
            self.ui.set_verse_text(OTCHE_NASH)
            LAUNCH_FILE.write_text(today, encoding="utf-8")
        else:
            self.ui.hide_prayer_title()
            self.update_verse()
            self._app_state.verse_started = True
            self._app_state.verse_updating = True
            self.verse_timer.start(VERSE_UPDATE_INTERVAL * 1000)

    def push(self, msg: str) -> None:
        self.tray_manager.show_notification("Православный таймер", msg)

    def start_day(self) -> None:
        if self._app_state.is_running:
            return

        if self._app_state.current_lunch_start:
            self._end_lunch_period()

        self._app_state.is_running = True
        self.ui.update_button_states(start_enabled=False, pause_enabled=True, end_enabled=True)

        if self.ui.title_label.isVisible():
            self.ui.hide_prayer_title()
            self.ui.set_verse_text("")

        if not self._app_state.verse_started:
            self.update_verse()
            self._app_state.verse_started = True
            self._app_state.verse_updating = True
            self.verse_timer.start(VERSE_UPDATE_INTERVAL * 1000)

        self.start_work_cycle()

    def start_work_cycle(self) -> None:
        self._last_timer_type = "work"
        self.start_timer(WORK_TIME, "Работа")

    def start_timer(self, duration: int, label: str, *, is_break: bool = False) -> None:
        if self.current_timer:
            self.current_timer.stop()

        if (is_break and self._last_timer_type != "break") or (not is_break and self._last_timer_type != "work"):
            self.push(f"{label} началась!")

        self._last_timer_type = "break" if is_break else "work"
        self._app_state.is_break = is_break

        self.current_timer = TimerThread(duration, label, is_break=is_break)
        self.current_timer.timer_signal.connect(self._on_timer_update)
        self.current_timer.timer_finished.connect(self._on_timer_finished)
        self.current_timer.start()

    def _on_timer_update(self, remaining: int, label: str, is_break: bool) -> None:  # noqa: FBT001
        self.ui.update_timer_display(remaining, label)
        if not is_break:
            self._app_state.total_work_seconds += 1

    def _on_timer_finished(self, *, is_break: bool) -> None:
        if not is_break:
            self._app_state.break_count += 1
            self.start_timer(BREAK_TIME, "Перерыв", is_break=True)
        else:
            self.start_timer(WORK_TIME, "Работа")

    def update_verse(self) -> None:
        verse = self.verse_manager.get_random_verse()
        self.ui.set_verse_text(verse)

    def prayer_reminder(self) -> None:
        self.push("Молиться не забывай, солнышко 🌞")

    def pause_day(self) -> None:
        lunch_start = datetime.now().strftime("%H:%M")
        self._app_state.current_lunch_start = lunch_start

        self.push("Правильно, большие перерывы тоже надо делать)")

        if self.current_timer:
            self.current_timer.stop()

        self._app_state.is_running = False
        self._app_state.is_break = False

        self.ui.set_timer_label_text("Пауза…")
        self.ui.set_start_button_text("Продолжить работу")
        self.ui.update_button_states(start_enabled=True, pause_enabled=False, end_enabled=True)

    def _end_lunch_period(self) -> None:
        if self._app_state.current_lunch_start:
            lunch_end = datetime.now().strftime("%H:%M")
            start_dt = datetime.strptime(self._app_state.current_lunch_start, "%H:%M")
            end_dt = datetime.strptime(lunch_end, "%H:%M")
            duration_minutes = (end_dt - start_dt).total_seconds() / 60

            if duration_minutes >= 1:
                lunch_period = LunchPeriod(start_time=self._app_state.current_lunch_start, end_time=lunch_end)
                self._app_state.lunch_periods.append(lunch_period)
                self._app_state.lunch_count += 1

            self._app_state.current_lunch_start = None

    def _calculate_day_summary(self) -> DaySummary:
        hours = self._app_state.total_work_seconds // 3600
        mins = (self._app_state.total_work_seconds % 3600) // 60

        if self._app_state.current_lunch_start:
            self._end_lunch_period()

        return DaySummary(
            work_hours=hours,
            work_minutes=mins,
            break_count=self._app_state.break_count,
            lunch_count=len(self._app_state.lunch_periods),
            lunch_periods=self._app_state.lunch_periods,
        )

    def end_day(self) -> None:
        if self.current_timer:
            self.current_timer.stop()

        self._app_state.is_running = False

        summary = self._calculate_day_summary()
        dialog = DaySummaryDialog(summary, self)
        dialog.exec()

        self._show_tray_notification = False
        self.quit_application()

    @override
    def closeEvent(self, event) -> None:
        event.ignore()
        self.hide()

        if self._show_tray_notification:
            self.push("Приложение свернуто в трей. Чтобы закрыть - используйте правую кнопку мыши на иконке.")

    def quit_application(self) -> None:
        self._show_tray_notification = False

        if self.current_timer:
            self.current_timer.stop()

        self.verse_timer.stop()
        self.prayer_timer.stop()
        QApplication.quit()


def main() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    window = WorkTimerApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
