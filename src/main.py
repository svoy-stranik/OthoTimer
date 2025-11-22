import random
import sys
import webbrowser
from datetime import datetime
from typing import override

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QAction, QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
)

from constants import (
    BIBLE_VERSES,
    BREAK_TIME,
    ICON_PATH,
    LAUNCH_FILE,
    OTCHE_NASH,
    PRAYER_REMINDER_INTERVAL,
    VERSE_UPDATE_INTERVAL,
    WORK_TIME,
)
from schema import AppState, DaySummary
from utils import reveal_project_version


class DaySummaryDialog(QMessageBox):
    """Диалог с итогами дня."""

    def __init__(self, summary: DaySummary, parent=None):
        super().__init__(parent)
        self.summary = summary
        self.setWindowTitle("Итоги дня")
        self.setIcon(QMessageBox.Icon.Information)

        self._setup_ui()

    def _setup_ui(self):
        # Основной текст
        result_text = (
            f"Итоги дня:\n\n"
            f"Работал: {self.summary.work_hours} ч {self.summary.work_minutes} мин\n"
            f"Перерывов: {self.summary.break_count}\n\n"
            f"Сделано Странником.\n"
            f"Надеюсь, вы нашли сегодня немного времени для молитвы!"
        )
        self.setText(result_text)

        # Создаем виджет для ссылки и кнопок
        link_widget = QWidget()
        link_layout = QHBoxLayout(link_widget)
        link_layout.setContentsMargins(0, 10, 0, 0)

        # Текст ссылки
        link_label = QLabel("https://t.me/periplanomenoc")
        link_label.setStyleSheet("font-weight: bold; color: #0066cc;")
        link_layout.addWidget(link_label)

        # Кнопка Copy
        copy_btn = QPushButton("Copy")
        copy_btn.setFixedSize(60, 25)
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        copy_btn.clicked.connect(self._copy_to_clipboard)
        link_layout.addWidget(copy_btn)

        # Кнопка Open
        open_btn = QPushButton("Open")
        open_btn.setFixedSize(60, 25)
        open_btn.setStyleSheet("""
            QPushButton {
                background-color: #0088cc;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #006699;
            }
        """)
        open_btn.clicked.connect(self._open_channel)
        link_layout.addWidget(open_btn)

        link_layout.addStretch()

        self.layout().addWidget(link_widget, self.layout().rowCount(), 0, 1, self.layout().columnCount())

        # Стандартные кнопки
        self.setStandardButtons(QMessageBox.StandardButton.Ok)

    def _copy_to_clipboard(self):
        """Копировать ссылку в буфер обмена."""
        clipboard = QApplication.clipboard()
        clipboard.setText("https://t.me/periplanomenoc")

    def _open_channel(self):
        """Открыть канал в браузере."""
        webbrowser.open("https://t.me/periplanomenoc")


