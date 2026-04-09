# Changelog

All notable changes to **surveyprep** are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [1.9.9] — 2026-03

### Fixed
- `individual.py` — `OccupationHeadSector` now maps raw KBLI codes to
  labeled categories (`'Pertanian'`, `'Industri'`, `'Jasa'`, etc.) instead
  of returning raw numeric strings (`'1'`, `'3'`). Added `_OCC_SECTOR` dict
  (9 sectors, KBLI 1-digit, Susenas 2017–2023).
- `individual_2024.py` — same fix for Susenas 2024 where `r706` carries
  26 KBLI 2-digit codes. Added `_OCC_SECTOR_2024` that collapses them to
  the same 9-sector taxonomy for cross-wave consistency.
- Both files: edge-case handling for `'2.0'`, `'3,0'` (comma decimal),
  `''`, `'nan'`, and `None` inputs — all return `<NA>` gracefully.

---

## [1.9.8] — 2026-03

### Added
- `core/reader.py` — native DBF reader (`read_bps_dbf`) implemented in
  pure Python (no external library). Reads dBase III/IV files as used by
  BPS for older Susenas distributions.
- `read_bps_csv()` now auto-detects `.dbf` extension and routes to the
  DBF reader transparently — no code changes needed by the caller.
- `pyproject.toml` — added `dbf = ["dbfread>=2.0.7"]` optional dependency
  for users who prefer the battle-tested `dbfread` library.
- `core/finder.py` — `.dbf` added to `SUPPORTED_EXT`; DBF files are
  scanned and classified the same way as CSV.
- `core/finder.py` — added `resolve_art_files(result)` helper that returns
  `(art_a_path, art_b_path)` and automatically handles the combined-file
  scenario (`art_b_path = None`).
- `susenas/individual.py` — `load_art_merged()` now accepts
  `art_b_path=None`; if only one file is provided (merged or subset), it
  is used as-is with a warning listing any missing blok columns.
- `core/finder.py` — added `art_combined` signature to detect merged ART
  files (blok A + B in one file) that some BPS distributions provide.
- `README.md` — documented: (1) CSV value codes are not pre-decoded,
  (2) DBF support, (3) incomplete-data scenarios (merged ART, subset
  columns, missing KP), (4) full variable domain coverage.

---

## [1.9.7] — 2026-03

### Added
- `core/finder.py` — `resolve_art_files()` (first draft, superseded
  by 1.9.8 version).

### Fixed
- `susenas/individual.py` — `load_art_merged()` signature updated to
  accept optional `art_b_path`.

---

## [1.9.6] — 2026-03

### Fixed
- Notebook generator (`tools/notebook_generator.py` and wizard
  `notebook.html`) — verification cell was looking for
  `{PREFIX}_CLUSTERING_ready.csv` but the exporter always writes
  `HH_CLUSTERING_ready.csv` (no prefix). Corrected path in both.

---

## [1.9.5] — 2026-03

### Fixed
- `core/runner.py` — `execute_runner()` was passing `art` twice:
  once as the second positional argument and again as `art=art` keyword
  argument, causing `TypeError: got multiple values for argument 'art'`
  for all `from_art_head` and `any_art` runner types.
  Fix: strip `rt`, `art`, and `kind` keys from `**item` before unpacking.

---

## [1.9.4] — 2026-03

### Fixed
- `core/imputer.py` — `cap_outliers()` was failing with
  `TypeError: Invalid value 'X.XX' for dtype 'Int64'` when columns
  stored as pandas nullable `Int64` (e.g. `HouseholdSize`) received a
  float cap value from `clip()`. Fix: cast all processed columns to
  `float64` before and after clipping.

---

## [1.9.3] — 2026-03

### Fixed
- `tools/notebook_generator.py` and `notebook.html` wizard — cells 4–8
  were generated with incorrect API calls. Corrected to match actual
  function signatures:
  - `build_hh_record(str(rt_file))` — accepts path string, not DataFrame
  - `load_art_merged(str(art_a), str(art_b) if art_b else None)`
  - `build_individual(df_art, soc=df_hh)`
  - `build_food_expenditure(kp41_paths)` — list of str, not Path objects
  - `build_nonfood_expenditure(kp42_paths, kp43_files=kp43_paths)`
  - `integrate_all(soc=df_soc, food=df_food, nonfood=...)`
