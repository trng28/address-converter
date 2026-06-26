from __future__ import annotations

import json
import time
from typing import Any, Iterable, List


def now_ms() -> float:
    """Return a high-resolution timestamp in milliseconds."""
    return time.perf_counter() * 1000


def elapsed_ms(started_at: float) -> float:
    """Return elapsed milliseconds since the supplied start timestamp."""
    return round(max(0.0, now_ms() - started_at), 3)


def unique(values: Iterable[Any]) -> List[Any]:
    """Return non-empty values with duplicates removed while preserving order."""
    seen = set()
    result = []
    for value in values:
        if not value:
            continue
        key = (
            json.dumps(value, sort_keys=True, ensure_ascii=False)
            if isinstance(value, (dict, list))
            else value
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def to_code(value: Any) -> str:
    """Normalize an optional administrative code to a stripped string."""
    return "" if value is None else str(value).strip()
