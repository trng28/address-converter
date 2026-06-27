# Vietnam Administrative Address Converter

Convert Vietnamese administrative addresses between the old structure (province / district / ward) and the new structure (province / ward) following the 2025 administrative merger.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![Dataset](https://img.shields.io/badge/HuggingFace-vietnam--address--collection-FFD21E?style=flat-square)](https://huggingface.co/datasets/trucmtnguyen/vietnam-address-collection)
[![CI](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)](.github/workflows/ci.yml)

---

## What it does
 
- Vietnam's 2025 administrative reform eliminated the district level nationwide, merging and renaming thousands of wards across all 63 provinces. Any system storing addresses in the old format - CRMs, logistics platforms, databases - now needs a reliable way to remap historical records to the new structure.
 
- This tool takes a free-form address string in the old format, parses it, and returns the correct new administrative unit with a confidence score and structured JSON output.

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

## Performance - validated on 79,931 real addresses
 
- The converter was tested against the full [vietnam-address-collection](https://huggingface.co/datasets/trucmtnguyen/vietnam-address-collection) dataset.
 
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 110" width="680" height="110" role="img">
<rect x="0" y="0" width="680" height="110" rx="8" fill="#ffffff"/>
<rect x="8" y="8" width="156" height="94" rx="6" fill="#F8F8F7"/><rect x="8" y="8" width="3" height="94" fill="#2a78d6" rx="2"/><text x="24" y="46" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="26" fill="#2a78d6" text-anchor="start" font-weight="600">79,931</text><text x="24" y="66" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#52514e" text-anchor="start" font-weight="400">Addresses processed</text><rect x="176" y="8" width="156" height="94" rx="6" fill="#F8F8F7"/><rect x="176" y="8" width="3" height="94" fill="#1baf7a" rx="2"/><text x="192" y="46" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="26" fill="#1baf7a" text-anchor="start" font-weight="600">98.5%</text><text x="192" y="66" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#52514e" text-anchor="start" font-weight="400">Successfully converted</text><rect x="344" y="8" width="156" height="94" rx="6" fill="#F8F8F7"/><rect x="344" y="8" width="3" height="94" fill="#185FA5" rx="2"/><text x="360" y="46" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="26" fill="#185FA5" text-anchor="start" font-weight="600">74.2%</text><text x="360" y="66" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#52514e" text-anchor="start" font-weight="400">Ward remapped</text><rect x="512" y="8" width="156" height="94" rx="6" fill="#F8F8F7"/><rect x="512" y="8" width="3" height="94" fill="#e34948" rx="2"/><text x="528" y="46" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="26" fill="#e34948" text-anchor="start" font-weight="600">1.5%</text><text x="528" y="66" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#52514e" text-anchor="start" font-weight="400">Could not convert</text></svg>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 176" width="680" height="176" role="img">
<rect x="0" y="0" width="680" height="176" rx="8" fill="#ffffff"/>
<text x="20" y="28" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="13" fill="#0b0b0b" text-anchor="start" font-weight="600">Conversion outcomes</text><text x="20" y="44" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#898781" text-anchor="start" font-weight="400">Breakdown of 79,931 processed addresses</text><text x="20" y="77" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="400">Successfully converted</text><rect x="200" y="65" width="420" height="18" rx="3" fill="#f0efec"/><rect x="200" y="65" width="413" height="18" rx="3" fill="#2a78d6"/><text x="628" y="77" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="600">78,738</text><text x="682" y="77" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#898781" text-anchor="start" font-weight="400">98.5%</text><line x1="20" y1="90" x2="660" y2="90" stroke="#e1e0d9" stroke-width="0.5"/><text x="32" y="105" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#52514e" text-anchor="start" font-weight="400">Ward remapped</text><rect x="210" y="93" width="410" height="14" rx="3" fill="#f0efec"/><rect x="210" y="93" width="304" height="14" rx="3" fill="#85B7EB"/><text x="628" y="105" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="600">59,270</text><text x="682" y="105" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#898781" text-anchor="start" font-weight="400">74.2%</text><line x1="20" y1="114" x2="660" y2="114" stroke="#e1e0d9" stroke-width="0.5"/><text x="32" y="133" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#52514e" text-anchor="start" font-weight="400">Ward unchanged</text><rect x="210" y="121" width="410" height="14" rx="3" fill="#f0efec"/><rect x="210" y="121" width="100" height="14" rx="3" fill="#1baf7a"/><text x="628" y="133" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="600">19,468</text><text x="682" y="133" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#898781" text-anchor="start" font-weight="400">24.4%</text><line x1="20" y1="142" x2="660" y2="142" stroke="#e1e0d9" stroke-width="0.5"/><text x="20" y="161" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="400">Could not convert</text><rect x="200" y="149" width="420" height="18" rx="3" fill="#f0efec"/><rect x="200" y="149" width="6" height="18" rx="3" fill="#e34948"/><text x="628" y="161" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="600">1,193</text><text x="682" y="161" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#898781" text-anchor="start" font-weight="400">1.5%</text><line x1="20" y1="174" x2="660" y2="174" stroke="#e1e0d9" stroke-width="0.5"/></svg>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 186" width="680" height="186" role="img">
<rect x="0" y="0" width="680" height="186" rx="8" fill="#ffffff"/>
<text x="20" y="28" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="13" fill="#0b0b0b" text-anchor="start" font-weight="600">Remap rate by administrative unit type</text><text x="20" y="44" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#898781" text-anchor="start" font-weight="400">% of addresses where ward name changed after conversion</text><text x="20" y="79" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="400">Thị trấn (township)</text><line x1="290" y1="64" x2="290" y2="64" stroke="#e1e0d9" stroke-width="0.5"/><line x1="380" y1="64" x2="380" y2="64" stroke="#e1e0d9" stroke-width="0.5"/><line x1="470" y1="64" x2="470" y2="64" stroke="#e1e0d9" stroke-width="0.5"/><rect x="200" y="64" width="360" height="20" rx="3" fill="#f0efec"/><rect x="200" y="64" width="264" height="20" rx="3" fill="#2a78d6"/><text x="470" y="78" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="12" fill="#0b0b0b" text-anchor="start" font-weight="600">89.4%</text><text x="628" y="78" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="10" fill="#898781" text-anchor="start" font-weight="400">3,610 rows</text><text x="20" y="113" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="400">Xã (commune)</text><line x1="290" y1="98" x2="290" y2="98" stroke="#e1e0d9" stroke-width="0.5"/><line x1="380" y1="98" x2="380" y2="98" stroke="#e1e0d9" stroke-width="0.5"/><line x1="470" y1="98" x2="470" y2="98" stroke="#e1e0d9" stroke-width="0.5"/><rect x="200" y="98" width="360" height="20" rx="3" fill="#f0efec"/><rect x="200" y="98" width="138" height="20" rx="3" fill="#2a78d6"/><text x="344" y="112" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="12" fill="#0b0b0b" text-anchor="start" font-weight="600">75.4%</text><text x="628" y="112" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="10" fill="#898781" text-anchor="start" font-weight="400">17,972 rows</text><text x="20" y="147" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="400">Phường (urban ward)</text><line x1="290" y1="132" x2="290" y2="132" stroke="#e1e0d9" stroke-width="0.5"/><line x1="380" y1="132" x2="380" y2="132" stroke="#e1e0d9" stroke-width="0.5"/><line x1="470" y1="132" x2="470" y2="132" stroke="#e1e0d9" stroke-width="0.5"/><rect x="200" y="132" width="360" height="20" rx="3" fill="#f0efec"/><rect x="200" y="132" width="113" height="20" rx="3" fill="#2a78d6"/><text x="319" y="146" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="12" fill="#0b0b0b" text-anchor="start" font-weight="600">72.6%</text><text x="628" y="146" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="10" fill="#898781" text-anchor="start" font-weight="400">58,348 rows</text><line x1="290" y1="168" x2="290" y2="168" stroke="#e1e0d9" stroke-width="0.5"/><text x="290" y="180" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="9" fill="#898781" text-anchor="middle" font-weight="400">70%</text><line x1="380" y1="168" x2="380" y2="168" stroke="#e1e0d9" stroke-width="0.5"/><text x="380" y="180" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="9" fill="#898781" text-anchor="middle" font-weight="400">80%</text><line x1="470" y1="168" x2="470" y2="168" stroke="#e1e0d9" stroke-width="0.5"/><text x="470" y="180" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="9" fill="#898781" text-anchor="middle" font-weight="400">90%</text><line x1="560" y1="168" x2="560" y2="168" stroke="#e1e0d9" stroke-width="0.5"/><text x="560" y="180" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="9" fill="#898781" text-anchor="middle" font-weight="400">100%</text></svg>


- Thị trấn units have the highest remap rate - most townships were either merged into communes or elevated to ward status under the reform. The 99.5% district removal rate confirms the reform's core goal: eliminating the district level from all addresses.
 
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 340" width="680" height="340" role="img">
<rect x="0" y="0" width="680" height="340" rx="8" fill="#ffffff"/>
<text x="20" y="28" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="13" fill="#0b0b0b" text-anchor="start" font-weight="600">Top 10 provinces by ward remap rate</text><text x="20" y="44" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#898781" text-anchor="start" font-weight="400">Percentage of addresses where ward changed, by province</text><line x1="208" y1="55" x2="208" y2="324" stroke="#e1e0d9" stroke-width="0.5"/><line x1="266" y1="55" x2="266" y2="324" stroke="#e1e0d9" stroke-width="0.5"/><line x1="325" y1="55" x2="325" y2="324" stroke="#e1e0d9" stroke-width="0.5"/><line x1="383" y1="55" x2="383" y2="324" stroke="#e1e0d9" stroke-width="0.5"/><line x1="442" y1="55" x2="442" y2="324" stroke="#e1e0d9" stroke-width="0.5"/><line x1="500" y1="55" x2="500" y2="324" stroke="#e1e0d9" stroke-width="0.5"/><line x1="150" y1="70" x2="459" y2="70" stroke="#85B7EB" stroke-width="2"/><circle cx="459" cy="70" r="5" fill="#2a78d6"/><text x="20" y="74" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="400">Lâm Đồng</text><text x="469" y="74" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="10" fill="#0b0b0b" text-anchor="start" font-weight="600">94.6%</text><line x1="150" y1="96" x2="459" y2="96" stroke="#85B7EB" stroke-width="2"/><circle cx="459" cy="96" r="5" fill="#2a78d6"/><text x="20" y="100" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="400">Vĩnh Phúc</text><text x="469" y="100" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="10" fill="#0b0b0b" text-anchor="start" font-weight="600">94.6%</text><line x1="150" y1="122" x2="413" y2="122" stroke="#85B7EB" stroke-width="2"/><circle cx="413" cy="122" r="5" fill="#2a78d6"/><text x="20" y="126" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="400">Quảng Nam</text><text x="423" y="126" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="10" fill="#0b0b0b" text-anchor="start" font-weight="600">93.0%</text><line x1="150" y1="148" x2="386" y2="148" stroke="#85B7EB" stroke-width="2"/><circle cx="386" cy="148" r="5" fill="#2a78d6"/><text x="20" y="152" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="400">Bạc Liêu</text><text x="396" y="152" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="10" fill="#0b0b0b" text-anchor="start" font-weight="600">92.1%</text><line x1="150" y1="174" x2="345" y2="174" stroke="#85B7EB" stroke-width="2"/><circle cx="345" cy="174" r="5" fill="#2a78d6"/><text x="20" y="178" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="400">Đồng Tháp</text><text x="355" y="178" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="10" fill="#0b0b0b" text-anchor="start" font-weight="600">90.7%</text><line x1="150" y1="200" x2="269" y2="200" stroke="#85B7EB" stroke-width="2"/><circle cx="269" cy="200" r="5" fill="#2a78d6"/><text x="20" y="204" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="400">Tây Ninh</text><text x="279" y="204" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="10" fill="#0b0b0b" text-anchor="start" font-weight="600">88.1%</text><line x1="150" y1="226" x2="243" y2="226" stroke="#85B7EB" stroke-width="2"/><circle cx="243" cy="226" r="5" fill="#2a78d6"/><text x="20" y="230" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="400">Phú Yên</text><text x="253" y="230" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="10" fill="#0b0b0b" text-anchor="start" font-weight="600">87.2%</text><line x1="150" y1="252" x2="240" y2="252" stroke="#85B7EB" stroke-width="2"/><circle cx="240" cy="252" r="5" fill="#2a78d6"/><text x="20" y="256" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="400">Quảng Trị</text><text x="250" y="256" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="10" fill="#0b0b0b" text-anchor="start" font-weight="600">87.1%</text><line x1="150" y1="278" x2="234" y2="278" stroke="#85B7EB" stroke-width="2"/><circle cx="234" cy="278" r="5" fill="#2a78d6"/><text x="20" y="282" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="400">Long An</text><text x="244" y="282" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="10" fill="#0b0b0b" text-anchor="start" font-weight="600">86.9%</text><line x1="150" y1="304" x2="223" y2="304" stroke="#85B7EB" stroke-width="2"/><circle cx="223" cy="304" r="5" fill="#2a78d6"/><text x="20" y="308" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="400">Quảng Bình</text><text x="233" y="308" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="10" fill="#0b0b0b" text-anchor="start" font-weight="600">86.5%</text><text x="208" y="332" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="9" fill="#898781" text-anchor="middle" font-weight="400">86%</text><text x="266" y="332" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="9" fill="#898781" text-anchor="middle" font-weight="400">88%</text><text x="325" y="332" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="9" fill="#898781" text-anchor="middle" font-weight="400">90%</text><text x="383" y="332" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="9" fill="#898781" text-anchor="middle" font-weight="400">92%</text><text x="442" y="332" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="9" fill="#898781" text-anchor="middle" font-weight="400">94%</text><text x="500" y="332" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="9" fill="#898781" text-anchor="middle" font-weight="400">96%</text><line x1="150" y1="55" x2="150" y2="324" stroke="#e1e0d9" stroke-width="0.5"/></svg>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 222" width="680" height="222" role="img">
<rect x="0" y="0" width="680" height="222" rx="8" fill="#ffffff"/>
<text x="20" y="28" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="13" fill="#0b0b0b" text-anchor="start" font-weight="600">Unresolved addresses by province</text><text x="20" y="44" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#898781" text-anchor="start" font-weight="400">1,193 total — could not find a matching new ward</text><rect x="196" y="60" width="380" height="18" rx="3" fill="#f0efec"/><rect x="196" y="60" width="380" height="18" rx="3" fill="#e34948"/><text x="20" y="73" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="400">Thừa Thiên Huế</text><text x="582" y="73" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="600">568</text><text x="584" y="73" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="10" fill="#898781" text-anchor="start" font-weight="400">47.6%</text><rect x="196" y="86" width="380" height="18" rx="3" fill="#f0efec"/><rect x="196" y="86" width="303" height="18" rx="3" fill="#e34948"/><text x="20" y="99" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="400">Bình Định</text><text x="505" y="99" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="600">454</text><text x="584" y="99" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="10" fill="#898781" text-anchor="start" font-weight="400">38.1%</text><rect x="196" y="112" width="380" height="18" rx="3" fill="#f0efec"/><rect x="196" y="112" width="58" height="18" rx="3" fill="#e34948"/><text x="20" y="125" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="400">Bà Rịa - Vũng Tàu</text><text x="260" y="125" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="600">88</text><text x="584" y="125" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="10" fill="#898781" text-anchor="start" font-weight="400">7.4%</text><rect x="196" y="138" width="380" height="18" rx="3" fill="#f0efec"/><rect x="196" y="138" width="24" height="18" rx="3" fill="#e34948"/><text x="20" y="151" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="400">Bắc Giang</text><text x="226" y="151" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="600">37</text><text x="584" y="151" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="10" fill="#898781" text-anchor="start" font-weight="400">3.1%</text><rect x="196" y="164" width="380" height="18" rx="3" fill="#f0efec"/><rect x="196" y="164" width="22" height="18" rx="3" fill="#e34948"/><text x="20" y="177" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="400">Ninh Bình</text><text x="224" y="177" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="600">34</text><text x="584" y="177" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="10" fill="#898781" text-anchor="start" font-weight="400">2.9%</text><rect x="196" y="190" width="380" height="18" rx="3" fill="#f0efec"/><rect x="196" y="190" width="8" height="18" rx="3" fill="#e34948"/><text x="20" y="203" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="400">Others</text><text x="210" y="203" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="11" fill="#0b0b0b" text-anchor="start" font-weight="600">12</text><text x="584" y="203" font-family="system-ui, -apple-system, 'Segoe UI', Arial, sans-serif" font-size="10" fill="#898781" text-anchor="start" font-weight="400">1.0%</text></svg>

- The 1.5% failure rate is concentrated in provinces where ward boundary changes were most extensive and the mapping table has coverage gaps.
 

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
