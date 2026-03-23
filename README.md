# SurveyPrep

**Modular preprocessing pipeline for mixed-type household survey data.**

Designed for Indonesia's Susenas (2017–2025), EHCVM (8 UEMOA countries), and extensible to other household surveys (LSMS, etc.).

## Features

- **Adapter system** — one file per survey year/country handles all schema differences (column names, value encodings, KLP shifts)
- **Verified adapters** — Susenas 2017–2025 (all ✅), EHCVM Benin 2021 (✅), 7 other UEMOA countries (placeholders)
- **Adapter Generator** — upload BPS metadata Excel → auto-generate `susenas_202X.py`
- **Dual output** — `HH_CLUSTERING_ready.csv` (no weights) + `HH_PROFILING_with_weights.csv`
- **Mixed-type support** — categorical + numerical, imputation, outlier capping
- **EHCVM support** — reads Stata `.dta` files, composite `grappe+menage` key

## Installation

```bash
# From GitHub (recommended)
pip install git+https://github.com/hqers/surveyprep.git

# For EHCVM (.dta support)
pip install "git+https://github.com/hqers/surveyprep.git#egg=surveyprep[stata]"

# From local clone
git clone https://github.com/hqers/surveyprep.git
pip install -e surveyprep/
```

## Quick Start

```python
from surveyprep.pipeline import run_susenas_pipeline
from surveyprep.adapters import susenas_2020

result = run_susenas_pipeline(
    data_dir   = "/path/to/susenas_raw/",
    adapter    = susenas_2020,
    output_dir = "/path/to/output/",
    prefix     = "susenas2020",
)
```

## Generate a Notebook

Use the **Preprocessing Wizard** in the dashboard to generate a ready-to-run `.ipynb`:

```bash
# Run dashboard locally
cd surveyprep_app/
python run_local.py
# Open http://localhost:5000 → Preprocessing Wizard
```

Or generate directly from CLI:

```bash
python -m surveyprep.tools.notebook_generator \
    --year 2020 \
    --data-path /path/to/raw \
    --output-path /path/to/output \
    --target jupyterhub \
    --jhub-url https://jupyterhub.university.ac.id \
    --out pipeline_2020.ipynb
```

## Adapter System

Each adapter is a thin Python module that overrides only what changed from the base (Susenas 2020):

```
adapters/
├── base.py              ← full definition, default = 2020
├── susenas_2017.py      ← override: blok R16xx, r801/r802 cols, 21-code KBLI
├── susenas_2022.py      ← override: hh_id=urut, KLP 183→192, r614 ijazah
├── susenas_2025.py      ← override: blok R16xx, KLP 183→220, r619 KIP
└── ehcvm_ben_2021.py    ← full EHCVM adapter (Stata, grappe+menage key)
```

### Schema drift across waves (verified from BPS metadata)

| Variable          | 2017   | 2018   | 2019   | 2020   | 2021   | 2022   | 2023   | 2024   | 2025   |
|-------------------|--------|--------|--------|--------|--------|--------|--------|--------|--------|
| `hh_id_col`       | renum  | urut   | renum  | renum  | renum  | urut   | renum  | renum  | renum  |
| `education_col`   | r615   | r615   | r615   | r615   | r615   | r614   | r614   | r613   | r615   |
| `activity_col`    | r802   | r802   | r702   | r703   | r703   | r703   | r704   | r704   | r704   |
| KLP rokok start   | 183    | 183    | 183    | 183    | 183    | 192    | 192    | 192    | 220    |
| N commodities KP  | 188    | 188    | 188    | 188    | 188    | 197    | 197    | 197    | 225    |

## Adapter Generator

Generate a new adapter from BPS metadata Excel automatically:

```bash
python -m surveyprep.tools.adapter_generator \
    --kor Metadata_Susenas_202603_Kor.xlsx \
    --kp  Metadata_Susenas_202603_KP.xlsx  \
    --year 2026 \
    --out surveyprep/adapters/susenas_2026.py
```

## Project Structure

```
surveyprep/
├── adapters/         ← per-year/country configuration
├── core/             ← reader, runner, imputer, exporter
├── susenas/          ← Susenas-specific builders
├── tools/            ← adapter_generator, notebook_generator
└── pipeline.py       ← top-level orchestration
```

## Citation

If you use SurveyPrep in research, please cite:

```
Pratama, H. (2026). SurveyPrep: A Configurable Preprocessing Pipeline
for Mixed-Type Household Survey Data. [Software]. 
https://github.com/hqers/surveyprep
```

## License

MIT © 2025 Hasta Pratama
