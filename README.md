# Vietnam Administrative Address Converter

Convert Vietnamese administrative addresses between the old and new administrative structures.

The converter can parse free-form address text, detect whether it looks like an old or new address, and return normalized province/ward conversion data as JSON.

## Features

- Convert old province/district/ward addresses to the new province/ward structure.
- Parse free-form address text from the command line.
- Return structured JSON with parsed input, converted output, mapping data, confidence, and warnings.
- Run with the Python standard library only.

## Installation

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

Install requirements:

```powershell
pip install -r requirements.txt
```

## Command Line Usage

```python
python main.py --address "Đường Trần Não, Phường Thảo Điền, TP Thủ Đức, Thành phố Hồ Chí Minh" 
```

Shortened output:

```json
{
  "input_type": "old",
  "normalized_text": "Đường Trần Não, Phường An Khánh, Thành phố Hồ Chí Minh",
  "parsed": {
    "province_name": "Thành Phố Hồ Chí Minh",
    "district_name": "Thành Phố Thủ Đức",
    "ward_name": "Phường Thảo Điền",
    "province_code": "12",
    "district_code": "4876",
    "ward_code": "1774348"
  },
  "converted_new": {
    "province": {
      "name": "Hồ Chí Minh",
      "slug": "ho-chi-minh",
      "type": "thanh-pho",
      "name_with_type": "Thành phố Hồ Chí Minh",
      "code": "12"
    },
    "ward": {
      "name": "An Khánh",
      "type": "phuong",
      "slug": "an-khanh",
      "name_with_type": "Phường An Khánh",
      "path": "An Khánh, Hồ Chí Minh",
      "path_with_type": "Phường An Khánh, Thành phố Hồ Chí Minh",
      "code": "11020",
      "parent_code": "12"
    }
  },
  "conversion": {
    "status": "matched",
    "match_level": "province_district_ward_name",
    "input": {
      "province_name": "Thành Phố Hồ Chí Minh",
      "district_name": "Thành Phố Thủ Đức",
      "ward_name": "Phường Thảo Điền",
      "province_code": "12",
      "district_code": "4876",
      "ward_code": "1774348"
    },
    "old": {
      "province": {
        "name": "Hồ Chí Minh",
        "slug": "ho-chi-minh",
        "type": "thanh-pho",
        "name_with_type": "Thành Phố Hồ Chí Minh",
        "code": "12"
      },
      "district": {
        "name": "Thủ Đức",
        "slug": "thu-duc",
        "type": "thanh-pho",
        "name_with_type": "Thành Phố Thủ Đức",
        "code": "4876",
        "parent_code": "12",
        "path": "Thủ Đức, Hồ Chí Minh",
        "path_with_type": "Thành Phố Thủ Đức, Thành phố Hồ Chí Minh"
      },
      "ward": {
        "name": "Thảo Điền",
        "slug": "thao-dien",
        "type": "phuong",
        "name_with_type": "Phường Thảo Điền",
        "path": "Thảo Điền, Thủ Đức, Hồ Chí Minh",
        "path_with_type": "Phường Thảo Điền, Thành Phố Thủ Đức, Thành phố Hồ Chí Minh",
        "code": "1774348",
        "parent_code": "4876"
      }
    },
    "result": {
      "new_province": {
        "name": "Hồ Chí Minh",
        "slug": "ho-chi-minh",
        "type": "thanh-pho",
        "name_with_type": "Thành phố Hồ Chí Minh",
        "code": "12"
      },
      "new_ward": {
        "name": "An Khánh",
        "type": "phuong",
        "slug": "an-khanh",
        "name_with_type": "Phường An Khánh",
        "path": "An Khánh, Hồ Chí Minh",
        "path_with_type": "Phường An Khánh, Thành phố Hồ Chí Minh",
        "code": "11020",
        "parent_code": "12"
      },
      "mapping": {
        "old_province_code": "12",
        "old_district_code": "4876",
        "old_ward_code": "1774348",
        "new_province_code": "12",
        "new_ward_code": "11020",
        "row_indexes": [
          893
        ]
      },
      "warnings": []
    },
    "candidates": [],
    "warnings": [],
    "confidence": 0.98,
    "match_strategy": "code_or_name_with_code_filter",
    "normalized_text": "ho chi minh|thu duc|thao dien",
    "meta": {
      "parser_version": "1.0.0",
      "mapping_version": "10_25",
      "elapsed_ms": 0.207,
      "warnings": []
    }
  },
  "old_candidates": [],
  "old_first": null
}
```

## Python Usage

```python
from src import auto_convert_address

result = auto_convert_address(
    "Phuong An Hai Nam, Quan Son Tra, Da Nang"
)

print(result["input_type"])
print(result["converted_new"])
```

## Project Structure

```text
.
+-- main.py
+-- requirements.txt
+-- README.md
+-- src/
    +-- __init__.py
    +-- conversion.py
    +-- converter.py
    +-- data.py
    +-- normalize.py
    +-- text.py
    +-- utils.py
```
