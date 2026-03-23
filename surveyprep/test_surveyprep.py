"""
test_surveyprep.py
==================
Test suite untuk memverifikasi instalasi surveyprep v1.9.0.
Tidak membutuhkan data aktual — semua test menggunakan data sintetis.

Cara jalankan:
    python test_surveyprep.py           # semua test
    python test_surveyprep.py -v        # verbose (tampilkan detail tiap test)
    python test_surveyprep.py adapter   # hanya test adapter
    python test_surveyprep.py ehcvm     # hanya test EHCVM
    python test_surveyprep.py susenas   # hanya test Susenas
    python test_surveyprep.py data      # hanya test dengan data sintetis
"""
import sys
import traceback
import io
import numpy as np
import pandas as pd

VERBOSE = '-v' in sys.argv
FILTER  = [a for a in sys.argv[1:] if not a.startswith('-')]

PASS = "✅ PASS"
FAIL = "❌ FAIL"
SKIP = "⏭  SKIP"

results = []

def run(name, category, fn):
    if FILTER and not any(f in category or f in name.lower() for f in FILTER):
        results.append((SKIP, name, ''))
        return
    try:
        fn()
        results.append((PASS, name, ''))
        if VERBOSE: print(f"  {PASS} {name}")
    except Exception as e:
        msg = str(e)
        results.append((FAIL, name, msg))
        if VERBOSE:
            print(f"  {FAIL} {name}")
            print(f"       {msg}")
            if '--tb' in sys.argv:
                traceback.print_exc()

# ══════════════════════════════════════════════════════════════════════════════
# 1. IMPORT TEST — apakah semua modul bisa diimport?
# ══════════════════════════════════════════════════════════════════════════════
print("\n[1] Import tests")

def test_import_base():
    from surveyprep.adapters.base import (
        BASE_CONFIG, BASE_VALUE_LABELS, BASE_KLP,
        BASE_RUNNER_RT, BASE_RUNNER_ART, BASE_EMPLOYMENT,
        make_config,
        # EHCVM additions
        EHCVM_BASE_CONFIG, EHCVM_BASE_VALUE_LABELS,
        EHCVM_BASE_RUNNER_HH, EHCVM_BASE_RUNNER_IND,
        EHCVM_BASE_EMPLOYMENT, EHCVM_FOOD_COL_MAP,
        make_ehcvm_config, EHCVM_COUNTRY_CODES,
    )
run("base.py imports (Susenas + EHCVM)", "adapter", test_import_base)

