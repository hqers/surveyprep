"""
surveyprep.adapters.ehcvm_mli_2021
==========================================
Adapter EHCVM2 MLI (2021/22).

STATUS: Placeholder — tunggu data/codebook aktual.
        Override value_labels atau runner jika ada perbedaan
        kode variabel antar negara setelah codebook tersedia.
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

CONFIG       = make_ehcvm_config('mli', '2021')
VALUE_LABELS = copy.deepcopy(EHCVM_BASE_VALUE_LABELS)
RUNNER_HH    = list(EHCVM_BASE_RUNNER_HH)
RUNNER_IND   = list(EHCVM_BASE_RUNNER_IND)
EMPLOYMENT   = dict(EHCVM_BASE_EMPLOYMENT)
FOOD_COL_MAP = dict(EHCVM_FOOD_COL_MAP)
