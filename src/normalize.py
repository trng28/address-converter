from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List, Optional

from .constants import ADMIN_PREFIXES
from .utils import unique


def normalize_vietnamese_name(value: Any) -> str:
    """Normalize a Vietnamese administrative name for exact key matching."""
    if value is None:
        return ""
    normalized = unicodedata.normalize("NFD", str(value).strip().lower())
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    normalized = normalized.replace("đ", "d")
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized).strip()
    normalized = re.sub(r"\s+", " ", normalized)
    while True:
        stripped = False
        for prefix in ADMIN_PREFIXES:
            if normalized == prefix:
                return ""
            if normalized.startswith(prefix + " "):
                normalized = normalized[len(prefix) + 1 :].strip()
                stripped = True
                break
        if not stripped:
            break
    return re.sub(r"\s+", " ", normalized).strip()


def normalize_address_text(value: Any) -> str:
    """Normalize free-form address text for loose text matching."""
    if value is None:
        return ""
    normalized = unicodedata.normalize("NFD", str(value).strip().lower())
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    normalized = normalized.replace("đ", "d")
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized).strip()
    normalized = re.sub(r"\s+", " ", normalized)
    for prefix in ADMIN_PREFIXES:
        normalized = re.sub(rf"(^|\s){re.escape(prefix)}(?=\s|$)", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def get_comparable_names(record: Optional[Dict[str, Any]]) -> List[str]:
    """Collect normalized names and aliases from an administrative record."""
    if not record:
        return []
    return unique(
        normalize_vietnamese_name(record.get(key))
        for key in ("name", "name_with_type", "slug", "path", "path_with_type")
    )
