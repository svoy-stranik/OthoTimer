from datetime import datetime
from typing import override

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QAction, QCloseEvent, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenu,
    QSystemTrayIcon,
    QWidget,
)

from constants import (
    BREAK_TIME,
    ICON_PATH,
    LAUNCH_FILE,
    OTCHE_NASH,
    PRAYER_REMINDER_INTERVAL,
    VERSE_UPDATE_INTERVAL,
    WORK_TIME,
)
from gui.day_summary_dialog import DaySummaryDialog
from gui.work_timer import WorkTimerUI
from schema import AppState, DaySummary, LunchPeriod
from timer import TimerThread
from utils import reveal_project_version
from verse_manager import VerseManager


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
    def closeEvent(self, a0: QCloseEvent | None) -> None:
        if a0 is None:
            raise RuntimeError("No Event!")

        a0.ignore()
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
