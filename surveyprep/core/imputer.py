"""
surveyprep.core.imputer
=======================
Imputasi tipe-sadar untuk data mixed-type survei rumah tangga.

Prinsip:
  - Numerik  → median imputation (robust terhadap outlier)
  - Kategorik → mode imputation (pertahankan tipe string, jangan encode)
  - Tidak ada encoding ordinal — kompatibel dengan Gower distance
  - Nilai nol pada data konsumsi BUKAN missing — jangan diimputasi
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import List, Optional


def detect_col_types(df: pd.DataFrame, force_cat: Optional[List[str]] = None):
    """
    Deteksi otomatis kolom numerik vs kategorik.

    Parameters
    ----------
    df : pd.DataFrame
    force_cat : list[str] | None
        Kolom yang dipaksa menjadi kategorik meskipun dtype-nya numerik.
        Berguna untuk kode wilayah (r101, r102) yang secara teknis integer.

    Returns
    -------
    num_cols : list[str]
    cat_cols : list[str]
    """
    force_cat = set(c.lower() for c in (force_cat or []))
    num_cols, cat_cols = [], []

    for c in df.columns:
        if c.lower() in force_cat:
            cat_cols.append(c)
        elif pd.api.types.is_numeric_dtype(df[c]):
            num_cols.append(c)
        else:
            cat_cols.append(c)

    return num_cols, cat_cols


def impute_mixed(
    df: pd.DataFrame,
    force_cat: Optional[List[str]] = None,
    skip_cols: Optional[List[str]] = None,
    verbose: bool = False,
) -> pd.DataFrame:
    """
    Imputasi ringan untuk dataset mixed-type.

    Numerik  → median per kolom
    Kategorik → mode per kolom (nilai paling sering)

    Parameters
    ----------
    df : pd.DataFrame
        Dataset yang akan diimputasi. Kolom ID (HHID) tidak disentuh.
    force_cat : list[str] | None
        Kolom yang dipaksa sebagai kategorik.
    skip_cols : list[str] | None
        Kolom yang tidak diimputasi (HHID, bobot survei, dll.).
    verbose : bool

    Returns
    -------
    pd.DataFrame (copy)
    """
    df = df.copy()
    skip = set(c.lower() for c in (skip_cols or []))

    # Pastikan kolom kategorik bertipe string sebelum deteksi
    _DEFAULT_CAT = [
        'EducationHead', 'OccupationHeadSector', 'SexHead',
        'UrbanRural', 'AccessEnergy', 'AccessCommunication',
        'Sanitation', 'HomeOwnership', 'CookingFuel', 'WaterSource',
        'StatusPekerjaanKRT',
    ]
    all_force_cat = list(force_cat or []) + [c for c in _DEFAULT_CAT if c in df.columns]
    for c in all_force_cat:
        if c in df.columns:
            df[c] = df[c].astype('string')

    num_cols, cat_cols = detect_col_types(df, force_cat=all_force_cat)

    n_imputed = 0

    # ── Numerik → median ──
    for c in num_cols:
        if c.lower() in skip:
            continue
        n_na = df[c].isna().sum()
        if n_na > 0:
            med = pd.to_numeric(df[c], errors='coerce').median()
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(med)
            n_imputed += n_na
            if verbose:
                print(f"  [imputer] {c}: {n_na} NA → median={med:.4f}")

    # ── Kategorik → mode ──
    for c in cat_cols:
        if c.lower() in skip:
            continue
        n_na = df[c].isna().sum()
        if n_na > 0:
            mode = df[c].mode(dropna=True)
            if not mode.empty:
                df[c] = df[c].fillna(mode.iloc[0])
                n_imputed += n_na
                if verbose:
                    print(f"  [imputer] {c}: {n_na} NA → mode='{mode.iloc[0]}'")
            df[c] = df[c].astype('string')

    if verbose:
        print(f"  [imputer] Total sel diimputasi: {n_imputed:,}")

    return df


def cap_outliers(
    df: pd.DataFrame,
    num_cols: Optional[List[str]] = None,
    n_sd: float = 5.0,
    verbose: bool = False,
) -> pd.DataFrame:
    """
    Cap (batas atas) outlier ekstrem pada kolom numerik.

    Nilai > median + n_sd * std di-cap ke batas tersebut.
    Nilai negatif pada kolom pengeluaran di-set ke 0.

    Parameters
    ----------
    df : pd.DataFrame
    num_cols : list[str] | None
        Kolom yang di-cap. Jika None, semua kolom numerik.
    n_sd : float
        Jumlah standar deviasi dari median sebagai batas atas. Default: 5.
    verbose : bool

    Returns
    -------
    pd.DataFrame (copy)
    """
    df = df.copy()

    if num_cols is None:
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

    for c in num_cols:
        col = pd.to_numeric(df[c], errors='coerce')
        med  = col.median()
        std  = col.std(ddof=0)
        cap  = med + n_sd * std

        # Nilai negatif pada pengeluaran → 0
        if col.min() < 0:
            df[c] = col.clip(lower=0)
            col   = pd.to_numeric(df[c], errors='coerce')

        n_capped = (col > cap).sum()
        if n_capped > 0:
            df[c] = col.clip(upper=cap)
            if verbose:
                print(f"  [cap] {c}: {n_capped} values capped at {cap:.2f}")

    return df
