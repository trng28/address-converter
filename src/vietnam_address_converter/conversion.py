from __future__ import annotations

from typing import Any, Dict, List, Optional

from .constants import DEFAULT_OPTIONS, PARSER_VERSION
from .data import DEFAULT_DATA
from .normalize import get_normalized_name_variants, normalize_vietnamese_name
from .utils import elapsed_ms, now_ms, to_code, unique


def _normalize_input_text(input_: Dict[str, Any]) -> str:
    """Build a compact normalized text key from old address input fields."""
    return "|".join(
        filter(
            None,
            [
                normalize_vietnamese_name(input_.get("province_name")),
                normalize_vietnamese_name(input_.get("district_name")),
                normalize_vietnamese_name(input_.get("ward_name")),
            ],
        )
    )


def _has_name_input(input_: Dict[str, Any]) -> bool:
    """Return whether the input contains at least one name field."""
    return bool(
        normalize_vietnamese_name(input_.get("province_name"))
        or normalize_vietnamese_name(input_.get("district_name"))
        or normalize_vietnamese_name(input_.get("ward_name"))
    )


def _get_match_strategy(
    match_level: Optional[str],
    input_: Dict[str, Any],
) -> Optional[str]:
    """Describe how a conversion match was found."""
    if not match_level:
        return None
    if (
        to_code(input_.get("province_code"))
        or to_code(input_.get("district_code"))
        or to_code(input_.get("ward_code"))
    ):
        return "code_or_name_with_code_filter"
    if "name" in match_level:
        return "normalized_name"
    return match_level


def _get_confidence(
    status: str,
    match_level: Optional[str],
    candidates: List[Dict[str, Any]],
) -> float:
    """Calculate a confidence score from status, level, and ambiguity."""
    if status in {"invalid_input", "not_found"}:
        return 0
    if status == "ambiguous" or len(candidates) > 1:
        return 0.6
    scores = {
        "province_district_ward_name": 0.98,
        "province_ward_name": 0.96,
        "ward_code": 0.95,
        "district_ward_name": 0.9,
        "province_district_name": 0.85,
        "district_code": 0.8,
        "province_code": 0.75,
        "district_name": 0.7,
        "province_name": 0.65,
        "ward_name_broad": 0.55,
    }
    return scores.get(match_level, 0.7)


def _intersect_indexes(groups: List[List[int]]) -> List[int]:
    """Intersect non-empty index groups from most selective to broadest."""
    groups = [group for group in groups if group]
    if not groups:
        return []
    groups.sort(key=len)
    result = set(groups[0])
    for group in groups[1:]:
        result &= set(group)
    return sorted(result)


def _indexes_for_names(index: Dict[str, List[int]], names: List[str]) -> List[int]:
    """Return unique row indexes for any normalized name variant."""
    result: List[int] = []
    for name in names:
        result.extend(index.get(name, []))
    return sorted(set(result))


def _get_indexes_by_input(
    input_: Dict[str, Any],
    mapping: Dict[str, Any],
) -> Dict[str, Any]:
    """Find candidate mapping row indexes for old address input."""
    province_name = normalize_vietnamese_name(input_.get("province_name"))
    province_names = get_normalized_name_variants(input_.get("province_name"))
    district_name = normalize_vietnamese_name(input_.get("district_name"))
    ward_name = normalize_vietnamese_name(input_.get("ward_name"))
    province_code = to_code(input_.get("province_code"))
    district_code = to_code(input_.get("district_code"))
    ward_code = to_code(input_.get("ward_code"))
    indexes = mapping.get("indexes", {})
    groups: List[List[int]] = []
    match_level = None

    if province_name and district_name and ward_name:
        groups.append(
            _indexes_for_names(
                indexes.get("by_old_name_path", {}),
                [
                    f"{province_name_variant}|{district_name}|{ward_name}"
                    for province_name_variant in province_names
                ],
            )
        )
        match_level = "province_district_ward_name"
    else:
        if province_name and district_name:
            groups.append(
                _indexes_for_names(
                    indexes.get("by_old_province_district", {}),
                    [
                        f"{province_name_variant}|{district_name}"
                        for province_name_variant in province_names
                    ],
                )
            )
            match_level = "province_district_name"
        elif province_name:
            groups.append(
                _indexes_for_names(
                    indexes.get("by_old_province_name", {}),
                    province_names,
                )
            )
            match_level = "province_name"
        if district_name:
            groups.append(
                indexes.get("by_old_district_name", {}).get(district_name, [])
            )
            match_level = match_level or "district_name"
        if ward_name:
            groups.append(indexes.get("by_old_ward_name", {}).get(ward_name, []))
            if province_name:
                match_level = "province_ward_name"
            elif district_name:
                match_level = "district_ward_name"
            else:
                match_level = "ward_name_broad"

    if province_code:
        groups.append(indexes.get("by_old_province_code", {}).get(province_code, []))
        match_level = match_level or "province_code"
    if district_code:
        groups.append(indexes.get("by_old_district_code", {}).get(district_code, []))
        match_level = match_level or "district_code"
    if ward_code:
        groups.append(indexes.get("by_old_ward_code", {}).get(ward_code, []))
        match_level = match_level if _has_name_input(input_) else "ward_code"

    return {
        "indexes": _intersect_indexes(groups),
        "match_level": match_level,
        "broad_match": match_level
        in {"province_name", "district_name", "ward_name_broad"},
    }


