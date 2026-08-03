"""US equity exchange-calendar abstraction."""

from datetime import date

import exchange_calendars as xcals


class USEquityCalendar:
    """XNYS sessions with exchange-local dates and UTC schedule timestamps."""

    name = "XNYS"
    timezone = "America/New_York"

    def __init__(self) -> None:
        self._calendar = xcals.get_calendar(self.name)

    def sessions(self, start: date, end: date) -> tuple[date, ...]:
        return tuple(timestamp.date() for timestamp in self._calendar.sessions_in_range(start, end))

    def missing_sessions(self, observed: set[date], start: date, end: date) -> tuple[date, ...]:
        return tuple(session for session in self.sessions(start, end) if session not in observed)