SUSENAS_YEARS = [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
for yr in SUSENAS_YEARS:
    def _test(y=yr):
        mod = __import__(f'surveyprep.adapters.susenas_{y}',
                         fromlist=['CONFIG','VALUE_LABELS','KLP','EMPLOYMENT'])
        assert 'hh_id_col' in mod.CONFIG
        assert 'r1817' in mod.VALUE_LABELS
        assert 'rokok' in mod.KLP
    run(f"susenas_{yr} importable", "susenas adapter", _test)

def test_import_ehcvm_ben():
    from surveyprep.adapters.ehcvm_ben_2021 import (
        CONFIG, VALUE_LABELS, RUNNER_HH, RUNNER_IND,
        EMPLOYMENT, FOOD_COL_MAP, SURVEY_META
    )
    assert CONFIG['survey_family'] == 'ehcvm'
    assert CONFIG['file_format'] == 'stata'
    assert CONFIG['country'] == 'ben'
    assert CONFIG['year'] == '2021'
    assert len(RUNNER_HH) >= 10
run("ehcvm_ben_2021 importable", "ehcvm adapter", test_import_ehcvm_ben)

EHCVM_COUNTRIES = ['bfa','civ','gnb','mli','ner','sen','tgo']
for cc in EHCVM_COUNTRIES:
    def _test(c=cc):
        mod = __import__(f'surveyprep.adapters.ehcvm_{c}_2021',
                         fromlist=['CONFIG'])
        assert mod.CONFIG['country'] == c
    run(f"ehcvm_{cc}_2021 importable", "ehcvm adapter", _test)

def test_import_reader_stata():
    from surveyprep.core.reader_stata import (
        read_ehcvm_dta, make_hhid, merge_ehcvm_files,
        load_ehcvm_housing, load_ehcvm_food,
        load_ehcvm_individual, load_ehcvm_nsu, load_ehcvm_weights,
    )
run("core/reader_stata.py importable", "ehcvm", test_import_reader_stata)

def test_import_individual_2024():
    from surveyprep.susenas.individual_2024 import build_individual_2024
run("susenas/individual_2024.py importable", "susenas", test_import_individual_2024)

def test_import_pipeline():
    from surveyprep.pipeline import run_susenas_pipeline
    from surveyprep.core.reader import read_bps_csv, read_bps_csv_multi
    from surveyprep.core.runner import execute_runner
    from surveyprep.core.imputer import impute_mixed, cap_outliers
    from surveyprep.core.exporter import export_dual
run("core pipeline modules importable", "adapter", test_import_pipeline)

# ══════════════════════════════════════════════════════════════════════════════
# 2. ADAPTER CONTENT TEST — nilai konfigurasi benar?
# ══════════════════════════════════════════════════════════════════════════════
print("\n[2] Adapter content tests (nilai konfigurasi)")

def test_klp_rokok_timeline():
    """KLP rokok harus mengikuti timeline: 183 (2017-2021), 192 (2022-2024), 220 (2025)"""
    import importlib
    expected = {
        2017: '183', 2018: '183', 2019: '183', 2020: '183', 2021: '183',
        2022: '192', 2023: '192', 2024: '192',
        2025: '220',
    }
    for yr, exp_klp in expected.items():
        mod = importlib.import_module(f'surveyprep.adapters.susenas_{yr}')
        actual = list(mod.KLP['rokok'])[0]
        assert actual == exp_klp, f"{yr}: KLP rokok={actual}, expect {exp_klp}"
run("KLP rokok timeline 2017-2025 benar", "susenas", test_klp_rokok_timeline)

def test_edu_col_timeline():
    """Kolom ijazah harus mengikuti timeline yang sudah diverifikasi"""
    import importlib
    expected = {
        2017: 'r615', 2018: 'r615', 2019: 'r615', 2020: 'r615', 2021: 'r615',
        2022: 'r614', 2023: 'r614',
        2024: 'r613',
        2025: 'r615',
    }
    for yr, exp_col in expected.items():
        mod = importlib.import_module(f'surveyprep.adapters.susenas_{yr}')
        actual = mod.EMPLOYMENT.get('education_col')
        assert actual == exp_col, f"{yr}: edu_col={actual}, expect {exp_col}"
run("Education column timeline 2017-2025 benar", "susenas", test_edu_col_timeline)

def test_activity_col_timeline():
    """Kolom kegiatan utama harus mengikuti timeline"""
    import importlib
    expected = {
        2017: 'r802', 2018: 'r802',
        2019: 'r702',
        2020: 'r703', 2021: 'r703', 2022: 'r703',
        2023: 'r704', 2024: 'r704', 2025: 'r704',
    }
    for yr, exp_col in expected.items():
        mod = importlib.import_module(f'surveyprep.adapters.susenas_{yr}')
        actual = mod.EMPLOYMENT.get('activity_col')
        assert actual == exp_col, f"{yr}: activity_col={actual}, expect {exp_col}"
run("Activity column timeline 2017-2025 benar", "susenas", test_activity_col_timeline)

def test_hh_id_timeline():
    """join key: renum (2017-2021,2023-2025), urut (2022)"""
    import importlib
    expected = {
        2017:'renum', 2018:'urut', 2019:'renum', 2020:'renum', 2021:'renum',
        2022:'urut', 2023:'renum', 2024:'renum', 2025:'renum',
    }
    for yr, exp in expected.items():
        mod = importlib.import_module(f'surveyprep.adapters.susenas_{yr}')
        actual = mod.CONFIG.get('hh_id_col','renum')
        assert actual == exp, f"{yr}: hh_id_col={actual}, expect {exp}"
run("hh_id_col timeline 2017-2025 benar", "susenas", test_hh_id_timeline)

def test_r1817_elpiji12_kode3():
    """Elpiji 12kg harus kode 3 di 2019-2025 (sebelumnya tidak ada di 2017-2018)"""
    import importlib
    for yr in range(2019, 2026):
        mod = importlib.import_module(f'surveyprep.adapters.susenas_{yr}')
        # cari kunci r1817 yang ada
        r1817_key = None
        for k in ['r1617','r1517','r1817']:
            if k in mod.VALUE_LABELS:
                r1817_key = k; break
        if r1817_key:
            assert mod.VALUE_LABELS[r1817_key].get(3,'') != '', \
                f"{yr}: kode 3 tidak ada di {r1817_key}"
run("r1817 Elpiji 12kg = kode 3 di 2019-2025", "susenas", test_r1817_elpiji12_kode3)

def test_ehcvm_config_files():
    """Semua nama file EHCVM harus konsisten dengan pattern s{xx}_me_{country}_{year}.dta"""
    from surveyprep.adapters.ehcvm_ben_2021 import CONFIG
    assert CONFIG['hh_housing_file'] == 's11_me_ben_2021.dta'
    assert CONFIG['food_file']       == 's07b_me_ben_2021.dta'
    assert CONFIG['hh_fies_file']    == 's08a_me_ben_2021.dta'
    assert CONFIG['nsu_file']        == 'ehcvm_NSU_ben_2021.dta'
    assert CONFIG['weights_file']    == 'ehcvm_ponderations_ben2021.dta'
    # non-food dict
    nf = CONFIG['nonfood_files']
    assert nf['nonfood_7d']  == 's09b_me_ben_2021.dta'
    assert nf['nonfood_12m'] == 's09f_me_ben_2021.dta'
run("EHCVM config file names konsisten", "ehcvm", test_ehcvm_config_files)

def test_make_ehcvm_config_multi_country():
    """make_ehcvm_config harus generate nama file yang benar per negara"""
    from surveyprep.adapters.base import make_ehcvm_config
    for cc in ['ben','bfa','civ','sen']:
        cfg = make_ehcvm_config(cc, '2021')
        assert cfg['hh_housing_file'] == f's11_me_{cc}_2021.dta'
        assert cfg['food_file']       == f's07b_me_{cc}_2021.dta'
        assert cfg['country'] == cc
        assert cfg['survey_family'] == 'ehcvm'
        assert cfg['file_format'] == 'stata'
run("make_ehcvm_config multi-country benar", "ehcvm", test_make_ehcvm_config_multi_country)

def test_make_ehcvm_config_invalid():
    """make_ehcvm_config harus raise ValueError untuk kode negara tidak valid"""
    from surveyprep.adapters.base import make_ehcvm_config
    try:
        make_ehcvm_config('idn', '2021')  # Indonesia bukan negara EHCVM
        assert False, "Harus raise ValueError"
    except ValueError:
        pass
run("make_ehcvm_config raise error untuk negara tidak valid", "ehcvm", test_make_ehcvm_config_invalid)

# ══════════════════════════════════════════════════════════════════════════════
# 3. DATA SYNTHETIC TEST — fungsi inti bekerja dengan data dummy?
# ══════════════════════════════════════════════════════════════════════════════
print("\n[3] Synthetic data tests (tidak butuh data aktual)")

def make_susenas_rt(n=100, seed=42):
    """Buat data RT sintetis ala Susenas."""
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        'renum'  : [str(i+1).zfill(6) for i in range(n)],
        'r105'   : rng.choice([1,2], n),
        'r1802'  : rng.choice([1,2,3,4,5], n),
        'r1806'  : rng.choice(range(1,9), n),
        'r1807'  : rng.choice(range(1,8), n),
        'r1808'  : rng.choice(range(1,10), n),
        'r1809a' : rng.choice(range(1,7), n),
        'r1809b' : rng.choice([1,2,3,4], n),
        'r1810a' : rng.choice(range(1,12), n),
        'r1816'  : rng.choice([1,2,3,4], n),
        'r1817'  : rng.choice(range(0,12), n),
        'r1701'  : rng.choice([1,5,8,9], n),
        'fwt'    : rng.uniform(1, 5, n),
    })

