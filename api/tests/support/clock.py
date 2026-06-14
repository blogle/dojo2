from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone


@dataclass(slots=True)
class MutableClock:
    current_time: datetime
    business_date: date | None = None

    def __post_init__(self) -> None:
        if self.current_time.tzinfo is None:
            raise ValueError("MutableClock.current_time must be timezone-aware")

    def now(self) -> datetime:
        return self.current_time.astimezone(timezone.utc)

    def today(self) -> date:
        return self.business_date or self.now().date()

    def set(self, current_time: datetime, *, business_date: date | None = None) -> None:
        if current_time.tzinfo is None:
            raise ValueError("MutableClock.set() requires a timezone-aware datetime")
        self.current_time = current_time.astimezone(timezone.utc)
        self.business_date = business_date

    def advance(self, **delta_kwargs: int) -> None:
        self.current_time = self.current_time + timedelta(**delta_kwargs)


def default_test_clock() -> MutableClock:
    return MutableClock(datetime(2026, 2, 15, 12, 0, tzinfo=timezone.utc))
