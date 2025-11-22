from dataclasses import dataclass


@dataclass(frozen=True)
class TimerConfig:
    duration: int
    label: str
    is_break: bool = False


@dataclass(frozen=True)
class AppConfig:
    work_time: int
    break_time: int
    prayer_interval: int
    verse_interval: int


@dataclass
class AppState:
    is_running: bool = False
    is_break: bool = False
    verse_updating: bool = False
    verse_started: bool = False
    total_work_seconds: int = 0
    break_count: int = 0


@dataclass
class DaySummary:
    work_hours: int
    work_minutes: int
    break_count: int
