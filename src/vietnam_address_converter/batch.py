from __future__ import annotations

import csv
from collections import OrderedDict
from typing import Any, Dict, Iterable, Optional

from .converter import VietnamAdministrativeAddressConverter, create_converter


OUTPUT_COLUMNS = [
    "index",
    "full_address",
    "street",
    "ward",
    "district",
    "city",
    "full_address_new",
]


def _flatten_result(
    row: Dict[str, Any],
    result: Dict[str, Any],
    row_index: int,
) -> Dict[str, Any]:
    """Flatten one conversion result into the standardized output schema."""
    converted = result.get("converted") or {}
    province = converted.get("province") or {}
    ward = converted.get("ward") or {}
    full_address_new = (
        result.get("normalized_text")
        or result.get("converted_text")
        or (
            ", ".join(
                part
                for part in [
                    result.get("street_address") or row.get("street") or "",
                    ward.get("name_with_type") or ward.get("name") or "",
                    province.get("name_with_type") or province.get("name") or "",
                ]
                if part
            )
            if (ward.get("name_with_type") or ward.get("name"))
            and (province.get("name_with_type") or province.get("name"))
            else ""
        )
    )

    return {
        "index": row.get("index") or row.get("STT") or row_index,
        "full_address": row.get("full_address") or "",
        "street": row.get("street") or "",
        "ward": row.get("ward") or "",
        "district": row.get("district") or "",
        "city": row.get("city") or "",
        "full_address_new": full_address_new,
    }


def iter_converted_rows(
    input_csv_path: str,
    address_column: str = "full_address",
    converter: Optional[VietnamAdministrativeAddressConverter] = None,
    cache_size: int = 4096,
) -> Iterable[Dict[str, Any]]:
    """Yield converted CSV rows one by one for large-file processing."""
    active_converter = converter or create_converter()
    cache: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()

    with open(input_csv_path, newline="", encoding="utf-8-sig") as input_file:
        reader = csv.DictReader(input_file)
        for row_index, row in enumerate(reader, start=1):
            address = (row.get(address_column) or "").strip()
            cached = cache.get(address)
            if cached is None:
                cached = active_converter.auto_convert_address(address)
                cache[address] = cached
                if cache_size > 0 and len(cache) > cache_size:
                    cache.popitem(last=False)
            else:
                cache.move_to_end(address)
            yield _flatten_result(row, cached, row_index)


def convert_csv_file(
    input_csv_path: str,
    output_csv_path: str,
    address_column: str = "full_address",
    converter: Optional[VietnamAdministrativeAddressConverter] = None,
    cache_size: int = 4096,
) -> int:
    """Convert a CSV file in streaming mode and return the written row count."""
    row_count = 0
    row_iter = iter_converted_rows(
        input_csv_path,
        address_column,
        converter,
        cache_size=cache_size,
    )

    first_row = next(row_iter, None)
    if first_row is None:
        with open(output_csv_path, "w", newline="", encoding="utf-8") as output_file:
            output_file.write("")
        return 0

    with open(output_csv_path, "w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerow(first_row)
        row_count += 1

        for row in row_iter:
            writer.writerow(row)
            row_count += 1

    return row_count
