"""
surveyprep.core.exporter
========================
Dual-output design: memisahkan profiling-ready dan clustering-ready dataset.

Latar belakang desain
---------------------
Variabel desain survei (PSU, strata, bobot/weights) bukan merupakan
fitur substantif rumah tangga. Jika dimasukkan ke dalam proses
klasterisasi, mereka akan mendistorsi jarak Gower karena:
  1. Bobot (fwt, wi1-wi3) memiliki skala yang sangat berbeda
  2. PSU dan strata mencerminkan desain sampling, bukan perilaku RT

Dua artefak yang dihasilkan
----------------------------
HH_PROFILING_with_weights
    - Memuat SEMUA kolom termasuk bobot dan variabel desain
    - Untuk analisis deskriptif berbobot, tabulasi, estimasi populasi
    - Kompatibel dengan R survey package dan Python's statsmodels

HH_CLUSTERING_ready
    - Hanya memuat fitur konten (tanpa bobot/desain)
    - Untuk input langsung ke AUFS-Samba dan MixClust
    - Kolom ID (HHID) tetap ada untuk traceability

HH_WEIGHTS_sidecar
    - HHID + semua variabel desain survei saja
    - Untuk menggabungkan kembali bobot ke hasil klasterisasi
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
from typing import List, Optional


# Variabel desain survei Susenas yang tidak masuk clustering-ready
_SURVEY_DESIGN_COLS = ['psu', 'ssu', 'strata', 'fwt', 'wi', 'wi1', 'wi2', 'wi3',
                       'wert', 'weind']

# Kolom numerik share/burden yang di-scale ke [0,1] sebelum output
_SCALE_COLS = [
    'StapleShare_monthly', 'ProteinShare_ASF', 'PlantProteinShare',
    'FVShare', 'ProcessedShare', 'PreparedFoodShare', 'TobaccoShare',
    'EnergyBurden', 'NonFoodBurden', 'FoodShare',
    'EducationShare', 'HealthShare', 'CommunicationShare',
    'HousingShare', 'TransportShare',
    'WorkerShare', 'DependencyRatio',
    'DDS14_norm', 'DDS13_noTob_norm', 'DDS12_noTobPrep_norm',
]


def _minmax_scale(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    """Min-max scaling ke [0,1] untuk kolom yang ditentukan."""
    for c in cols:
        if c not in df.columns:
            continue
        x = pd.to_numeric(df[c], errors='coerce')
        xmin, xmax = x.min(skipna=True), x.max(skipna=True)
        if pd.notna(xmin) and pd.notna(xmax) and xmax > xmin:
            df[c] = (x - xmin) / (xmax - xmin)
        else:
            df[c] = x.fillna(0.0)
    return df


def export_dual(
    df: pd.DataFrame,
    outdir: str,
    id_col: str = 'HHID',
    scale: bool = True,
    survey_design_cols: Optional[List[str]] = None,
    scale_cols: Optional[List[str]] = None,
    format: str = 'csv',        # 'csv', 'parquet', atau 'both'
    sep: str = ';',
    verbose: bool = True,
) -> dict:
    """
    Ekspor dataset ke dua versi: profiling-ready dan clustering-ready.

    Parameters
    ----------
    df : pd.DataFrame
        Dataset lengkap hasil integrasi semua modul.
    outdir : str
        Direktori output. Dibuat otomatis jika belum ada.
    id_col : str
        Nama kolom ID rumah tangga. Default: 'HHID'.
    scale : bool
        Jika True, terapkan min-max scaling pada kolom share/burden. Default: True.
    survey_design_cols : list[str] | None
        Kolom desain survei yang dikeluarkan dari clustering-ready.
        Default: PSU, SSU, strata, fwt, wi1-wi3, wert, weind.
    scale_cols : list[str] | None
        Kolom yang di-scale. Default: semua share/burden/DDS.
    format : str
        Format output: 'csv', 'parquet', atau 'both'.
    sep : str
        Separator CSV. Default: semicolon (format BPS).
    verbose : bool

    Returns
    -------
    dict dengan keys:
        profiling_path, clustering_path, weights_path
        n_rows, n_features_clustering
    """
    os.makedirs(outdir, exist_ok=True)

    src = df.copy()

    # ── Paksa tipe kategorik sebagai string ──
    _CAT_COLS = [
        'EducationHead', 'OccupationHeadSector', 'SexHead', 'UrbanRural',
        'AccessEnergy', 'AccessCommunication', 'Sanitation', 'HomeOwnership',
        'CookingFuel', 'WaterSource', 'StatusPekerjaanKRT',
    ]
    for c in _CAT_COLS:
        if c in src.columns:
            src[c] = src[c].astype('string')

    # ── AgeHead → Int64 ──
    if 'AgeHead' in src.columns:
        src['AgeHead'] = pd.to_numeric(src['AgeHead'], errors='coerce').round().astype('Int64')

    # ── Scaling ──
    if scale:
        sc_cols = [c for c in (scale_cols or _SCALE_COLS) if c in src.columns]
        src = _minmax_scale(src, sc_cols)
        if verbose:
            print(f"  [exporter] Scaled {len(sc_cols)} columns to [0,1]")

    # ── Profiling-ready (semua kolom termasuk bobot) ──
    df_profiling = src.copy()

    # ── Clustering-ready (tanpa kolom desain survei) ──
    design_cols = set(c.lower() for c in (survey_design_cols or _SURVEY_DESIGN_COLS))
    drop_for_clustering = [c for c in src.columns
                           if c.lower() in design_cols and c != id_col]
    df_cluster = src.drop(columns=drop_for_clustering, errors='ignore')
    n_features  = df_cluster.shape[1] - (1 if id_col in df_cluster.columns else 0)

    # ── Sidecar bobot ──
    side_cols = [id_col] + [c for c in src.columns
                            if c.lower() in design_cols | {'fwt'}]
    side_cols = list(dict.fromkeys(side_cols))  # dedup order-preserving
    df_sidecar = src[[c for c in side_cols if c in src.columns]].drop_duplicates(id_col)

    # ── Simpan ──
    def _save(frame, name):
        paths = {}
        if format in ('csv', 'both'):
            p = os.path.join(outdir, f"{name}.csv")
            frame.to_csv(p, index=False, sep=sep)
            paths['csv'] = p
        if format in ('parquet', 'both'):
            try:
                p = os.path.join(outdir, f"{name}.parquet")
                frame.to_parquet(p, index=False)
                paths['parquet'] = p
            except Exception as e:
                if verbose:
                    print(f"  [exporter] Parquet gagal ({name}): {e}")
        return paths

    p_profiling = _save(df_profiling, 'HH_PROFILING_with_weights')
    p_cluster   = _save(df_cluster,   'HH_CLUSTERING_ready')
    p_sidecar   = _save(df_sidecar,   'HH_WEIGHTS_sidecar')

    if verbose:
        print(f"\n  [exporter] ✅ Output di: {outdir}")
        print(f"    - HH_PROFILING_with_weights : {df_profiling.shape[0]:,} rows × {df_profiling.shape[1]} cols")
        print(f"    - HH_CLUSTERING_ready       : {df_cluster.shape[0]:,} rows × {df_cluster.shape[1]} cols ({n_features} fitur)")
        print(f"    - HH_WEIGHTS_sidecar        : {df_sidecar.shape[0]:,} rows × {df_sidecar.shape[1]} cols")

    return {
        'profiling_path'       : p_profiling.get('csv') or p_profiling.get('parquet'),
        'clustering_path'      : p_cluster.get('csv')   or p_cluster.get('parquet'),
        'weights_path'         : p_sidecar.get('csv')   or p_sidecar.get('parquet'),
        'n_rows'               : len(src),
        'n_features_clustering': n_features,
    }
