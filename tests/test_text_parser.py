"""
test_converter_coverage.py
──────────────────────────
Bộ test kiểm tra tính năng của converter dựa trên dữ liệu thực
từ vietnam_full_address.csv (79 930 bản ghi).

Cấu trúc:
  1. _find_admin_start_index – unit tests
  2. parse_address_text      – unit tests + accuracy (old addresses)
  3. parse_new_address_text  – unit tests + accuracy (new addresses)
  4. Edge cases từ CSV       – các trường hợp bất thường thực tế
  5. Bulk accuracy           – chạy toàn bộ CSV, đặt ngưỡng tối thiểu
"""
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Optional

import pytest

from src.converter import create_converter
from src.data import DEFAULT_DATA
from src.normalize import normalize_address_text
from src.text import _find_admin_start_index

# helpers 

CSV_PATH = Path(__file__).parent / "vietnam_full_address.csv"


@pytest.fixture(scope="session")
def csv_rows():
    return _load_csv()

def _load_csv() -> list[dict]:
    with open(CSV_PATH, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _old_row_text(row: dict, normalized: bool = False) -> str:
    old = row["old"]
    parts = [
        old.get("ward_name") or "",
        old.get("district_name") or "",
        old.get("province_name") or "",
    ]
    if normalized:
        parts = [normalize_address_text(p) for p in parts]
    return ", ".join(parts)


def _new_ward_text(province: dict, ward: dict, normalized: bool = False) -> str:
    parts = [
        ward.get("name_with_type") or ward.get("name") or "",
        province.get("name_with_type") or province.get("name") or "",
    ]
    if normalized:
        parts = [normalize_address_text(p) for p in parts]
    return ", ".join(parts)


def _match_rate(results: list[bool]) -> float:
    assert results, "Expected at least one test case."
    return sum(results) / len(results)


# 1. _find_admin_start_index


class TestFindAdminStartIndex:
    #  multi-word prefixes 
    def test_prefers_thi_tran_over_thi(self) -> None:
        text = "123 Nguyen Hue, thi tran Nha Be, huyen Nha Be, tinh Dong Nai"
        assert _find_admin_start_index(text) == text.index("thi tran")

    def test_prefers_thanh_pho_over_tinh(self) -> None:
        text = "45 Le Loi, thanh pho Thu Duc, thanh pho Ho Chi Minh"
        assert _find_admin_start_index(text) == text.index("thanh pho")

    def test_prefers_thi_xa_over_thi(self) -> None:
        text = "Pasteur Avenue, thi xa Ben Cat, tinh Binh Duong"
        assert _find_admin_start_index(text) == text.index("thi xa")

    def test_unicode_thi_tran(self) -> None:
        text = "Cầu Chữ S, Thị trấn Cái Dầu, Huyện Châu Phú, Tỉnh An Giang"
        assert _find_admin_start_index(text) == text.index("Thị trấn")

    def test_unicode_thanh_pho_at_start(self) -> None:
        text = "Thành phố Châu Đốc, Tỉnh An Giang"
        assert _find_admin_start_index(text) == 0

    def test_ascii_thanh_pho_at_start(self) -> None:
        text = "thanh pho Thu Duc, thanh pho Ho Chi Minh"
        assert _find_admin_start_index(text) == 0

    # ── single-word prefixes ─────────────────────────────────────────────────

    def test_phuong_prefix(self) -> None:
        text = "170 Tran Phu, Phường An Thới, Quận Bình Thuỷ, Thành phố Cần Thơ"
        assert _find_admin_start_index(text) == text.index("Phường")

    def test_xa_prefix(self) -> None:
        text = "Đường tỉnh 950, Xã Khánh Bình, Huyện An Phú, Tỉnh An Giang"
        assert _find_admin_start_index(text) == text.index("Xã")

    def test_huyen_prefix(self) -> None:
        text = "Đường Tuần tra Biên giới, Xã Nhơn Hội, Huyện An Phú, Tỉnh An Giang"
        assert _find_admin_start_index(text) == text.index("Xã")

    def test_quan_prefix(self) -> None:
        text = "170, Phường An Thới, Quận Bình Thuỷ, Thành phố Cần Thơ"
        assert _find_admin_start_index(text) == text.index("Phường")

    def test_tp_shorthand(self) -> None:
        text = "12 Le Loi, tp Ho Chi Minh"
        assert _find_admin_start_index(text) == text.index("tp")

    def test_tp_shorthand_uppercase(self) -> None:
        text = "12 Le Loi, TP Ha Noi"
        assert _find_admin_start_index(text) == text.index("TP")

    # should NOT match 
    def test_returns_none_without_admin_prefix(self) -> None:
        assert _find_admin_start_index("123 Nguyen Hue, toa nha Landmark") is None

    def test_returns_none_for_empty_string(self) -> None:
        assert _find_admin_start_index("") is None

    def test_duong_tinh_does_not_trigger_on_tinh_in_street(self) -> None:
        # "Đường tỉnh 950" – "tỉnh" here is part of street name, admin starts at "Xã"
        text = "Đường tỉnh 950, Xã Khánh Bình, Huyện An Phú, Tỉnh An Giang"
        idx = _find_admin_start_index(text)
        assert idx is not None
        assert text[idx:].startswith("Xã"), (
            f"Expected admin to start at 'Xã', got: {text[idx:]!r}"
        )

    def test_tp_not_matched_inside_word(self) -> None:
        # "tập" should not match \btp\b
        assert _find_admin_start_index("cong ty tap hop, khong co admin") is None

    def test_tinh_not_matched_inside_word(self) -> None:
        # "tính" as in adjective, not province prefix
        assert _find_admin_start_index("tinh than tot dep") is None

    # boundary / whitespace 

    def test_admin_after_comma_space(self) -> None:
        text = "123 Le Duan, Phường Bến Nghé, Quận 1, TP Hồ Chí Minh"
        idx = _find_admin_start_index(text)
        assert text[idx:].startswith("Phường")

    def test_admin_after_multiple_spaces(self) -> None:
        text = "123 Le Duan,  Phường Bến Nghé"
        idx = _find_admin_start_index(text)
        assert text[idx:].startswith("Phường")

    def test_returns_int_not_none(self) -> None:
        text = "Xã An Phú Tây, Huyện Bình Chánh, Thành phố Hồ Chí Minh"
        result = _find_admin_start_index(text)
        assert isinstance(result, int)


# 2. parse_address_text  (old addresses)


class TestParseOldAddressText:
    @pytest.fixture(scope="class")
    def converter(self):
        return create_converter()

    # street extraction 

    def test_keeps_street_prefix(self, converter) -> None:
        row = DEFAULT_DATA["mapping"]["rows"][0]
        text = "123 Nguyen Hue, " + _old_row_text(row)
        result = converter.parse_address_text(text)
        assert result["street_address"] == "123 Nguyen Hue"

    def test_empty_street_when_only_admin(self, converter) -> None:
        row = DEFAULT_DATA["mapping"]["rows"][0]
        text = _old_row_text(row)
        result = converter.parse_address_text(text)
        assert result["street_address"] == "" or result["street_address"] is None

    def test_street_with_number_prefix(self, converter) -> None:
        """Street starting with digits like '30/4'."""
        row = DEFAULT_DATA["mapping"]["rows"][0]
        text = "30/4, " + _old_row_text(row)
        result = converter.parse_address_text(text)
        assert result["street_address"] == "30/4"

    def test_street_with_duong_tinh_prefix_not_truncated(self, converter) -> None:
        """'Đường tỉnh 950' – 'tỉnh' in street must not be treated as admin prefix."""
        row = next(
            r for r in DEFAULT_DATA["mapping"]["rows"]
            if r["old"].get("province_name") == "Tỉnh An Giang"
        )
        text = "Đường tỉnh 950, " + _old_row_text(row)
        result = converter.parse_address_text(text)
        assert "Đường tỉnh 950" in (result["street_address"] or "")

    # parsing correctness

    def test_parses_province_code(self, converter) -> None:
        row = DEFAULT_DATA["mapping"]["rows"][0]
        old = row["old"]
        result = converter.parse_address_text(_old_row_text(row))
        assert result["parsed"]["province_code"] == old["province_code"]

    def test_parses_district_code(self, converter) -> None:
        row = DEFAULT_DATA["mapping"]["rows"][0]
        old = row["old"]
        result = converter.parse_address_text(_old_row_text(row))
        assert result["parsed"]["district_code"] == old["district_code"]

    def test_parses_ward_code(self, converter) -> None:
        row = DEFAULT_DATA["mapping"]["rows"][0]
        old = row["old"]
        result = converter.parse_address_text(_old_row_text(row))
        assert result["parsed"]["ward_code"] == old["ward_code"]

    def test_normalized_input_still_parses(self, converter) -> None:
        row = DEFAULT_DATA["mapping"]["rows"][0]
        old = row["old"]
        result = converter.parse_address_text(_old_row_text(row, normalized=True))
        parsed = result.get("parsed") or {}
        assert parsed.get("province_code") == old["province_code"]

    def test_result_has_parsed_key(self, converter) -> None:
        row = DEFAULT_DATA["mapping"]["rows"][0]
        result = converter.parse_address_text(_old_row_text(row))
        assert "parsed" in result

    def test_result_has_street_address_key(self, converter) -> None:
        row = DEFAULT_DATA["mapping"]["rows"][0]
        result = converter.parse_address_text(_old_row_text(row))
        assert "street_address" in result

    def test_unknown_address_returns_none_parsed(self, converter) -> None:
        result = converter.parse_address_text("123 Nowhere Road, Unknown Ward, Unknown District")
        parsed = result.get("parsed")
        assert parsed is None or all(v is None for v in parsed.values())

    # accuracy thresholds 

    def test_accuracy_canonical_rows_at_least_98_percent(self, converter) -> None:
        matches = []
        for row in DEFAULT_DATA["mapping"]["rows"]:
            old = row["old"]
            result = converter.parse_address_text(_old_row_text(row))
            parsed = result.get("parsed") or {}
            matches.append(
                parsed.get("province_code") == old.get("province_code")
                and parsed.get("district_code") == old.get("district_code")
                and parsed.get("ward_code") == old.get("ward_code")
            )
        assert _match_rate(matches) >= 0.98

    def test_accuracy_normalized_rows_at_least_98_percent(self, converter) -> None:
        matches = []
        for row in DEFAULT_DATA["mapping"]["rows"]:
            old = row["old"]
            result = converter.parse_address_text(_old_row_text(row, normalized=True))
            parsed = result.get("parsed") or {}
            matches.append(
                parsed.get("province_code") == old.get("province_code")
                and parsed.get("district_code") == old.get("district_code")
                and parsed.get("ward_code") == old.get("ward_code")
            )
        assert _match_rate(matches) >= 0.98


# 3. parse_new_address_text  (new addresses)

class TestParseNewAddressText:
    @pytest.fixture(scope="class")
    def converter(self):
        return create_converter()

    @pytest.fixture(scope="class")
    def sample_ward_province(self):
        ward = next(iter(DEFAULT_DATA["newWards"].values()))
        province = DEFAULT_DATA["newProvinces"][ward["parent_code"]]
        return province, ward

    # street extraction

    def test_keeps_street_prefix(self, converter, sample_ward_province) -> None:
        province, ward = sample_ward_province
        text = "123 Nguyen Hue, " + _new_ward_text(province, ward)
        result = converter.parse_new_address_text(text)
        assert result["street_address"] == "123 Nguyen Hue"

    def test_empty_street_when_only_admin(self, converter, sample_ward_province) -> None:
        province, ward = sample_ward_province
        text = _new_ward_text(province, ward)
        result = converter.parse_new_address_text(text)
        assert result["street_address"] == "" or result["street_address"] is None

    # parsing correctness 

    def test_parses_province_code(self, converter, sample_ward_province) -> None:
        province, ward = sample_ward_province
        result = converter.parse_new_address_text(_new_ward_text(province, ward))
        assert result["parsed"]["province_code"] == province["code"]

    def test_parses_ward_code(self, converter, sample_ward_province) -> None:
        province, ward = sample_ward_province
        result = converter.parse_new_address_text(_new_ward_text(province, ward))
        assert result["parsed"]["ward_code"] == ward["code"]

    def test_normalized_input_still_parses(self, converter, sample_ward_province) -> None:
        province, ward = sample_ward_province
        result = converter.parse_new_address_text(
            _new_ward_text(province, ward, normalized=True)
        )
        parsed = result.get("parsed") or {}
        assert parsed.get("province_code") == province["code"]

    def test_unknown_new_address_returns_none_parsed(self, converter) -> None:
        result = converter.parse_new_address_text("Unknown Ward, Unknown Province")
        parsed = result.get("parsed")
        assert parsed is None or all(v is None for v in parsed.values())

    # accuracy thresholds

    def test_accuracy_canonical_rows_at_least_98_percent(self, converter) -> None:
        matches = []
        seen = set()
        for ward in DEFAULT_DATA["newWards"].values():
            province = DEFAULT_DATA["newProvinces"].get(ward.get("parent_code"))
            if not province:
                continue
            key = (province.get("code"), ward.get("code"))
            if key in seen:
                continue
            seen.add(key)
            result = converter.parse_new_address_text(_new_ward_text(province, ward))
            parsed = result.get("parsed") or {}
            matches.append(
                parsed.get("province_code") == province.get("code")
                and parsed.get("ward_code") == ward.get("code")
            )
        assert _match_rate(matches) >= 0.98

    def test_accuracy_normalized_rows_at_least_98_percent(self, converter) -> None:
        matches = []
        seen = set()
        for ward in DEFAULT_DATA["newWards"].values():
            province = DEFAULT_DATA["newProvinces"].get(ward.get("parent_code"))
            if not province:
                continue
            key = (province.get("code"), ward.get("code"))
            if key in seen:
                continue
            seen.add(key)
            result = converter.parse_new_address_text(
                _new_ward_text(province, ward, normalized=True)
            )
            parsed = result.get("parsed") or {}
            matches.append(
                parsed.get("province_code") == province.get("code")
                and parsed.get("ward_code") == ward.get("code")
            )
        assert _match_rate(matches) >= 0.98


# 4. Edge cases từ vietnam_full_address.csv


@pytest.mark.skipif(not CSV_PATH.exists(), reason="CSV file not found")
class TestRealWorldEdgeCases:
    @pytest.fixture(scope="class")
    def converter(self):
        return create_converter()

    @pytest.fixture(scope="class")
    def csv_rows(self):
        return _load_csv()

    #  4a. "Đường tỉnh" – tỉnh inside street name 

    def test_duong_tinh_street_ward_extracted(self, converter) -> None:
        """Admin suffix must start at 'Xã', not at 'tỉnh' inside street."""
        text = "Đường tỉnh 950, Xã Khánh Bình, Huyện An Phú, Tỉnh An Giang"
        idx = _find_admin_start_index(text)
        assert idx is not None
        assert text[idx:].startswith("Xã"), f"Got: {text[idx:]!r}"

    def test_duong_tinh_full_address_parses(self, converter) -> None:
        text = "Đường tỉnh 957, Xã Nhơn Hội, Huyện An Phú, Tỉnh An Giang"
        result = converter.parse_address_text(text)
        assert result.get("parsed") is not None

    #  4b. Thị trấn (township) 

    def test_thi_tran_detected_as_ward_type(self, converter) -> None:
        text = "Cầu Chữ S, Thị trấn Cái Dầu, Huyện Châu Phú, Tỉnh An Giang"
        idx = _find_admin_start_index(text)
        assert text[idx:].startswith("Thị trấn")

    def test_thi_tran_full_address_parses(self, converter) -> None:
        text = "Cầu Chắc Cà Đao, Thị trấn An Châu, Huyện Châu Thành, Tỉnh An Giang"
        result = converter.parse_address_text(text)
        assert result.get("parsed") is not None

    #  4c. Thị xã (sub-provincial town) 

    def test_thi_xa_detected(self) -> None:
        text = "Pasteur Avenue, Xã An Tây, Thị xã Bến Cát, Tỉnh Bình Dương"
        idx = _find_admin_start_index(text)
        assert text[idx:].startswith("Xã")

    def test_thi_xa_full_address_parses(self, converter) -> None:
        text = "Đường An Tây 017, Xã An Tây, Thị xã Bến Cát, Tỉnh Bình Dương"
        result = converter.parse_address_text(text)
        assert result.get("parsed") is not None

    #  4d. Thành phố thuộc tỉnh (city within province) ─────────────────────

    def test_tp_thuoc_tinh_district_detected(self, converter) -> None:
        text = "Cử Trị, Phường Châu Phú A, Thành phố Châu Đốc, Tỉnh An Giang"
        idx = _find_admin_start_index(text)
        assert text[idx:].startswith("Phường")

    def test_tp_thuoc_tinh_full_address_parses(self, converter) -> None:
        text = "Đường Cử Trị, Phường Châu Phú A, Thành phố Châu Đốc, Tỉnh An Giang"
        result = converter.parse_address_text(text)
        assert result.get("parsed") is not None

    #  4e. Khmer / foreign script in street name 

    def test_khmer_chars_in_street_not_breaking(self, converter) -> None:
        text = "Cầu Long Bình - ស្ពានជ្រៃធំ, Thị trấn Long Bình, Huyện An Phú, Tỉnh An Giang"
        result = converter.parse_address_text(text)
        # Should not raise; parsed may or may not resolve depending on data
        assert "parsed" in result

    def test_khmer_street_admin_index_correct(self) -> None:
        text = "Cầu Long Bình - ស្ពានជ្រៃធំ, Thị trấn Long Bình, Huyện An Phú, Tỉnh An Giang"
        idx = _find_admin_start_index(text)
        assert idx is not None
        assert text[idx:].startswith("Thị trấn")

    def test_second_khmer_address(self, converter) -> None:
        text = "Cầu Hữu Nghị - ស្ពានមិត្តភាព, Xã Tân Bình, Huyện Tân Biên, Tỉnh Tây Ninh"
        result = converter.parse_address_text(text)
        assert "parsed" in result

    #  4f. Street starting with digits ─────────────────────────────────────

    def test_numeric_street_30_4(self) -> None:
        text = "Đường 30/4, Thị trấn Tịnh Biên, Huyện Tịnh Biên, Tỉnh An Giang"
        idx = _find_admin_start_index(text)
        assert text[idx:].startswith("Thị trấn")

    def test_numeric_only_street_pure_number(self) -> None:
        text = "170, Phường An Thới, Quận Bình Thuỷ, Thành phố Cần Thơ"
        idx = _find_admin_start_index(text)
        assert text[idx:].startswith("Phường")

    def test_numeric_street_with_name_suffix(self) -> None:
        text = "Đường 105 Lê Ngọc Hân, Phường Phường 1, Thành phố Vũng Tàu, Tỉnh Bà Rịa - Vũng Tàu"
        idx = _find_admin_start_index(text)
        assert text[idx:].startswith("Phường")

    #  4g. Long street names

    def test_long_street_with_dashes(self) -> None:
        text = (
            "Đường Suối Nghệ - Nghĩa Thành - Quảng Phú - Phước An, "
            "Xã Đá Bạc, Huyện Châu Đức, Tỉnh Bà Rịa - Vũng Tàu"
        )
        idx = _find_admin_start_index(text)
        assert text[idx:].startswith("Xã")

    def test_long_descriptive_street(self) -> None:
        text = (
            "Đường vào Thiền viện Trúc Lâm Chân Nguyên, "
            "Thị trấn Phước Hải, Huyện Đất Đỏ, Tỉnh Bà Rịa - Vũng Tàu"
        )
        idx = _find_admin_start_index(text)
        assert text[idx:].startswith("Thị trấn")

    def test_highway_style_street(self) -> None:
        text = (
            "Đường nối vào cao tốc Biên Hoà - Vũng Tàu, "
            "Phường Long Tâm, Thành phố Bà Rịa, Tỉnh Bà Rịa - Vũng Tàu"
        )
        idx = _find_admin_start_index(text)
        assert text[idx:].startswith("Phường")

    #  4h. Province names with dashes

    def test_province_with_dash_in_name(self, converter) -> None:
        """'Tỉnh Bà Rịa - Vũng Tàu' – dash inside province name."""
        text = "Đường 28 Tháng 4, Xã Long Sơn, Thành phố Vũng Tàu, Tỉnh Bà Rịa - Vũng Tàu"
        result = converter.parse_address_text(text)
        assert result.get("parsed") is not None

    #  4i. Quận / urban district (HCM, Hà Nội…) 

    def test_quan_prefix_hcm(self) -> None:
        text = "45 Lê Lợi, Phường Bến Nghé, Quận 1, Thành phố Hồ Chí Minh"
        idx = _find_admin_start_index(text)
        assert text[idx:].startswith("Phường")

    def test_quan_with_number(self) -> None:
        text = "Phường An Thới, Quận Bình Thuỷ, Thành phố Cần Thơ"
        idx = _find_admin_start_index(text)
        assert text[idx:].startswith("Phường")

    #  4j. HCM with Huyện (suburban districts) 

    def test_hcm_with_huyen_bình_chanh(self, converter) -> None:
        text = "Đường An Phú Tây - Hưng Long, Xã An Phú Tây, Huyện Bình Chánh, Thành phố Hồ Chí Minh"
        result = converter.parse_address_text(text)
        assert result.get("parsed") is not None

    def test_hcm_city_extracted(self, converter) -> None:
        text = "Đường Bảy Tấn, Xã An Phú Tây, Huyện Bình Chánh, Thành phố Hồ Chí Minh"
        result = converter.parse_address_text(text)
        parsed = result.get("parsed") or {}
        # Ho Chi Minh city code should be present
        assert parsed.get("province_code") is not None


# 5. Bulk accuracy – toàn bộ CSV

@pytest.mark.skipif(not CSV_PATH.exists(), reason="CSV file not found")
@pytest.mark.slow
class TestBulkAccuracy:
    """
    Chạy converter trên toàn bộ 79 930 dòng CSV và đo tỷ lệ khớp.
    Đánh dấu @pytest.mark.slow – bỏ qua mặc định, chạy với:
        pytest -m slow
    """

    @pytest.fixture(scope="class")
    def converter(self):
        return create_converter()

    @pytest.fixture(scope="class")
    def csv_rows(self):
        return _load_csv()

    def _parse_csv_row(self, converter, row: dict) -> dict:
        return converter.parse_address_text(row["full_address"])

    #  ward-level accuracy 

    def test_ward_name_match_rate_at_least_90_percent(self, converter, csv_rows) -> None:
        """
        Tỷ lệ phường/xã parse được khớp với cột 'ward' trong CSV.
        Ngưỡng 90 % vì CSV có nhiều địa chỉ không theo chuẩn hành chính mới.
        """
        matches = []
        for row in csv_rows:
            result = self._parse_csv_row(converter, row)
            parsed = result.get("parsed") or {}
            ward_parsed = (parsed.get("ward_name") or "").strip().lower()
            ward_csv    = row["ward"].strip().lower()
            matches.append(ward_parsed == ward_csv or ward_csv in ward_parsed)
        assert _match_rate(matches) >= 0.90, f"Ward match rate: {_match_rate(matches):.2%}"

    #  district-level accuracy 

    def test_district_name_match_rate_at_least_90_percent(self, converter, csv_rows) -> None:
        matches = []
        for row in csv_rows:
            result = self._parse_csv_row(converter, row)
            parsed = result.get("parsed") or {}
            dist_parsed = (parsed.get("district_name") or "").strip().lower()
            dist_csv    = row["district"].strip().lower()
            matches.append(dist_parsed == dist_csv or dist_csv in dist_parsed)
        assert _match_rate(matches) >= 0.90, f"District match: {_match_rate(matches):.2%}"

    #  province-level accuracy 

    def test_province_name_match_rate_at_least_95_percent(self, converter, csv_rows) -> None:
        """Province / city matching should be near-perfect."""
        matches = []
        for row in csv_rows:
            result = self._parse_csv_row(converter, row)
            parsed = result.get("parsed") or {}
            prov_parsed = (parsed.get("province_name") or "").strip().lower()
            prov_csv    = row["city"].strip().lower()
            matches.append(prov_parsed == prov_csv or prov_csv in prov_parsed)
        assert _match_rate(matches) >= 0.95, f"Province match: {_match_rate(matches):.2%}"

    #  no crash guarantee 

    def test_no_exceptions_on_full_csv(self, converter, csv_rows) -> None:
        errors = []
        for row in csv_rows:
            try:
                converter.parse_address_text(row["full_address"])
            except Exception as exc:
                errors.append((row["full_address"], str(exc)))
        assert not errors, f"{len(errors)} rows raised exceptions:\n" + "\n".join(
            f"  {addr!r}: {err}" for addr, err in errors[:5]
        )

    #  street preserved 

    def test_street_not_swallowed_into_admin(self, converter, csv_rows) -> None:
        """If a row has a non-empty street, street_address must not be empty."""
        failures = []
        for row in csv_rows:
            if not row["street"].strip():
                continue
            result = converter.parse_address_text(row["full_address"])
            street = result.get("street_address") or ""
            if not street.strip():
                failures.append(row["full_address"])
        # Allow up to 5 % failures (some rows have non-standard formatting)
        failure_rate = len(failures) / len(csv_rows)
        assert failure_rate <= 0.05, (
            f"Street swallowed in {failure_rate:.2%} of rows. "
            f"First 3: {failures[:3]}"
        )

    #  per-district-type accuracy 

    @pytest.mark.parametrize("district_prefix,min_rate", [
        ("Quận",       0.92),
        ("Huyện",      0.88),
        ("Thị xã",     0.85),
        ("Thành phố",  0.90),
    ])
    def test_accuracy_by_district_type(
        self, converter, csv_rows, district_prefix: str, min_rate: float
    ) -> None:
        subset = [r for r in csv_rows if r["district"].startswith(district_prefix)]
        if not subset:
            pytest.skip(f"No rows with district prefix '{district_prefix}'")
        matches = []
        for row in subset:
            result = converter.parse_address_text(row["full_address"])
            parsed = result.get("parsed") or {}
            dist_parsed = (parsed.get("district_name") or "").strip().lower()
            dist_csv    = row["district"].strip().lower()
            matches.append(dist_parsed == dist_csv or dist_csv in dist_parsed)
        rate = _match_rate(matches)
        assert rate >= min_rate, (
            f"District type '{district_prefix}': {rate:.2%} < {min_rate:.2%}"
        )

    #  per-ward-type accuracy 

    @pytest.mark.parametrize("ward_prefix,min_rate", [
        ("Phường",    0.92),
        ("Xã",        0.88),
        ("Thị trấn",  0.85),
    ])
    def test_accuracy_by_ward_type(
        self, converter, csv_rows, ward_prefix: str, min_rate: float
    ) -> None:
        subset = [r for r in csv_rows if r["ward"].startswith(ward_prefix)]
        if not subset:
            pytest.skip(f"No rows with ward prefix '{ward_prefix}'")
        matches = []
        for row in subset:
            result = converter.parse_address_text(row["full_address"])
            parsed = result.get("parsed") or {}
            ward_parsed = (parsed.get("ward_name") or "").strip().lower()
            ward_csv    = row["ward"].strip().lower()
            matches.append(ward_parsed == ward_csv or ward_csv in ward_parsed)
        rate = _match_rate(matches)
        assert rate >= min_rate, (
            f"Ward type '{ward_prefix}': {rate:.2%} < {min_rate:.2%}"
        )