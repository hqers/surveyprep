"""
surveyprep.adapters.ehcvm_ben_2021
===================================
Adapter EHCVM2 Benin (Enquête Harmonisée sur les Conditions de Vie
des Ménages, édition 2021/22).

Sumber: Basic Information Document EHCVM2 Benin (Septembre 2023)
        UEMOA Commission / World Bank / INStaD Benin

STATUS: ✅ VERIFIED struktur dari BID dokumen resmi.
        ⚠ Value labels perlu konfirmasi dari codebook data aktual
          (BID tidak memuat kode nilai lengkap untuk semua variabel).

Perbedaan kunci dari adapter Susenas
--------------------------------------
survey_family : 'ehcvm'  (vs 'susenas')
Format file   : Stata .dta  (vs CSV)
Join key      : grappe + menage  (vs renum/urut)
Struktur file : satu file per section questionnaire
                (s00, s01, s07b, s11, dll.)
Unit konsumsi : perlu NSU conversion file sebelum analisis
                (ehcvm_NSU_ben_2021.dta)
Panel         : EHCVM adalah cluster panel (bukan HH panel penuh)
                variabel 'PanelHH' menandai RT yang valid untuk merge
                dengan EHCVM1

Catatan spesifik Benin EHCVM2
-------------------------------
- Pengumpulan data: Wave 1 = Nov–Des 2021, Wave 2 = Apr–Jul 2022
- Sampel: 670 cluster × 12 RT = 8.040 RT target (actual: 8.032 RT)
- Total individu: 42.391
- CAPI dengan Survey Solutions (SuSo)
- 2 cluster tidak dapat dienumerasi (serangan teroris + demolisi urbanisasi)
"""
import copy
from .base import (
    make_ehcvm_config,
    EHCVM_BASE_VALUE_LABELS,
    EHCVM_BASE_RUNNER_HH,
    EHCVM_BASE_RUNNER_IND,
    EHCVM_BASE_EMPLOYMENT,
    EHCVM_FOOD_COL_MAP,
)

# ── CONFIG ────────────────────────────────────────────────────────────────────
CONFIG = make_ehcvm_config('ben', '2021')

# ── Value labels: Benin-specific overrides ────────────────────────────────────
# Sebagian besar sama dengan EHCVM_BASE_VALUE_LABELS.
# Override hanya jika ada perbedaan dibanding default UEMOA.
VALUE_LABELS = copy.deepcopy(EHCVM_BASE_VALUE_LABELS)

# Benin: tidak ada override diketahui dari BID — semua sama dengan base.
# Saat codebook aktual tersedia, override di sini.
# Contoh jika ada perbedaan kode wilayah:
# VALUE_LABELS['region'] = {1: 'Alibori', 2: 'Atacora', ...}

# ── RUNNER HH: sama dengan base ───────────────────────────────────────────────
RUNNER_HH = list(EHCVM_BASE_RUNNER_HH)

# ── RUNNER IND: sama dengan base ──────────────────────────────────────────────
RUNNER_IND = list(EHCVM_BASE_RUNNER_IND)

# ── Kolom ketenagakerjaan ─────────────────────────────────────────────────────
EMPLOYMENT = dict(EHCVM_BASE_EMPLOYMENT)

# ── Peta kolom konsumsi pangan ────────────────────────────────────────────────
FOOD_COL_MAP = dict(EHCVM_FOOD_COL_MAP)

# ── Metadata survei (untuk dokumentasi & profiling) ───────────────────────────
SURVEY_META = {
    'survey_family'  : 'ehcvm',
    'survey_name'    : 'EHCVM2 — Enquête Harmonisée sur les Conditions de Vie des Ménages',
    'edition'        : 2,
    'country'        : 'Benin',
    'country_code'   : 'ben',
    'year'           : '2021',
    'wave_1_period'  : 'November–December 2021',
    'wave_2_period'  : 'April–July 2022',
    'n_clusters'     : 670,
    'n_hh_target'    : 8040,
    'n_hh_actual'    : 8032,
    'n_individuals'  : 42391,
    'capi_software'  : 'Survey Solutions (SuSo)',
    'funding'        : 'World Bank ($42M for Benin)',
    'implementing_org': 'INStaD (Institut National de la Statistique et de la Démographie)',
    'panel_variable' : 'PanelHH',  # kolom untuk filter RT panel dari EHCVM1
    'sections'       : list(range(0, 21)),  # s00–s20
    'language'       : 'French/local',
    'currency'       : 'FCFA',
    'sampling_design': 'Two-stage stratified, PPS at stage 1, equal prob at stage 2',
}
