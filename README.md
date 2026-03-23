# SurveyPrep

**Modular preprocessing pipeline for mixed-type household survey data.**

Designed for Indonesia's Susenas (2017–2025), EHCVM (8 UEMOA countries), and extensible to other household surveys (LSMS, etc.).

## Features

- **Adapter system** — one file per survey year/country handles all schema differences
- **Verified adapters** — Susenas 2017–2025 (all ✅), EHCVM Benin 2021 (✅)
- **Auto file detection** — `finder.py` identifies RT/ART/KP files by column content, not filename
- **Flexible ART loading** — handles single combined file or two separate files (A+B)
- **DBF support** — convert BPS `.dbf` files before use (see below)
- **Dual output** — `HH_CLUSTERING_ready.csv` (no weights) + `HH_PROFILING_with_weights.csv`

## Installation

```bash
pip install git+https://github.com/hqers/surveyprep.git
```

## Quick Start

```python
from surveyprep.core.finder     import find_susenas_files, print_scan_report, resolve_art_files
from surveyprep.susenas.hh_record  import build_hh_record
from surveyprep.susenas.individual import load_art_merged, build_individual
from surveyprep.susenas.food_exp   import build_food_expenditure
from surveyprep.susenas.integrator import integrate_all

# 1. Auto-detect semua file
scan = find_susenas_files('data/', year=2020)
print_scan_report(scan)

# 2. Build HH record
df_hh = build_hh_record(str(scan['rt_file']))

# 3. Build individual (handle ART gabungan otomatis)
art_a, art_b = resolve_art_files(scan)
df_art = load_art_merged(art_a, art_b)
df_soc = build_individual(df_art, soc=df_hh)

# 4. Food expenditure
kp41_paths = [str(f) for f in scan['kp41_files']]
df_food = build_food_expenditure(kp41_paths)

# 5. Integrate + export
df_final = integrate_all(soc=df_soc, food=df_food, nonfood=None)
```

## Variabel Output (asumsi data lengkap)

Output `HH_CLUSTERING_ready.csv` berisi ~55 fitur:

| Domain | Variabel | Sumber |
|--------|----------|--------|
| **Kondisi hunian** | UrbanRural, HomeOwnership, RoofMaterial, WallMaterial, FloorMaterial, Sanitation, ToiletType, WaterSource, AccessEnergy, CookingFuel | KOR RT (r1802–r1817) |
| **Sosio-demografi** | StatusPekerjaanKRT, HasSavingsAccount, AccessCommunication | KOR ART (r701, r706, r802) |
| **Pengeluaran pangan** | PADI-PADIAN, UMBI, IKAN, DAGING, TELUR_SUSU, SAYUR, KACANG, BUAH, MINYAK, MINUMAN, BUMBU, MAK_LAINNYA, MAK_JADI, ROKOK (per bulan) | KP41 |
| **Gizi** | TotalFoodExp_month, Kalori_month, Protein_month | KP41 |
| **Pengeluaran non-pangan** | TotalNonFoodExp_month, TotalExpenditure_month, PerCapitaExpenditure | KP42/KP43 |

> **Catatan**: Jumlah fitur aktual bergantung pada kelengkapan data yang diterima.
> Kolom yang tidak tersedia di dataset akan diisi NA dan tidak dimasukkan ke clustering-ready output.

## Format Data BPS

### CSV (diseminasi)

File CSV Susenas diseminasi **belum mengganti kode numerik dengan label**.
Kode masih berupa integer (contoh: `r105 = 1` untuk Perkotaan, `2` untuk Perdesaan).
Penggantian kode dilakukan otomatis oleh `VALUE_LABELS` di masing-masing adapter.

### DBF

BPS kadang mendistribusikan data dalam format `.dbf` (dBase). SurveyPrep mendukung
pembacaan DBF secara langsung. Jika ada masalah, konversi manual:

```python
# Opsi 1: Konversi DBF ke CSV dulu (direkomendasikan)
import dbfread
import pandas as pd

table = dbfread.DBF('kor20rt_diseminasi.dbf', encoding='latin-1')
df = pd.DataFrame(iter(table))
df.to_csv('kor20rt_diseminasi.csv', sep=';', index=False, encoding='latin-1')

# Opsi 2: Install dbfread dan baca langsung
pip install dbfread
```

### Skenario data tidak lengkap (mahasiswa/permintaan khusus)

BPS sering memberikan subset kolom kepada mahasiswa. Beberapa skenario umum:

| Skenario | Penanganan |
|----------|------------|
| ART A dan B digabung jadi satu file | `finder.py` otomatis deteksi sebagai `art_combined` |
| Kolom tertentu tidak ada | Fitur terkait diisi NA, pipeline tetap jalan |
| Hanya KOR RT (tanpa KP) | Jalankan tanpa `food_exp` dan `nonfood_exp` |
| Hanya beberapa provinsi | Set `PROV_FILTER` di notebook |

## Adapter System

```
adapters/
├── base.py              ← definisi lengkap (default = 2020)
├── susenas_2017.py      ← override: kolom ketenagakerjaan r80x
├── susenas_2022.py      ← override: hh_id=urut, KLP 183→192
├── susenas_2025.py      ← override: KLP 183→220, r619 KIP
└── ehcvm_ben_2021.py    ← full EHCVM adapter (Stata, grappe+menage)
```

### Schema drift Susenas 2017–2025

| Variable | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|----------|------|------|------|------|------|------|------|------|------|
| `hh_id_col` | renum | urut | renum | renum | renum | urut | renum | renum | renum |
| `education_col` | r615 | r615 | r615 | r615 | r615 | r614 | r614 | r613 | r615 |
| `activity_col` | r802 | r802 | r702 | r703 | r703 | r703 | r704 | r704 | r704 |
| KLP rokok start | 183 | 183 | 183 | 183 | 183 | 192 | 192 | 192 | 220 |

## Generate Notebook

Buka [hqers.my.id/mixclust](https://hqers.my.id/mixclust) → Notebook Generator
→ pilih tahun → download `.ipynb` siap pakai.

## Citation

```
Pratama, H. (2026). SurveyPrep: A Configurable Preprocessing Pipeline
for Mixed-Type Household Survey Data. https://github.com/hqers/surveyprep
```

## License

MIT © 2025 Hasta Pratama
