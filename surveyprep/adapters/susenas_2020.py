"""
surveyprep.adapters.susenas_2020
=================================
Adapter Susenas 2020 Maret (KOR).
Sumber: metadata resmi BPS — Master Variabel KOR (525 var) + KP.

Tidak ada override dari base — 2020 adalah tahun basis.
"""
import copy
from .base import (
    make_config,
    BASE_VALUE_LABELS,
    BASE_KLP,
    BASE_ALL14, BASE_NO_TOB, BASE_NO_TOB_PREP,
    BASE_PREPARED_RANGE, BASE_PROC_CODES,
    BASE_FOOD_GROUP_HEADERS,
    BASE_RUNNER_RT, BASE_RUNNER_ART,
    BASE_EMPLOYMENT,
)

CONFIG       = make_config('20')
VALUE_LABELS = copy.deepcopy(BASE_VALUE_LABELS)
VALUE_LABELS['r615'] = VALUE_LABELS['r615_ijazah']
VALUE_LABELS['r706'] = VALUE_LABELS['r706_status']

KLP               = copy.deepcopy(BASE_KLP)
ALL14             = set(BASE_ALL14)
NO_TOB            = set(BASE_NO_TOB)
NO_TOB_PREP       = set(BASE_NO_TOB_PREP)
PREPARED_RANGE    = BASE_PREPARED_RANGE
PROC_CODES        = set(BASE_PROC_CODES)
FOOD_GROUP_HEADERS = dict(BASE_FOOD_GROUP_HEADERS)

RUNNER_RT  = list(BASE_RUNNER_RT)
RUNNER_ART = list(BASE_RUNNER_ART)
EMPLOYMENT = dict(BASE_EMPLOYMENT)
