"""
surveyprep.tools.notebook_generator
=====================================
Generate Jupyter notebook (.ipynb) siap pakai untuk menjalankan
pipeline surveyprep di JupyterHub atau lokal.

Cara pakai (CLI):
    python -m surveyprep.tools.notebook_generator \\
        --year 2020 \\
        --data-path /home/user/susenas/raw \\
        --output-path /home/user/susenas/output \\
        --out pipeline_susenas2020.ipynb

    # Dengan JupyterHub install dari GitHub:
    python -m surveyprep.tools.notebook_generator \\
        --year 2022 \\
        --data-path /srv/data/susenas/2022 \\
        --output-path /srv/data/susenas/output \\
        --github-url https://github.com/hastapratama/surveyprep.git \\
        --out pipeline_susenas2022.ipynb

Cara pakai (API):
    from surveyprep.tools.notebook_generator import generate_notebook
    nb = generate_notebook(
        year=2020,
        data_path='/home/user/data/susenas',
        output_path='/home/user/output',
        github_url='https://github.com/hastapratama/surveyprep.git',
    )
    with open('pipeline_2020.ipynb', 'w') as f:
        import json; json.dump(nb, f, indent=1)
"""
from __future__ import annotations

import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional


# ── Notebook cell helpers ─────────────────────────────────────────────────────

def _code_cell(source: str | list[str], tags: list[str] = None) -> dict:
    """Buat satu code cell."""
    if isinstance(source, list):
        source = '\n'.join(source)
    cell = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source,
    }
    if tags:
        cell["metadata"]["tags"] = tags
    return cell


def _md_cell(source: str | list[str]) -> dict:
    """Buat satu markdown cell."""
    if isinstance(source, list):
        source = '\n'.join(source)
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source,
    }


# ── Adapter info (sama dengan dashboard) ─────────────────────────────────────

ADAPTER_INFO = {
    2017: dict(hh_id='renum', edu='r615', act='r802', klp='183',
               design="['renum', 'fwt']", has_psu=False),
    2018: dict(hh_id='urut',  edu='r615', act='r802', klp='183',
               design="['wi', 'wi2', 'wi3', 'fwt']", has_psu=False),
    2019: dict(hh_id='renum', edu='r615', act='r702', klp='183',
               design="['wi', 'wi1', 'wi2', 'fwt']", has_psu=False),
    2020: dict(hh_id='renum', edu='r615', act='r703', klp='183',
               design="['psu', 'ssu', 'strata', 'fwt']", has_psu=True),
    2021: dict(hh_id='renum', edu='r615', act='r703', klp='183',
               design="['psu', 'ssu', 'strata', 'fwt']", has_psu=True),
    2022: dict(hh_id='urut',  edu='r614', act='r703', klp='192',
               design="['psu', 'ssu', 'strata', 'fwt']", has_psu=True),
    2023: dict(hh_id='renum', edu='r614', act='r704', klp='192',
               design="['psu', 'ssu', 'strata', 'fwt']", has_psu=True),
    2024: dict(hh_id='renum', edu='r613', act='r704', klp='192',
               design="['psu', 'ssu', 'strata', 'fwt']", has_psu=True),
    2025: dict(hh_id='renum', edu='r615', act='r704', klp='220',
               design="['psu', 'ssu', 'strata', 'fwt']", has_psu=True),
}


# ── Main generator ────────────────────────────────────────────────────────────

