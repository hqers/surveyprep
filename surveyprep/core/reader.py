"""
surveyprep.core.reader
======================
Pembaca CSV dan DBF adaptif untuk format BPS/Susenas.

Format BPS standar:
  - Separator  : semicolon (;)
  - Encoding   : latin-1
  - Desimal    : koma (,)
  - Ribuan     : titik (.)
  - ID kolom   : lowercase setelah normalisasi

Format DBF (dBase III/IV):
  - BPS kadang mendistribusikan data dalam format .dbf
  - read_bps_dbf() membaca tanpa library eksternal (pure Python)
  - Otomatis dideteksi oleh read_bps_csv() berdasarkan ekstensi

Fungsi utama:
    read_bps_csv(path)          ← reader utama, handle CSV dan DBF
    read_bps_dbf(path)          ← reader DBF pure Python
    read_csv_generic(path, ...) ← reader generik untuk survei lain
"""
from __future__ import annotations
import struct
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



# ─── DBF reader (pure Python, tanpa library eksternal) ───────────────────────

def read_bps_dbf(
    path: Union[str, Path],
    encoding: str = 'latin-1',
    verbose: bool = False,
) -> pd.DataFrame:
    """
    Baca file dBase III/IV (.dbf) tanpa library eksternal.

    BPS kadang mendistribusikan Susenas dalam format .dbf, terutama
    untuk data lama (sebelum 2017) atau distribusi khusus ke mahasiswa.

    Parameters
    ----------
    path : str | Path
        Path ke file .dbf
    encoding : str
        Encoding karakter. Default: 'latin-1' (format BPS).
    verbose : bool

    Returns
    -------
    pd.DataFrame — kolom lowercase, string kolom ID dinormalisasi
    """
    path = Path(path)
    with open(path, 'rb') as f:
        # ── Header DBF ─────────────────────────────────────────────────────
        header = f.read(32)
        if len(header) < 32:
            raise ValueError(f"File DBF tidak valid atau rusak: {path}")

        n_records    = struct.unpack_from('<I', header, 4)[0]
        header_size  = struct.unpack_from('<H', header, 8)[0]
        record_size  = struct.unpack_from('<H', header, 10)[0]

        # ── Field descriptors ───────────────────────────────────────────────
        fields = []
        field_data = f.read(header_size - 32 - 1)  # -1 untuk terminator 0x0D
        for i in range(0, len(field_data), 32):
            chunk = field_data[i:i+32]
            if len(chunk) < 32 or chunk[0] == 0x0D:
                break
            name     = chunk[0:11].replace(b'\x00', b'').decode(encoding, errors='replace').strip()
            ftype    = chr(chunk[11])
            flength  = chunk[16]
            fields.append((name.lower(), ftype, flength))

        # ── Records ─────────────────────────────────────────────────────────
        f.seek(header_size)
        rows = []
        for _ in range(n_records):
            rec = f.read(record_size)
            if not rec or len(rec) < record_size:
                break
            if rec[0] == 0x2A:  # deleted record
                continue
            row = {}
            pos = 1  # skip deletion flag
            for name, ftype, flength in fields:
                raw = rec[pos:pos+flength].decode(encoding, errors='replace').strip()
                if ftype == 'N' or ftype == 'F':
                    try:
                        row[name] = float(raw) if '.' in raw else (int(raw) if raw else None)
                    except ValueError:
                        row[name] = None
                elif ftype == 'D':
                    row[name] = raw  # date as string YYYYMMDD
                elif ftype == 'L':
                    row[name] = True if raw in ('T','t','Y','y') else (False if raw in ('F','f','N','n') else None)
                else:
                    row[name] = raw if raw else None
                pos += flength
            rows.append(row)

    df = pd.DataFrame(rows)

    if verbose:
        print(f"[reader] DBF {path.name}: {len(df):,} rows × {df.shape[1]} cols")

    return df



def read_bps_csv(
    path: Union[str, Path],
    str_cols: Tuple[str, ...] = _DEFAULT_STR_COLS,
    verbose: bool = False,
    sep: Optional[str] = None,
    encoding: Optional[str] = None,
    decimal: Optional[str] = None,
    thousands: Optional[str] = None,
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
    sep : str, optional
        Separator kolom. Default: ';' (format BPS standar).
    encoding : str, optional
        Encoding file. Default: 'latin-1'.
    decimal : str, optional
        Karakter desimal. Default: ',' (format BPS standar).
    thousands : str, optional
        Karakter ribuan. Default: '.'.

    Returns
    -------
    pd.DataFrame
    """
    path = Path(path)

    # Auto-detect DBF
    if path.suffix.lower() == '.dbf':
        df = read_bps_dbf(path, encoding=encoding or 'latin-1', verbose=verbose)
        # Normalisasi kolom ID tetap dilakukan di bawah
    else:
        kw = dict(_BPS_READ_KW)
        # Override default BPS jika parameter eksplisit diberikan
        if sep is not None:      kw['sep']       = sep
        if encoding is not None: kw['encoding']  = encoding
        if decimal is not None:  kw['decimal']   = decimal
        if thousands is not None: kw['thousands'] = thousands

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
