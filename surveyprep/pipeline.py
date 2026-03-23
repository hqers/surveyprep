"""
surveyprep.pipeline
====================
Fungsi pipeline end-to-end Susenas: dari raw CSV → clustering-ready dataset.

Penggunaan minimal:
    from surveyprep.pipeline import run_susenas_pipeline
    df = run_susenas_pipeline(data_dir="data/", output_dir="outputs/")

Penggunaan dengan konfigurasi kustom:
    from surveyprep.pipeline import run_susenas_pipeline
    from surveyprep.susenas.hh_record import RUNNER_RT

    extra_runner = [
        dict(kind='from_rt', out='FloorArea', col='r1804'),  # luas lantai
    ]
    df = run_susenas_pipeline(
        data_dir="data/",
        output_dir="outputs/2020/",
        extra_runner_rt=extra_runner,
        verbose=True,
    )
"""
from __future__ import annotations
import glob
import os
from typing import Optional

import pandas as pd

from .susenas.hh_record   import build_hh_record
from .susenas.individual  import load_art_merged, build_individual
from .susenas.food_exp    import build_food_expenditure
from .susenas.nonfood_exp import build_nonfood_expenditure
from .susenas.integrator  import integrate_all
from .adapters.susenas_2020 import CONFIG


def run_susenas_pipeline(
    data_dir: str,
    output_dir: Optional[str] = None,
    config: dict = CONFIG,
    extra_runner_rt: Optional[list] = None,
    extra_runner_art: Optional[list] = None,
    verbose: bool = True,
) -> pd.DataFrame:
    """
    Jalankan seluruh pipeline Susenas dari raw CSV → dataset siap klasterisasi.

    Parameters
    ----------
    data_dir : str
        Direktori tempat semua file CSV Susenas berada.
    output_dir : str | None
        Jika diberikan, simpan HH_PROFILING_with_weights.csv,
        HH_CLUSTERING_ready.csv, dan HH_WEIGHTS_sidecar.csv di sini.
    config : dict
        Konfigurasi nama file. Default: susenas_2020.CONFIG.
    extra_runner_rt : list | None
        Entri RUNNER tambahan untuk modul RT.
    extra_runner_art : list | None
        Entri RUNNER tambahan untuk modul ART/individual.
    verbose : bool

    Returns
    -------
    pd.DataFrame — dataset lengkap, satu baris per RT.
    """
    d = data_dir.rstrip('/\\')

    # ── Modul RT ──────────────────────────────────────────────────────
    rt_path = os.path.join(d, config['rt_file'])
    if verbose:
        print(f"\n[pipeline] === Modul RT ===")
        print(f"  File: {rt_path}")

    soc = build_hh_record(
        rt_path      = rt_path,
        verbose      = verbose,
        extra_runner = extra_runner_rt,
    )

    # ── Modul ART ─────────────────────────────────────────────────────
    art_a = os.path.join(d, config['art_a_file'])
    art_b = os.path.join(d, config['art_b_file'])
    if verbose:
        print(f"\n[pipeline] === Modul ART ===")
        print(f"  Files: {art_a}, {art_b}")

    art = load_art_merged(art_a, art_b, verbose=verbose)
    soc = build_individual(
        art          = art,
        soc          = soc,
        verbose      = verbose,
        extra_runner = extra_runner_art,
    )

    # ── Modul KP41 (Food) ─────────────────────────────────────────────
    kp41_files = sorted(glob.glob(os.path.join(d, config['kp41_glob'])))
    if not kp41_files:
        raise FileNotFoundError(
            f"Tidak menemukan file KP41 dengan pola: "
            f"{os.path.join(d, config['kp41_glob'])}"
        )
    if verbose:
        print(f"\n[pipeline] === Modul KP41 (Food) ===")
        print(f"  {len(kp41_files)} file ditemukan")

    food = build_food_expenditure(kp41_files, verbose=verbose)

    # ── Modul KP42+43 (NonFood) ───────────────────────────────────────
    kp42_files = sorted(glob.glob(os.path.join(d, config['kp42_glob'])))
    kp43_files = sorted(glob.glob(os.path.join(d, config['kp43_glob'])))
    if not kp42_files:
        raise FileNotFoundError(
            f"Tidak menemukan file KP42 dengan pola: "
            f"{os.path.join(d, config['kp42_glob'])}"
        )
    if verbose:
        print(f"\n[pipeline] === Modul KP42/43 (NonFood) ===")
        print(f"  KP42: {len(kp42_files)} file | KP43: {len(kp43_files)} file")

    nonfood = build_nonfood_expenditure(
        kp42_files = kp42_files,
        kp43_files = kp43_files or None,
        verbose    = verbose,
    )

    # ── Integrasi ─────────────────────────────────────────────────────
    if verbose:
        print(f"\n[pipeline] === Integrasi ===")

    df_final = integrate_all(
        soc     = soc,
        food    = food,
        nonfood = nonfood,
        outdir  = output_dir,
        verbose = verbose,
    )

    if verbose:
        print(f"\n[pipeline] ✅ Selesai! Shape: {df_final.shape}")
        print(f"  Kolom: {list(df_final.columns)}")

    return df_final