def _validate_relationships(row: Dict[str, Any], data: Dict[str, Any]) -> List[str]:
    """Validate old and new administrative parent-child relationships."""
    warnings = []
    old_province = data["oldProvinces"].get(row["old"].get("province_code"))
    old_district = data["oldDistricts"].get(row["old"].get("district_code"))
    old_ward = data["oldWards"].get(row["old"].get("ward_code"))
    new_province = data["newProvinces"].get(row["new"].get("province_code"))
    new_ward = data["newWards"].get(row["new"].get("ward_code"))
    if not old_province:
        warnings.append(
            f"Old province code {row['old'].get('province_code')} was not found."
        )
    if not old_district:
        warnings.append(
            f"Old district code {row['old'].get('district_code')} was not found."
        )
    if not old_ward:
        warnings.append(f"Old ward code {row['old'].get('ward_code')} was not found.")
    if (
        old_ward
        and old_district
        and old_ward.get("parent_code") != old_district.get("code")
    ):
        warnings.append(
            f"Old ward {old_ward.get('code')} does not belong to old district "
            f"{old_district.get('code')}."
        )
    if (
        old_district
        and old_province
        and old_district.get("parent_code") != old_province.get("code")
    ):
        warnings.append(
            f"Old district {old_district.get('code')} does not belong to old "
            f"province {old_province.get('code')}."
        )
    if not new_province:
        warnings.append(
            f"New province code {row['new'].get('province_code')} was not found."
        )
    if not new_ward:
        warnings.append(f"New ward code {row['new'].get('ward_code')} was not found.")
    if (
        new_ward
        and new_province
        and new_ward.get("parent_code") != new_province.get("code")
    ):
        warnings.append(
            f"New ward {new_ward.get('code')} does not belong to new province "
            f"{new_province.get('code')}."
        )
    return warnings