def make_susenas_ind(renum_list, n_per_hh=4, seed=99):
    """Buat data IND sintetis ala Susenas."""
    rng = np.random.default_rng(seed)
    rows = []
    for r in renum_list:
        n = rng.integers(1, n_per_hh+1)
        for i in range(n):
            rows.append({
                'renum': r,
                'r401' : i+1,
                'r403' : 1 if i==0 else rng.choice([2,3,4,5,6,7,9]),
                'r405' : rng.choice([1,2]),
                'r407' : rng.integers(5, 80),
                'r615' : rng.choice(range(1,23)),
                'r703' : rng.choice([1,2,3,4]),
                'r706' : rng.choice(range(1,7)),
                'r701' : rng.choice([1,2]),
                'r802' : rng.choice([1,2]),
            })
    return pd.DataFrame(rows)

def make_ehcvm_hh(n=50, seed=7):
    """Buat data HH sintetis ala EHCVM (s11)."""
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        'grappe'  : rng.integers(1, 20, n),
        'menage'  : rng.integers(1, 13, n),
        'milieu'  : rng.choice([1,2], n),
        's11q01'  : rng.choice(range(1,6), n),
        's11q04'  : rng.choice(range(1,7), n),
        's11q05'  : rng.choice(range(1,7), n),
        's11q06'  : rng.choice(range(1,6), n),
        's11q12'  : rng.choice(range(1,12), n),
        's11q18'  : rng.choice([1,2,3,4], n),
        's11q21'  : rng.choice(range(1,8), n),
        's11q26'  : rng.choice(range(1,7), n),
        'hhweight': rng.uniform(0.5, 5, n),
        'vague'   : rng.choice([1,2], n),
    })

