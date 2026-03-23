"""
surveyprep.adapters
===================
Adapter per survei. Mendukung dua survey_family:

SUSENAS (Indonesia BPS) — format CSV, join key = renum/urut
  susenas_2017.py  ✅  susenas_2021.py  ✅  susenas_2025.py  ✅
  susenas_2018.py  ✅  susenas_2022.py  ✅
  susenas_2019.py  ✅  susenas_2023.py  ✅
  susenas_2020.py  ✅  susenas_2024.py  ✅

EHCVM (UEMOA / World Bank) — format Stata .dta, join key = grappe+menage
  ehcvm_ben_2021.py  ✅ Verified (BID Benin 2023)
  ehcvm_bfa_2021.py  ⏳  ehcvm_mli_2021.py  ⏳
  ehcvm_civ_2021.py  ⏳  ehcvm_ner_2021.py  ⏳
  ehcvm_gnb_2021.py  ⏳  ehcvm_sen_2021.py  ⏳
  ehcvm_tgo_2021.py  ⏳

LSMS (World Bank) — placeholder, belum dibuat
"""
