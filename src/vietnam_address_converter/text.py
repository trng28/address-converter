from __future__ import annotations

import re
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional, Set

from .constants import PARSER_VERSION
from .conversion import convert_old_to_new
from .data import DEFAULT_DATA
from .normalize import (
    get_comparable_names,
    normalize_address_text,
    normalize_vietnamese_name,
)
from .utils import elapsed_ms, now_ms, unique

ConvertFunc = Callable[[Dict[str, Any], Optional[Dict[str, Any]]], Dict[str, Any]]


def _index_aliases(
    index: Dict[str, Set[int]],
    aliases: Set[str],
    candidate_index: int,
) -> None:
    """Map each alias string to the candidate indexes that use it."""
    for alias in aliases:
        if not alias:
            continue
        index.setdefault(alias, set()).add(candidate_index)


def _create_aliases(record: Optional[Dict[str, Any]], fallback: str = "") -> Set[str]:
    """Create normalized aliases for one administrative record."""
    values = [
        *get_comparable_names(record),
        normalize_vietnamese_name(fallback),
        normalize_address_text((record or {}).get("name")),
        normalize_address_text((record or {}).get("name_with_type")),
        normalize_address_text(fallback),
    ]
    return set(unique(values))


def _build_text_candidates(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build searchable candidates for old administrative address text."""
    seen = set()
    candidates = []
    for row in data["mapping"]["rows"]:
        key = (
            f"{row['old'].get('province_code')}|"
            f"{row['old'].get('district_code')}|"
            f"{row['old'].get('ward_code')}"
        )
        if key in seen:
            continue
        seen.add(key)

        province = data["oldProvinces"].get(row["old"].get("province_code"))
        district = data["oldDistricts"].get(row["old"].get("district_code"))
        ward = data["oldWards"].get(row["old"].get("ward_code"))
        input_ = {
            "province_name": row["old"].get("province_name") or "",
            "district_name": row["old"].get("district_name") or "",
            "ward_name": row["old"].get("ward_name") or "",
            "province_code": row["old"].get("province_code") or "",
            "district_code": row["old"].get("district_code") or "",
            "ward_code": row["old"].get("ward_code") or "",
        }
        path = " ".join(
            filter(
                None,
                [
                    input_["ward_name"],
                    input_["district_name"],
                    input_["province_name"],
                ],
            )
        )
        candidates.append(
            {
                "input": input_,
                "province_aliases": _create_aliases(province, input_["province_name"]),
                "district_aliases": _create_aliases(district, input_["district_name"]),
                "ward_aliases": _create_aliases(ward, input_["ward_name"]),
                "normalized_path": normalize_address_text(path),
            }
        )
    return candidates


def _build_candidate_search_index(
    candidates: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Build lookup tables so text parsing does not scan every candidate."""
    province_index: Dict[str, Set[int]] = {}
    district_index: Dict[str, Set[int]] = {}
    ward_index: Dict[str, Set[int]] = {}
    normalized_path_index: Dict[str, List[int]] = {}

    for candidate_index, candidate in enumerate(candidates):
        _index_aliases(
            province_index,
            candidate.get("province_aliases") or set(),
            candidate_index,
        )
        _index_aliases(
            district_index,
            candidate.get("district_aliases") or set(),
            candidate_index,
        )
        _index_aliases(
            ward_index,
            candidate.get("ward_aliases") or set(),
            candidate_index,
        )
        normalized_path = candidate.get("normalized_path") or ""
        if normalized_path:
            normalized_path_index.setdefault(normalized_path, []).append(candidate_index)

    return {
        "candidates": candidates,
        "province_aliases": province_index,
        "district_aliases": district_index,
        "ward_aliases": ward_index,
        "normalized_paths": normalized_path_index,
    }


@lru_cache(maxsize=1)
def _text_candidates() -> List[Dict[str, Any]]:
    """Return cached old-format text candidates for the default data set."""
    return _build_text_candidates(DEFAULT_DATA)


@lru_cache(maxsize=1)
def _text_candidate_index() -> Dict[str, Any]:
    """Return cached old-format text candidate lookup tables."""
    return _build_candidate_search_index(_text_candidates())


def _build_new_text_candidates(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build searchable candidates for new administrative address text."""
    candidates = []
    for ward in data["newWards"].values():
        province = data["newProvinces"].get(ward.get("parent_code"))
        if not province:
            continue

        input_ = {
            "province_name": province.get("name_with_type")
            or province.get("name")
            or "",
            "ward_name": ward.get("name_with_type") or ward.get("name") or "",
            "province_code": province.get("code") or "",
            "ward_code": ward.get("code") or "",
        }
        path = " ".join(filter(None, [input_["ward_name"], input_["province_name"]]))
        candidates.append(
            {
                "input": input_,
                "new_province": province,
                "new_ward": ward,
                "province_aliases": _create_aliases(province, input_["province_name"]),
                "ward_aliases": _create_aliases(ward, input_["ward_name"]),
                "normalized_path": normalize_address_text(path),
            }
        )
    return candidates


@lru_cache(maxsize=1)
def _new_text_candidates() -> List[Dict[str, Any]]:
    """Return cached new-format text candidates for the default data set."""
    return _build_new_text_candidates(DEFAULT_DATA)


@lru_cache(maxsize=1)
def _new_text_candidate_index() -> Dict[str, Any]:
    """Return cached new-format text candidate lookup tables."""
    return _build_candidate_search_index(_new_text_candidates())


def _split_address_tokens(text: Any) -> List[Dict[str, str]]:
    """Split comma-separated address text into normalized token payloads."""
    return [
        {
            "raw": token.strip(),
            "key": normalize_vietnamese_name(token),
            "loose_key": normalize_address_text(token),
        }
        for token in str(text).split(",")
        if token.strip()
    ]


def _alias_matches(aliases: Set[str], token: Dict[str, str]) -> bool:
    """Return whether a token matches either strict or loose aliases."""
    return token["key"] in aliases or token["loose_key"] in aliases


def _candidate_ids_for_token(
    alias_index: Dict[str, Set[int]],
    token: Dict[str, str],
) -> Set[int]:
    """Return candidate indexes matching either strict or loose token keys."""
    matches = set(alias_index.get(token["key"], set()))
    matches.update(alias_index.get(token["loose_key"], set()))
    return matches


def _create_match(
    candidate: Dict[str, Any],
    level: str,
    score: int,
    token_start: Optional[int],
    token_count: Optional[int],
    tokens: List[Dict[str, str]],
    source: str,
) -> Dict[str, Any]:
    """Create a normalized parser match payload."""
    remaining_text = None
    if token_start is not None:
        remaining_text = ", ".join(token["raw"] for token in tokens[:token_start])

    return {
        "candidate": candidate,
        "input": candidate["input"],
        "level": level,
        "score": score,
        "token_start": token_start,
        "token_count": token_count,
        "source": source,
        "remaining_text": remaining_text,
    }


def _pick_better_match(
    current: Optional[Dict[str, Any]],
    candidate: Dict[str, Any],
    level: str,
    score: int,
    token_start: Optional[int],
    token_count: Optional[int],
    tokens: List[Dict[str, str]],
    source: str,
) -> Dict[str, Any]:
    """Keep only the highest-scoring match and build it lazily."""
    if current is not None and current["score"] >= score:
        return current
    return _create_match(
        candidate,
        level,
        score,
        token_start,
        token_count,
        tokens,
        source,
    )


def _add_comma_matches(
    matches: List[Dict[str, Any]],
    candidate: Dict[str, Any],
    tokens: List[Dict[str, str]],
    index: int,
) -> None:
    """Append comma-token matches for a candidate at one token index."""
    remaining = len(tokens) - index
    has_district = bool(candidate.get("district_aliases"))

    if (
        has_district
        and remaining >= 3
        and _alias_matches(candidate["ward_aliases"], tokens[index])
        and _alias_matches(candidate["district_aliases"], tokens[index + 1])
        and _alias_matches(candidate["province_aliases"], tokens[index + 2])
    ):
        matches.append(
            _create_match(
                candidate,
                "province_district_ward_name",
                3000 + index,
                index,
                3,
                tokens,
                "comma",
            )
        )

    if (
        has_district
        and remaining >= 2
        and _alias_matches(candidate["district_aliases"], tokens[index])
        and _alias_matches(candidate["province_aliases"], tokens[index + 1])
    ):
        matches.append(
            _create_match(
                candidate,
                "province_district_name",
                2000 + index,
                index,
                2,
                tokens,
                "comma",
            )
        )

    if (
        has_district
        and remaining >= 2
        and _alias_matches(candidate["ward_aliases"], tokens[index])
        and _alias_matches(candidate["province_aliases"], tokens[index + 1])
    ):
        matches.append(
            _create_match(
                candidate,
                "province_ward_name",
                2400 + index,
                index,
                2,
                tokens,
                "comma",
            )
        )

    if (
        not has_district
        and remaining >= 2
        and _alias_matches(candidate["ward_aliases"], tokens[index])
        and _alias_matches(candidate["province_aliases"], tokens[index + 1])
    ):
        matches.append(
            _create_match(
                candidate,
                "province_ward_name",
                2500 + index,
                index,
                2,
                tokens,
                "comma",
            )
        )

    if _alias_matches(candidate["province_aliases"], tokens[index]):
        matches.append(
            _create_match(
                candidate,
                "province_name",
                1000 + index,
                index,
                1,
                tokens,
                "comma",
            )
        )


def _match_comma_separated_text(
    text: Any,
    candidates: List[Dict[str, Any]],
    search_index: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Find the best administrative match from comma-separated text."""
    tokens = _split_address_tokens(text)
    if not tokens:
        return None

    if search_index:
        indexed = _match_comma_separated_text_indexed(tokens, search_index)
        if indexed:
            return indexed

    matches = []
    for candidate in candidates:
        for index in range(len(tokens)):
            _add_comma_matches(matches, candidate, tokens, index)
    if not matches:
        return None
    return sorted(matches, key=lambda item: item["score"], reverse=True)[0]


def _match_comma_separated_text_indexed(
    tokens: List[Dict[str, str]],
    search_index: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Find the best comma-token match using alias indexes instead of scans."""
    best = None
    candidates = search_index["candidates"]
    province_aliases = search_index["province_aliases"]
    district_aliases = search_index["district_aliases"]
    ward_aliases = search_index["ward_aliases"]

    for index in range(len(tokens)):
        remaining = len(tokens) - index
        province_ids = _candidate_ids_for_token(province_aliases, tokens[index])
        if province_ids:
            for candidate_index in province_ids:
                best = _pick_better_match(
                    best,
                    candidates[candidate_index],
                    "province_name",
                    1000 + index,
                    index,
                    1,
                    tokens,
                    "comma",
                )

        if remaining < 2:
            continue

        ward_ids = _candidate_ids_for_token(ward_aliases, tokens[index])
        district_ids = _candidate_ids_for_token(district_aliases, tokens[index])
        province_next_ids = _candidate_ids_for_token(province_aliases, tokens[index + 1])

        for candidate_index in district_ids & province_next_ids:
            best = _pick_better_match(
                best,
                candidates[candidate_index],
                "province_district_name",
                2000 + index,
                index,
                2,
                tokens,
                "comma",
            )

        for candidate_index in ward_ids & province_next_ids:
            candidate = candidates[candidate_index]
            score = 2400 + index if candidate.get("district_aliases") else 2500 + index
            best = _pick_better_match(
                best,
                candidate,
                "province_ward_name",
                score,
                index,
                2,
                tokens,
                "comma",
            )

        if remaining < 3:
            continue

        district_next_ids = _candidate_ids_for_token(
            district_aliases,
            tokens[index + 1],
        )
        province_third_ids = _candidate_ids_for_token(
            province_aliases,
            tokens[index + 2],
        )
        for candidate_index in ward_ids & district_next_ids & province_third_ids:
            best = _pick_better_match(
                best,
                candidates[candidate_index],
                "province_district_ward_name",
                3000 + index,
                index,
                3,
                tokens,
                "comma",
            )

    return best


def _match_normalized_admin_suffix(
    text: Any,
    search_index: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Match normalized administrative suffix directly via a path lookup."""
    original = str(text)
    start = _find_admin_start_index(original)
    if start is None:
        return None

    admin_text = original[start:].strip()
    normalized_admin = normalize_address_text(admin_text)
    if not normalized_admin:
        return None

    candidate_indexes = search_index["normalized_paths"].get(normalized_admin, [])
    if not candidate_indexes:
        return None

    candidate = search_index["candidates"][candidate_indexes[0]]
    return {
        "candidate": candidate,
        "input": candidate["input"],
        "level": "province_district_ward_name"
        if candidate.get("district_aliases")
        else "province_ward_name",
        "score": 3999,
        "token_start": None,
        "token_count": None,
        "source": "substring",
        "remaining_text": re.sub(r"[\s,]+$", "", original[0:start].strip()),
    }


def _find_admin_start_index(text: str) -> Optional[int]:
    """Find where the administrative suffix starts in original text."""
    # Multi-word variants MUST come before single-word to avoid partial match
    admin_words = (
        r"thị\s+trấn|thi\s+tran"
        r"|thị\s+xã|thi\s+xa"
        r"|thành\s+phố|thanh\s+pho"
        r"|phường|phuong"
        r"|quận|quan"
        r"|huyện|huyen"
        r"|tỉnh|tinh"
        r"|thị|thi"
        r"|xã|xa"
        r"|\btp\b"
    )
    match = re.search(
        rf"(?:^|(?<=[\s,]))({admin_words})(?=\s)",
        text,
        flags=re.IGNORECASE | re.UNICODE,
    )
    if not match:
        return None
    return match.start()


def _find_admin_start_index(text: str) -> Optional[int]:
    """Find where the administrative suffix starts in original text."""
    admin_words = (
        r"thị\s+trấn|thi\s+tran"
        r"|thị\s+xã|thi\s+xa"
        r"|thành\s+phố|thanh\s+pho"
        r"|phường|phuong"
        r"|quận|quan"
        r"|huyện|huyen"
        r"|tỉnh|tinh"
        r"|thị|thi"
        r"|xã|xa"
        r"|\btp\b"
    )
    match = re.search(
        rf"(?:^|(?<=[\s,]))({admin_words})(?=\s)",
        text,
        flags=re.IGNORECASE | re.UNICODE,
    )
    if not match:
        return None
    return match.start()


def _find_admin_start_index(text: str) -> Optional[int]:
    """Find where the administrative suffix starts in original text."""
    if not text or not str(text).strip():
        return None

    admin_prefix = re.compile(
        r"^(?:"
        r"thị\s+trấn|thi\s+tran"
        r"|thị\s+xã|thi\s+xa"
        r"|thành\s+phố|thanh\s+pho"
        r"|phường|phuong"
        r"|quận|quan"
        r"|huyện|huyen"
        r"|tỉnh|tinh"
        r"|thị|thi"
        r"|xã|xa"
        r"|tp"
        r")\s+",
        flags=re.IGNORECASE | re.UNICODE,
    )

    text_value = str(text)
    for match in re.finditer(r"(^|,)\s*", text_value):
        token_start = match.end()
        token = text_value[token_start:].lstrip()
        if not token:
            continue

        token_start += len(text_value[token_start:]) - len(token)
        prefix_match = admin_prefix.match(token)
        if not prefix_match:
            continue

        remainder = token[prefix_match.end() :].lstrip()
        if not remainder:
            continue

        first_char = remainder[0]
        if not (first_char.isupper() or first_char.isdigit()):
            continue

        return token_start

    return None


def _match_substring_text(
    text: Any,
    candidates: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Find the best administrative match using normalized substring search."""
    normalized = normalize_address_text(text)
    if not normalized:
        return None

    searchable = f" {normalized} "
    matches = []
    for candidate in candidates:
        needle = f" {candidate.get('normalized_path') or ''} "
        index = searchable.find(needle)
        if needle.strip() and index != -1:
            matches.append(
                {
                    "candidate": candidate,
                    "input": candidate["input"],
                    "level": "province_district_ward_name"
                    if candidate.get("district_aliases")
                    else "province_ward_name",
                    "score": 3000 + index,
                    "token_start": None,
                    "token_count": None,
                    "source": "substring",
                    "remaining_text": None,
                }
            )

    if not matches:
        return None

    best = sorted(matches, key=lambda item: item["score"], reverse=True)[0]
    start = _find_admin_start_index(str(text))
    best["remaining_text"] = (
        None
        if start is None
        else re.sub(r"[\s,]+$", "", str(text)[0:start].strip())
    )
    return best


def _parse_confidence(match: Optional[Dict[str, Any]]) -> float:
    """Return parser confidence for a text match."""
    if not match:
        return 0
    if match["source"] == "comma":
        return 0.65 if match["level"] == "province_name" else 0.98
    return 0.55 if match["level"] == "province_name" else 0.9


def _parse_strategy(match: Optional[Dict[str, Any]]) -> Optional[str]:
    """Return a readable parser strategy name for a text match."""
    if not match:
        return None
    return "comma_token_alias" if match["source"] == "comma" else "normalized_substring"


def _parse_meta(
    started_at: float,
    data: Dict[str, Any],
    warnings: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Build common parser metadata."""
    warning_list = unique(warnings or [])
    return {
        "parser_version": PARSER_VERSION,
        "mapping_version": data["mapping"].get("meta", {}).get("version"),
        "elapsed_ms": elapsed_ms(started_at),
        "warnings": warning_list,
    }


def _pick_parsed_input(match: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Return only the input fields supported by the match level."""
    if not match:
        return {}
    if match["level"] == "province_name":
        return {
            "province_name": match["input"].get("province_name"),
            "province_code": match["input"].get("province_code"),
        }
    if match["level"] == "province_district_name":
        return {
            "province_name": match["input"].get("province_name"),
            "district_name": match["input"].get("district_name"),
            "province_code": match["input"].get("province_code"),
            "district_code": match["input"].get("district_code"),
        }
    return match["input"]


def _pick_new_parsed_input(match: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Return new-format fields supported by the match level."""
    if not match:
        return {}
    if match["level"] == "province_name":
        return {
            "province_name": match["input"].get("province_name"),
            "province_code": match["input"].get("province_code"),
        }
    return match["input"]


def _empty_old_parse(
    text: Any,
    started_at: float,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """Return an old-address parse result for empty input."""
    return {
        "text": text,
        "parsed": {},
        "street_address": "",
        "match_level": None,
        "source": None,
        "confidence": 0,
        "match_strategy": None,
        "normalized_text": "",
        "meta": _parse_meta(
            started_at,
            data,
            ["Provide a non-empty address text."],
        ),
    }


def _not_found_old_parse(
    text: str,
    started_at: float,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """Return an old-address parse result when no candidate matches."""
    return {
        "text": text,
        "parsed": {},
        "street_address": text,
        "match_level": None,
        "source": None,
        "confidence": 0,
        "match_strategy": None,
        "normalized_text": normalize_address_text(text),
        "meta": _parse_meta(
            started_at,
            data,
            ["Could not parse old administrative address from text."],
        ),
    }


def parse_address_text(
    text: str,
    data: Dict[str, Any] = DEFAULT_DATA,
) -> Dict[str, Any]:
    """Parse old-format administrative address text into structured fields."""
    started_at = now_ms()
    candidates = (
        _text_candidates()
        if data is DEFAULT_DATA
        else _build_text_candidates(data)
    )
    search_index = (
        _text_candidate_index()
        if data is DEFAULT_DATA
        else _build_candidate_search_index(candidates)
    )

    if not isinstance(text, str) or not text.strip():
        return _empty_old_parse(text, started_at, data)

    match = (
        _match_comma_separated_text(text, candidates, search_index)
        or _match_normalized_admin_suffix(text, search_index)
        or _match_substring_text(text, candidates)
    )
    if not match:
        return _not_found_old_parse(text, started_at, data)

    return {
        "text": text,
        "parsed": _pick_parsed_input(match),
        "street_address": match.get("remaining_text") or "",
        "match_level": match["level"],
        "source": match["source"],
        "confidence": _parse_confidence(match),
        "match_strategy": _parse_strategy(match),
        "normalized_text": normalize_address_text(text),
        "meta": _parse_meta(started_at, data),
    }


def _format_new_text(
    street_address: str,
    ward: Optional[Dict[str, Any]],
    province: Optional[Dict[str, Any]],
) -> Optional[str]:
    """Format street text with new ward and province display names."""
    if not ward or not province:
        return None
    return ", ".join(
        filter(
            None,
            [
                street_address,
                ward.get("name_with_type") or ward.get("name"),
                province.get("name_with_type") or province.get("name"),
            ],
        )
    )


def _empty_new_parse(
    text: Any,
    started_at: float,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """Return a new-address parse result for empty input."""
    return {
        "text": text,
        "parsed": {},
        "street_address": "",
        "match_level": None,
        "source": None,
        "new_province": None,
        "new_ward": None,
        "converted_text": None,
        "components": None,
        "confidence": 0,
        "match_strategy": None,
        "normalized_text": "",
        "meta": _parse_meta(
            started_at,
            data,
            ["Provide a non-empty address text."],
        ),
    }


def _not_found_new_parse(
    text: str,
    started_at: float,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """Return a new-address parse result when no candidate matches."""
    return {
        "text": text,
        "parsed": {},
        "street_address": text,
        "match_level": None,
        "source": None,
        "new_province": None,
        "new_ward": None,
        "converted_text": None,
        "components": None,
        "confidence": 0,
        "match_strategy": None,
        "normalized_text": normalize_address_text(text),
        "meta": _parse_meta(
            started_at,
            data,
            ["Could not parse new administrative address from text."],
        ),
    }


def parse_new_address_text(
    text: str,
    data: Dict[str, Any] = DEFAULT_DATA,
) -> Dict[str, Any]:
    """Parse new-format administrative address text into structured fields."""
    started_at = now_ms()
    candidates = (
        _new_text_candidates()
        if data is DEFAULT_DATA
        else _build_new_text_candidates(data)
    )
    search_index = (
        _new_text_candidate_index()
        if data is DEFAULT_DATA
        else _build_candidate_search_index(candidates)
    )

    if not isinstance(text, str) or not text.strip():
        return _empty_new_parse(text, started_at, data)

    match = (
        _match_comma_separated_text(text, candidates, search_index)
        or _match_normalized_admin_suffix(text, search_index)
        or _match_substring_text(text, candidates)
    )
    if not match:
        return _not_found_new_parse(text, started_at, data)

    street_address = match.get("remaining_text") or ""
    province = match["candidate"].get("new_province")
    ward = None
    if match["level"] != "province_name":
        ward = match["candidate"].get("new_ward")
    return {
        "text": text,
        "parsed": _pick_new_parsed_input(match),
        "street_address": street_address,
        "converted_text": _format_new_text(street_address, ward, province),
        "components": {"province": province, "ward": ward}
        if ward and province
        else None,
        "match_level": match["level"],
        "source": match["source"],
        "new_province": province,
        "new_ward": ward,
        "confidence": _parse_confidence(match),
        "match_strategy": _parse_strategy(match),
        "normalized_text": normalize_address_text(text),
        "meta": _parse_meta(started_at, data),
    }


def _format_converted_text(
    street_address: str,
    conversion: Dict[str, Any],
) -> Optional[str]:
    """Format converted old-address output as new address text."""
    result = conversion.get("result")
    if not result:
        return None
    return _format_new_text(
        street_address,
        result.get("new_ward"),
        result.get("new_province"),
    )


def _conversion_components(conversion: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract new province and ward components from conversion output."""
    result = conversion.get("result")
    if not result:
        return None
    return {
        "province": result.get("new_province"),
        "ward": result.get("new_ward"),
    }


def _new_conversion_result(
    new_parse: Dict[str, Any],
    input_type: Optional[str],
) -> Dict[str, Any]:
    """Build conversion-like output for text that is already new-format."""
    province = new_parse.get("new_province") or {}
    ward = new_parse.get("new_ward") or {}
    return {
        "status": "matched" if input_type == "new" else "not_found",
        "match_level": new_parse.get("match_level"),
        "input": new_parse.get("parsed") or {},
        "old": None,
        "result": {
            "new_province": new_parse.get("new_province"),
            "new_ward": new_parse.get("new_ward"),
            "mapping": {
                "new_province_code": province.get("code"),
                "new_ward_code": ward.get("code"),
                "row_indexes": [],
            },
            "warnings": [],
        }
        if input_type == "new"
        else None,
        "candidates": [],
        "warnings": []
        if input_type == "new"
        else ["Could not parse new administrative address from text."],
        "confidence": new_parse.get("confidence") or 0,
        "match_strategy": new_parse.get("match_strategy"),
        "normalized_text": new_parse.get("normalized_text") or "",
    }


def convert_address_text(
    text: str,
    options: Optional[Dict[str, Any]] = None,
    data: Dict[str, Any] = DEFAULT_DATA,
    convert_func: Optional[ConvertFunc] = None,
) -> Dict[str, Any]:
    """Parse address text and return old-to-new conversion details."""
    started_at = now_ms()
    options = options or {}
    if convert_func is None:
        convert_func = lambda payload, convert_options=None: convert_old_to_new(
            payload,
            convert_options,
            data,
        )

    new_parse = parse_new_address_text(text, data)
    old_parse = parse_address_text(text, data)
    conversion = convert_func(
        old_parse.get("parsed") or {},
        options.get("convertOptions") or options,
    )

    if conversion["status"] not in {"not_found", "invalid_input"}:
        should_prefer_new = (
            new_parse.get("match_level") == "province_ward_name"
            and old_parse.get("match_level") != "province_district_ward_name"
        )
        if should_prefer_new:
            converted_text = new_parse.get("converted_text")
            converted = new_parse.get("components")
            input_type = "new" if new_parse.get("match_level") else None
            parse_result = new_parse
        else:
            converted_text = _format_converted_text(
                old_parse.get("street_address") or "",
                conversion,
            )
            converted = _conversion_components(conversion)
            input_type = "old"
            parse_result = old_parse
    elif conversion["status"] == "invalid_input":
        converted_text = None
        converted = None
        input_type = None
        parse_result = old_parse
    else:
        converted_text = new_parse.get("converted_text")
        converted = new_parse.get("components")
        input_type = "new" if new_parse.get("components") else None
        parse_result = new_parse
        conversion = _new_conversion_result(new_parse, input_type)

    warnings = unique(
        [
            *(parse_result.get("meta", {}).get("warnings") or []),
            *(conversion.get("warnings") or []),
        ]
    )
    return {
        "text": text,
        "input_type": input_type,
        "parsed": parse_result.get("parsed") or {},
        "street_address": parse_result.get("street_address") or "",
        "converted_text": converted_text,
        "converted": converted,
        "match_level": parse_result.get("match_level"),
        "conversion": conversion,
        "meta": {
            "parser_version": PARSER_VERSION,
            "mapping_version": (data.get("mapping") or {}).get("meta", {}).get(
                "version"
            ),
            "elapsed_ms": elapsed_ms(started_at),
            "warnings": warnings,
        },
    }


def reverse_new_to_old(
    converted: Optional[Dict[str, Any]],
    data: Dict[str, Any] = DEFAULT_DATA,
) -> List[Dict[str, Any]]:
    """Find old province/district/ward candidates for a new address."""
    province_code = ((converted or {}).get("province") or {}).get("code")
    ward_code = ((converted or {}).get("ward") or {}).get("code")
    if not province_code or not ward_code:
        return []

    candidates = []
    for row in data["mapping"]["rows"]:
        if (
            row["new"].get("province_code") == province_code
            and row["new"].get("ward_code") == ward_code
        ):
            province = data["oldProvinces"].get(row["old"].get("province_code"))
            district = data["oldDistricts"].get(row["old"].get("district_code"))
            ward = data["oldWards"].get(row["old"].get("ward_code"))
            candidates.append(
                {
                    "province": (province or {}).get("name_with_type")
                    or row["old"].get("province_name"),
                    "district": (district or {}).get("name_with_type")
                    or row["old"].get("district_name"),
                    "ward": (ward or {}).get("name_with_type")
                    or row["old"].get("ward_name"),
                    "text": ", ".join(
                        filter(
                            None,
                            [
                                (ward or {}).get("name_with_type"),
                                (district or {}).get("name_with_type"),
                                (province or {}).get("name_with_type"),
                            ],
                        )
                    ),
                    "codes": {
                        "province": row["old"].get("province_code"),
                        "district": row["old"].get("district_code"),
                        "ward": row["old"].get("ward_code"),
                    },
                }
            )
    return candidates


def auto_convert_address(
    text: str,
    options: Optional[Dict[str, Any]] = None,
    data: Dict[str, Any] = DEFAULT_DATA,
    convert_func: Optional[ConvertFunc] = None,
) -> Dict[str, Any]:
    """Automatically parse, detect type, and convert an address string."""
    result = convert_address_text(
        text,
        options or {"multiple": "first"},
        data,
        convert_func=convert_func,
    )
    old_candidates = (
        reverse_new_to_old(result.get("converted"), data)
        if result.get("input_type") == "new"
        else []
    )
    return {
        "input_type": result.get("input_type"),
        "normalized_text": result.get("converted_text"),
        "parsed": result.get("parsed"),
        "converted_new": result.get("converted"),
        "conversion": result.get("conversion"),
        "old_candidates": old_candidates,
        "old_first": old_candidates[0] if old_candidates else None,
    }
