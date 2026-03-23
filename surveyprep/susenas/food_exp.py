"""
surveyprep.susenas.food_exp
===========================
Modul KP41 (Food-Expenditure): konsumsi pangan mingguan → bulanan,
indikator kelompok pangan, Dietary Diversity Score.

Sumber data: Blok41_gab*.csv  (bisa multi-file, satu per provinsi)

Struktur KP41 (per baris = satu komoditas per RT)
--------------------------------------------------
  renum   → ID rumah tangga (join key)
  KODE    → No urut rincian komoditas (1–188)
  KLP     → Kode subkelompok pangan (1, 8, 16, 52, 62, dst.)
  COICOP  → Kode COICOP internasional (opsional)
  b41k5   → Banyaknya konsumsi seminggu (dari pembelian)
  b41k6   → Nilai pengeluaran seminggu (dari pembelian)
  b41k7   → Banyaknya konsumsi seminggu (produksi sendiri/pemberian)
  b41k8   → Nilai pengeluaran seminggu (produksi sendiri/pemberian)
  b41k9   → Total banyaknya konsumsi seminggu
  b41k10  → Total nilai pengeluaran seminggu  ← KOLOM UTAMA
  KALORI  → Konsumsi kalori seminggu per RT
  PROTEIN → Konsumsi protein seminggu per RT

Konversi waktu
--------------
Semua nilai mingguan dikalikan W2M = 30/7 ≈ 4.286
untuk mendapatkan estimasi bulanan yang konsisten dengan KP42/KP43.

Kelompok pangan (KLP) yang digunakan
--------------------------------------
KLP 1   = Padi-padian (Beras, Jagung, Tepung terigu)
KLP 8   = Umbi-umbian (Singkong, Ubi, Kentang)
KLP 16  = Ikan (segar dan olahan)
KLP 52  = Daging (sapi, ayam, kambing)
KLP 62  = Telur dan susu
KLP 72  = Sayur-sayuran
KLP 98  = Kacang-kacangan (termasuk Tahu, Tempe)
KLP 106 = Buah-buahan
KLP 120 = Minyak dan kelapa
KLP 125 = Bahan minuman (Gula, Teh, Kopi)
KLP 133 = Bumbu-bumbuan
KLP 146 = Bahan makanan lainnya (Mie instan, Kerupuk)
KLP 151 = Makanan dan minuman jadi (siap saji)
KLP 183 = Rokok dan tembakau

DDS (Dietary Diversity Score)
------------------------------
DDS14         : 14 kelompok (semua di atas)
DDS13_noTob   : 13 kelompok (tanpa tembakau/183)
DDS12_noTobPrep: 12 kelompok (tanpa tembakau dan makanan jadi/151)
Nilai ternormalisasi: DDS14_norm = DDS14 / 14, dst.

Indikator yang dihasilkan (level RT, per bulan)
------------------------------------------------
  TotalFoodExp_month    → total pengeluaran pangan sebulan
  Staple_month          → padi-padian + umbi-umbian
  ProteinASF_month      → ikan + daging + telur & susu (protein hewani)
  PlantProt_month       → kacang-kacangan (protein nabati)
  FV_month              → sayur + buah
  Processed_month       → makanan olahan kemasan (kode item: 167,168,177,178,180,181)
  Prepared_month        → makanan/minuman jadi (KLP 151 atau kode 151–182)
  Tobacco_month         → rokok dan tembakau (KLP 183)
  DDS14/13/12           → dietary diversity score (raw dan normalized)
  Kalori_month          → total kalori sebulan (opsional jika kolom ada)
  Protein_month         → total protein sebulan (opsional)
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import List, Optional
from pathlib import Path

from ..core.reader import read_bps_csv_multi


# ─── Konstanta ───────────────────────────────────────────────────────────────

W2M: float = 30 / 7   # konversi mingguan → bulanan

# 14 kelompok pangan untuk DDS (menggunakan KLP)
ALL14   = {'1', '8', '16', '52', '62', '72', '98', '106',
           '120', '125', '133', '146', '151', '183'}
NO_TOB  = ALL14 - {'183'}
NO_TOB_PREP = ALL14 - {'183', '151'}

# Kode item yang termasuk makanan olahan kemasan (dari KLP 151)
PROC_CODES = {'167', '168', '177', '178', '180', '181'}

# Kode item makanan jadi (rentang 151–182 termasuk semua jenis)
PREPARED_RANGE = (151, 182)


# ─── Loader ──────────────────────────────────────────────────────────────────

def _load_kp41(files: List[str], verbose: bool = False) -> pd.DataFrame:
    """
    Baca dan gabungkan file-file KP41 menjadi satu DataFrame long-format.

    Validasi kolom wajib: renum, b41k10, dan salah satu dari kode/klp.
    Hasil: kolom [renum, kode, kelompok, valw, valm]
    """
    kp41 = read_bps_csv_multi(files, verbose=verbose)

    # Validasi kolom wajib
    for c in ('renum', 'b41k10'):
        if c not in kp41.columns:
            raise KeyError(f"KP41: kolom wajib '{c}' tidak ditemukan.")
    if 'kode' not in kp41.columns and 'klp' not in kp41.columns:
        raise KeyError("KP41: harus punya kolom 'kode' atau 'klp'.")

    # Nilai mingguan
    kp41['valw'] = pd.to_numeric(kp41['b41k10'], errors='coerce').fillna(0.0)

    # Normalisasi kode item
    if 'kode' in kp41.columns:
        kp41['kode'] = kp41['kode'].astype('string').str.strip().str.lstrip('0')
    else:
        kp41['kode'] = pd.NA

    # Normalisasi kelompok (klp atau kelompok)
    if 'klp' in kp41.columns:
        kp41['kelompok'] = kp41['klp'].astype('string').str.strip().str.lstrip('0')
    elif 'kelompok' in kp41.columns:
        kp41['kelompok'] = kp41['kelompok'].astype('string').str.strip().str.lstrip('0')
    else:
        kp41['kelompok'] = pd.NA

    # Konversi mingguan → bulanan
    kp41['valm'] = kp41['valw'] * W2M

    return kp41[['renum', 'kode', 'kelompok', 'valw', 'valm']].copy()


# ─── Agregasi per kelompok pangan ────────────────────────────────────────────

def _sum_by_kelompok(df: pd.DataFrame, groups: set, outname: str) -> pd.DataFrame:
    """Agregasi bulanan per RT untuk kelompok KLP tertentu."""
    mask = df['kelompok'].isin(groups)
    result = (df.loc[mask]
                .groupby('renum', as_index=False)['valm']
                .sum()
                .rename(columns={'valm': outname}))
    if result.empty:
        result = df[['renum']].drop_duplicates().assign(**{outname: 0.0})
    return result


def _sum_by_kode(df: pd.DataFrame, codes: set, outname: str) -> pd.DataFrame:
    """Agregasi bulanan per RT untuk kode komoditas tertentu."""
    mask = df['kode'].isin(codes)
    result = (df.loc[mask]
                .groupby('renum', as_index=False)['valm']
                .sum()
                .rename(columns={'valm': outname}))
    if result.empty:
        result = df[['renum']].drop_duplicates().assign(**{outname: 0.0})
    return result


# ─── Fungsi utama ─────────────────────────────────────────────────────────────

def build_food_expenditure(
    kp41_files: List[str],
    verbose: bool = True,
    include_nutrition: bool = True,
) -> pd.DataFrame:
    """
    Bangun indikator konsumsi pangan bulanan dari file KP41.

    Parameters
    ----------
    kp41_files : list[str]
        Daftar path file KP41 (glob pattern sudah di-resolve sebelumnya).
        Contoh: sorted(glob.glob('data/Blok41_gab*.csv'))
    verbose : bool
    include_nutrition : bool
        Jika True, sertakan Kalori_month dan Protein_month jika kolom ada.

    Returns
    -------
    pd.DataFrame
        Satu baris per RT. Kolom: renum + semua indikator pangan.
    """
    if not kp41_files:
        raise ValueError("kp41_files kosong. Berikan setidaknya satu file KP41.")

    if verbose:
        print(f"  [food_exp] Memuat {len(kp41_files)} file KP41...")

    kp41 = _load_kp41(kp41_files, verbose=verbose)

    if verbose:
        print(f"  [food_exp] {len(kp41):,} baris, {kp41['renum'].nunique():,} RT unik")

    # ── Total pangan per bulan ──────────────────────────────────────────
    food_m = (kp41.groupby('renum', as_index=False)['valm']
                  .sum()
                  .rename(columns={'valm': 'TotalFoodExp_month'}))

    # ── Indikator kelompok pangan ───────────────────────────────────────
    # Padi-padian (KLP 1) + Umbi-umbian (KLP 8)
    stap  = _sum_by_kelompok(kp41, {'1', '8'},         'Staple_month')
    # Protein hewani: Ikan (16) + Daging (52) + Telur & Susu (62)
    asf   = _sum_by_kelompok(kp41, {'16', '52', '62'}, 'ProteinASF_month')
    # Protein nabati: Kacang-kacangan (98)
    plant = _sum_by_kelompok(kp41, {'98'},              'PlantProt_month')
    # Sayur (72) + Buah (106)
    fv    = _sum_by_kelompok(kp41, {'72', '106'},       'FV_month')
    # Tembakau (183)
    tob   = _sum_by_kelompok(kp41, {'183'},             'Tobacco_month')

    # Makanan jadi/siap saji: KLP 151 atau kode dalam range 151-182
    kode_num  = pd.to_numeric(kp41['kode'], errors='coerce')
    klp_str   = kp41['kelompok'].astype('string')
    prep_mask = (kode_num.between(*PREPARED_RANGE) | klp_str.eq('151')).fillna(False)
    prep = (kp41.loc[prep_mask]
                .groupby('renum', as_index=False)['valm']
                .sum()
                .rename(columns={'valm': 'Prepared_month'}))
    if prep.empty:
        prep = food_m[['renum']].assign(Prepared_month=0.0)

    # Olahan kemasan (subset dari makanan jadi)
    proc = _sum_by_kode(kp41, PROC_CODES, 'Processed_month')

    # ── DDS (Dietary Diversity Score) ──────────────────────────────────
    g = (kp41.dropna(subset=['kelompok'])
             .groupby(['renum', 'kelompok'], as_index=False)['valw']
             .sum())
    wide = (g.pivot(index='renum', columns='kelompok', values='valw')
              .fillna(0.0))

    # Pastikan semua 14 kolom ada
    for k in ALL14:
        if k not in wide.columns:
            wide[k] = 0.0
    wide = wide[sorted(ALL14, key=lambda x: int(x))]

    wide['DDS14']                = (wide[list(ALL14)]        > 0).sum(axis=1)
    wide['DDS13_noTob']          = (wide[list(NO_TOB)]       > 0).sum(axis=1)
    wide['DDS12_noTobPrep']      = (wide[list(NO_TOB_PREP)]  > 0).sum(axis=1)
    wide['DDS14_norm']           = wide['DDS14']          / 14
    wide['DDS13_noTob_norm']     = wide['DDS13_noTob']    / 13
    wide['DDS12_noTobPrep_norm'] = wide['DDS12_noTobPrep']/ 12
    dds = wide[['DDS14','DDS13_noTob','DDS12_noTobPrep',
                'DDS14_norm','DDS13_noTob_norm','DDS12_noTobPrep_norm']].reset_index()

    # ── Nutrisi (opsional) ──────────────────────────────────────────────
    nutr_dfs = []
    if include_nutrition:
        for col_raw, col_out in [('kalori','Kalori_month'), ('protein','Protein_month')]:
            if col_raw in kp41.columns:
                val_w = pd.to_numeric(kp41[col_raw], errors='coerce').fillna(0.0)
                tmp = (kp41.assign(_val=val_w * W2M)
                           .groupby('renum', as_index=False)['_val']
                           .sum()
                           .rename(columns={'_val': col_out}))
                nutr_dfs.append(tmp)

    # ── Gabung semua ────────────────────────────────────────────────────
    result = food_m.copy()
    for df_part in [stap, asf, plant, fv, proc, prep, tob]:
        result = result.merge(df_part, on='renum', how='left')
    result = result.merge(dds, on='renum', how='left')
    for df_nutr in nutr_dfs:
        result = result.merge(df_nutr, on='renum', how='left')

    result = result.fillna(0.0)

    if verbose:
        print(f"  [food_exp] ✓ {len(result):,} RT, {result.shape[1]} kolom")
    return result
