"""
surveyprep.susenas.individual_2024
===================================
Versi build_individual() yang disesuaikan untuk Susenas 2024.

Perbedaan utama dari individual.py (2020):
  1. r615 ≠ ijazah — ijazah ada di r613/r614
  2. r703 dipecah → r703_a (bekerja), r703_b (sekolah), dst.
  3. r704 = kegiatan utama (bukan flag tidak bekerja)
  4. r705 = flag sementara tidak bekerja (bukan lapangan usaha)
  5. r706 = lapangan usaha 26 kode (bukan status pekerjaan)
  6. r707 = status pekerjaan (bukan jam kerja)
  7. r701/r802: 1=Ya, 5=Tidak (bukan 1=Ya, 2=Tidak)
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Optional

from ..core.reader import read_bps_csv
from ..core.runner import execute_runner
from .individual   import _detect_krt   # reuse KRT detection logic
from ..adapters.susenas_2024 import (
    RUNNER_ART as RUNNER_ART_2024,
    EDUCATION_COL_2024,
    WORKING_FLAG_COL_2024,
    ACTIVITY_COL_2024,
    TEMP_NOT_WORK_2024,
)

# Recode pendidikan 2024 (menggunakan r613: jenjang pendidikan)
# r613: 1=Tidak/belum sekolah, 2=SD, 3=SMP, 4=SMA, 5=PT (Perguruan Tinggi)
# Catatan: lebih kasar dari 2020 (22 kode → 5 kode)
_EDU_2024 = {
    '1': 'Tidak/Belum Sekolah',
    '2': 'SD',
    '3': 'SMP',
    '4': 'SMA',
    '5': 'Perguruan Tinggi',
}


def build_individual_2024(
    art: pd.DataFrame,
    soc: Optional[pd.DataFrame] = None,
    verbose: bool = True,
    extra_runner: Optional[list] = None,
) -> pd.DataFrame:
    """
    Build sosio-demografi level RT dari data ART Susenas 2024.

    Menangani pergeseran kolom r7xx secara otomatis.

    Parameters
    ----------
    art : pd.DataFrame
        Data ART hasil load_art_merged().
    soc : pd.DataFrame | None
        DataFrame level RT dari build_hh_record (dengan RUNNER_RT_2024).
    verbose : bool
    extra_runner : list | None

    Returns
    -------
    pd.DataFrame — level RT dengan kolom sosio-demografi
    """
    art = art.copy()
    art['renum'] = art['renum'].astype('string').str.strip()

    if soc is None:
        hhsize = (art.groupby('renum', as_index=False)
                     .size()
                     .rename(columns={'size': 'HouseholdSize'}))
        hhsize['HouseholdSize'] = hhsize['HouseholdSize'].astype('Int64')
        soc = hhsize.copy()
    else:
        soc = soc.copy()
        if 'HHID' in soc.columns and 'renum' not in soc.columns:
            soc = soc.rename(columns={'HHID': 'renum'})

    # ── Deteksi KRT ──
    if 'r403' not in art.columns:
        print("  [individual_2024] WARN: r403 tidak ada")
        is_head = pd.Series(False, index=art.index)
    else:
        is_head = _detect_krt(art, 'r403')
    if verbose:
        print(f"  [individual_2024] KRT: {is_head.sum():,} baris "
              f"({art.loc[is_head,'renum'].nunique():,} RT)")

    # ── Pendidikan KRT (r613 di 2024, bukan r615) ──
    edu_col = EDUCATION_COL_2024  # 'r613'
    if edu_col in art.columns:
        head_edu = (art.loc[is_head, ['renum', edu_col]]
                       .assign(renum=lambda d: d['renum'].astype('string').str.strip())
                       .drop_duplicates('renum'))
        head_edu['EducationHead'] = (
            head_edu[edu_col]
            .apply(lambda v: _EDU_2024.get(str(int(float(str(v).replace(',','.')))) 
                                           if pd.notna(v) else '', pd.NA))
            .astype('string')
        )
        soc = (soc.drop(columns=['EducationHead'], errors='ignore')
                  .merge(head_edu[['renum','EducationHead']], on='renum', how='left'))
    else:
        print(f"  [individual_2024] WARN: '{edu_col}' tidak ada → EducationHead = NA")
        soc['EducationHead'] = pd.NA

    # ── Lapangan usaha KRT (r706 di 2024, bukan r705) ──
    if 'r706' in art.columns:
        head_occ = (art.loc[is_head, ['renum', 'r706']]
                       .assign(renum=lambda d: d['renum'].astype('string').str.strip())
                       .drop_duplicates('renum'))
        head_occ['OccupationHeadSector'] = (
            head_occ['r706']
            .apply(lambda v: str(int(float(str(v).replace(',','.')))) 
                   if pd.notna(v) else pd.NA)
            .astype('string')
        )
        soc = (soc.drop(columns=['OccupationHeadSector'], errors='ignore')
                  .merge(head_occ[['renum','OccupationHeadSector']], on='renum', how='left'))
    else:
        soc['OccupationHeadSector'] = pd.NA

    # ── Jenis kelamin KRT (r405 — sama di 2024) ──
    if 'r405' in art.columns:
        head_sex = (art.loc[is_head, ['renum','r405']]
                       .assign(renum=lambda d: d['renum'].astype('string').str.strip())
                       .drop_duplicates('renum'))
        sex_num = pd.to_numeric(head_sex['r405'], errors='coerce').astype('Int64')
        head_sex['SexHead'] = sex_num.map({1:'Laki-laki', 2:'Perempuan'}).astype('string')
        soc = (soc.drop(columns=['SexHead'], errors='ignore')
                  .merge(head_sex[['renum','SexHead']], on='renum', how='left'))
    else:
        soc['SexHead'] = pd.NA

    # ── Umur KRT (r407 — sama) ──
    if 'r407' in art.columns:
        head_age = (art.loc[is_head, ['renum','r407']]
                       .assign(renum=lambda d: d['renum'].astype('string').str.strip())
                       .drop_duplicates('renum'))
        head_age['AgeHead'] = pd.to_numeric(
            head_age['r407'], errors='coerce').round().astype('Int64')
        soc = (soc.drop(columns=['AgeHead'], errors='ignore')
                  .merge(head_age[['renum','AgeHead']], on='renum', how='left'))
    else:
        soc['AgeHead'] = pd.Series(pd.NA, index=soc.index, dtype='Int64')

    # ── N_Working (2024: r703_a = bekerja, ATAU r704 == 1) ──
    work = pd.Series(False, index=art.index)
    # Metode 1: r703_a (checklist, 1=bekerja)
    if WORKING_FLAG_COL_2024 in art.columns:
        work = work | (art[WORKING_FLAG_COL_2024].astype(str).str.strip().isin(['1','01']))
    # Metode 2: r704 == 1 (kegiatan utama = bekerja)
    elif ACTIVITY_COL_2024 in art.columns:
        work = work | (pd.to_numeric(art[ACTIVITY_COL_2024], errors='coerce') == 1)
    # Fallback: r705 == 1 (sementara tidak bekerja, tapi punya pekerjaan)
    if TEMP_NOT_WORK_2024 in art.columns:
        tmp_not_work = pd.to_numeric(art[TEMP_NOT_WORK_2024], errors='coerce') == 1
        work = work | tmp_not_work

    work_cnt = (art.assign(_w=work)
                   .groupby('renum', as_index=False)['_w']
                   .sum()
                   .rename(columns={'_w': 'N_Working'}))
    soc = (soc.drop(columns=['N_Working','WorkerShare'], errors='ignore')
              .merge(work_cnt, on='renum', how='left'))
    soc['N_Working'] = soc['N_Working'].fillna(0).astype('Int64')
    _den = pd.to_numeric(soc.get('HouseholdSize', pd.Series(dtype=float)),
                         errors='coerce').astype(float)
    _num = pd.to_numeric(soc['N_Working'], errors='coerce').astype(float)
    soc['WorkerShare'] = np.where(_den > 0, _num / _den, 0.0)

    # ── DependencyRatio (sama dengan 2020) ──
    if 'r407' in art.columns:
        age_df = art[['renum','r407']].copy()
        age_df['age'] = pd.to_numeric(age_df['r407'], errors='coerce')
        grp = (age_df.assign(
                    child=lambda d: d['age'].between(0,14),
                    adult=lambda d: d['age'].between(15,64),
                    elder=lambda d: d['age'] >= 65)
                .groupby('renum')
                .agg(N_child=('child','sum'), N_adult=('adult','sum'), N_elder=('elder','sum'))
                .reset_index())
        soc = (soc.drop(columns=['N_child','N_adult','N_elder','DependencyRatio'], errors='ignore')
                  .merge(grp, on='renum', how='left')
                  .fillna({'N_child':0,'N_adult':0,'N_elder':0}))
        _d = soc['N_adult'].astype(float)
        _n = (soc['N_child'] + soc['N_elder']).astype(float)
        soc['DependencyRatio'] = np.where(_d > 0, _n / _d, 0.0)
    else:
        soc['DependencyRatio'] = np.nan

    # ── RUNNER ART 2024 (StatusPekerjaan r707, HP r802, tabungan r701) ──
    runner = RUNNER_ART_2024 + (extra_runner or [])
    if verbose:
        print(f"  [individual_2024] Menjalankan {len(runner)} RUNNER items...")
    stub_rt = art[['renum']].drop_duplicates().copy()
    soc = execute_runner(soc, stub_rt, art, runner_list=runner, verbose=verbose)

    # ── Rename → HHID ──
    if 'renum' in soc.columns:
        soc = soc.rename(columns={'renum': 'HHID'})

    if verbose:
        print(f"  [individual_2024] ✓ {len(soc):,} RT, {soc.shape[1]} kolom")
    return soc