def generate_notebook(
    year: int,
    data_path: str,
    output_path: str,
    *,
    prefix: str = '',
    github_url: str = 'https://github.com/hastapratama/surveyprep.git',
    prov_filter: str = '',
    impute: bool = True,
    cap_outliers: bool = True,
    include_food: bool = True,
    include_nonfood: bool = False,
    notes: str = '',
) -> dict:
    """
    Generate Jupyter notebook (.ipynb) sebagai dict Python.

    Parameters
    ----------
    year         : Tahun survei (2017–2025)
    data_path    : Path folder data raw Susenas
    output_path  : Path folder output
    prefix       : Prefix nama file output
    github_url   : URL repo surveyprep di GitHub untuk pip install
    prov_filter  : Kode provinsi dipisah koma (kosong = semua)
    impute       : Jalankan impute_mixed()
    cap_outliers : Jalankan cap_outliers()
    include_food : Sertakan food expenditure (KP41)
    include_nonfood : Sertakan non-food expenditure (KP42)
    notes        : Catatan tambahan di markdown header

    Returns
    -------
    dict — struktur notebook .ipynb (nbformat v4)
    """
    if year not in ADAPTER_INFO:
        raise ValueError(f"Tahun {year} tidak didukung. Pilih: {sorted(ADAPTER_INFO)}")

    ada = ADAPTER_INFO[year]
    yr2 = str(year)[-2:]
    prefix = prefix or f'susenas{year}'
    ts = datetime.now().strftime('%Y-%m-%d %H:%M')

    cells = []

    # ── Cell 0: Header markdown ──────────────────────────────────────────────
    cells.append(_md_cell([
        f"# Pipeline Susenas {year}",
        f"",
        f"Generated oleh **SurveyPrep Preprocessing Wizard** — {ts}",
        f"",
        f"| Parameter | Nilai |",
        f"|-----------|-------|",
        f"| Tahun | {year} |",
        f"| Adapter | `susenas_{year}` |",
        f"| hh_id_col | `{ada['hh_id']}` |",
        f"| KLP rokok start | `{ada['klp']}` |",
        f"| Data path | `{data_path}` |",
        f"| Output path | `{output_path}` |",
        *(([f"| Catatan | {notes} |"]) if notes else []),
        f"",
        f"> **Cara pakai**: Jalankan cell satu per satu dari atas ke bawah,",
        f"> atau klik **Run All** (⏩) untuk menjalankan semua sekaligus.",
    ]))

    # ── Cell 1: Install surveyprep ────────────────────────────────────────────
    import surveyprep as _sp
    _min_ver = _sp.__version__   # versi saat notebook di-generate

    cells.append(_md_cell("## 1. Install SurveyPrep"))
    cells.append(_code_cell([
        "import subprocess, sys",
        f'GITHUB_URL = "git+{github_url}"',
        f'MIN_VERSION = "{_min_ver}"   # versi minimum yang dibutuhkan notebook ini',
        "",
        "# Cek apakah sudah terinstall dan versinya cukup",
        "def _ver_tuple(v):",
        "    try: return tuple(int(x) for x in v.split('.'))",
        "    except: return (0,)",
        "",
        "needs_install = False",
        "try:",
        "    import surveyprep as _sp",
        "    installed = _sp.__version__",
        "    if _ver_tuple(installed) < _ver_tuple(MIN_VERSION):",
        "        print(f'⚠ Versi terinstall ({installed}) < minimum ({MIN_VERSION}) — reinstall...')",
        "        needs_install = True",
        "    else:",
        "        print(f'✓ surveyprep {installed} sudah memenuhi syarat (min: {MIN_VERSION})')",
        "except ImportError:",
        "    print('surveyprep belum terinstall — install sekarang...')",
        "    needs_install = True",
        "",
        "if needs_install:",
        '    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q",',
        '                           "--force-reinstall", "--no-cache-dir",',
        '                           GITHUB_URL])',
        "    import importlib",
        "    import surveyprep",
        "    importlib.reload(surveyprep)",
        "    print(f'✅ surveyprep {surveyprep.__version__} berhasil diinstall')",
        "else:",
        "    import surveyprep",
        "",
        "print(f'surveyprep versi: {surveyprep.__version__}')",
    ], tags=['setup']))

    # ── Cell 2: Import & konfigurasi ─────────────────────────────────────────
    cells.append(_md_cell("## 2. Import dan Konfigurasi"))
    cells.append(_code_cell([
        "import sys",
        "from pathlib import Path",
        "import pandas as pd",
        "import warnings",
        "warnings.filterwarnings('ignore')",
        "",
        "# Import adapter dan modul pipeline",
        f"from surveyprep.adapters.susenas_{year} import (",
        f"    CONFIG, VALUE_LABELS, KLP, RUNNER_RT, RUNNER_ART, EMPLOYMENT",
        f")",
        f"from surveyprep.core.reader  import read_bps_csv, read_bps_csv_multi",
        f"from surveyprep.core.runner  import execute_runner",
        f"from surveyprep.core.imputer import impute_mixed, cap_outliers",
        f"from surveyprep.core.exporter import export_dual",
        f"from surveyprep.susenas.hh_record  import build_hh_record",
        f"from surveyprep.susenas.individual import load_art_merged, build_individual",
        *(["from surveyprep.susenas.food_exp    import build_food_expenditure"] if include_food else []),
        *(["from surveyprep.susenas.nonfood_exp import build_nonfood_expenditure"] if include_nonfood else []),
        f"from surveyprep.susenas.integrator  import integrate_all",
        "",
        "# ── Path konfigurasi ──────────────────────────────────────────────",
        f'DATA_DIR   = Path("{data_path}")',
        f'OUTPUT_DIR = Path("{output_path}")',
        f'PREFIX     = "{prefix}"',
        "",
        "OUTPUT_DIR.mkdir(parents=True, exist_ok=True)",
        "",
        "# Verifikasi path",
        "print(f'Data   : {DATA_DIR}  (exists={DATA_DIR.exists()})')",
        "print(f'Output : {OUTPUT_DIR}')",
    ], tags=['config']))

    # ── Cell 3: Filter provinsi (opsional) ───────────────────────────────────
    if prov_filter:
        prov_list = [p.strip() for p in prov_filter.split(',') if p.strip()]
        cells.append(_md_cell("## 3. Filter Provinsi"))
        cells.append(_code_cell([
            "# Filter provinsi — hapus atau ubah sesuai kebutuhan",
            f"PROV_FILTER = {prov_list}  # kode provinsi BPS",
            "print(f'Filter aktif: {PROV_FILTER}')",
        ]))
    else:
        cells.append(_md_cell("## 3. Filter Provinsi (Opsional)"))
        cells.append(_code_cell([
            "# Tidak ada filter — semua provinsi akan diproses",
            "# Untuk filter spesifik, uncomment dan isi kode provinsi:",
            "# PROV_FILTER = ['32', '33', '34']  # Jawa Barat, Jawa Tengah, DI Yogyakarta",
            "PROV_FILTER = []  # kosong = semua provinsi",
        ]))

    # ── Cell 3b: File scanner ────────────────────────────────────────────────
    cells.append(_md_cell("## 3b. Scan & Verifikasi File Data"))
    cells.append(_code_cell([
        "from surveyprep.core.finder import find_susenas_files, print_scan_report, assert_files_found",
        "",
        "# Scan otomatis — tidak perlu tahu nama file persisnya",
        f"scan = find_susenas_files(DATA_DIR, year={year}, verbose=True)",
        "print_scan_report(scan)",
        "",
        "# Override CONFIG dengan file yang terdeteksi",
        "if scan['rt_file']:    CONFIG['rt_file']    = scan['rt_file'].name",
        "if scan['art_a_file']: CONFIG['art_a_file'] = scan['art_a_file'].name",
        "if scan['art_b_file']: CONFIG['art_b_file'] = scan['art_b_file'].name",
        "if scan['sep']:        CONFIG['sep']        = scan['sep']",
        "",
        "# Stop di sini kalau file penting tidak ditemukan",
        "assert_files_found(scan)",
        "print('\n✅ Semua file ditemukan — lanjutkan ke cell berikutnya')",
    ]))

    # ── Cell 4: Build HH Record ───────────────────────────────────────────────
    cells.append(_md_cell(f"## 4. Build HH Record (RT)"))
    cells.append(_code_cell([
        "# build_hh_record menerima PATH ke file RT, bukan DataFrame",
        "rt_file = scan['rt_file'] if scan['rt_file'] else DATA_DIR / CONFIG['rt_file']",
        "print(f'Membaca RT: {{rt_file}}')",
        "",
        "df_hh = build_hh_record(str(rt_file), verbose=True)",
        "",
        "print(f'HH record : {{len(df_hh):,}} baris x {{df_hh.shape[1]}} kolom')",
        "df_hh.head(3)",
    ]))

    # ── Cell 5: Build Individual ──────────────────────────────────────────────
    cells.append(_md_cell("## 5. Build Individual (ART)"))
    cells.append(_code_cell([
        "# load_art_merged menerima dua PATH: art_a dan art_b",
        "art_a = scan['art_a_file'] if scan['art_a_file'] else DATA_DIR / CONFIG['art_a_file']",
        "art_b = scan['art_b_file'] if scan['art_b_file'] else DATA_DIR / CONFIG.get('art_b_file', '')",
        "print(f'ART A: {{art_a.name}}')",
        "print(f'ART B: {{art_b.name if art_b else "(tidak ada)"}}' )",
        "",
        "df_art = load_art_merged(str(art_a), str(art_b) if art_b else None, verbose=True)",
        "",
        "# build_individual menerima DataFrame ART + opsional DataFrame RT",
        "df_soc = build_individual(df_art, soc=df_hh, verbose=True)",
        "",
        "print(f'Sosio-demografi: {{len(df_soc):,}} RT x {{df_soc.shape[1]}} kolom')",
        "df_soc.head(3)",
    ]))

    # ── Cell 6: Food expenditure (opsional) ───────────────────────────────────
    if include_food:
        cells.append(_md_cell("## 6. Food Expenditure (KP41)"))
        cells.append(_code_cell([
            "from surveyprep.susenas.food_exp import build_food_expenditure",
            "",
            "kp41_files = scan['kp41_files'] if scan['kp41_files'] else sorted(DATA_DIR.glob(CONFIG['kp41_glob']))",
            "kp41_paths = [str(f) for f in kp41_files]  # konversi Path ke str",
            "print(f'File KP41: {{len(kp41_paths)}} file')",
            "",
            "df_food = build_food_expenditure(kp41_paths, verbose=True)",
            "print(f'Food exp: {{len(df_food):,}} RT')",
            "df_food.head(3)",
        ]))

    # ── Cell 7: Non-food expenditure (opsional) ───────────────────────────────
    if include_nonfood:
        cells.append(_md_cell("## 7. Non-Food Expenditure (KP42 + KP43)"))
        cells.append(_code_cell([
            "from surveyprep.susenas.nonfood_exp import build_nonfood_expenditure",
            "",
            "kp42_files = scan['kp42_files'] if scan['kp42_files'] else sorted(DATA_DIR.glob(CONFIG['kp42_glob']))",
            "kp43_files = scan.get('kp43_files', [])",
            "kp42_paths = [str(f) for f in kp42_files]",
            "kp43_paths = [str(f) for f in kp43_files] if kp43_files else None",
            "print(f'File KP42: {{len(kp42_paths)}} | KP43: {{len(kp43_paths) if kp43_paths else 0}}')",
            "",
            "df_nonfood = build_nonfood_expenditure(kp42_paths, kp43_files=kp43_paths, verbose=True)",
            "print(f'Non-food: {{len(df_nonfood):,}} RT')",
            "df_nonfood.head(3)",
        ]))

    # ── Cell 8: Integrate ─────────────────────────────────────────────────────
    step = 6 + int(include_food) + int(include_nonfood) + 1
    cells.append(_md_cell(f"## {step}. Integrate Semua Komponen"))
    food_arg   = "df_food"   if include_food    else "None"
    nonfood_arg = "df_nonfood" if include_nonfood else "None"
    cells.append(_code_cell([
        "# integrate_all menerima: soc (RT level), food, nonfood",
        f"df_integrated = integrate_all(",
        f"    soc     = df_soc,",
        f"    food    = {food_arg},",
        f"    nonfood = {nonfood_arg},",
        f"    verbose = True,",
        f")",
        "print(f'Integrated: {{len(df_integrated):,}} RT x {{df_integrated.shape[1]}} kolom')",
        "df_integrated.head(3)",
    ]))

    # ── Cell 9: Impute & cap ──────────────────────────────────────────────────
    step += 1
    cells.append(_md_cell(f"## {step}. Preprocessing (Impute & Cap Outliers)"))
    cells.append(_code_cell([
        "cat_cols = df_integrated.select_dtypes(include='object').columns.tolist()",
        "num_cols = df_integrated.select_dtypes(include='number').columns.tolist()",
        "design_cols = CONFIG.get('design_cols', [])",
        "num_feat = [c for c in num_cols if c not in design_cols + ['HHID']]",
        "",
        *(["df_integrated = impute_mixed(df_integrated, force_cat=cat_cols)",
           "print('Impute selesai')"] if impute else
          ["# Impute dinonaktifkan — uncomment jika diperlukan:",
           "# df_integrated = impute_mixed(df_integrated, force_cat=cat_cols)"]),
        "",
        *(["df_integrated = cap_outliers(df_integrated, num_cols=num_feat)",
           "print('Cap outliers selesai')"] if cap_outliers else
          ["# Cap outliers dinonaktifkan:",
           "# df_integrated = cap_outliers(df_integrated, num_cols=num_feat)"]),
        "",
        "print(f'Missing values tersisa: {df_integrated.isna().sum().sum()}')",
    ]))

    # ── Cell 10: Export ───────────────────────────────────────────────────────
    step += 1
    cells.append(_md_cell(f"## {step}. Export Output"))
    cells.append(_code_cell([
        "result = export_dual(",
        "    df_integrated,",
        "    outdir = str(OUTPUT_DIR),",
        "    id_col = 'HHID',",
        "    survey_design_cols = CONFIG.get('design_cols', []),",
        f"    verbose = True,",
        ")",
        "",
        "print('\\n=== Output yang dihasilkan ===')",
        "for name, path in result.items():",
        "    print(f'  {name}: {path}')",
    ]))

    # ── Cell 11: Ringkasan ────────────────────────────────────────────────────
    step += 1
    cells.append(_md_cell(f"## {step}. Ringkasan Hasil"))
    cells.append(_code_cell([
        "# Exporter menyimpan dengan nama tetap (tanpa prefix)",
        "clust_file  = OUTPUT_DIR / 'HH_CLUSTERING_ready.csv'",
        "profil_file = OUTPUT_DIR / 'HH_PROFILING_with_weights.csv'",
        "",
        "if clust_file.exists():",
        "    df_check = pd.read_csv(clust_file, sep=';')",
        "    print(f'CLUSTERING_ready  : {{len(df_check):,}} baris x {{df_check.shape[1]}} kolom')",
        "    print(f'Kolom fitur       : {{list(df_check.columns[:10])}} ...')",
        "    display(df_check.head(3))",
        "else:",
        "    print(f'File tidak ditemukan di: {{OUTPUT_DIR}}')",
        "    print('Pastikan cell Export sudah dijalankan dan OUTPUT_DIR benar')",
        "",
        "if profil_file.exists():",
        "    df_prof = pd.read_csv(profil_file, sep=';', nrows=2)",
        "    print(f'PROFILING_with_weights: {{df_prof.shape[1]}} kolom (termasuk bobot survei)')",
    ]))

    # ── Assemble notebook ─────────────────────────────────────────────────────
    notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.10.0",
            },
            "surveyprep": {
                "generated_by": "notebook_generator",
                "generated_at": ts,
                "year": year,
                "adapter": f"susenas_{year}",
                "data_path": data_path,
                "output_path": output_path,
                "github_url": github_url,
            },
        },
        "cells": cells,
    }
    return notebook


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Generate Jupyter notebook pipeline surveyprep'
    )
    parser.add_argument('--year',        required=True,  type=int)
    parser.add_argument('--data-path',   required=True,  help='Path folder data raw')
    parser.add_argument('--output-path', required=True,  help='Path folder output')
    parser.add_argument('--prefix',      default='',     help='Prefix nama file output')
    parser.add_argument('--github-url',  default='https://github.com/hastapratama/surveyprep.git')
    parser.add_argument('--prov-filter', default='',     help='Kode provinsi dipisah koma')
    parser.add_argument('--no-impute',   action='store_true')
    parser.add_argument('--no-cap',      action='store_true')
    parser.add_argument('--food',        action='store_true', default=True)
    parser.add_argument('--nonfood',     action='store_true', default=False)
    parser.add_argument('--notes',       default='')
    parser.add_argument('--out',         required=True,  help='Path output .ipynb')
    args = parser.parse_args()

    nb = generate_notebook(
        year          = args.year,
        data_path     = args.data_path,
        output_path   = args.output_path,
        prefix        = args.prefix,
        github_url    = args.github_url,
        prov_filter   = args.prov_filter,
        impute        = not args.no_impute,
        cap_outliers  = not args.no_cap,
        include_food  = args.food,
        include_nonfood = args.nonfood,
        notes         = args.notes,
    )

    out_path = Path(args.out)
    out_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding='utf-8')
    n_cells = len(nb['cells'])
    print(f"✅ Notebook ditulis ke: {out_path} ({n_cells} cells)")
    print(f"   Selanjutnya: upload ke JupyterHub → Run All Cells")


if __name__ == '__main__':
    main()