def _create_candidate(
    row: Dict[str, Any],
    row_index: int,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """Create a conversion candidate from one mapping row."""
    return {
        "old": {
            "province": data["oldProvinces"].get(row["old"].get("province_code")),
            "district": data["oldDistricts"].get(row["old"].get("district_code")),
            "ward": data["oldWards"].get(row["old"].get("ward_code")),
        },
        "new_province": data["newProvinces"].get(row["new"].get("province_code")),
        "new_ward": data["newWards"].get(row["new"].get("ward_code")),
        "mapping": {
            "old_province_code": row["old"].get("province_code"),
            "old_district_code": row["old"].get("district_code"),
            "old_ward_code": row["old"].get("ward_code"),
            "new_province_code": row["new"].get("province_code"),
            "new_ward_code": row["new"].get("ward_code"),
            "row_indexes": [row_index],
        },
        "warnings": _validate_relationships(row, data),
    }


def _candidate_key(candidate: Dict[str, Any]) -> str:
    """Build a stable key for deduplicating candidates."""
    new_ward = candidate.get("new_ward") or {}
    new_province = candidate.get("new_province") or {}
    mapping = candidate.get("mapping", {})
    ward_code = new_ward.get("code") or mapping.get("new_ward_code")
    province_code = new_province.get("code") or mapping.get("new_province_code")
    return f"{ward_code}|{province_code}"


def _dedupe_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge candidates that point to the same new province and ward."""
    by_key: Dict[str, Dict[str, Any]] = {}
    for candidate in candidates:
        key = _candidate_key(candidate)
        if key in by_key:
            by_key[key]["mapping"]["row_indexes"].extend(
                candidate["mapping"].get("row_indexes", [])
            )
        else:
            by_key[key] = candidate
    result = []
    for candidate in by_key.values():
        candidate["mapping"]["row_indexes"] = sorted(
            set(candidate["mapping"].get("row_indexes", []))
        )
        result.append(candidate)
    return result


def _without_old(candidate: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Return a candidate without the old administrative record payload."""
    if not candidate:
        return None
    return {k: v for k, v in candidate.items() if k != "old"}


def _add_conversion_details(result: Dict[str, Any]) -> Dict[str, Any]:
    """Attach confidence, match strategy, and normalized input text."""
    result["confidence"] = _get_confidence(
        result["status"],
        result.get("match_level"),
        result.get("candidates") or [],
    )
    result["match_strategy"] = _get_match_strategy(
        result.get("match_level"),
        result.get("input") or {},
    )
    result["normalized_text"] = _normalize_input_text(result.get("input") or {})
    return result


def _finalize_conversion(
    result: Dict[str, Any],
    data: Dict[str, Any],
    started_at: float,
) -> Dict[str, Any]:
    """Add metadata and de-duplicated warnings to a conversion result."""
    warnings = unique(result.get("warnings") or [])
    result["warnings"] = warnings
    result["meta"] = {
        "parser_version": PARSER_VERSION,
        "mapping_version": (data.get("mapping") or {}).get("meta", {}).get("version"),
        "elapsed_ms": elapsed_ms(started_at),
        "warnings": warnings,
    }
    return result


def _assert_input_consistency(
    input_: Dict[str, Any],
    data: Dict[str, Any],
    warnings: List[str],
) -> None:
    """Append warnings when supplied old codes are missing or inconsistent."""
    province_code = to_code(input_.get("province_code"))
    district_code = to_code(input_.get("district_code"))
    ward_code = to_code(input_.get("ward_code"))
    if province_code and province_code not in data["oldProvinces"]:
        warnings.append(f"Old province code {province_code} was not found.")
    if district_code and district_code not in data["oldDistricts"]:
        warnings.append(f"Old district code {district_code} was not found.")
    if ward_code and ward_code not in data["oldWards"]:
        warnings.append(f"Old ward code {ward_code} was not found.")
    if (
        province_code
        and district_code
        and (data["oldDistricts"].get(district_code) or {}).get("parent_code")
        != province_code
    ):
        warnings.append(
            f"Old district {district_code} does not belong to old province "
            f"{province_code}."
        )
    if (
        district_code
        and ward_code
        and (data["oldWards"].get(ward_code) or {}).get("parent_code")
        != district_code
    ):
        warnings.append(
            f"Old ward {ward_code} does not belong to old district "
            f"{district_code}."
        )


def convert_old_to_new(
    input_: Optional[Dict[str, Any]] = None,
    options: Optional[Dict[str, Any]] = None,
    data: Dict[str, Any] = DEFAULT_DATA,
) -> Dict[str, Any]:
    """Convert old administrative address fields to new province and ward."""
    started_at = now_ms()
    input_ = input_ or {}
    resolved = {**DEFAULT_OPTIONS, **(options or {})}
    warnings: List[str] = []
    found = _get_indexes_by_input(input_, data["mapping"])
    match_level = found["match_level"]
    _assert_input_consistency(input_, data, warnings)

    if not match_level:
        return _finalize_conversion(
            _add_conversion_details(
                {
                    "status": "invalid_input",
                    "match_level": None,
                    "input": input_,
                    "old": None,
                    "result": None,
                    "candidates": [],
                    "warnings": ["Provide at least one name or code field."],
                }
            ),
            data,
            started_at,
        )

    if found["broad_match"] and not resolved.get("allowBroadMatch"):
        return _finalize_conversion(
            _add_conversion_details(
                {
                    "status": "not_found",
                    "match_level": match_level,
                    "input": input_,
                    "old": None,
                    "result": None,
                    "candidates": [],
                    "warnings": [
                        "Input is too broad. Provide province and district "
                        "context, or set allowBroadMatch: True."
                    ],
                }
            ),
            data,
            started_at,
        )

    rows = [(idx, data["mapping"]["rows"][idx]) for idx in found["indexes"]]
    candidates = _dedupe_candidates(
        [_create_candidate(row, idx, data) for idx, row in rows]
    )
    all_warnings = unique(
        [*warnings, *(w for c in candidates for w in c.get("warnings", []))]
    )

    if resolved.get("strict") and all_warnings:
        result = {
            "status": "invalid_input",
            "match_level": match_level,
            "input": input_,
            "old": None,
            "result": None,
            "candidates": [],
            "warnings": all_warnings,
        }
    elif not candidates:
        result = {
            "status": "not_found",
            "match_level": match_level,
            "input": input_,
            "old": None,
            "result": None,
            "candidates": [],
            "warnings": all_warnings,
        }
    elif resolved.get("multiple") == "first":
        first = candidates[0]
        if len(candidates) > 1:
            all_warnings.append(
                f"Multiple candidates found; returning the first of "
                f"{len(candidates)}."
            )
        result = {
            "status": "matched",
            "match_level": match_level,
            "input": input_,
            "old": first.get("old"),
            "result": _without_old(first),
            "candidates": candidates if len(candidates) > 1 else [],
            "warnings": unique(all_warnings),
        }
    else:
        result = {
            "status": "matched" if len(candidates) == 1 else "ambiguous",
            "match_level": match_level,
            "input": input_,
            "old": candidates[0].get("old") if candidates else None,
            "result": _without_old(candidates[0]) if len(candidates) == 1 else None,
            "candidates": candidates,
            "warnings": all_warnings,
        }
    return _finalize_conversion(_add_conversion_details(result), data, started_at)