- `core/finder.py` — `art_b_file` signature updated to match actual
  Susenas 2020 `kor20ind_2` columns (blok 13–16: health, immunisation, KB)
  instead of incorrectly expected blok 6–8.
- `core/finder.py` — `kp41_files`, `kp42_files`, `kp43_files` signatures
  rewritten based on actual BPS column headers (`b41k5`, `b41k6`,
  `kalori` for KP41; `b42k3`, `sebulan` for KP42; `food`, `nonfood`,
  `expend`, `kapita` for KP43). Previous signatures caused all KP files
  to be mis-detected as `rt_file`.

---

## [1.9.2] — 2026-03

### Added
- `core/reader.py` — `read_bps_csv()` now accepts optional `sep`,
  `encoding`, `decimal`, `thousands` parameters to override BPS defaults.
  Useful for non-standard distributions or EHCVM files.

### Fixed
- `core/finder.py` — `rt_file` signature now excludes files containing
  `b41k5`, `coicop`, `klp`, `food`, or `nonfood` columns, preventing KP
  files from being mis-classified as RT files.

---

## [1.9.1] — 2026-03

### Added
- `core/finder.py` — new module for auto-detecting Susenas file types
  by column content (not filename). Supports RT, ART A, ART B, KP41,
  KP42, KP43. Works regardless of filename conventions.
  Key functions: `find_susenas_files()`, `print_scan_report()`,
  `assert_files_found()`.
- Notebook generator now embeds a **file scanner cell** (step 3b) that
  auto-detects and validates all required files before the pipeline runs.

### Fixed
- `surveyprep/__init__.py` — `__version__` now reads from package
  metadata via `importlib.metadata` instead of being hardcoded `"1.0.0"`.
- `pyproject.toml` — `build-backend` corrected from
  `setuptools.backends.legacy:build` to `setuptools.build_meta` for
  compatibility with older setuptools versions on JupyterHub (TLJH).

### Changed
- Notebook generator: install cell now checks installed version against
  `MIN_VERSION` embedded at generation time. Auto-reinstalls if version
  is outdated.

---

## [1.9.0] — 2026-03

### Added
- `tools/notebook_generator.py` — generate ready-to-run `.ipynb` for
  any Susenas wave (2017–2025). Configurable via CLI or API.
- `tools/adapter_generator.py` — generate `susenas_202X.py` adapter
  from BPS metadata Excel files.
- Notebook wizard (`notebook.html`) at `hqers.my.id/mixclust/` —
  4-step browser wizard with Simple/Advanced path mode, year chip selector,
  adapter info panel, preprocessing toggles.
- GitHub repo `hqers/surveyprep` published with pip-installable package
  structure (`pyproject.toml`, MIT license).

### Changed
- Package renamed from internal `surveyprep` to published
  `hqers/surveyprep` on GitHub.
- All adapter URLs updated to `https://github.com/hqers/surveyprep`.

---

## [1.0.0] — 2026-01

### Added
- Initial release of surveyprep preprocessing framework.
- Adapters for Susenas 2017–2025 (all verified against official BPS
  metadata). Schema drift documented for all 9 waves.
- `core/reader.py` — BPS CSV reader with latin-1 encoding, semicolon
  separator, comma decimal.
- `core/runner.py` — RUNNER system for declarative variable mapping.
- `core/imputer.py` — mixed-type imputation (median for numeric,
  mode for categorical).
- `core/exporter.py` — dual output: `HH_CLUSTERING_ready.csv` (no
  survey weights) and `HH_PROFILING_with_weights.csv`.
- `susenas/hh_record.py` — household-level record builder (10 RT
  features: housing quality, sanitation, water, energy, fuel).
- `susenas/individual.py` — individual-level merge and aggregation
  (education, employment, demographics).
- `susenas/food_exp.py` — KP41 food expenditure: 14 food groups, DDS,
  nutrition indicators.
- `susenas/nonfood_exp.py` — KP42/KP43 non-food expenditure with
  thematic breakdown (energy, education, health, transport, housing).
- `susenas/integrator.py` — full integration pipeline with share/burden
  calculations and cap-outliers.
- EHCVM adapters (placeholder) for 8 UEMOA countries.

---

## Legend

| Symbol | Meaning |
|--------|---------|
| **Added** | New features or files |
| **Changed** | Changes to existing behaviour |
| **Fixed** | Bug fixes |
| **Deprecated** | Features to be removed in future |
| **Removed** | Features removed in this release |
| **Security** | Security-related changes |
