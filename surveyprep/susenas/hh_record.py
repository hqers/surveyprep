"""
surveyprep.susenas.hh_record
============================
Modul RT (HH-Record): karakteristik rumah tangga, akses layanan, bobot survei.

Sumber data: kor20rt_diseminasi.csv  (Susenas 2020 Maret)

Variabel yang diekstrak
-----------------------
Dari file RT (satu baris per rumah tangga):

  Identifikasi & desain survei:
    renum   → HHID (kunci join semua modul)
    psu     → Primary Sampling Unit
    ssu     → Secondary Sampling Unit
    strata  → Strata (kombinasi kota/desa + Wealth Index)
    wi1     → No urut NKS
    wi2     → No urut Ruta
    wi3     → No urut ART (untuk join)
    fwt     → Penimbang (sampling weight)

  Ukuran rumah tangga:
    r301    → Banyaknya ART (prioritas); fallback: hitung dari file ART

  Karakteristik fisik rumah:
    r1802   → Status kepemilikan bangunan (Milik sendiri / Kontrak-sewa / dll.)
    r1806   → Bahan atap terluas
    r1807   → Bahan dinding terluas
    r1808   → Bahan lantai terluas

  Akses layanan:
    r105    → Tipe daerah (Perkotaan / Perdesaan)
    r1809a  → Fasilitas buang air besar / sanitasi
    r1809b  → Jenis kloset
    r1810a  → Sumber air minum utama
    r1816   → Sumber penerangan utama
    r1817   → Jenis bahan bakar memasak

Catatan versi
-------------
Susenas berubah antar tahun. Kolom yang paling sering berganti:
  - r1802 (kepemilikan) — kadang r1801 di tahun lain
  - r1816 (penerangan) — subkategori PLN bisa berubah
  - r1817 (bahan bakar) — tambahan kode Elpiji 5.5kg muncul di ~2018+
Selalu verifikasi dengan metadata tahun yang digunakan.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Optional, List

from ..core.reader  import read_bps_csv
from ..core.runner  import execute_runner


# ─── Daftar kolom desain survei ──────────────────────────────────────────────
SURVEY_DESIGN_COLS = ['psu', 'ssu', 'strata', 'fwt', 'wi1', 'wi2', 'wi3',
                      'wert', 'weind']


# ─── RUNNER LIST: variabel RT → level rumah tangga ──────────────────────────
#
# Semua mapping nilai berdasarkan metadata resmi BPS (Susenas 2020 Maret).
# Untuk tahun lain, buat salinan list ini dengan mapping yang diperbarui.
#
RUNNER_RT = [
    # ── Tipe daerah ──────────────────────────────────────────────────────
    # r105: Tipe daerah (Susenas 2020: 1=Perkotaan, 2=Perdesaan)
    # ⚠ Perhatian: nilai di raw data bisa "1" atau "2" (string/int)
    dict(kind='from_rt', out='UrbanRural', col='r105',
         map={'1': 'Perkotaan', '2': 'Perdesaan'}),

    # ── Kepemilikan rumah ─────────────────────────────────────────────────
    # r1802: Apakah status kepemilikan bangunan tempat tinggal yang ditempati?
    # 1=Milik sendiri, 2=Kontrak, 3=Sewa, 4=Bebas sewa milik orang lain,
    # 5=Bebas sewa milik orang tua/saudara, 6=Dinas, 7=Lainnya
    dict(kind='from_rt', out='HomeOwnership', col='r1802',
         map={
             '1': 'Milik sendiri',
             '2': 'Kontrak',
             '3': 'Sewa',
             '4': 'Bebas sewa (orang lain)',
             '5': 'Bebas sewa (orang tua/saudara)',
             '6': 'Dinas',
             '7': 'Lainnya',
         }),

    # ── Atap, dinding, lantai ─────────────────────────────────────────────
    # r1806: Bahan bangunan utama atap rumah terluas
    # 1=Beton, 2=Genteng, 3=Sirap, 4=Seng, 5=Asbes, 6=Ijuk/Rumbia, 7=Lainnya
    dict(kind='from_rt', out='RoofMaterial', col='r1806',
         map={
             '1': 'Beton', '2': 'Genteng', '3': 'Sirap',
             '4': 'Seng',  '5': 'Asbes',   '6': 'Ijuk/Rumbia', '7': 'Lainnya',
         }),

    # r1807: Bahan bangunan utama dinding rumah terluas
    # 1=Tembok, 2=Plesteran anyaman bambu/kawat, 3=Kayu/papan,
    # 4=Anyaman bambu, 5=Batang kayu, 6=Bambu, 7=Lainnya
    dict(kind='from_rt', out='WallMaterial', col='r1807',
         map={
             '1': 'Tembok', '2': 'Plesteran anyaman', '3': 'Kayu/papan',
             '4': 'Anyaman bambu', '5': 'Batang kayu', '6': 'Bambu', '7': 'Lainnya',
         }),

    # r1808: Bahan bangunan utama lantai rumah terluas
    # 1=Marmer/Granit, 2=Keramik, 3=Parket/Vinil/Permadani, 4=Ubin/Tegel/Teraso,
    # 5=Kayu/Papan, 6=Semen/Bata merah, 7=Bambu, 8=Tanah, 9=Lainnya
    dict(kind='from_rt', out='FloorMaterial', col='r1808',
         map={
             '1': 'Marmer/Granit',   '2': 'Keramik',
             '3': 'Parket/Vinil',    '4': 'Ubin/Tegel/Teraso',
             '5': 'Kayu/Papan',      '6': 'Semen/Bata merah',
             '7': 'Bambu',           '8': 'Tanah', '9': 'Lainnya',
         }),

    # ── Sanitasi ─────────────────────────────────────────────────────────
    # r1809a: Apakah memiliki fasilitas tempat buang air besar?
    # 1=Ada, digunakan sendiri   2=Ada, digunakan bersama RT tertentu
    # 3=Ada, MCK komunal         4=Ada, MCK umum/WC umum
    # 5=Ada, ART tidak menggunakan (gunakan lainnya)
    # 6=Tidak ada fasilitas
    dict(kind='from_rt', out='Sanitation', col='r1809a',
         map={
             '1': 'Sendiri',
             '2': 'Bersama (RT tertentu)',
             '3': 'MCK komunal',
             '4': 'MCK/WC umum',
             '5': 'Ada tapi tidak digunakan',
             '6': 'Tidak ada',
         }),

    # r1809b: Jenis kloset (opsional, untuk analisis WASH lebih detail)
    # 1=Leher angsa (toilet duduk), 2=Plengsengan, 3=Cemplung/cubluk, 4=Tidak ada
    dict(kind='from_rt', out='ToiletType', col='r1809b',
         map={
             '1': 'Leher angsa', '2': 'Plengsengan',
             '3': 'Cemplung/cubluk', '4': 'Tidak ada',
         }),

    # ── Air minum ─────────────────────────────────────────────────────────
    # r1810a: Apa sumber air utama yang digunakan untuk minum?
    # 1=Air kemasan bermerk  2=Air isi ulang  3=Leding meteran
    # 4=Leding eceran        5=Sumur bor/pompa  6=Sumur terlindung
    # 7=Sumur tak terlindung 8=Mata air terlindung  9=Mata air tak terlindung
    # 10=Air permukaan (sungai, danau, dll.)  11=Air hujan  12=Lainnya
    dict(kind='from_rt', out='WaterSource', col='r1810a',
         map={
             '1':  'Air kemasan bermerk', '2':  'Air isi ulang',
             '3':  'Leding meteran',      '4':  'Leding eceran',
             '5':  'Sumur bor/pompa',     '6':  'Sumur terlindung',
             '7':  'Sumur tak terlindung','8':  'Mata air terlindung',
             '9':  'Mata air tak terlindung', '10': 'Air permukaan',
             '11': 'Air hujan',           '12': 'Lainnya',
         }),

    # ── Penerangan ───────────────────────────────────────────────────────
    # r1816: Sumber utama penerangan rumah tangga
    # 1=Listrik PLN (meteran sendiri)   2=Listrik PLN (meteran bersama/menumpang)
    # 3=Listrik non-PLN                 4=Bukan listrik
    dict(kind='from_rt', out='AccessEnergy', col='r1816',
         map={
             '1': 'PLN_meteran_sendiri',
             '2': 'PLN_meteran_bersama',
             '3': 'Non_PLN',
             '4': 'Bukan_listrik',
         }),

    # ── Bahan bakar memasak ──────────────────────────────────────────────
    # r1817: Jenis bahan bakar utama untuk memasak
    # 1=Listrik    2=Gas/elpiji ≥ 5.5 kg   3=Gas/elpiji 3 kg
    # 4=Gas kota   5=Biogas                 6=Minyak tanah
    # 7=Briket     8=Arang/batok kelapa     9=Kayu bakar
    # 10=Lainnya   0=Tidak memasak
    dict(kind='from_rt', out='CookingFuel', col='r1817',
         map={
             '1': 'Listrik',      '2': 'Elpiji ≥5.5kg', '3': 'Elpiji 3kg',
             '4': 'Gas kota',     '5': 'Biogas',         '6': 'Minyak tanah',
             '7': 'Briket',       '8': 'Arang/batok',    '9': 'Kayu bakar',
             '10': 'Lainnya',     '0': 'Tidak memasak',
         }),
]


# ─── Fungsi utama ────────────────────────────────────────────────────────────

def build_hh_record(
    rt_path: str,
    art: Optional[pd.DataFrame] = None,
    verbose: bool = True,
    extra_runner: Optional[list] = None,
) -> pd.DataFrame:
    """
    Bangun dataset level rumah tangga dari file RT.

    Langkah-langkah:
      1. Baca file RT
      2. Ekstrak variabel desain survei (PSU, strata, bobot)
      3. Ekstrak ukuran RT (r301 jika ada, else hitung dari ART)
      4. Eksekusi RUNNER_RT → kolom kategorik akses layanan

    Parameters
    ----------
    rt_path : str
        Path ke file RT (misal: kor20rt_diseminasi.csv).
    art : pd.DataFrame | None
        Data ART yang sudah di-load (untuk fallback HouseholdSize).
        Jika None dan r301 tidak ada di RT, HouseholdSize = NA.
    verbose : bool
    extra_runner : list | None
        Entri RUNNER tambahan di luar RUNNER_RT default.
        Berguna untuk menambah variabel RT spesifik tanpa mengubah modul ini.

    Returns
    -------
    pd.DataFrame
        Satu baris per rumah tangga, kolom: HHID + desain + fitur.
    """
    rt = read_bps_csv(rt_path, verbose=verbose)

    # ── Normalisasi kunci ──
    if 'renum' not in rt.columns:
        raise KeyError(f"Kolom 'renum' tidak ada di RT: {rt_path}")
    rt['renum'] = rt['renum'].astype('string').str.strip()

    # ── Desain survei ──
    design_found = [c for c in SURVEY_DESIGN_COLS if c in rt.columns]
    rt_design = (rt[['renum'] + design_found]
                   .drop_duplicates('renum')
                   .copy())

    # ── Ukuran rumah tangga ──
    if 'r301' in rt.columns:
        hhsize = (rt[['renum', 'r301']]
                    .rename(columns={'r301': 'HouseholdSize'})
                    .copy())
        hhsize['HouseholdSize'] = pd.to_numeric(
            hhsize['HouseholdSize'], errors='coerce'
        ).astype('Int64')
        if verbose:
            print(f"  [hh_record] HouseholdSize dari r301")
    elif art is not None:
        _art = art.copy()
        _art['renum'] = _art['renum'].astype('string').str.strip()
        hhsize = (_art.groupby('renum', as_index=False)
                      .size()
                      .rename(columns={'size': 'HouseholdSize'}))
        hhsize['HouseholdSize'] = hhsize['HouseholdSize'].astype('Int64')
        if verbose:
            print(f"  [hh_record] HouseholdSize dihitung dari ART (r301 tidak ada)")
    else:
        hhsize = rt[['renum']].assign(HouseholdSize=pd.NA).drop_duplicates('renum')
        if verbose:
            print(f"  [hh_record] WARN: HouseholdSize = NA (r301 tidak ada, art=None)")

    # ── Gabung: desain + ukuran → soc dasar ──
    soc = rt_design.merge(hhsize, on='renum', how='left')

    # ── Eksekusi RUNNER ──
    runner = RUNNER_RT + (extra_runner or [])
    if verbose:
        print(f"  [hh_record] Menjalankan {len(runner)} RUNNER items...")
    soc = execute_runner(soc, rt, rt, runner_list=runner, verbose=verbose)
    # Note: ART tidak diperlukan untuk RUNNER_RT (semuanya from_rt)

    # ── Rename kunci → HHID ──
    soc = soc.rename(columns={'renum': 'HHID'})

    if verbose:
        print(f"  [hh_record] ✓ {len(soc):,} rumah tangga, {soc.shape[1]} kolom")
    return soc
