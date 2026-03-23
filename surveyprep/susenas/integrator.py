"""
surveyprep.susenas.integrator
==============================
Integrasi semua modul Susenas menjadi satu dataset siap klasterisasi.

Fungsi ini menggabungkan output dari:
  build_hh_record()    → soc (sosio-demografi RT)
  build_individual()   → fitur ART-level
  build_food_expenditure()    → indikator pangan
  build_nonfood_expenditure() → indikator non-pangan

Dan menghitung share/burden berbasis pengeluaran:
  Share (denom = TotalFoodExp)         → StapleShare, ProteinShare, dll.
  Burden (denom = TotalExp)            → FoodShare, EnergyBurden, dll.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Optional

from ..core.imputer  import impute_mixed, cap_outliers
from ..core.exporter import export_dual


# ─── Helper safe division ────────────────────────────────────────────────────

def _safe_div(a, b) -> np.ndarray:
    """Pembagian aman: 0 jika denominator ≤ 0."""
    a = np.asarray(a, dtype='float64')
    b = np.asarray(b, dtype='float64')
    return np.where(b > 0, a / b, 0.0)


# ─── Prioritas totals KP43 ───────────────────────────────────────────────────

def _resolve_totals(tot: pd.DataFrame) -> pd.DataFrame:
    """
    Tetapkan nilai total food/nonfood/expend menggunakan hierarki sumber:
      1. KP43 resmi BPS (jika tersedia dan > 0)
      2. Agregasi bottom-up dari KP41/KP42 (fallback)
    """
    tot = tot.copy()

    # Inisialisasi kolom target jika belum ada
    for c in ['TotalFoodExp_month', 'TotalNonFoodExp_month', 'TotalExp_month']:
        if c not in tot.columns:
            tot[c] = np.nan

    # Food → KP43 > KP41
    if 'TotalFoodExp_month_kp43' in tot.columns:
        tot['TotalFoodExp_month'] = (
            tot['TotalFoodExp_month_kp43']
            .replace(0, np.nan)
            .combine_first(tot['TotalFoodExp_month'])
        )

    # NonFood → KP43 > KP42 items
    if ('TotalNonFoodExp_month_kp43' in tot.columns and
            'TotalNonFoodExp_month_from_items' in tot.columns):
        tot['TotalNonFoodExp_month'] = (
            tot['TotalNonFoodExp_month_kp43']
            .replace(0, np.nan)
            .combine_first(tot['TotalNonFoodExp_month_from_items'])
        )
    elif 'TotalNonFoodExp_month_from_items' in tot.columns:
        tot['TotalNonFoodExp_month'] = tot['TotalNonFoodExp_month_from_items']

    # Total → KP43 > food+nonfood
    sum_ = tot['TotalFoodExp_month'].fillna(0) + tot['TotalNonFoodExp_month'].fillna(0)
    if 'TotalExp_month_kp43' in tot.columns:
        tot['TotalExp_month'] = (
            tot['TotalExp_month_kp43']
            .replace(0, np.nan)
            .combine_first(sum_)
        )
    else:
        tot['TotalExp_month'] = sum_

    return tot


# ─── Hitung shares dan burdens ──────────────────────────────────────────────

def _compute_shares(tot: pd.DataFrame) -> pd.DataFrame:
    """
    Hitung semua share dan burden dari kolom pengeluaran yang ada.

    Share (denominator = TotalFoodExp_month):
      StapleShare_monthly, ProteinShare_ASF, PlantProteinShare,
      FVShare, ProcessedShare, PreparedFoodShare, TobaccoShare

    Burden (denominator = TotalExp_month):
      FoodShare, EnergyBurden, NonFoodBurden,
      EducationShare, HealthShare, CommunicationShare,
      HousingShare, TransportShare
    """
    tot = tot.copy()
    F = tot['TotalFoodExp_month'].values
    T = tot['TotalExp_month'].values

    # ── Share berbasis pangan ──
    share_food = [
        ('Staple_month',      'StapleShare_monthly'),
        ('ProteinASF_month',  'ProteinShare_ASF'),
        ('PlantProt_month',   'PlantProteinShare'),
        ('FV_month',          'FVShare'),
        ('Processed_month',   'ProcessedShare'),
        ('Prepared_month',    'PreparedFoodShare'),
        ('Tobacco_month',     'TobaccoShare'),
    ]
    for src, dst in share_food:
        if src in tot.columns:
            tot[dst] = _safe_div(tot[src].values, F)

    # ── Burden berbasis total pengeluaran ──
    tot['FoodShare']    = _safe_div(F, T)
    tot['NonFoodBurden'] = _safe_div(tot['TotalNonFoodExp_month'].values
                                     if 'TotalNonFoodExp_month' in tot.columns
                                     else np.zeros(len(tot)), T)

    # Energi = listrik + BBM
    elec  = tot.get('Elec_month',  pd.Series(0.0, index=tot.index)).fillna(0)
    fuels = tot.get('Fuels_month', pd.Series(0.0, index=tot.index)).fillna(0)
    tot['EnergyExp_month'] = elec + fuels
    tot['EnergyBurden']    = _safe_div(tot['EnergyExp_month'].values, T)

    burden_cols = [
        ('Education_month',    'EducationShare'),
        ('Health_month',       'HealthShare'),
        ('Communication_month','CommunicationShare'),
        ('HousingBase_month',  'HousingShare'),
        ('Transport_month',    'TransportShare'),
    ]
    for src, dst in burden_cols:
        if src in tot.columns:
            tot[dst] = _safe_div(tot[src].values, T)

    return tot


# ─── Fungsi utama ─────────────────────────────────────────────────────────────

def integrate_all(
    soc: pd.DataFrame,
    food: pd.DataFrame,
    nonfood: pd.DataFrame,
    dds_cols: Optional[list] = None,
    outdir: Optional[str] = None,
    cap_outliers_n_sd: float = 5.0,
    verbose: bool = True,
) -> pd.DataFrame:
    """
    Gabungkan semua modul menjadi satu dataset level RT siap analisis.

    Parameters
    ----------
    soc : pd.DataFrame
        Output build_hh_record() + build_individual(). Kunci: HHID.
    food : pd.DataFrame
        Output build_food_expenditure(). Kunci: renum.
    nonfood : pd.DataFrame
        Output build_nonfood_expenditure(). Kunci: renum.
    dds_cols : list | None
        Kolom DDS dari food yang ikut digabung (default: semua DDS).
    outdir : str | None
        Jika diberikan, panggil export_dual() ke direktori ini.
    cap_outliers_n_sd : float
        Threshold cap outlier. Default: 5 SD dari median.
    verbose : bool

    Returns
    -------
    pd.DataFrame — dataset lengkap level RT (HHID sebagai kunci)
    """
    # ── Normalisasi kunci ──
    soc = soc.copy()
    food = food.copy()
    nonfood = nonfood.copy()

    # Pastikan soc punya HHID
    if 'HHID' not in soc.columns and 'renum' in soc.columns:
        soc = soc.rename(columns={'renum': 'HHID'})

    # food dan nonfood pakai 'renum' untuk join
    for df in (food, nonfood):
        if 'renum' not in df.columns and 'HHID' in df.columns:
            df.rename(columns={'HHID': 'renum'}, inplace=True)

    # ── Gabung food + nonfood ──
    _dds = dds_cols or [
        'DDS14', 'DDS13_noTob', 'DDS12_noTobPrep',
        'DDS14_norm', 'DDS13_noTob_norm', 'DDS12_noTobPrep_norm',
    ]
    dds_present = [c for c in _dds if c in food.columns]

    # Kolom dari food yang ikut
    food_keep = (['renum', 'TotalFoodExp_month',
                  'Staple_month', 'ProteinASF_month', 'PlantProt_month',
                  'FV_month', 'Processed_month', 'Prepared_month', 'Tobacco_month']
                 + dds_present
                 + [c for c in food.columns if c in ('Kalori_month', 'Protein_month')])
    food_keep = [c for c in dict.fromkeys(food_keep) if c in food.columns]

    tot = (food[food_keep]
               .merge(nonfood, on='renum', how='outer')
               .fillna(0.0))

    # ── Resolusi totals ──
    tot = _resolve_totals(tot)

    # ── Hitung shares & burdens ──
    tot = _compute_shares(tot)

    if verbose:
        print(f"  [integrator] Food + NonFood merged: {len(tot):,} RT")

    # ── Gabung dengan soc ──
    out = soc.merge(tot, left_on='HHID', right_on='renum', how='left')
    out.drop(columns=['renum'], inplace=True, errors='ignore')

    # ── Cap outlier pada kolom numerik pengeluaran ──
    exp_cols = [c for c in out.columns if 'exp' in c.lower() or 'month' in c.lower()]
    out = cap_outliers(out, num_cols=exp_cols, n_sd=cap_outliers_n_sd, verbose=verbose)

    # ── Imputasi ──
    design_skip = ['HHID', 'psu', 'ssu', 'strata', 'fwt', 'wi1', 'wi2', 'wi3',
                   'wert', 'weind']
    out = impute_mixed(out, skip_cols=design_skip, verbose=verbose)

    if verbose:
        n_num = sum(1 for c in out.columns
                    if pd.api.types.is_numeric_dtype(out[c]) and c not in design_skip)
        n_cat = sum(1 for c in out.columns
                    if not pd.api.types.is_numeric_dtype(out[c]) and c != 'HHID')
        print(f"  [integrator] ✓ {len(out):,} RT | "
              f"{n_num} fitur numerik + {n_cat} kategorik = {n_num+n_cat} total")

    # ── Ekspor jika diminta ──
    if outdir:
        export_dual(out, outdir=outdir, id_col='HHID', verbose=verbose)

    return out
