"""
surveyprep.core.reader
======================
Pembaca CSV adaptif untuk format BPS/Susenas.

Format BPS standar:
  - Separator  : semicolon (;)
  - Encoding   : latin-1
  - Desimal    : koma (,)
  - Ribuan     : titik (.)
  - ID kolom   : lowercase setelah normalisasi

Fungsi utama:
    read_bps_csv(path)          ← reader utama Susenas
    read_csv_generic(path, ...) ← reader generik untuk survei lain
"""
from __future__ import annotations
import pandas as pd
from pathlib import Path
from typing import Union, Tuple, Optional


# ─── Konstanta format BPS ────────────────────────────────────────────────────
_BPS_READ_KW = dict(
    sep=';',
    encoding='latin-1',
    decimal=',',
    thousands='.',
    low_memory=False,
)

# Kolom yang selalu diperlakukan sebagai string (jangan jadi float)
_DEFAULT_STR_COLS = ('renum', 'kode', 'kelompok', 'klp', 'coicop')


def read_bps_csv(
    path: Union[str, Path],
    str_cols: Tuple[str, ...] = _DEFAULT_STR_COLS,
    verbose: bool = False,
) -> pd.DataFrame:
    """
    Membaca satu file CSV format BPS (Susenas).

    Normalisasi otomatis:
      - Nama kolom → lowercase + strip
      - Kolom ID (renum, kode, dll.) → string + strip
      - Coba C-engine dulu; fallback ke python engine jika gagal

    Parameters
    ----------
    path : str | Path
        Path ke file CSV.
    str_cols : tuple[str]
        Kolom yang dipaksa menjadi string. Default: renum, kode, kelompok, klp, coicop.
    verbose : bool
        Jika True, cetak info shape setelah membaca.

    Returns
    -------
    pd.DataFrame
    """
    path = Path(path)
    kw = dict(_BPS_READ_KW)

    try:
        df = pd.read_csv(path, **kw)
    except Exception:
        # python engine tidak mendukung low_memory
        kw.pop('low_memory', None)
        df = pd.read_csv(path, engine='python', **kw)

    # Normalisasi nama kolom
    df.columns = df.columns.str.lower().str.strip()

    # Paksa kolom ID sebagai string bersih
    for c in str_cols:
        if c in df.columns:
            df[c] = df[c].astype('string').str.strip()

    if verbose:
        print(f"[reader] {path.name}: {df.shape[0]:,} rows × {df.shape[1]} cols")

    return df


def read_bps_csv_multi(
    paths: list,
    str_cols: Tuple[str, ...] = _DEFAULT_STR_COLS,
    verbose: bool = False,
) -> pd.DataFrame:
    """
    Membaca dan menggabungkan (concat) beberapa file CSV format BPS.
    Berguna untuk KP41 yang sering dibagi menjadi beberapa file per provinsi.

    Parameters
    ----------
    paths : list[str | Path]
        Daftar path file CSV.
    str_cols : tuple[str]
        Kolom yang dipaksa string.
    verbose : bool

    Returns
    -------
    pd.DataFrame  (hasil pd.concat, reset_index)
    """
    if not paths:
        raise ValueError("Daftar paths kosong.")

    dfs = []
    for p in paths:
        df = read_bps_csv(p, str_cols=str_cols, verbose=verbose)
        dfs.append(df)

    result = pd.concat(dfs, ignore_index=True, sort=False)
    if verbose:
        print(f"[reader] Merged {len(paths)} files → {result.shape[0]:,} rows")
    return result


def read_csv_generic(
    path: Union[str, Path],
    sep: str = ',',
    encoding: str = 'utf-8',
    decimal: str = '.',
    str_cols: Tuple[str, ...] = (),
    verbose: bool = False,
) -> pd.DataFrame:
    """
    Reader generik untuk survei non-BPS (LSMS, HBS, CEX, dll.).

    Parameters
    ----------
    sep : str
        Separator kolom. Default: koma (CSV standar internasional).
    encoding : str
        Encoding file. Default: utf-8.
    decimal : str
        Karakter desimal. Default: titik.
    str_cols : tuple[str]
        Kolom yang dipaksa string.
    verbose : bool

    Returns
    -------
    pd.DataFrame
    """
    path = Path(path)
    df = pd.read_csv(path, sep=sep, encoding=encoding, decimal=decimal, low_memory=False)
    df.columns = df.columns.str.lower().str.strip()

    for c in str_cols:
        if c in df.columns:
            df[c] = df[c].astype('string').str.strip()

    if verbose:
        print(f"[reader] {path.name}: {df.shape[0]:,} rows × {df.shape[1]} cols")
    return df