class WorkTimerUI:
    """Класс для управления пользовательским интерфейсом таймера."""

    def __init__(self, central_widget: QWidget) -> None:
        self.central_widget = central_widget
        self.layout = QVBoxLayout(central_widget)

        self.timer_label: QLabel
        self.start_button: QPushButton
        self.pause_button: QPushButton
        self.end_button: QPushButton
        self.title_label: QLabel
        self.verse_label: QLabel

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Настройка пользовательского интерфейса."""
        self._create_timer_label()
        self._create_buttons()
        self._create_prayer_section()

    def _create_timer_label(self) -> None:
        """Создание метки таймера."""
        self.timer_label = QLabel("")
        self.timer_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("margin: 20px; color: darkgreen;")
        self.layout.addWidget(self.timer_label)

    def _create_buttons(self) -> None:
        """Создание кнопок управления."""
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
        self.layout.addStretch(1)

    def _create_prayer_section(self) -> None:
        """Создание секции с молитвой и стихами."""
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

    def update_timer_display(self, remaining: int, label: str, is_break: bool) -> None:
        """Обновление отображения таймера."""
        mins = remaining // 60
        secs = remaining % 60
        self.timer_label.setText(f"{label}: {mins:02d}:{secs:02d}")

    def set_verse_text(self, text: str) -> None:
        """Установка текста стиха."""
        self.verse_label.setText(text)

    def hide_prayer_title(self) -> None:
        """Скрыть заголовок молитвы."""
        self.title_label.hide()

    def update_button_states(self, *, start_enabled: bool, pause_enabled: bool, end_enabled: bool) -> None:
        """Обновление состояний кнопок."""
        self.start_button.setEnabled(start_enabled)
        self.pause_button.setEnabled(pause_enabled)
        self.end_button.setEnabled(end_enabled)

    def set_start_button_text(self, text: str) -> None:
        """Установка текста кнопки старта."""
        self.start_button.setText(text)

    def set_timer_label_text(self, text: str) -> None:
        """Установка текста метки таймера."""
        self.timer_label.setText(text)


class SystemTrayManager:
    """Менеджер системного трея."""

    def __init__(self, main_window: WorkTimerApp) -> None:
        self.main_window = main_window
        self.tray_icon: QSystemTrayIcon | None = None
        self.notifier: QSystemTrayIcon | None = None

        self._setup_tray()

    def _setup_tray(self) -> None:
        """Настройка системного трея."""
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
        """Выход из трея без уведомления."""
        self.main_window.quit_application()  # Просто вызываем quit_application, он сам сбросит флаг

    def _on_tray_icon_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Обработка активации иконки в трее."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.main_window.show()
            self.main_window.activateWindow()

    def show_notification(self, title: str, message: str) -> None:
        """Показать уведомление."""
        if self.notifier:
            self.notifier.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 5000)


class WorkTimerApp(QMainWindow):
    """Основной класс приложения рабочего таймера."""

    def __init__(self) -> None:
        super().__init__()
        self._app_state = AppState()
        self.current_timer: TimerThread | None = None
        self._show_tray_notification: bool = True

        self._init_ui()
        self.tray_manager = SystemTrayManager(self)
        self._init_timers()
        self._check_first_launch()

    def _init_ui(self) -> None:
        """Инициализация пользовательского интерфейса."""
        self.setWindowTitle(f"Рабочий таймер от Странника v{reveal_project_version()}")
        self.setFixedSize(400, 500)
        self.setWindowIcon(QIcon(str(ICON_PATH)))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.ui = WorkTimerUI(central_widget)
        self._connect_ui_signals()

    def _connect_ui_signals(self) -> None:
        """Подключение сигналов UI."""
        self.ui.start_button.clicked.connect(self.start_day)
        self.ui.pause_button.clicked.connect(self.pause_day)
        self.ui.end_button.clicked.connect(self.end_day)

    def _init_timers(self) -> None:
        """Инициализация таймеров."""
        # Таймер для напоминаний о молитве
        self.prayer_timer = QTimer()
        self.prayer_timer.timeout.connect(self.prayer_reminder)
        self.prayer_timer.start(PRAYER_REMINDER_INTERVAL * 1000)

        # Таймер для обновления стихов
        self.verse_timer = QTimer()
        self.verse_timer.timeout.connect(self.update_verse)

    def _check_first_launch(self) -> None:
        """Проверка первого запуска за день."""
        today = datetime.now().strftime("%Y-%m-%d")
        last_launch = ""

        if LAUNCH_FILE.exists():
            last_launch = LAUNCH_FILE.read_text(encoding="utf-8")

        if last_launch != today:
            # Первый запуск дня - показываем молитву
            self.ui.set_verse_text(OTCHE_NASH)
            LAUNCH_FILE.write_text(today, encoding="utf-8")
        else:
            # Повторный запуск - случайный стих
            self.ui.hide_prayer_title()
            self.update_verse(initial=True)
            self._app_state.verse_started = True
            self._app_state.verse_updating = True
            self.verse_timer.start(VERSE_UPDATE_INTERVAL * 1000)

    def push(self, msg: str) -> None:
        """Показать уведомление."""
        self.tray_manager.show_notification("Православный таймер", msg)

    def start_day(self) -> None:
        """Начать рабочий день."""
        if self._app_state.is_running:
            return

        self._app_state.is_running = True
        self.ui.update_button_states(start_enabled=False, pause_enabled=True, end_enabled=True)

        # Убираем заголовок молитвы если он есть
        if self.ui.title_label.isVisible():
            self.ui.hide_prayer_title()
            self.ui.set_verse_text("")

        # Запускаем обновление стихов если ещё не запущено
        if not self._app_state.verse_started:
            self.update_verse(initial=True)
            self._app_state.verse_started = True
            self._app_state.verse_updating = True
            self.verse_timer.start(VERSE_UPDATE_INTERVAL * 1000)

        self.start_work_cycle()

    def start_work_cycle(self) -> None:
        """Запуск цикла работы."""
        self.start_timer(WORK_TIME, "Работа")

    def start_timer(self, duration: int, label: str, *, is_break: bool = False) -> None:
        """Запуск таймера."""
        if self.current_timer:
            self.current_timer.stop()

        self.push(f"{label} началась!")
        self._app_state.is_break = is_break

        self.current_timer = TimerThread(duration, label, is_break=is_break)
        self.current_timer.timer_signal.connect(self._on_timer_update)
        self.current_timer.timer_finished.connect(self._on_timer_finished)
        self.current_timer.start()

    def _on_timer_update(self, remaining: int, label: str, is_break: bool) -> None:
        """Обработка обновления таймера."""
        self.ui.update_timer_display(remaining, label, is_break)

        # Увеличиваем счётчик рабочего времени
        if not is_break:
            self._app_state.total_work_seconds += 1

    def _on_timer_finished(self, label: str, is_break: bool) -> None:
        """Обработка завершения таймера."""
        self.push(f"{label} завершена!")

        if not is_break:
            # Закончилась работа - начинаем перерыв
            self._app_state.break_count += 1
            self.start_timer(BREAK_TIME, "Перерыв", is_break=True)
        else:
            # Закончился перерыв - продолжаем работу
            self.start_timer(WORK_TIME, "Работа")

    def update_verse(self, *, initial: bool = False) -> None:
        """Обновление библейского стиха."""
        verse = random.choice(BIBLE_VERSES)
        self.ui.set_verse_text(verse)

    def prayer_reminder(self) -> None:
        """Напоминание о молитве."""
        self.push("Молиться не забывай, солнышко 🌞")

    def pause_day(self) -> None:
        """Пауза на обед."""
        self.push("Правильно, большие перерывы тоже надо делать)")

        if self.current_timer:
            self.current_timer.stop()

        self._app_state.is_running = False
        self._app_state.is_break = False
        self._app_state.break_count += 1

        self.ui.set_timer_label_text("Пауза…")
        self.ui.set_start_button_text("Продолжить работу")
        self.ui.update_button_states(start_enabled=True, pause_enabled=False, end_enabled=True)

    def _calculate_day_summary(self) -> DaySummary:
        """Расчет итогов дня."""
        hours = self._app_state.total_work_seconds // 3600
        mins = (self._app_state.total_work_seconds % 3600) // 60
        return DaySummary(work_hours=hours, work_minutes=mins, break_count=self._app_state.break_count)

    def end_day(self) -> None:
        """Завершение рабочего дня."""
        if self.current_timer:
            self.current_timer.stop()

        self._app_state.is_running = False

        summary = self._calculate_day_summary()

        # Используем кастомный диалог с кликабельными элементами
        dialog = DaySummaryDialog(summary, self)
        dialog.exec()

        # Отключаем уведомление и выходим
        self._show_tray_notification = False
        self.quit_application()

    @override
    def closeEvent(self, event) -> None:
        """Обработка закрытия окна."""
        event.ignore()
        self.hide()

        if self._show_tray_notification:
            self.push("Приложение свернуто в трей. Чтобы закрыть - используйте правкую кнопку мыши на иконке.")

    def quit_application(self) -> None:
        """Корректный выход из приложения."""
        # Сбрасываем флаг уведомления при любом выходе
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
