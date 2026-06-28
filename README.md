# Vietnam Administrative Address Converter Toolkit

Convert Vietnamese administrative addresses from the old `province / district / ward` structure to the 2025 normalized `province / ward` structure.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![PyPI Version](https://img.shields.io/pypi/v/vietnam-address-converter?style=flat-square&logo=pypi&logoColor=white&label=vietnam-address-converter)](https://pypi.org/project/vietnam-address-converter/)
[![Dataset](https://img.shields.io/badge/HuggingFace-vietnam--address--collection-FFD21E?style=flat-square&logo=huggingface&logoColor=black)](https://huggingface.co/datasets/trucmtnguyen/vietnam-address-collection)
[![CI](https://github.com/trng28/address-converter/actions/workflows/ci.yml/badge.svg)](https://github.com/trng28/address-converter/actions/workflows/ci.yml)

---

## Features

- Parse free-form Vietnamese addresses in the old administrative format.
- Convert old province/district/ward references into the new province/ward format.
- Normalize large CSV datasets in streaming mode.
- Reuse an in-memory converter with caching for better batch performance.

---

## Package Name

- PyPI distribution: `vietnam-address-converter`
- Python import: `vietnam_address_converter`
- CLI command: `vietnam-address-converter`

---

## Installation

### From source

```bash
git clone https://github.com/trng28/address-converter.git
cd address-converter

python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

pip install -e .
```

### From PyPI

```bash
pip install vietnam-address-converter
```

### Development-only test dependencies

```bash
pip install -r requirements.txt
```

---

## CLI Usage

### Convert one address

```bash
vietnam-address-converter --address "Đường Trần Não, Phường Thảo Điền, TP Thủ Đức, Thành phố Hồ Chí Minh"
```

### Run as a module

```bash
python -m vietnam_address_converter --address "Đường Trần Não, Phường Thảo Điền, TP Thủ Đức, Thành phố Hồ Chí Minh"
```

### Convert a CSV file

```bash
vietnam-address-converter \
  --input-csv data/vietnam_full_address.csv \
  --output-csv data/vietnam_full_address.converted.csv \
  --address-column full_address \
  --cache-size 4096
```

Output schema:

```text
index,full_address,street,ward,district,city,full_address_new
```

---

## Python API

```python
from vietnam_address_converter import auto_convert_address, create_converter

result = auto_convert_address(
    "Đường Trần Não, Phường Thảo Điền, TP Thủ Đức, Thành phố Hồ Chí Minh"
)

converter = create_converter()
batch_result = converter.auto_convert_address(
    "Quốc lộ 91C, Xã Đa Phước, Huyện An Phú, Tỉnh An Giang"
)
```

---

## Dataset

This project uses the public dataset:

- [trucmtnguyen/vietnam-address-collection](https://huggingface.co/datasets/trucmtnguyen/vietnam-address-collection)

Download example:

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

---

## Performance

Validated on **79,931** real addresses from the full dataset.

![Performance Summary](docs/assets/performance-summary.svg)
![Conversion Outcomes](docs/assets/conversion-outcomes.svg)
![Remap Rate by Administrative Unit Type](docs/assets/unit-type-remap.svg)
![Top Provinces by Ward Remap Rate](docs/assets/top-provinces-remap.svg)
![Unresolved Addresses by Province](docs/assets/unresolved-by-province.svg)

---

## Project Structure

```text
address-converter/
├── .github/
│   └── workflows/
├── data/
├── docs/
│   └── assets/
├── src/
│   ├── vietnam_address_converter/  # installable Python package
│   ├── batch.py                    # compatibility wrappers for old imports
│   ├── converter.py
│   └── ...
├── tests/
├── pyproject.toml
├── main.py
├── README.md
└── requirements.txt
```

---

## Release Flow

- CI runs on every push and pull request.
- Create a tag like `v0.1.0` to trigger the release workflow.
- Release artifacts include both `.whl` and `.tar.gz`.

---

## License

Apache 2.0 © [trng28](https://github.com/trng28)
