"""
surveyprep.core.runner
======================
Mesin eksekusi RUNNER pattern.

RUNNER adalah daftar deklaratif yang menentukan variabel turunan level
rumah tangga. Setiap entri menentukan SUMBER dan OUTPUT — bukan logika
pengambilan, yang sudah dikapsulasi di sini.

Tiga jenis sumber yang didukung
--------------------------------
from_rt
    Variabel langsung dari level RT (satu baris per RT).
    Contoh: tipe daerah (r105), kepemilikan rumah (r1802).

from_art_head
    Variabel individu yang diambil dari baris KRT (Kepala Rumah Tangga).
    Membutuhkan kolom flag KRT (default: r403 == '1').
    Contoh: pendidikan (r615), jenis pekerjaan (r706).

any_art
    Flag rumah tangga yang True jika minimal satu anggota RT memenuhi kondisi.
    Contoh: kepemilikan HP (r802), penggunaan telepon seluler (r801).

Format entri RUNNER
-------------------
dict(
    kind     = 'from_rt' | 'from_art_head' | 'any_art',
    out      = str,          # nama kolom output
    col      = str,          # nama kolom sumber di RT atau ART
    map      = dict,         # optional: mapping nilai {raw_val: label}
    head_flag= str,          # optional: kolom flag KRT (default: 'r403')
    truthy   = tuple[str],   # optional: nilai yang dianggap True (untuk any_art)
    yes      = str,          # optional: label True (default: 'Ya')
    no       = str,          # optional: label False (default: 'Tidak')
)
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple


# ─── Helper internal ─────────────────────────────────────────────────────────

def _as_str(s: pd.Series) -> pd.Series:
    """Konversi series ke string, strip whitespace dan non-breaking spaces."""
    return (s.astype('string')
             .str.replace('\xa0', '', regex=False)
             .str.strip())


def _get_key(df: pd.DataFrame) -> str:
    """Temukan kolom kunci HH (HHID atau renum)."""
    for c in ('HHID', 'hhid', 'renum', 'RENUM'):
        if c in df.columns:
            return c
    raise KeyError("Tidak ditemukan kolom kunci 'HHID' atau 'renum'.")


def _apply_mapping(series: pd.Series, mapping: Optional[Dict]) -> pd.Series:
    """Terapkan mapping nilai; nilai yang tidak ada di mapping → pd.NA."""
    if not mapping:
        return series
    # Normalisasi semua key mapping ke string
    m = {str(k): v for k, v in mapping.items()}
    return series.map(m)


def _merge_col(soc: pd.DataFrame, tmp: pd.DataFrame, out_col: str) -> pd.DataFrame:
    """
    Merge kolom out_col dari tmp ke soc menggunakan kunci HH.
    Jika out_col sudah ada di soc, di-drop dulu agar tidak terduplikasi.
    """
    lk = _get_key(soc)
    rk = _get_key(tmp)

    if lk != rk:
        tmp = tmp.rename(columns={rk: lk})

    # Ambil hanya kunci + kolom output
    keep = [lk, out_col]
    soc = soc.drop(columns=[c for c in [out_col] if c in soc.columns], errors='ignore')
    return soc.merge(tmp[keep], on=lk, how='left')


# ─── Tiga fungsi eksekutor ───────────────────────────────────────────────────

def _run_from_rt(
    soc: pd.DataFrame,
    rt: pd.DataFrame,
    *,
    out: str,
    col: str,
    map: Optional[Dict] = None,
    **_kw,
) -> pd.DataFrame:
    """
    Ambil variabel dari level RT (satu baris per RT).

    Metadata variabel RT yang relevan (Susenas 2020):
      r105   = Tipe daerah (1=Perkotaan, 2=Perdesaan)
      r301   = Banyaknya ART
      r1802  = Status kepemilikan bangunan tempat tinggal
      r1806  = Bahan atap terluas
      r1807  = Bahan dinding terluas
      r1808  = Bahan lantai terluas
      r1809a = Fasilitas buang air besar
      r1810a = Sumber air minum utama
      r1816  = Sumber penerangan utama
      r1817  = Jenis bahan bakar memasak
    """
    if col not in rt.columns:
        print(f"  [RUNNER] WARN: kolom '{col}' tidak ada di RT → '{out}' = NA")
        soc[out] = pd.NA
        return soc

    rk = _get_key(rt)
    tmp = rt[[rk, col]].copy()
    tmp[col] = _as_str(tmp[col])
    tmp[out] = _apply_mapping(tmp[col], map)
    if map:
        tmp[out] = tmp[out].astype('string')

    return _merge_col(soc, tmp[[rk, out]], out)


def _run_from_art_head(
    soc: pd.DataFrame,
    art: pd.DataFrame,
    *,
    out: str,
    col: str,
    map: Optional[Dict] = None,
    head_flag: str = 'r403',
    **_kw,
) -> pd.DataFrame:
    """
    Ambil variabel dari baris KRT di ART.

    Metadata ART KRT yang relevan (Susenas 2020):
      r403   = Hubungan dengan KRT (1 = KRT itu sendiri)
      r405   = Jenis kelamin (1=Laki-laki, 2=Perempuan)
      r407   = Umur (tahun)
      r615   = Ijazah/STTB tertinggi
               1=SD, 5=SMP, 9=SMA, 15=DI-DIII, 17=DIV/S1, 19=Profesi, 20=S2, 21=S3, 22=Tidak punya
      r705   = Lapangan usaha utama (kode KBLI 1 digit)
      r706   = Status/kedudukan pekerjaan utama
               1=Berusaha sendiri, 2=Berusaha+buruh tdk tetap, 3=Berusaha+buruh tetap,
               4=Buruh/karyawan/pegawai, 5=Pekerja bebas, 6=Pekerja keluarga/tidak dibayar
    """
    if head_flag not in art.columns or col not in art.columns:
        missing = head_flag if head_flag not in art.columns else col
        print(f"  [RUNNER] WARN: kolom '{missing}' tidak ada di ART → '{out}' = NA")
        soc[out] = pd.NA
        return soc

    rk = _get_key(art)

    # Deteksi KRT: robust terhadap format string/numerik
    v_str = _as_str(art[head_flag])
    v_num = pd.to_numeric(
        v_str.str.replace(',', '.', regex=False), errors='coerce'
    )
    is_head = v_str.isin({'1', '01', 'YA', 'Ya', 'ya', 'A', 'a'}) | (v_num == 1)

    sub = (art.loc[is_head, [rk, col]]
             .assign(**{rk: lambda d: _as_str(d[rk])})
             .drop_duplicates(rk))

    sub[col] = _as_str(sub[col])
    sub[out] = _apply_mapping(sub[col], map)
    if map:
        sub[out] = sub[out].astype('string')

    return _merge_col(soc, sub[[rk, out]], out)


def _run_any_art(
    soc: pd.DataFrame,
    art: pd.DataFrame,
    *,
    out: str,
    col: str,
    truthy: Tuple[str, ...] = ('1', '01', 'YA', 'Ya', 'ya', 'Y', 'y', 'TRUE', 'True', 'true'),
    yes: str = 'Ya',
    no: str = 'Tidak',
    **_kw,
) -> pd.DataFrame:
    """
    Flag RT = True jika minimal satu ART memenuhi kondisi.

    Metadata variabel any_art yang relevan (Susenas 2020):
      r801 = Menggunakan telepon seluler dalam 3 bulan terakhir
      r802 = Memiliki/menguasai telepon seluler dalam 3 bulan terakhir
      r701 = Memiliki rekening tabungan
    """
    if col not in art.columns:
        print(f"  [RUNNER] WARN: kolom '{col}' tidak ada di ART → '{out}' = NA")
        soc[out] = pd.NA
        return soc

    rk = _get_key(art)

    a = art[[rk, col]].copy()
    a[col] = _as_str(a[col])
    grp = (a.assign(_flag=a[col].isin(set(truthy)))
            .groupby(rk, as_index=False)['_flag']
            .any())
    grp[out] = grp['_flag'].map({True: yes, False: no}).astype('string')

    return _merge_col(soc, grp[[rk, out]], out)


# ─── Dispatcher utama ────────────────────────────────────────────────────────

_RUNNERS = {
    'from_rt':       _run_from_rt,
    'from_art_head': _run_from_art_head,
    'any_art':       _run_any_art,
}


def execute_runner(
    soc: pd.DataFrame,
    rt: pd.DataFrame,
    art: pd.DataFrame,
    runner_list: List[Dict[str, Any]],
    verbose: bool = False,
) -> pd.DataFrame:
    """
    Eksekusi seluruh daftar RUNNER secara berurutan.

    Parameters
    ----------
    soc : pd.DataFrame
        DataFrame level RT yang sedang dibangun (dari build_hh_record / build_individual).
    rt : pd.DataFrame
        Data RT mentah.
    art : pd.DataFrame
        Data ART mentah (sudah di-merge A+B).
    runner_list : list[dict]
        Daftar entri RUNNER. Lihat docstring modul untuk format.
    verbose : bool
        Jika True, cetak progress setiap item.

    Returns
    -------
    pd.DataFrame
        soc dengan kolom-kolom baru dari RUNNER.
    """
    for item in runner_list:
        kind = item.get('kind')
        out  = item.get('out', '?')

        if kind not in _RUNNERS:
            print(f"  [RUNNER] WARN: kind '{kind}' tidak dikenali, lewati '{out}'")
            continue

        if verbose:
            print(f"  [RUNNER] {kind:16s} → {out}")

        fn = _RUNNERS[kind]
        try:
            soc = fn(soc, rt if kind == 'from_rt' else art,
                     rt=rt, art=art, **item)
        except Exception as e:
            print(f"  [RUNNER] ERROR pada '{out}': {e}")

    return soc
