import tkinter as tk
from datetime import datetime
from random import choice
from threading import Event, Thread
from time import sleep
from tkinter import messagebox

from plyer import notification

from constants import (
    BIBLE_VERSES,
    BREAK_TIME,
    LAUNCH_FILE,
    OTCHE_NASH,
    PRAYER_REMINDER_INTERVAL,
    VERSE_UPDATE_INTERVAL,
    WORK_TIME,
)


class WorkTimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Рабочий таймер от Странника v.1.0.0")

        # --- Устанавливаем иконку окна ---
        try:
            root.iconbitmap("icon.ico")  # .ico для Windows
        except Exception as e:
            print("Не удалось установить иконку:", e)

        self.is_running = False
        self.is_break = False
        self.stop_event = Event()
        self.verse_updating = False
        self.verse_started = False
        self.total_work_seconds = 0
        self.break_count = 0

        # --- UI ---
        self.start_button = tk.Button(root, text="Начать рабочий день", command=self.start_day)
        self.start_button.pack(pady=5)
        self.pause_button = tk.Button(root, text="Обед (пауза)", command=self.pause_day, state=tk.DISABLED)
        self.pause_button.pack(pady=5)
        self.end_button = tk.Button(root, text="Закончить день", command=self.end_day)
        self.end_button.pack(pady=5)
        self.timer_label = tk.Label(root, text="", font=("Arial", 14))
        self.timer_label.pack(pady=8)

        # --- Заголовок и стих ---
        self.title_label = None
        self.verse_label = tk.Label(root, wraplength=350, justify="center", font=("Arial", 10))
        self.verse_label.pack(pady=(10, 10))

        # Проверка первого запуска
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.last_launch = ""
        if LAUNCH_FILE.exists():
            self.last_launch = LAUNCH_FILE.read_text()

        if self.last_launch != self.today:
            # первый запуск дня — создаём заголовок сверху
            self.title_label = tk.Label(
                root, text="Молитва Господа Нашего Иисуса Христа:", font=("Arial", 12, "bold"), fg="darkblue"
            )
            self.title_label.pack(pady=(10, 0), before=self.verse_label)
            self.verse_label.config(text=OTCHE_NASH)
            LAUNCH_FILE.write_text(self.today)
        else:
            # повторный запуск — сразу случайный стих
            self.update_verse(initial=True)
            self.verse_started = True
            self.verse_updating = True
            self.schedule_verse_update()

        # Перехват закрытия
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Пуш-напоминание о молитве каждые 1.5 часа
        self.root.after(PRAYER_REMINDER_INTERVAL * 1000, self.prayer_reminder_loop)

    def push(self, msg):
        notify = notification.notify

        if notify is None:
            raise RuntimeError("notification.notify is None!")

        Thread(target=lambda: notify(title="Православный таймер", message=msg, timeout=5), daemon=True).start()

    def start_day(self):
        if not self.is_running:
            self.is_running = True
            self.stop_event.clear()
            self.start_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            self.end_button.config(state=tk.NORMAL)
            if self.title_label:
                self.title_label.destroy()
                self.title_label = None
            if self.verse_label.cget("text") == OTCHE_NASH:
                self.verse_label.config(text="")

            if not self.verse_started:
                self.update_verse(initial=True)
                self.verse_started = True
                self.verse_updating = True
                self.schedule_verse_update()

            Thread(target=self.work_cycle, daemon=True).start()

    def schedule_verse_update(self):
        if self.verse_updating:
            self.root.after(VERSE_UPDATE_INTERVAL * 1000, self.update_verse)

    def update_verse(self, *, initial=False):
        verse = choice(BIBLE_VERSES)
        self.verse_label.config(text=verse)
        if not initial:
            self.schedule_verse_update()

    def prayer_reminder_loop(self):
        self.push("Молиться не забывай, солнышко 🌞")
        self.root.after(PRAYER_REMINDER_INTERVAL * 1000, self.prayer_reminder_loop)

    def work_cycle(self):
        while not self.stop_event.is_set():
            self.run_timer(WORK_TIME, "Работа")
            if self.stop_event.is_set():
                break
            self.break_count += 1
            self.run_timer(BREAK_TIME, "Перерыв", is_break=True)

    def run_timer(self, duration, label, *, is_break=False):
        self.is_break = is_break
        self.push(f"{label} началась!")
        remaining = duration
        while remaining > 0 and not self.stop_event.is_set():
            mins = remaining // 60
            secs = remaining % 60
            self.timer_label.config(text=f"{label}: {mins:02d}:{secs:02d}")
            self.root.update()
            sleep(1)
            if not is_break:
                self.total_work_seconds += 1
            remaining -= 1
        if remaining <= 0 and not self.stop_event.is_set():
            self.push(f"{label} завершена!")

    def pause_day(self):
        self.push("Правильно, большие перерывы тоже надо делать)")
        self.stop_event.set()
        self.is_running = False
        self.is_break = False
        self.break_count += 1
        self.timer_label.config(text="Пауза…")
        self.start_button.config(text="Продолжить работу", state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)

    def end_day(self):
        self.stop_event.set()
        self.is_running = False

        hours = self.total_work_seconds // 3600
        mins = (self.total_work_seconds % 3600) // 60

        result_text = (
            f"Итоги дня:\n\n"
            f"Работал: {hours} ч {mins} мин\n"
            f"Перерывов: {self.break_count}\n\n"
            f"Сделано Странником: https://t.me/periplanomenoc. Надеюсь, вы нашли сегодня немного времени для молитвы!"
        )

        messagebox.showinfo("Итоги дня", result_text)
        self.root.destroy()

    def on_close(self):
        messagebox.showinfo(
            "Не забудьте поблагодарить)",
            "Сделано Странником: https://t.me/periplanomenoc. Надеюсь, вы нашли сегодня немного времени для молитвы!",
        )
        self.root.destroy()


def main():
    root = tk.Tk()
    WorkTimerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
