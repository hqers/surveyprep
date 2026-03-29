# SurveyPrep

**SurveyPrep** is a configurable preprocessing framework designed to handle **schema drift in multi-year household survey data**.

It enables reproducible harmonization of heterogeneous survey datasets such as Indonesia's Susenas (2017–2025) and EHCVM (multi-country), and can be extended to other survey systems (e.g., LSMS).

---

## Key Features

- **Adapter-based schema handling**  
  Each survey year or country is defined through an adapter, isolating schema differences (column names, coding, structure).

- **Modular feature construction (runner system)**  
  Features are defined declaratively and can be extended without modifying core code.

- **Automatic file detection**  
  Survey files (RT/ART/KP) are identified based on content, not filename.

- **Flexible data loading**  
  Supports combined or split individual files (ART A/B).

- **Dual-output design**  
  - `HH_CLUSTERING_ready.csv` → for machine learning (no weights)  
  - `HH_PROFILING_with_weights.csv` → for statistical analysis  

- **Extensible across survey systems**  
  Supports Susenas and EHCVM, and can be adapted to other household surveys.

---

## Installation

Install directly from GitHub:

```bash
pip install git+https://github.com/hqers/surveyprep.git
```
## Requirements
Python ≥ 3.9
pandas
numpy
dbfread (optional, for .dbf files)

## Quick Start

```python
from surveyprep.core.finder import find_susenas_files, print_scan_report, resolve_art_files
from surveyprep.susenas.hh_record import build_hh_record
from surveyprep.susenas.individual import load_art_merged, build_individual
from surveyprep.susenas.food_exp import build_food_expenditure
from surveyprep.susenas.integrator import integrate_all

# 1. Detect files automatically
scan = find_susenas_files('data/', year=2020)
print_scan_report(scan)

# 2. Build household data
df_hh = build_hh_record(str(scan['rt_file']))

# 3. Build individual data
art_a, art_b = resolve_art_files(scan)
df_art = load_art_merged(art_a, art_b)
df_soc = build_individual(df_art, soc=df_hh)

# 4. Build food expenditure
kp41_paths = [str(f) for f in scan['kp41_files']]
df_food = build_food_expenditure(kp41_paths)

# 5. Integrate datasets
df_final = integrate_all(soc=df_soc, food=df_food, nonfood=None)
```

## Example Output
The pipeline generates two datasets:

HH_CLUSTERING_ready.csv
HH_PROFILING_with_weights.csv

Example:

| HH_ID | UrbanRural | TotalFoodExp_month |
|--------|----------|--------|
| 001 | Urban | 1250000 |
| 002 | Rural | 850000 |


## Supported Data

### Susenas (Indonesia)

Supported years: 2017–2025
Automatically handles schema changes across years

### EHCVM (UEMOA countries)

Example: Benin 2021
Uses household identifiers (grappe, menage)


## Adapter System

```
adapters/
├── base.py              ← definisi lengkap (default = 2020)
├── susenas_2017.py      ← override: kolom ketenagakerjaan r80x
├── susenas_2022.py      ← override: hh_id=urut, KLP 183→192
├── susenas_2025.py      ← override: KLP 183→220, r619 KIP
└── ehcvm_ben_2021.py    ← full EHCVM adapter (Stata, grappe+menage)
```

### Example schema drift handled:

- Household ID: renum → urut
- Education variable: r615 → r614 → r613
- Activity variable: r802 → r703 → r704

## Data Format Notes
- CSV files use numeric codes (labels mapped automatically)
- .dbf files are supported (via dbfread)
- Missing variables are handled gracefully (filled as NA)

## Use Cases
SurveyPrep enables:
- Longitudinal analysis across survey years
- Cross-country household comparisons
- Household clustering and segmentation
- Poverty and socio-economic modeling

## Generate Notebook

Open [hqers.my.id/mixclust](https://hqers.my.id/mixclust) → Notebook Generator
→ Choose Year → download `.ipynb` ready to use.

## Associated Publication
If you use this software, please cite:
```
Pratama, H. (2026). SurveyPrep: A Configurable Framework for Harmonizing Multi-Schema Household Survey Data. (JOSS submission)
```
## Repository
https://github.com/hqers/surveyprep

## License

MIT © 2025 Hasta Pratama
