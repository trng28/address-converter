from __future__ import annotations

PARSER_VERSION = "1.0.0"

DEFAULT_OPTIONS = {
    "allowBroadMatch": False,
    "multiple": "all",
    "strict": False,
}

ADMIN_PREFIXES = [
    "thanh pho",
    "tinh",
    "quan",
    "huyen",
    "thi xa",
    "phuong",
    "xa",
    "thi tran",
    "tt",
    "tx",
    "x",
    "tp",
    "q",
    "p",
]

ADMIN_NAME_ALIASES_BY_CANONICAL = {
    "hue": ["thua thien hue"],
    "phu quy": ["dao phu quy"],
}
