from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime: ...

    def today(self) -> date: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)

    def today(self) -> date:
        return self.now().date()


@dataclass(frozen=True, slots=True)
class FrozenClock:
    current_time: datetime
    business_date: date | None = None

    def __post_init__(self) -> None:
        if self.current_time.tzinfo is None:
            raise ValueError("FrozenClock.current_time must be timezone-aware")

    def now(self) -> datetime:
        return self.current_time.astimezone(timezone.utc)

    def today(self) -> date:
        return self.business_date or self.now().date()


def budget_month(clock: Clock) -> str:
    return clock.today().strftime("%Y-%m")
