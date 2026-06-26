from __future__ import annotations

from typing import Any, Dict, List, Optional

from .conversion import convert_old_to_new
from .data import DEFAULT_DATA
from .normalize import normalize_address_text
from .text import (
    _build_new_text_candidates,
    _build_text_candidates,
    _format_new_text,
    _match_comma_separated_text,
    _match_substring_text,
    _parse_confidence,
    _parse_meta,
    _parse_strategy,
    _pick_parsed_input,
    auto_convert_address,
    convert_address_text,
    reverse_new_to_old,
)
from .utils import now_ms


class VietnamAdministrativeAddressConverter:
    """Reusable converter for Vietnamese administrative address data."""

    def __init__(self, data: Optional[Dict[str, Any]] = None):
        """Initialize indexes and text candidates for the supplied data set."""
        self.data = data or DEFAULT_DATA
        self.indexes = {
            "oldProvinces": self.data.get("oldProvinces", {}),
            "oldDistricts": self.data.get("oldDistricts", {}),
            "oldWards": self.data.get("oldWards", {}),
            "newProvinces": self.data.get("newProvinces", {}),
            "newWards": self.data.get("newWards", {}),
        }
        self._text_candidates = _build_text_candidates(self.data)
        self._new_text_candidates = _build_new_text_candidates(self.data)

    def convert_old_to_new(
        self,
        input_: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Convert old province/district/ward input to the new structure."""
        return convert_old_to_new(input_, options, self.data)

    def parse_address_text(self, text: str) -> Dict[str, Any]:
        """Parse an old-format administrative address from free-form text."""
        started_at = now_ms()
        if not isinstance(text, str) or not text.strip():
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
                    self.data,
                    ["Provide a non-empty address text."],
                ),
            }

        match = _match_comma_separated_text(
            text,
            self._text_candidates,
        ) or _match_substring_text(text, self._text_candidates)

        if not match:
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
                    self.data,
                    ["Could not parse old administrative address from text."],
                ),
            }

        return {
            "text": text,
            "parsed": _pick_parsed_input(match),
            "street_address": match.get("remaining_text") or "",
            "match_level": match["level"],
            "source": match["source"],
            "confidence": _parse_confidence(match),
            "match_strategy": _parse_strategy(match),
            "normalized_text": normalize_address_text(text),
            "meta": _parse_meta(started_at, self.data),
        }

    def parse_new_address_text(self, text: str) -> Dict[str, Any]:
        """Parse a new-format administrative address from free-form text."""
        started_at = now_ms()
        if not isinstance(text, str) or not text.strip():
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
                    self.data,
                    ["Provide a non-empty address text."],
                ),
            }

        match = _match_comma_separated_text(
            text,
            self._new_text_candidates,
        ) or _match_substring_text(text, self._new_text_candidates)

        if not match:
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
                    self.data,
                    ["Could not parse new administrative address from text."],
                ),
            }

        street_address = match.get("remaining_text") or ""
        province = match["candidate"].get("new_province")
        ward = match["candidate"].get("new_ward")
        return {
            "text": text,
            "parsed": match["input"],
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
            "meta": _parse_meta(started_at, self.data),
        }

    def convert_address_text(
        self,
        text: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Parse and convert old-format address text to new components."""
        return convert_address_text(text, options, self.data, self.convert_old_to_new)

    def reverse_new_to_old(
        self,
        converted: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Find old administrative addresses for a converted new address."""
        return reverse_new_to_old(converted, self.data)

    def auto_convert_address(
        self,
        text: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Automatically detect address type and return conversion details."""
        return auto_convert_address(
            text,
            options,
            self.data,
            convert_func=self.convert_old_to_new,
        )


def create_converter(
    custom_data: Optional[Dict[str, Any]] = None,
) -> VietnamAdministrativeAddressConverter:
    """Create a converter instance using default data or custom data."""
    return VietnamAdministrativeAddressConverter(custom_data or DEFAULT_DATA)
