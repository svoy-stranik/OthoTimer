import json
import random
from datetime import datetime

from constants import (
    BIBLE_VERSES,
    USED_VERSES_FILE,
)
from logger import logger


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
                logger.warning("Failed to load used verses", exc_info=True)
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
