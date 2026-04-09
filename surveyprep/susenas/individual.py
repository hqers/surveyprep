"""
surveyprep.susenas.individual
=============================
Modul ART (Individual-Record): merge kuesioner A+B, ekstraksi KRT,
variabel sosio-demografi level rumah tangga.

Sumber data:
  kor20ind_1_diseminasi.csv   ← kuesioner individu bagian A (r4xx-r8xx)
  kor20ind_2_diseminasi.csv   ← kuesioner individu bagian B (r9xx-r22xx)

Variabel ART yang digunakan
----------------------------
  r401  → Nomor urut ART
  r403  → Hubungan dengan KRT  (1=KRT, 2=pasangan, 3=anak, dst.)
  r405  → Jenis kelamin        (1=Laki-laki, 2=Perempuan)
  r407  → Umur (tahun)
  r408  → Apakah suami/istri biasanya tinggal di RT ini?

  r615  → Ijazah/STTB tertinggi
    1=Tidak punya ijazah SD   2=SD tamat   3=SD tidak tamat
    4=Paket A                 5=SMP/sederajat   6=Paket B
    7=SMA/sederajat           8=Paket C         9=SMA kejuruan
    ...lihat recode_education() untuk mapping lengkap...
    17=DIV/S1   18=DIV/S1 (kode lama)   19=Profesi
    20=S2       21=S3                   22=Tidak punya ijazah

  r703  → Kegiatan utama seminggu terakhir
    1=Bekerja  2=Sementara tidak bekerja  3=Mencari pekerjaan  ...
  r704  → Sementara tidak bekerja (flag)
  r705  → Lapangan usaha utama (kode KBLI 1 digit: 1-9, A=pertanian, dll.)
  r706  → Status/kedudukan pekerjaan utama
    1=Berusaha sendiri
    2=Berusaha dibantu buruh tidak tetap/tidak dibayar
    3=Berusaha dibantu buruh tetap/dibayar
    4=Buruh/karyawan/pegawai
    5=Pekerja bebas di pertanian
    6=Pekerja keluarga/tidak dibayar

  r701  → Memiliki rekening tabungan (1=Ya, 2=Tidak)
  r801  → Menggunakan telepon seluler 3 bulan terakhir
  r802  → Memiliki/menguasai telepon seluler 3 bulan terakhir

Variabel yang dihasilkan (level RT)
-------------------------------------
  EducationHead        → pendidikan tertinggi KRT (string kategori)
  OccupationHeadSector → lapangan usaha KRT (kode string)
  StatusPekerjaanKRT   → status pekerjaan KRT
  SexHead              → jenis kelamin KRT
  AgeHead              → umur KRT (integer)
  N_Working            → jumlah ART bekerja
  WorkerShare          → N_Working / HouseholdSize
  DependencyRatio      → (anak 0-14 + lansia 65+) / dewasa 15-64
  AccessCommunication  → apakah ada ART yang memiliki HP (Ya/Tidak)
  HasSavingsAccount    → apakah ada ART yang punya rekening tabungan
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Optional, List, Tuple

from ..core.reader import read_bps_csv
from ..core.runner import execute_runner


# ─── Mapping pendidikan (r615) ───────────────────────────────────────────────
# Berdasarkan metadata Susenas 2020
# Disederhanakan ke 7 band untuk clustering (mengurangi kardinalitas)
_EDU_BAND: dict = {
    # Tidak punya / Tidak tamat SD
    '1':  'Tidak punya ijazah SD',
    '2':  'SD tamat',
    '3':  'SD tidak tamat',
    '4':  'Paket A',
    # SMP
    '5':  'SMP/Sederajat',
    '6':  'Paket B',
    # SMA
    '7':  'SMA/Sederajat',
    '8':  'Paket C',
    '9':  'SMK/Kejuruan',
    # Diploma
    '13': 'DI/DII',
    '14': 'DI/DII',
    '15': 'DIII',
    '16': 'DIII',
    # Sarjana
    '17': 'DIV/S1',
    '18': 'DIV/S1',
    # Pascasarjana
    '19': 'Profesi',
    '20': 'S2',
    '21': 'S3',
    # Tidak punya (kode khusus)
    '22': 'Tidak punya ijazah SD',
}

# Band yang lebih sederhana (7 level ordinal — tetap sebagai string)
_EDU_SIMPLE: dict = {
    'Tidak punya ijazah SD':  'Tidak_Tamat_SD',
    'SD tamat':               'SD',
    'SD tidak tamat':         'Tidak_Tamat_SD',
    'Paket A':                'SD',
    'SMP/Sederajat':          'SMP',
    'Paket B':                'SMP',
    'SMA/Sederajat':          'SMA',
    'Paket C':                'SMA',
    'SMK/Kejuruan':           'SMA',
    'DI/DII':                 'Diploma',
    'DIII':                   'Diploma',
    'DIV/S1':                 'S1',
    'Profesi':                'S1',
    'S2':                     'S2_S3',
    'S3':                     'S2_S3',
}


# Mapping lapangan usaha (r705) — KBLI 1 digit, Susenas 2017–2023
# Susenas 2024: r706 (kode berbeda, 26 sektor), mapping di individual_2024.py
_OCC_SECTOR: dict = {
    '1': 'Pertanian',          # Pertanian, kehutanan, perikanan
    '2': 'Pertambangan',       # Pertambangan dan penggalian
    '3': 'Industri',           # Industri pengolahan
    '4': 'Listrik_Gas_Air',    # Listrik, gas, air bersih
    '5': 'Konstruksi',         # Konstruksi/bangunan
    '6': 'Perdagangan',        # Perdagangan, hotel, restoran
    '7': 'Transportasi',       # Transportasi dan komunikasi
    '8': 'Keuangan',           # Keuangan, perbankan, asuransi
    '9': 'Jasa',               # Jasa kemasyarakatan, sosial, pribadi
}

# RUNNER untuk variabel ART-level
RUNNER_ART = [
    # Pendidikan KRT — dari baris KRT di ART
    # (hasil recode dilakukan terpisah di build_individual)

    # Status pekerjaan KRT
    dict(kind='from_art_head', out='StatusPekerjaanKRT', col='r706',
         map={
             '1': 'Berusaha sendiri',
             '2': 'Berusaha + buruh tdk tetap',
             '3': 'Berusaha + buruh tetap',
             '4': 'Buruh/karyawan/pegawai',
             '5': 'Pekerja bebas',
             '6': 'Pekerja keluarga/tidak dibayar',
         }),

    # Kepemilikan HP (any_art: True jika ada ART yang punya)
    # r802: Memiliki/menguasai telepon seluler dalam 3 bulan terakhir
    dict(kind='any_art', out='AccessCommunication', col='r802',
         truthy=('1', '01', 'YA', 'Ya', 'ya'),
         yes='Ya', no='Tidak'),

    # Rekening tabungan (any_art)
    # r701: Apakah memiliki rekening tabungan?
    dict(kind='any_art', out='HasSavingsAccount', col='r701',
         truthy=('1', '01'),
         yes='Ya', no='Tidak'),
]


# ─── Fungsi helper ───────────────────────────────────────────────────────────

def _detect_krt(art: pd.DataFrame, head_col: str = 'r403') -> pd.Series:
    """
    Deteksi baris KRT secara robust (string atau numerik).
    Kembalikan boolean Series.
    """
    v_str = (art[head_col].astype(str)
                          .str.replace('\xa0', '', regex=False)
                          .str.strip())
    v_num = pd.to_numeric(v_str.str.replace(',', '.', regex=False), errors='coerce')
    return v_str.isin({'1', '01', 'YA', 'Ya', 'ya', 'A', 'a'}) | (v_num == 1)


def _recode_education(raw_val) -> str:
    """Recode nilai r615 ke band pendidikan (string)."""
    try:
        x = str(int(float(str(raw_val).replace(',', '.'))))
    except Exception:
        return pd.NA
    detail = _EDU_BAND.get(x, pd.NA)
    if pd.isna(detail):
        return pd.NA
    return _EDU_SIMPLE.get(detail, detail)


# ─── Fungsi utama ────────────────────────────────────────────────────────────

def load_art_merged(
    art_a_path: str,
    art_b_path: Optional[str] = None,
    verbose: bool = True,
) -> pd.DataFrame:
    """
    Baca dan merge file individu (kuesioner A + B, atau satu file gabungan).

    Susenas membagi kuesioner individu menjadi dua file:
      - ind_1: blok r4xx–r8xx (identitas, pendidikan, ketenagakerjaan, HP)
      - ind_2: blok r9xx–r22xx (kesehatan, disabilitas, program sosial, dll.)

    Tapi beberapa distribusi (mahasiswa, permintaan khusus) bisa jadi:
      - Satu file gabungan (art_b_path=None)
      - Dua file tapi kolom tidak lengkap (subset kolom)
      - Format DBF (dikonversi ke CSV dulu, lihat README)

    Merge dilakukan dengan outer join pada kunci bersama.
    Kolom duplikat (_bdup) digabungkan dengan combine_first.

    Parameters
    ----------
    art_a_path : str
        Path ke file individu A (atau file gabungan jika art_b_path=None).
    art_b_path : str | None
        Path ke file individu B. Jika None, hanya art_a yang digunakan.
    verbose : bool

    Returns
    -------
    pd.DataFrame — satu baris per individu
    """
    a = read_bps_csv(art_a_path, verbose=verbose)

    # Kalau hanya satu file (gabungan atau subset)
    if art_b_path is None:
        if verbose:
            print(f"  [individual] Satu file ART: {a.shape[0]:,} baris x {a.shape[1]} kolom")
            missing_blok = []
            if not any(c.startswith('r4') for c in a.columns):
                missing_blok.append('blok 4 (identitas)')
            if not any(c.startswith('r13') or c.startswith('r14') for c in a.columns):
                missing_blok.append('blok 13-14 (kesehatan/imunisasi)')
            if missing_blok:
                print(f"  [individual] WARN: kolom berikut tidak ditemukan: {missing_blok}")
                print(f"  [individual] Pipeline tetap jalan tapi beberapa fitur mungkin NA")
        return a

    b = read_bps_csv(art_b_path, verbose=verbose)

    # Normalisasi key
    for df in (a, b):
        for kc in ('renum', 'r401'):
            if kc in df.columns:
                df[kc] = df[kc].astype('string').str.strip()

    # Tentukan key join
    keys = [k for k in ('renum', 'r401') if k in a.columns and k in b.columns]
    if not keys:
        keys = ['renum']

    art = pd.merge(a, b, on=keys, how='outer', suffixes=('', '_bdup'))

    # Gabungkan kolom duplikat
    dups = [c for c in art.columns if c.endswith('_bdup')]
    for c in dups:
        base = c[:-5]
        if base in art.columns:
            art[base] = art[base].combine_first(art[c])
    art.drop(columns=dups, inplace=True, errors='ignore')

    # Normalisasi tipe
    for c in ('renum', 'r401', 'r403'):
        if c in art.columns:
            art[c] = art[c].astype('string').str.strip()
    for c in ('r405', 'r407', 'r615', 'r705'):
        if c in art.columns:
            art[c] = pd.to_numeric(art[c], errors='coerce')

    if verbose:
        print(f"  [individual] ART merged: {len(art):,} individu")
    return art


def build_individual(
    art: pd.DataFrame,
    soc: Optional[pd.DataFrame] = None,
    verbose: bool = True,
    extra_runner: Optional[list] = None,
) -> pd.DataFrame:
    """
    Bangun fitur sosio-demografi level RT dari data ART.

    Jika soc (dari build_hh_record) diberikan, variabel baru di-merge ke soc.
    Jika tidak, DataFrame baru dibuat mulai dari HouseholdSize.

    Parameters
    ----------
    art : pd.DataFrame
        Data ART hasil load_art_merged().
    soc : pd.DataFrame | None
        DataFrame level RT dari build_hh_record. Jika None, dibuat baru.
    verbose : bool
    extra_runner : list | None
        Entri RUNNER tambahan (selain RUNNER_ART default).

    Returns
    -------
    pd.DataFrame — level RT dengan kolom sosio-demografi
    """
    art = art.copy()
    art['renum'] = art['renum'].astype('string').str.strip()

    # ── Ukuran RT (fallback jika soc belum punya HouseholdSize) ──
    if soc is None:
        hhsize = (art.groupby('renum', as_index=False)
                     .size()
                     .rename(columns={'size': 'HouseholdSize'}))
        hhsize['HouseholdSize'] = hhsize['HouseholdSize'].astype('Int64')
        soc = hhsize.copy()
    else:
        soc = soc.copy()
        # Normalisasi kunci: HHID → renum untuk join internal
        if 'HHID' in soc.columns and 'renum' not in soc.columns:
            soc = soc.rename(columns={'HHID': 'renum'})

    # ── Deteksi KRT ──
    if 'r403' not in art.columns:
        print("  [individual] WARN: r403 tidak ada → tidak bisa deteksi KRT")
        is_head = pd.Series(False, index=art.index)
    else:
        is_head = _detect_krt(art, 'r403')
    if verbose:
        print(f"  [individual] KRT terdeteksi: {is_head.sum():,} baris "
              f"({art.loc[is_head,'renum'].nunique():,} RT unik)")

    # ── Pendidikan KRT (recode r615) ──
    if 'r615' in art.columns:
        head_edu = (art.loc[is_head, ['renum', 'r615']]
                       .assign(renum=lambda d: d['renum'].astype('string').str.strip())
                       .drop_duplicates('renum'))
        head_edu['EducationHead'] = (
            head_edu['r615']
            .apply(lambda v: _recode_education(pd.to_numeric(v, errors='coerce')))
            .astype('string')
        )
        soc = (soc.drop(columns=['EducationHead'], errors='ignore')
                  .merge(head_edu[['renum', 'EducationHead']], on='renum', how='left'))
    else:
        print("  [individual] WARN: r615 tidak ada → EducationHead = NA")
        soc['EducationHead'] = pd.NA

    # ── Lapangan usaha KRT (r705) ──
    if 'r705' in art.columns:
        head_occ = (art.loc[is_head, ['renum', 'r705']]
                       .assign(renum=lambda d: d['renum'].astype('string').str.strip())
                       .drop_duplicates('renum'))
        head_occ['OccupationHeadSector'] = (
            head_occ['r705']
            .apply(lambda v: _OCC_SECTOR.get(
                str(int(float(str(v).replace(',','.')))), pd.NA)
                if pd.notna(v) and str(v).strip() not in ('', 'nan') else pd.NA)
            .astype('string')
        )
        soc = (soc.drop(columns=['OccupationHeadSector'], errors='ignore')
                  .merge(head_occ[['renum', 'OccupationHeadSector']], on='renum', how='left'))
    else:
        soc['OccupationHeadSector'] = pd.NA

    # ── Jenis kelamin KRT (r405) ──
    if 'r405' in art.columns:
        head_sex = (art.loc[is_head, ['renum', 'r405']]
                       .assign(renum=lambda d: d['renum'].astype('string').str.strip())
                       .drop_duplicates('renum'))
        sex_num = pd.to_numeric(head_sex['r405'], errors='coerce').astype('Int64')
        head_sex['SexHead'] = sex_num.map({1: 'Laki-laki', 2: 'Perempuan'}).astype('string')
        soc = (soc.drop(columns=['SexHead'], errors='ignore')
                  .merge(head_sex[['renum', 'SexHead']], on='renum', how='left'))
    else:
        soc['SexHead'] = pd.NA

    # ── Umur KRT (r407) ──
    if 'r407' in art.columns:
        head_age = (art.loc[is_head, ['renum', 'r407']]
                       .assign(renum=lambda d: d['renum'].astype('string').str.strip())
                       .drop_duplicates('renum'))
        head_age['AgeHead'] = pd.to_numeric(
            head_age['r407'], errors='coerce'
        ).round().astype('Int64')
        soc = (soc.drop(columns=['AgeHead'], errors='ignore')
                  .merge(head_age[['renum', 'AgeHead']], on='renum', how='left'))
    else:
        soc['AgeHead'] = pd.Series(pd.NA, index=soc.index, dtype='Int64')

    # ── N_Working dan WorkerShare ──
    work = pd.Series(False, index=art.index)
    for wc in ('r703', 'r704'):
        if wc in art.columns:
            work = work | (art[wc].astype(str).str.strip().isin(['1', '01']))
    work_cnt = (art.assign(_w=work)
                   .groupby('renum', as_index=False)['_w']
                   .sum()
                   .rename(columns={'_w': 'N_Working'}))
    soc = (soc.drop(columns=['N_Working', 'WorkerShare'], errors='ignore')
              .merge(work_cnt, on='renum', how='left'))
    soc['N_Working'] = soc['N_Working'].fillna(0).astype('Int64')
    _den = pd.to_numeric(soc.get('HouseholdSize', pd.Series(dtype=float)), errors='coerce').astype(float)
    _num = pd.to_numeric(soc['N_Working'], errors='coerce').astype(float)
    soc['WorkerShare'] = np.where(_den > 0, _num / _den, 0.0)

    # ── Dependency Ratio ──
    if 'r407' in art.columns:
        age_df = art[['renum', 'r407']].copy()
        age_df['age'] = pd.to_numeric(age_df['r407'], errors='coerce')
        grp = (age_df.assign(
                    child=lambda d: d['age'].between(0, 14),
                    adult=lambda d: d['age'].between(15, 64),
                    elder=lambda d: d['age'] >= 65)
                .groupby('renum')
                .agg(N_child=('child','sum'), N_adult=('adult','sum'), N_elder=('elder','sum'))
                .reset_index())
        soc = (soc.drop(columns=['N_child','N_adult','N_elder','DependencyRatio'], errors='ignore')
                  .merge(grp, on='renum', how='left')
                  .fillna({'N_child':0, 'N_adult':0, 'N_elder':0}))
        _den2 = soc['N_adult'].astype(float)
        _num2 = (soc['N_child'] + soc['N_elder']).astype(float)
        soc['DependencyRatio'] = np.where(_den2 > 0, _num2 / _den2, 0.0)
    else:
        soc['DependencyRatio'] = np.nan

    # ── RUNNER ART (StatusPekerjaanKRT, AccessCommunication, HasSavingsAccount) ──
    runner = RUNNER_ART + (extra_runner or [])
    if verbose:
        print(f"  [individual] Menjalankan {len(runner)} RUNNER items...")
    # Buat stub rt agar runner tidak error (from_rt tidak digunakan di sini)
    stub_rt = art[['renum']].drop_duplicates().copy()
    soc = execute_runner(soc, stub_rt, art, runner_list=runner, verbose=verbose)

    # ── Buang kolom mentah KRT ──
    soc.drop(columns=[c for c in ['r615','r705','r405','r407'] if c in soc.columns],
             inplace=True, errors='ignore')

    # ── Rename kunci → HHID ──
    if 'renum' in soc.columns:
        soc = soc.rename(columns={'renum': 'HHID'})

    if verbose:
        print(f"  [individual] ✓ {len(soc):,} RT, {soc.shape[1]} kolom")
    return soc