def test_make_hhid():
    """make_hhid harus menghasilkan composite key yang unik-ish"""
    from surveyprep.core.reader_stata import make_hhid
    df = make_ehcvm_hh(50)
    df2 = make_hhid(df)
    assert 'hhid' in df2.columns
    assert df2['hhid'].dtype in (object, 'string', str) or str(df2['hhid'].dtype) in ('object','string')
    # Format: 4 digit grappe + _ + 2 digit menage
    sample = df2['hhid'].iloc[0]
    assert '_' in sample, f"hhid harus mengandung '_': {sample}"
    parts = sample.split('_')
    assert len(parts) == 2
    assert len(parts[0]) == 4  # grappe zero-padded ke 4 digit
    assert len(parts[1]) == 2  # menage zero-padded ke 2 digit
run("make_hhid menghasilkan composite key yang benar", "ehcvm data", test_make_hhid)

def test_imputer():
    """impute_mixed harus mengisi NaN tanpa error"""
    from surveyprep.core.imputer import impute_mixed
    rt = make_susenas_rt(200)
    # Tambah NaN
    rt.loc[::5, 'r1802'] = np.nan
    rt.loc[::7, 'r1817'] = np.nan
    result = impute_mixed(rt, force_cat=['r1802','r1816','r1817'])
    assert result['r1802'].isna().sum() == 0
    assert result['r1817'].isna().sum() == 0
run("impute_mixed mengisi NaN dengan benar", "data", test_imputer)

def test_cap_outliers():
    """cap_outliers harus memotong nilai ekstrem"""
    from surveyprep.core.imputer import cap_outliers
    rt = make_susenas_rt(500)
    rt.loc[0, 'fwt'] = 9999  # outlier ekstrem
    result = cap_outliers(rt, num_cols=['fwt'], n_sd=3.0)
    assert result['fwt'].max() < 9999  # outlier ekstrem harus terpotong
run("cap_outliers memotong nilai ekstrem", "data", test_cap_outliers)

def test_runner_rt_2021():
    """RUNNER_RT 2021 harus memetakan r1806 dengan benar (Bambu=kode 5)"""
    from surveyprep.adapters.susenas_2021 import RUNNER_RT
    # Cari item RoofMaterial
    roof = next((item for item in RUNNER_RT if item['out']=='RoofMaterial'), None)
    assert roof is not None, "RoofMaterial tidak ada di RUNNER_RT 2021"
    assert roof['col'] == 'r1806'
    assert roof['map'].get('5') == 'Bambu', \
        f"kode 5 atap 2021 harus Bambu, dapat: {roof['map'].get('5')}"
run("RUNNER_RT 2021: RoofMaterial col=r1806, kode 5=Bambu", "susenas data", test_runner_rt_2021)

def test_runner_rt_2024():
    """RUNNER_RT 2024 harus memetakan r1806a (bukan r1806)"""
    from surveyprep.adapters.susenas_2024 import RUNNER_RT
    roof = next((item for item in RUNNER_RT if item['out']=='RoofMaterial'), None)
    assert roof is not None
    assert roof['col'] == 'r1806a', \
        f"2024 harus r1806a, dapat: {roof['col']}"
run("RUNNER_RT 2024: RoofMaterial col=r1806a", "susenas data", test_runner_rt_2024)

