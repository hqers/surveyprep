"""
surveyprep.susenas.nonfood_exp
==============================
Modul KP42/KP43 (NonFood-Expenditure): pengeluaran non-pangan bulanan,
koreksi periode tahunan, breakdown tematik.

Sumber data:
  blok42*.csv  ← item-level non-pangan (KP42), format long
  blok43*.csv  ← totals resmi per RT (KP43), format wide

Perbedaan KP42 vs KP43
-----------------------
KP42  Item-level: satu baris per RT per komoditas non-pangan.
      Memuat nilai bulanan (b42k4) DAN tahunan (b42k5).
      Beberapa item dilaporkan per tahun → harus dibagi 12.

KP43  Total resmi per RT: FOOD, NONFOOD, EXPEND sudah dalam satuan bulanan.
      Ini angka resmi BPS yang digunakan untuk publikasi.
      Prioritas: jika KP43 tersedia, gunakan sebagai total; KP42 untuk breakdown tematik.

Kolom KP42
----------
  renum   → ID RT
  KODE    → No urut rincian komoditas (kode item non-pangan)
  KLP     → Kode subkelompok
  b42k3   → Banyaknya penggunaan
  b42k4   → Nilai pengeluaran sebulan terakhir   ← prioritas
  b42k5   → Nilai pengeluaran setahun terakhir
  SEBULAN → Rata-rata nilai pengeluaran non-pangan sebulan (level RT, bukan item)

Kode item dengan periode TAHUNAN (bagi 12)
------------------------------------------
Pendidikan   255–260
Kesehatan    239–254
Transportasi 261–264
Komunikasi   228, 230  (biaya tahunan: iuran, asuransi)
Rumah        195       (pemeliharaan bangunan tahunan)

Indikator tematik yang dihasilkan
----------------------------------
  TotalNonFoodExp_month   → total non-pangan sebulan
  Elec_month              → listrik (kode 197)
  Water_month             → air (kode 199)
  Fuels_month             → bahan bakar RT (kode 200–224)
  Communication_month     → komunikasi (226–230)
  Education_month         → pendidikan (255–260)
  Health_month            → kesehatan (239–254)
  HousingBase_month       → perumahan dasar (191–195)
  Transport_month         → transportasi (261–264)
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import List, Optional

from ..core.reader import read_bps_csv_multi, read_bps_csv


# ─── Kode item dengan periode tahunan (harus dibagi 12) ─────────────────────
# Berdasarkan metadata KP42 Susenas 2020
ANNUAL_CODES: frozenset = frozenset(
    {str(i) for i in range(239, 255)}   # Kesehatan  239–254
  | {str(i) for i in range(255, 261)}   # Pendidikan 255–260
  | {str(i) for i in range(261, 265)}   # Transportasi besar 261–264
  | {'228', '230'}                       # Komunikasi (iuran/asuransi tahunan)
  | {'195'}                              # Pemeliharaan bangunan
)

# ─── Set kode per tema non-pangan ────────────────────────────────────────────
# Berdasarkan COICOP adaptasi Susenas 2020
ELECTRICITY   = frozenset({'197'})
WATER         = frozenset({'199'})
FUELS         = frozenset({str(i) for i in range(200, 226)}
                          - {'197', '199'})   # BBM RT, elpiji, minyak tanah
COMMUNICATION = frozenset({'226', '227', '228', '229', '230'})
EDUCATION     = frozenset({str(i) for i in range(255, 261)})
HEALTH        = frozenset({str(i) for i in range(239, 255)})
HOUSING_BASE  = frozenset({'191', '192', '193', '194', '195'})  # sewa, iuran perumahan
TRANSPORT     = frozenset({str(i) for i in range(261, 265)})

# Mapping tema → (set kode, nama kolom output)
THEMATIC_MAP = [
    (ELECTRICITY,   'Elec_month'),
    (WATER,         'Water_month'),
    (FUELS,         'Fuels_month'),
    (COMMUNICATION, 'Communication_month'),
    (EDUCATION,     'Education_month'),
    (HEALTH,        'Health_month'),
    (HOUSING_BASE,  'HousingBase_month'),
    (TRANSPORT,     'Transport_month'),
]


# ─── Loader KP42 ─────────────────────────────────────────────────────────────

def _load_kp42(files: List[str], verbose: bool = False) -> pd.DataFrame:
    """
    Baca dan gabungkan file KP42 menjadi format long dengan nilai bulanan.

    Logika nilai:
      - Prioritas: b42k4 (nilai sebulan terakhir, sudah bulanan)
      - Fallback:  b42k5 / 12  (nilai setahun ÷ 12)
      - Fallback2: total komponen k3a–k3e jika keduanya tidak ada
      - Koreksi ANNUAL_CODES: kode dalam set ini selalu dibagi 12

    Returns
    -------
    pd.DataFrame  columns: [renum, kode, valm]
    """
    kp42 = read_bps_csv_multi(files, verbose=verbose)

    if 'renum' not in kp42.columns or 'kode' not in kp42.columns:
        raise KeyError("KP42: wajib punya kolom 'renum' dan 'kode'.")

    kp42['kode'] = kp42['kode'].astype('string').str.strip().str.lstrip('0')

    # Tentukan nilai
    # 1) Coba b42k4 (bulanan)
    if 'b42k4' in kp42.columns:
        val_m = pd.to_numeric(kp42['b42k4'], errors='coerce').fillna(0.0)
    else:
        val_m = pd.Series(0.0, index=kp42.index)

    # 2) Jika b42k4 nol/NA tapi b42k5 ada → pakai b42k5/12
    if 'b42k5' in kp42.columns:
        val_y = pd.to_numeric(kp42['b42k5'], errors='coerce').fillna(0.0)
        # Gunakan tahunan/12 jika bulanan = 0 dan tahunan > 0
        use_annual = (val_m == 0) & (val_y > 0)
        val_m = np.where(use_annual, val_y / 12.0, val_m)

    # 3) Koreksi ANNUAL_CODES: kode ini selalu dilaporkan per tahun
    is_annual = kp42['kode'].isin(ANNUAL_CODES)
    # Ambil nilai tahunan jika b42k5 ada
    if 'b42k5' in kp42.columns:
        val_y_corr = pd.to_numeric(kp42['b42k5'], errors='coerce').fillna(0.0)
        val_m = np.where(is_annual & (val_y_corr > 0), val_y_corr / 12.0, val_m)

    result = pd.DataFrame({
        'renum': kp42['renum'].astype('string').str.strip(),
        'kode':  kp42['kode'],
        'valm':  np.asarray(val_m, dtype='float64'),
    })
    return result


# ─── Loader KP43 ─────────────────────────────────────────────────────────────

def _load_kp43(files: List[str], verbose: bool = False) -> pd.DataFrame:
    """
    Baca file KP43 (totals bulanan resmi BPS per RT).

    Kolom yang dicari (case-insensitive, flexible naming):
      FOOD    → total pangan sebulan
      NONFOOD → total non-pangan sebulan
      EXPEND  → total pengeluaran sebulan

    Returns
    -------
    pd.DataFrame  columns: [renum, TotalFoodExp_month_kp43,
                                    TotalNonFoodExp_month_kp43,
                                    TotalExp_month_kp43]
    """
    if not files:
        return pd.DataFrame(columns=['renum', 'TotalFoodExp_month_kp43',
                                     'TotalNonFoodExp_month_kp43',
                                     'TotalExp_month_kp43'])

    FOOD_CANDS    = ['food', 'makanan', 'total_makanan', 'foodexp']
    NONFOOD_CANDS = ['nonfood', 'non_makanan', 'total_nonmakanan', 'nonfoodexp']
    EXPEND_CANDS  = ['expend', 'expand', 'totalexp', 'total',
                     'pengeluaran', 'total_pengeluaran']

    dfs = []
    for p in files:
        df = read_bps_csv(p, verbose=verbose)

        def _pick(cands):
            for c in cands:
                if c in df.columns:
                    return pd.to_numeric(df[c], errors='coerce')
            return pd.Series(np.nan, index=df.index)

        row = pd.DataFrame({
            'renum':                     df['renum'].astype('string').str.strip(),
            'TotalFoodExp_month_kp43':   _pick(FOOD_CANDS),
            'TotalNonFoodExp_month_kp43':_pick(NONFOOD_CANDS),
            'TotalExp_month_kp43':       _pick(EXPEND_CANDS),
        })
        dfs.append(row)

    if not dfs:
        return pd.DataFrame(columns=['renum','TotalFoodExp_month_kp43',
                                     'TotalNonFoodExp_month_kp43','TotalExp_month_kp43'])

    res = pd.concat(dfs, ignore_index=True)
    # Jika RT muncul di lebih dari satu file → ambil max (identik = sama)
    return res.groupby('renum', as_index=False).max(numeric_only=True)


# ─── Fungsi utama ─────────────────────────────────────────────────────────────

def build_nonfood_expenditure(
    kp42_files: List[str],
    kp43_files: Optional[List[str]] = None,
    verbose: bool = True,
) -> pd.DataFrame:
    """
    Bangun indikator pengeluaran non-pangan bulanan dari KP42 (+KP43 jika ada).

    Hierarki sumber total:
      1. KP43 (NONFOOD, FOOD, EXPEND) → angka resmi BPS, prioritas utama
      2. Agregasi bottom-up dari KP42 → fallback jika KP43 tidak ada/NA

    Parameters
    ----------
    kp42_files : list[str]
        File KP42 item-level.
    kp43_files : list[str] | None
        File KP43 totals (opsional tapi sangat dianjurkan).
    verbose : bool

    Returns
    -------
    pd.DataFrame
        Satu baris per RT. Kolom: renum + semua indikator non-pangan.
    """
    if not kp42_files:
        raise ValueError("kp42_files kosong.")

    if verbose:
        print(f"  [nonfood_exp] Memuat {len(kp42_files)} file KP42...")
    nonfood = _load_kp42(kp42_files, verbose=verbose)

    if verbose:
        print(f"  [nonfood_exp] {len(nonfood):,} baris, "
              f"{nonfood['renum'].nunique():,} RT unik")

    # ── Total non-pangan dari KP42 (bottom-up) ──
    total_kp42 = (nonfood.groupby('renum', as_index=False)['valm']
                         .sum()
                         .rename(columns={'valm': 'TotalNonFoodExp_month_from_items'}))

    # ── Breakdown tematik ──
    result = total_kp42.copy()
    for codes, col in THEMATIC_MAP:
        mask  = nonfood['kode'].isin(codes)
        tema  = (nonfood.loc[mask]
                        .groupby('renum', as_index=False)['valm']
                        .sum()
                        .rename(columns={'valm': col}))
        if tema.empty:
            tema = total_kp42[['renum']].assign(**{col: 0.0})
        result = result.merge(tema, on='renum', how='left')

    # ── KP43 totals ──
    if kp43_files:
        if verbose:
            print(f"  [nonfood_exp] Memuat {len(kp43_files)} file KP43...")
        kp43 = _load_kp43(kp43_files, verbose=verbose)
        result = result.merge(kp43, on='renum', how='left')
    else:
        result['TotalFoodExp_month_kp43']    = np.nan
        result['TotalNonFoodExp_month_kp43'] = np.nan
        result['TotalExp_month_kp43']        = np.nan

    result = result.fillna(0.0)

    if verbose:
        print(f"  [nonfood_exp] ✓ {len(result):,} RT, {result.shape[1]} kolom")
    return result
