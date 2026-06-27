# Vietnam Administrative Address Converter

Convert Vietnamese administrative addresses between the old structure (province / district / ward) and the new structure (province / ward) following the 2025 administrative merger.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![Dataset](https://img.shields.io/badge/HuggingFace-vietnam--address--collection-FFD21E?style=flat-square)](https://huggingface.co/datasets/trucmtnguyen/vietnam-address-collection)
[![CI](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)](.github/workflows/ci.yml)

---

## Features

- **Free-form address parsing** - accepts any address string and automatically detects old or new administrative structure.
- **Old-to-new conversion** - maps province / district / ward from the pre-merger structure to the new administrative units.
- **Structured JSON output** - returns normalized address text, mapping data, confidence score, and warnings.
- **Batch processing** - converts entire address files with a configurable LRU cache.


---

## Installation

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

---

## Usage

### Single address

```bash
python main.py --address "Đường Trần Não, Phường Thảo Điền, TP Thủ Đức, Thành phố Hồ Chí Minh"
```

<details>
<summary>View full JSON output</summary>

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
      "name_with_type": "Thành phố Hồ Chí Minh",
      "code": "12"
    },
    "ward": {
      "name": "An Khánh",
      "name_with_type": "Phường An Khánh",
      "path_with_type": "Phường An Khánh, Thành phố Hồ Chí Minh",
      "code": "11020"
    }
  },
  "conversion": {
    "status": "matched",
    "confidence": 0.98,
    "match_level": "province_district_ward_name",
    "warnings": []
  }
}
```

</details>

### Batch CSV

**Step 1 - Download the dataset**

```bash
pip install huggingface_hub
python -c "
from huggingface_hub import hf_hub_download
hf_hub_download(
    repo_id='trucmtnguyen/vietnam-address-collection',
    filename='vietnam_full_address.csv',
    repo_type='dataset',
    local_dir='data/'
)
"
```

Dataset: [trucmtnguyen/vietnam-address-collection](https://huggingface.co/datasets/trucmtnguyen/vietnam-address-collection)

**Step 2 - Run conversion**

```bash
python main.py \
  --input-csv  data/vietnam_full_address.csv \
  --output-csv data/vietnam_full_address.converted.csv \
  --address-column full_address \
  --cache-size 4096
```

```json
{
  "status": "ok",
  "input_csv": "data/vietnam_full_address.csv",
  "output_csv": "data/vietnam_full_address.converted.csv",
  "address_column": "full_address",
  "cache_size": 4096,
  "rows_written": 79931
}
```

---

## Project Structure

```
address-converter/
├── main.py
├── requirements.txt
├── data/
└── src/
    ├── __init__.py
    ├── constants.py       # Configuration and constants
    ├── conversion.py      # Old-to-new mapping logic
    ├── converter.py       # Main conversion entrypoint
    ├── data.py            # Administrative data loading and caching
    ├── normalize.py       # Text normalization (diacritics, lowercase)
    ├── text.py            # Free-form address parser
    └── utils.py           # Shared utilities
```

---

## JSON Response Reference

| Field | Description |
|-------|-------------|
| `input_type` | `"old"` or `"new"` - detected address structure |
| `normalized_text` | Normalized address string after conversion |
| `parsed` | Resolved province / district / ward from the input |
| `converted_new` | Corresponding new administrative units |
| `conversion.status` | `"matched"` / `"partial"` / `"unmatched"` |
| `conversion.confidence` | Match confidence score (0.0 - 1.0) |
| `conversion.match_level` | Granularity of match: `province_district_ward_name`, … |
| `conversion.warnings` | List of warnings, if any |

---

## Dataset

This project uses the Vietnam address dataset published by [Truc Nguyen](https://huggingface.co/trucmtnguyen) on Hugging Face.

[trucmtnguyen/vietnam-address-collection](https://huggingface.co/datasets/trucmtnguyen/vietnam-address-collection)

```bibtex
@dataset{nguyen2026vietnam_address,
  author    = {Nguyen, Truc},
  title     = {Vietnam Address Collection},
  year      = {2026},
  publisher = {Hugging Face},
  url       = {https://huggingface.co/datasets/trucmtnguyen/vietnam-address-collection}
}
```

---

## License

Apache 2.0 © [trng28](https://github.com/trng28)