def test_runner_rt_2025_blok_geser():
    """RUNNER_RT 2025 harus pakai r16xx (blok perumahan bergeser ~200 dari 2024)"""
    from surveyprep.adapters.susenas_2025 import RUNNER_RT
    cols = {item['col'] for item in RUNNER_RT}
    # Harus ada r1606 (atap 2025), r1616 (listrik 2025), r1617 (BBM 2025)
    assert 'r1606' in cols, f"r1606 tidak ada. Cols: {cols}"
    assert 'r1616' in cols, f"r1616 tidak ada."
    assert 'r1617' in cols, f"r1617 tidak ada."
    # Tidak boleh ada r1806a (2024) atau r1816 (2024)
    assert 'r1806a' not in cols, "r1806a seharusnya tidak ada di 2025"
run("RUNNER_RT 2025: kolom perumahan di r16xx", "susenas data", test_runner_rt_2025_blok_geser)

def test_fies_2018_blok_14xx():
    """FIES 2018 harus ada di blok R14xx (bukan R17xx seperti 2019+)"""
    from surveyprep.adapters.susenas_2018 import RUNNER_RT
    fies_cols = [item['col'] for item in RUNNER_RT
                 if 'FoodInsecurity' in item.get('out','')]
    assert len(fies_cols) == 8, f"Harus 8 FIES items, dapat {len(fies_cols)}"
    assert all(c.startswith('r1401') or c.startswith('r140') or c[0:4]=='r140'
               for c in fies_cols), \
        f"2018 FIES harus di r14xx, dapat: {fies_cols}"
run("FIES 2018: ada di r14xx (bukan r17xx)", "susenas data", test_fies_2018_blok_14xx)

def test_fies_2019_blok_17xx():
    """FIES 2019 harus ada di blok R17xx"""
    from surveyprep.adapters.susenas_2019 import RUNNER_RT
    fies_cols = [item['col'] for item in RUNNER_RT
                 if 'FoodInsecurity' in item.get('out','')]
    assert len(fies_cols) == 8
    assert all(c.startswith('r1701') or c.startswith('r170') or 'r170' in c
               for c in fies_cols), \
        f"2019 FIES harus di r17xx, dapat: {fies_cols}"
run("FIES 2019: ada di r17xx", "susenas data", test_fies_2019_blok_17xx)

def test_ehcvm_runner_hh_complete():
    """EHCVM RUNNER_HH harus mencakup semua 9 variabel fisik + 8 FIES"""
    from surveyprep.adapters.ehcvm_ben_2021 import RUNNER_HH
    outs = {item['out'] for item in RUNNER_HH}
    required_physical = {
        'UrbanRural','HomeOwnership','RoofMaterial','WallMaterial',
        'FloorMaterial','WaterSource','ToiletType','AccessEnergy','CookingFuel'
    }
    required_fies = {
        'FoodInsecurity_Worry','FoodInsecurity_NoHealthy','FoodInsecurity_FewKinds',
        'FoodInsecurity_SkipMeal','FoodInsecurity_EatLess','FoodInsecurity_RanOut',
        'FoodInsecurity_Hungry','FoodInsecurity_NoBowl',
    }
    missing = (required_physical | required_fies) - outs
    assert not missing, f"RUNNER_HH kekurangan: {missing}"
run("EHCVM RUNNER_HH lengkap (9 fisik + 8 FIES)", "ehcvm data", test_ehcvm_runner_hh_complete)

def test_ehcvm_runner_uses_from_hh():
    """Semua item RUNNER_HH EHCVM harus pakai kind='from_hh' (bukan 'from_rt')"""
    from surveyprep.adapters.ehcvm_ben_2021 import RUNNER_HH
    wrong = [item for item in RUNNER_HH if item.get('kind') != 'from_hh']
    assert not wrong, f"Item RUNNER_HH dengan kind != 'from_hh': {wrong}"
run("EHCVM RUNNER_HH: semua kind='from_hh'", "ehcvm data", test_ehcvm_runner_uses_from_hh)

def test_exporter_dual():
    """export_dual harus menghasilkan dua output tanpa error"""
    from surveyprep.core.exporter import export_dual
    import tempfile, os
    df = pd.DataFrame({
        'HHID'         : [str(i) for i in range(20)],
        'UrbanRural'   : ['Perkotaan']*10 + ['Perdesaan']*10,
        'RoofMaterial' : ['Genteng']*20,
        'HouseholdSize': range(1,21),
        'AgeHead'      : range(30,50),
        'fwt'          : [1.5]*20,
    })
    with tempfile.TemporaryDirectory() as tmpdir:
        out = export_dual(df, outdir=tmpdir)
        assert 'clustering' in out or 'profiling' in out or len(out) > 0
run("export_dual berjalan tanpa error", "data", test_exporter_dual)

