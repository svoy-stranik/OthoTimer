import random
import sys
from datetime import datetime

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
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
from utils import reveal_project_version


class TimerThread(QThread):
    timer_signal = pyqtSignal(int, str, bool)  # remaining, label, is_break
    timer_finished = pyqtSignal(str, bool)  # label, is_break

    def __init__(self, duration, label, is_break=False):
        super().__init__()
        self.duration = duration
        self.label = label
        self.is_break = is_break
        self._is_running = True

    def run(self):
        remaining = self.duration
        while remaining > 0 and self._is_running:
            self.timer_signal.emit(remaining, self.label, self.is_break)
            self.sleep(1)
            remaining -= 1

        if remaining <= 0 and self._is_running:
            self.timer_finished.emit(self.label, self.is_break)

    def stop(self):
        self._is_running = False
        self.wait()


class WorkTimerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.notifier = None
        self.is_running = False
        self.is_break = False
        self.verse_updating = False
        self.verse_started = False
        self.total_work_seconds = 0
        self.break_count = 0
        self.current_timer = None

        self.init_ui()
        self.init_tray()

        # Таймер для напоминаний о молитве
        self.prayer_timer = QTimer()
        self.prayer_timer.timeout.connect(self.prayer_reminder)
        self.prayer_timer.start(PRAYER_REMINDER_INTERVAL * 1000)

        # Таймер для обновления стихов
        self.verse_timer = QTimer()
        self.verse_timer.timeout.connect(self.update_verse)

        self.check_first_launch()

    def init_ui(self):
        self.setWindowTitle(f"Рабочий таймер от Странника v{reveal_project_version()}")
        self.setFixedSize(400, 500)

        # Устанавливаем иконку
        self.setWindowIcon(QIcon(str(ICON_PATH)))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Метка таймера
        self.timer_label = QLabel("")
        self.timer_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("margin: 20px; color: darkgreen;")

        # Кнопки в столбик
        self.start_button = QPushButton("Начать рабочий день")
        self.start_button.clicked.connect(self.start_day)
        self.start_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")

        self.pause_button = QPushButton("Обед (пауза)")
        self.pause_button.clicked.connect(self.pause_day)
        self.pause_button.setEnabled(False)
        self.pause_button.setStyleSheet("QPushButton { background-color: #FF9800; color: white; }")

        self.end_button = QPushButton("Закончить день")
        self.end_button.clicked.connect(self.end_day)
        self.end_button.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")

        # Добавляем кнопки в столбик
        layout.addWidget(self.timer_label)
        layout.addWidget(self.start_button)
        layout.addWidget(self.pause_button)
        layout.addWidget(self.end_button)
        layout.addStretch(1)

        # Заголовок молитвы (будет удалён при первом запуске)
        self.title_label = QLabel("Молитва Господа Нашего Иисуса Христа:")
        self.title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: darkblue;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Метка для стихов
        self.verse_label = QLabel()
        self.verse_label.setFont(QFont("Arial", 10))
        self.verse_label.setWordWrap(True)
        self.verse_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.verse_label.setStyleSheet("margin: 10px;")

        # Добавляем текст писания под кнопками
        layout.addWidget(self.title_label)
        layout.addWidget(self.verse_label)

    def init_tray(self):
        """Инициализация системного трея"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(QIcon(str(ICON_PATH)))

            tray_menu = QMenu()

            show_action = QAction("Показать", self)
            show_action.triggered.connect(self.show)
            tray_menu.addAction(show_action)

            quit_action = QAction("Выход", self)
            quit_action.triggered.connect(self.quit_application)
            tray_menu.addAction(quit_action)

            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self.tray_icon_activated)
            self.tray_icon.show()

            self.notifier = self.tray_icon

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.activateWindow()

    def check_first_launch(self):
        """Проверка первого запуска за день"""
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.last_launch = ""

        if LAUNCH_FILE.exists():
            self.last_launch = LAUNCH_FILE.read_text(encoding="utf-8")

        if self.last_launch != self.today:
            # Первый запуск дня - показываем молитву
            self.verse_label.setText(OTCHE_NASH)
            LAUNCH_FILE.write_text(self.today, encoding="utf-8")
        else:
            # Повторный запуск - случайный стих
            self.title_label.hide()
            self.update_verse(initial=True)
            self.verse_started = True
            self.verse_updating = True
            self.verse_timer.start(VERSE_UPDATE_INTERVAL * 1000)

    def push(self, msg):
        """Показать уведомление"""
        if self.notifier:
            self.notifier.showMessage("Православный таймер", msg, QSystemTrayIcon.MessageIcon.Information, 5000)

    def start_day(self):
        if self.is_running:
            return

        self.is_running = True
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.end_button.setEnabled(True)

        # Убираем заголовок молитвы если он есть
        if self.title_label.isVisible():
            self.title_label.hide()
            self.verse_label.setText("")

        # Запускаем обновление стихов если ещё не запущено
        if not self.verse_started:
            self.update_verse(initial=True)
            self.verse_started = True
            self.verse_updating = True
            self.verse_timer.start(VERSE_UPDATE_INTERVAL * 1000)

        self.start_work_cycle()

    def start_work_cycle(self):
        """Запуск цикла работы"""
        self.start_timer(WORK_TIME, "Работа")

    def start_timer(self, duration, label, is_break=False):
        """Запуск таймера"""
        if self.current_timer:
            self.current_timer.stop()

        self.push(f"{label} началась!")
        self.is_break = is_break

        self.current_timer = TimerThread(duration, label, is_break)
        self.current_timer.timer_signal.connect(self.update_timer_display)
        self.current_timer.timer_finished.connect(self.timer_finished)
        self.current_timer.start()

    def update_timer_display(self, remaining, label, is_break):
        """Обновление отображения таймера"""
        mins = remaining // 60
        secs = remaining % 60
        self.timer_label.setText(f"{label}: {mins:02d}:{secs:02d}")

        # Увеличиваем счётчик рабочего времени
        if not is_break:
            self.total_work_seconds += 1

    def timer_finished(self, label, is_break):
        """Обработка завершения таймера"""
        self.push(f"{label} завершена!")

        if not is_break:
            # Закончилась работа - начинаем перерыв
            self.break_count += 1
            self.start_timer(BREAK_TIME, "Перерыв", is_break=True)
        else:
            # Закончился перерыв - продолжаем работу
            self.start_timer(WORK_TIME, "Работа")

    def update_verse(self, initial=False):
        """Обновление библейского стиха"""
        verse = random.choice(BIBLE_VERSES)
        self.verse_label.setText(verse)

    def prayer_reminder(self):
        """Напоминание о молитве"""
        self.push("Молиться не забывай, солнышко 🌞")

    def pause_day(self):
        """Пауза на обед"""
        self.push("Правильно, большие перерывы тоже надо делать)")

        if self.current_timer:
            self.current_timer.stop()

        self.is_running = False
        self.is_break = False
        self.break_count += 1
        self.timer_label.setText("Пауза…")
        self.start_button.setText("Продолжить работу")
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)

    def end_day(self):
        """Завершение рабочего дня"""
        if self.current_timer:
            self.current_timer.stop()

        self.is_running = False

        hours = self.total_work_seconds // 3600
        mins = (self.total_work_seconds % 3600) // 60

        result_text = (
            f"Итоги дня:\n\n"
            f"Работал: {hours} ч {mins} мин\n"
            f"Перерывов: {self.break_count}\n\n"
            f"Сделано Странником: https://t.me/periplanomenoc.\n"
            f"Надеюсь, вы нашли сегодня немного времени для молитвы!"
        )

        QMessageBox.information(self, "Итоги дня", result_text)
        self.quit_application()

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        event.ignore()
        self.hide()
        self.push("Приложение свернуто в трей. Чтобы закрыть - используйте правую кнопку мыши на иконке.")

    def quit_application(self):
        """Корректный выход из приложения"""
        if self.current_timer:
            self.current_timer.stop()

        self.verse_timer.stop()
        self.prayer_timer.stop()

        QApplication.quit()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    window = WorkTimerApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
