"""
surveyprep.core.reader_stata
=============================
Reader untuk file Stata (.dta) yang digunakan oleh survei keluarga EHCVM
dan LSMS. Melengkapi reader.py yang menangani CSV Susenas.

Perbedaan utama CSV vs Stata untuk pipeline SurveyPrep
-------------------------------------------------------
CSV (Susenas):
  - read_csv() dengan separator ; dan encoding latin-1
  - join key: satu kolom 'renum' atau 'urut'
  - kolom desain survei: psu, ssu, strata, wi1, wi2

Stata (EHCVM):
  - read_stata() — menangani format .dta v13/v14/v15/v16/v18 otomatis
  - join key: COMPOSITE (grappe + menage) → di-hash menjadi hhid
  - kolom desain survei: grappe, menage, hhweight, vague, milieu
  - Stata sering menyimpan value labels di file — bisa dipakai langsung
    tapi kita normalisasi ke string untuk konsistensi dengan Susenas

Cara pakai
----------
    from surveyprep.core.reader_stata import (
        read_ehcvm_dta, make_hhid, merge_ehcvm_files
    )

    # Baca satu file
    df_housing = read_ehcvm_dta('data/s11_me_ben_2021.dta')

    # Buat composite hhid
    df_housing = make_hhid(df_housing)

    # Merge beberapa file sekaligus pada hhid
    df = merge_ehcvm_files(
        data_dir='data/',
        files=['s11_me_ben_2021.dta', 's12_me_ben_2021.dta'],
        on='hhid',
    )
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Union, List

import numpy as np
import pandas as pd


# ─── Konstanta ────────────────────────────────────────────────────────────────
EHCVM_CLUSTER_COL = 'grappe'
EHCVM_HH_COL      = 'menage'
EHCVM_HHID_COL    = 'hhid'
EHCVM_IND_COL     = 's01q00a'   # individual ID dalam HH (sesuai BID)
EHCVM_WAVE_COL    = 'vague'
EHCVM_WEIGHT_COL  = 'hhweight'


# ─── Core reader ─────────────────────────────────────────────────────────────
def read_ehcvm_dta(
    path: Union[str, Path],
    *,
    columns: Optional[List[str]] = None,
    convert_categoricals: bool = False,
    verbose: bool = False,
) -> pd.DataFrame:
    """
    Baca satu file Stata EHCVM (.dta) menjadi DataFrame.

    Parameters
    ----------
    path : str | Path
        Path ke file .dta.
    columns : list[str] | None
        Subset kolom yang akan dibaca. None = semua kolom.
    convert_categoricals : bool
        False (default): kode numerik dipertahankan → konsisten dengan Susenas CSV.
        True: konversi Stata value labels ke string Categorical.
    verbose : bool

    Returns
    -------
    pd.DataFrame — semua nama kolom sudah di-lowercase.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File tidak ditemukan: {path}")

    if verbose:
        print(f"  [read_ehcvm_dta] Membaca {path.name} ...")

    df = pd.read_stata(
        path,
        columns=columns,
        convert_categoricals=convert_categoricals,
        convert_missing=False,   # biarkan Stata missing → NaN
    )

    # Normalisasi nama kolom ke lowercase
    df.columns = [c.lower() for c in df.columns]

    if verbose:
        print(f"  [read_ehcvm_dta] ✓ {len(df):,} baris × {df.shape[1]} kolom")

    return df


# ─── Composite key builder ────────────────────────────────────────────────────
def make_hhid(
    df: pd.DataFrame,
    cluster_col: str = EHCVM_CLUSTER_COL,
    hh_col: str = EHCVM_HH_COL,
    out_col: str = EHCVM_HHID_COL,
    sep: str = '_',
) -> pd.DataFrame:
    """
    Buat kolom hhid dari grappe + menage sebagai composite key.

    Format: "{grappe}{sep}{menage}"  mis. "101_3" atau "101-3"

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame yang mengandung cluster_col dan hh_col.
    cluster_col : str
        Nama kolom cluster (default 'grappe').
    hh_col : str
        Nama kolom nomor RT dalam cluster (default 'menage').
    out_col : str
        Nama kolom output (default 'hhid').
    sep : str
        Separator antara grappe dan menage (default '_').

    Returns
    -------
    pd.DataFrame dengan kolom hhid ditambahkan (atau di-overwrite).
    """
    df = df.copy()
    g = df[cluster_col].astype(str).str.strip().str.zfill(4)
    m = df[hh_col].astype(str).str.strip().str.zfill(2)
    df[out_col] = g + sep + m
    return df