# ══════════════════════════════════════════════════════════════════════════════
# 4. CROSS-CHECK TEST — konsistensi antar tahun
# ══════════════════════════════════════════════════════════════════════════════
print("\n[4] Cross-check tests (konsistensi antar adapter)")

def test_all_adapters_have_employment():
    """Semua adapter Susenas harus punya EMPLOYMENT dict"""
    import importlib
    missing = []
    for yr in range(2017, 2026):
        mod = importlib.import_module(f'surveyprep.adapters.susenas_{yr}')
        if not hasattr(mod, 'EMPLOYMENT'):
            missing.append(yr)
    assert not missing, f"EMPLOYMENT tidak ada di: {missing}"
run("Semua adapter Susenas punya EMPLOYMENT", "susenas", test_all_adapters_have_employment)

def test_all_adapters_have_runner():
    """Semua adapter Susenas harus punya RUNNER_RT dan RUNNER_ART"""
    import importlib
    for yr in range(2017, 2026):
        mod = importlib.import_module(f'surveyprep.adapters.susenas_{yr}')
        assert hasattr(mod,'RUNNER_RT'), f"RUNNER_RT tidak ada di {yr}"
        assert hasattr(mod,'RUNNER_ART'), f"RUNNER_ART tidak ada di {yr}"
        assert len(mod.RUNNER_RT) >= 10, f"{yr} RUNNER_RT < 10 items"
run("Semua adapter Susenas punya RUNNER_RT & RUNNER_ART", "susenas", test_all_adapters_have_runner)

def test_all_adapters_have_klp():
    """KLP semua adapter harus punya 13 kelompok pangan"""
    import importlib
    for yr in range(2017, 2026):
        mod = importlib.import_module(f'surveyprep.adapters.susenas_{yr}')
        assert len(mod.KLP) == 13, \
            f"{yr}: KLP punya {len(mod.KLP)} kelompok (harus 13)"
run("KLP semua adapter punya 13 kelompok pangan", "susenas", test_all_adapters_have_klp)

def test_all14_consistency():
    """ALL14 harus konsisten dengan KLP di semua tahun"""
    import importlib
    for yr in range(2017, 2026):
        mod = importlib.import_module(f'surveyprep.adapters.susenas_{yr}')
        klp_headers = set()
        for v in mod.KLP.values():
            klp_headers |= v
        # ALL14 harus subset dari klp_headers union
        diff = mod.ALL14 - klp_headers
        assert not diff, f"{yr}: ALL14 punya kode {diff} yang tidak ada di KLP"
run("ALL14 konsisten dengan KLP di semua tahun", "susenas", test_all14_consistency)

def test_ehcvm_countries_same_structure():
    """Semua adapter EHCVM harus punya CONFIG, RUNNER_HH, RUNNER_IND"""
    import importlib
    countries = ['ben','bfa','civ','gnb','mli','ner','sen','tgo']
    for cc in countries:
        mod = importlib.import_module(f'surveyprep.adapters.ehcvm_{cc}_2021')
        assert hasattr(mod,'CONFIG'), f"{cc}: tidak punya CONFIG"
        assert hasattr(mod,'RUNNER_HH'), f"{cc}: tidak punya RUNNER_HH"
        assert hasattr(mod,'RUNNER_IND'), f"{cc}: tidak punya RUNNER_IND"
        assert mod.CONFIG['survey_family'] == 'ehcvm'
        assert mod.CONFIG['country'] == cc
run("Semua adapter EHCVM punya struktur yang konsisten", "ehcvm", test_ehcvm_countries_same_structure)

# ══════════════════════════════════════════════════════════════════════════════
# RINGKASAN
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "═"*60)
n_pass = sum(1 for s,_,_ in results if s==PASS)
n_fail = sum(1 for s,_,_ in results if s==FAIL)
n_skip = sum(1 for s,_,_ in results if s==SKIP)
total  = n_pass + n_fail

print(f"HASIL: {n_pass}/{total} PASS  |  {n_fail} FAIL  |  {n_skip} SKIP")
print("═"*60)

if n_fail > 0:
    print("\nFailed tests:")
    for status, name, msg in results:
        if status == FAIL:
            print(f"  {FAIL} {name}")
            if msg:
                print(f"       {msg[:120]}")
    sys.exit(1)
else:
    print("\nSemua test PASS. surveyprep v1.9.0 terinstall dengan benar! 🎉")
    sys.exit(0)
