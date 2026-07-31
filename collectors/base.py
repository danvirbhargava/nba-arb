from abc import ABC, abstractmethod
from datetime import datetime, timezone


class SportsbookCollector(ABC):
    sportsbook_name: str

    @abstractmethod
    async def fetch_odds(self) -> list[dict]:
        """Return normalized odds dicts, one per (game, selection)."""

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _normalize(self, event: str, selection: str, odds: float) -> dict:
        return {
            "event": event,
            "market": "moneyline",
            "selection": selection,
            "odds": odds,
            "sportsbook": self.sportsbook_name,
            "timestamp": self._timestamp(),
        }