# ─── Multi-file merger ────────────────────────────────────────────────────────
def merge_ehcvm_files(
    data_dir: Union[str, Path],
    files: List[str],
    *,
    on: str = EHCVM_HHID_COL,
    how: str = 'inner',
    make_id: bool = True,
    verbose: bool = True,
) -> pd.DataFrame:
    """
    Baca dan merge beberapa file EHCVM pada hhid.

    Parameters
    ----------
    data_dir : str | Path
        Direktori tempat file .dta berada.
    files : list[str]
        Daftar nama file .dta yang akan di-merge.
    on : str
        Kolom kunci join (default 'hhid').
    how : str
        Jenis merge: 'inner', 'left', 'outer' (default 'inner').
    make_id : bool
        Jika True, panggil make_hhid() pada setiap file sebelum merge.
    verbose : bool

    Returns
    -------
    pd.DataFrame hasil merge semua file.
    """
    data_dir = Path(data_dir)
    dfs = []

    for fname in files:
        fpath = data_dir / fname
        df = read_ehcvm_dta(fpath, verbose=verbose)
        if make_id:
            df = make_hhid(df)
        dfs.append(df)

    if not dfs:
        raise ValueError("Tidak ada file yang berhasil dibaca.")

    result = dfs[0]
    for df in dfs[1:]:
        # Hindari duplikasi kolom grappe/menage/hhid
        overlap = [c for c in df.columns
                   if c in result.columns and c != on]
        df = df.drop(columns=overlap, errors='ignore')
        result = result.merge(df, on=on, how=how)

    if verbose:
        print(f"  [merge_ehcvm_files] ✓ merged {len(files)} files → "
              f"{len(result):,} baris × {result.shape[1]} kolom")
    return result


# ─── Loader preset untuk blok utama ──────────────────────────────────────────
def load_ehcvm_housing(data_dir: Union[str, Path], config: dict,
                       verbose: bool = True) -> pd.DataFrame:
    """
    Load data perumahan EHCVM (s11) dan buat hhid.
    Analog dengan build_hh_record() di Susenas.
    """
    path = Path(data_dir) / config['hh_housing_file']
    df = read_ehcvm_dta(path, verbose=verbose)
    df = make_hhid(df)
    return df


def load_ehcvm_food(data_dir: Union[str, Path], config: dict,
                    verbose: bool = True) -> pd.DataFrame:
    """
    Load data konsumsi pangan EHCVM (s07b) dan buat hhid.
    Analog dengan build_food_expenditure() di Susenas.

    Kolom utama output:
        hhid    : household identifier
        codpr   : kode produk
        s07bq02c: nilai konsumsi total (FCFA/minggu)
        s07bq02e: dari pembelian
        s07bq02g: dari produksi sendiri/hadiah
    """
    path = Path(data_dir) / config['food_file']
    df = read_ehcvm_dta(path, verbose=verbose)
    df = make_hhid(df)
    return df


def load_ehcvm_individual(data_dir: Union[str, Path], config: dict,
                           section: str = 'ind_socdemo_file',
                           verbose: bool = True) -> pd.DataFrame:
    """
    Load data individu EHCVM (s01 atau section lain) dan buat hhid.
    Analog dengan load_art_merged() di Susenas.
    """
    path = Path(data_dir) / config[section]
    df = read_ehcvm_dta(path, verbose=verbose)
    df = make_hhid(df)
    return df


def load_ehcvm_nsu(data_dir: Union[str, Path], config: dict,
                   verbose: bool = True) -> pd.DataFrame:
    """
    Load tabel konversi Non-Standard Units (NSU) EHCVM.
    Tidak ada padanannya di Susenas (Susenas sudah dalam unit standar).

    Output: DataFrame dengan kolom codpr, unit, size, weight
    untuk konversi non-standard → kg.
    """
    path = Path(data_dir) / config['nsu_file']
    df = read_ehcvm_dta(path, verbose=verbose)
    # Normalisasi kolom kunci
    df.columns = [c.lower() for c in df.columns]
    return df


def load_ehcvm_weights(data_dir: Union[str, Path], config: dict,
                       verbose: bool = True) -> pd.DataFrame:
    """
    Load tabel bobot survei EHCVM.
    Kolom: grappe, menage, hhweight.
    """
    path = Path(data_dir) / config['weights_file']
    df = read_ehcvm_dta(path, verbose=verbose)
    df = make_hhid(df)
    return df[['hhid', 'grappe', 'menage', EHCVM_WEIGHT_COL]]
