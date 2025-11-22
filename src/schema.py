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
class LunchPeriod:
    start_time: str
    end_time: str | None = None


@dataclass
class AppState:
    is_running: bool = False
    is_break: bool = False
    verse_updating: bool = False
    verse_started: bool = False
    total_work_seconds: int = 0
    break_count: int = 0
    lunch_count: int = 0
    lunch_periods: list[LunchPeriod] = None
    current_lunch_start: str | None = None

    def __post_init__(self):
        if self.lunch_periods is None:
            self.lunch_periods = []


@dataclass
class DaySummary:
    work_hours: int
    work_minutes: int
    break_count: int
    lunch_count: int
    lunch_periods: list[LunchPeriod]
