"""Thread-safe in-process operational counters; no research values are retained."""

from collections import Counter
from threading import Lock


class OperationalMetrics:
    def __init__(self) -> None:
        self._values: Counter[str] = Counter()
        self._lock = Lock()

    def increment(self, name: str) -> None:
        with self._lock:
            self._values[name] += 1

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return dict(sorted(self._values.items()))

    def clear(self) -> None:
        with self._lock:
            self._values.clear()
