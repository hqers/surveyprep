"""
surveyprep.tools.adapter_generator
=====================================
Generator adapter Susenas otomatis dari metadata Excel BPS.

Cara pakai (CLI):
    python -m surveyprep.tools.adapter_generator \\
        --kor  Metadata_Susenas_202603_Kor.xlsx \\
        --kp   Metadata_Susenas_202603_KP.xlsx  \\
        --year 2026 \\
        --out  surveyprep/adapters/susenas_2026.py

Cara pakai (API):
    from surveyprep.tools.adapter_generator import generate_adapter
    code = generate_adapter(year=2026,
                            kor_path='Metadata_2026_Kor.xlsx',
                            kp_path='Metadata_2026_KP.xlsx')
    with open('susenas_2026.py', 'w') as f:
        f.write(code)

Output:
    File .py yang valid, siap di-import oleh pipeline SurveyPrep.
    File ini menggunakan inheritance dari base.py — hanya variabel yang
    berbeda dari default (2020) yang di-override.

Didukung format:
    - SPSS-style (KOR18/19/20/21/22/23/24): sheet dengan "Variable Values"
    - Layout-style (KOR17, KOR25): sheet dengan kolom Variable + Label
    - Auto-detect format dari struktur sheet

Variabel yang di-generate otomatis:
    RT  : R105, R1802/R1502/R1602/R1606 (kepemilikan), R1806/R1507/R1607/R1606 (atap),
          R1807/... (dinding), R1808/... (lantai), R1809A/... (sanitasi),
          R1816/... (listrik), R1817/... (BBM), R1810A/... (air minum)
    IND : R615/R614/R613 (ijazah), R616/R615/R619 (KIP), R403 (hubungan), R405 (gender)
    KP  : KLP rokok start code, jumlah komoditi
"""
from __future__ import annotations

import re
import sys
import textwrap
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional

import pandas as pd


# ── Konstanta mapping kolom antar tahun ──────────────────────────────────────
# Peta: nama konsep → kemungkinan nama variabel di Excel per era
CONCEPT_CANDIDATES = {
    # RT perumahan
    'ownership'  : ['R1802','R1502','R1602','R2202'],    # kepemilikan
    'roof'       : ['R1806','R1806A','R1507','R1607','R1606'],  # atap
    'wall'       : ['R1807','R1508','R1608','R1607'],    # dinding
    'floor'      : ['R1808','R1509','R1609','R1608'],    # lantai
    'sanitation' : ['R1809A','R1510A','R1610A'],         # sanitasi
    'toilet_type': ['R1809B','R1510B','R1610B'],         # jenis kloset
    'water'      : ['R1810A','R1511A','R1611A','R1611'], # air minum
    'electricity': ['R1816','R1518A','R1618A'],          # listrik
    'fuel'       : ['R1817','R1519','R1619','R1617'],    # BBM memasak
    'urban_rural': ['R105'],                              # perkotaan/perdesaan

    # IND pendidikan
    'edu_cert'   : ['R615','R614','R613'],               # ijazah
    'kip'        : ['R616','R615','R619'],               # KIP
    'relation'   : ['R403','R401'],                      # hub dg KRT
    'gender'     : ['R405','R404'],                      # jenis kelamin
    'activity'   : ['R703','R702','R704','R802'],        # kegiatan utama
    'emp_status' : ['R706','R705','R707','R805'],        # status pekerjaan
    'working_flag': ['R702_A','R701_A','R703_A','R801_A'],
}

# Output feature names per konsep (untuk RUNNER_RT)
CONCEPT_OUTPUT = {
    'ownership'  : ('HomeOwnership',  'from_rt'),
    'roof'       : ('RoofMaterial',   'from_rt'),
    'wall'       : ('WallMaterial',   'from_rt'),
    'floor'      : ('FloorMaterial',  'from_rt'),
    'sanitation' : ('Sanitation',     'from_rt'),
    'toilet_type': ('ToiletType',     'from_rt'),
    'water'      : ('WaterSource',    'from_rt'),
    'electricity': ('AccessEnergy',   'from_rt'),
    'fuel'       : ('CookingFuel',    'from_rt'),
    'urban_rural': ('UrbanRural',     'from_rt'),
}

# KLP rokok berdasarkan jumlah komoditi total
KLP_ROKOK_MAP = {
    188: '183',
    197: '192',
    225: '220',
}

# ── Parser metadata Excel ─────────────────────────────────────────────────────

def parse_metadata_excel(path: str | Path, sheet_hint: str = '') -> dict[str, dict[int, str]]:
    """
    Baca satu file metadata Excel BPS dan return dict value labels.

    Returns:
        { 'R1806': {1: 'Beton', 2: 'Genteng', ...}, ... }
    """
    path = Path(path)
    xf   = pd.ExcelFile(path)

    # Pilih sheet yang paling relevan
    target_sheet = _pick_sheet(xf.sheet_names, sheet_hint)
    df = xf.parse(target_sheet, header=None)
    df.columns = (
        ['Variable', 'Position', 'Label'] +
        [f'x{i}' for i in range(max(0, df.shape[1] - 3))]
    )[:df.shape[1]]

    df['Variable'] = (df['Variable'].fillna('')
                      .astype(str).str.replace('\xa0', '')
                      .str.strip().str.upper())
    df['Position'] = df['Position'].fillna('').astype(str).str.strip()
    df['Label']    = df['Label'].fillna('').astype(str).str.strip()

    # Deteksi format: SPSS (ada "Variable Values") vs Layout (langsung var/label)
    val_idx_rows = df[df['Variable'].str.contains(
        r'VARIABLE VALUES|VALUE LABEL', na=False)].index

    if len(val_idx_rows):
        # Format SPSS
        return _parse_spss_value_labels(df, val_idx_rows[0])
    else:
        # Format Layout (KOR17, KOR25) — value labels ada di sheet terpisah
        return _parse_layout_value_labels(xf, df, target_sheet)


def _pick_sheet(sheets: list[str], hint: str) -> str:
    """Pilih sheet RT atau IND dari daftar sheet."""
    hint_upper = hint.upper()
    if hint_upper:
        for s in sheets:
            if hint_upper in s.upper():
                return s
    # Preferensikan sheet RT
    for keyword in ['RT', 'KOR', 'RUMAH']:
        for s in sheets:
            if keyword in s.upper():
                return s
    return sheets[0]


def _parse_spss_value_labels(df: pd.DataFrame,
                              val_start: int) -> dict[str, dict[int, str]]:
    """Parse value labels dari format SPSS (ada header 'Variable Values')."""
    cur_var = None
    result: dict[str, dict[int, str]] = {}

    for _, r in df.iloc[val_start + 2:].iterrows():
        v = r['Variable']
        if v and v not in ('NAN', 'VALUE', 'LABEL', ''):
            cur_var = v
            if cur_var not in result:
                result[cur_var] = {}

        val, lbl = r['Position'], r['Label']
        if cur_var and val and val not in ('', 'nan') and lbl not in ('', 'nan'):
            try:
                result[cur_var][int(float(val))] = lbl
            except (ValueError, TypeError):
                pass

    return result


def _parse_layout_value_labels(xf: pd.ExcelFile,
                                df: pd.DataFrame,
                                base_sheet: str) -> dict[str, dict[int, str]]:
    """
    Parse value labels dari format Layout (KOR17 / KOR25).
    Value labels biasanya di sheet terpisah bernama 'value-*' atau 'Value-*'.
    """
    # Cari sheet value labels
    val_sheet = None
    for s in xf.sheet_names:
        if 'value' in s.lower() and s != base_sheet:
            if 'rt' in s.lower() or 'kor' in s.lower():
                val_sheet = s
                break

    if val_sheet is None:
        for s in xf.sheet_names:
            if 'value' in s.lower() and s != base_sheet:
                val_sheet = s
                break

    if val_sheet is None:
        return {}

    dfv = xf.parse(val_sheet, header=None)
    dfv.columns = (
        ['Variable', 'Value', 'Label'] +
        [f'x{i}' for i in range(max(0, dfv.shape[1] - 3))]
    )[:dfv.shape[1]]
    dfv['Variable'] = (dfv['Variable'].fillna('')
                       .astype(str).str.replace('\xa0', '')
                       .str.strip().str.upper())
    dfv['Value'] = dfv['Value'].fillna('').astype(str).str.strip()
    dfv['Label'] = dfv['Label'].fillna('').astype(str).str.strip()

    cur_var = None
    result: dict[str, dict[int, str]] = {}
    for _, r in dfv.iterrows():
        v = r['Variable']
        if v and v not in ('NAN', 'VALUE', 'LABEL', 'VARIABLE', ''):
            cur_var = v
            if cur_var not in result:
                result[cur_var] = {}
        val, lbl = r['Value'], r['Label']
        if cur_var and val and val not in ('', 'nan') and lbl not in ('', 'nan'):
            try:
                result[cur_var][int(float(val))] = lbl
            except (ValueError, TypeError):
                pass

    return result


def parse_kp_metadata(path: str | Path) -> dict:
    """
    Baca metadata KP Excel dan return info komoditi.
    Returns: { 'n_commodities': 188, 'klp_rokok': '183', 'sheet': 'BLOK41' }
    """
    path = Path(path)
    xf   = pd.ExcelFile(path)

    # Cari sheet BLOK41
    blok41 = next((s for s in xf.sheet_names if '41' in s or 'BLOK' in s.upper()), xf.sheet_names[0])
    df = xf.parse(blok41, header=None)
    df.columns = (['Variable', 'Position', 'Label'] +
                  [f'x{i}' for i in range(max(0, df.shape[1] - 3))])[:df.shape[1]]
    df['Variable'] = df['Variable'].fillna('').astype(str).str.strip().str.upper()
    df['Position'] = df['Position'].fillna('').astype(str).str.strip()
    df['Label']    = df['Label'].fillna('').astype(str).str.strip()

    # Value labels section — cari 'KODE' variabel
    val_idx_rows = df[df['Variable'].str.contains(r'VARIABLE VALUES|VALUE LABEL', na=False)].index
    if not len(val_idx_rows):
        return {'n_commodities': 0, 'klp_rokok': '183', 'sheet': blok41}

    kode_vals: dict[int, str] = {}
    cur_var = None
    for _, r in df.iloc[val_idx_rows[0] + 2:].iterrows():
        v = r['Variable']
        if v and v not in ('NAN', 'VALUE', 'LABEL', ''):
            cur_var = v
        val, lbl = r['Position'], r['Label']
        if cur_var == 'KODE' and val and val not in ('', 'nan'):
            try:
                kode_vals[int(float(val))] = str(lbl).strip()
            except (ValueError, TypeError):
                pass

    n_total   = len(kode_vals)
    klp_rokok = str(KLP_ROKOK_MAP.get(n_total, '183'))

    # Cari KLP rokok dari label header — "ROKOK" dalam label ALL CAPS
    for code, label in kode_vals.items():
        if label.isupper() and 'ROKOK' in label:
            klp_rokok = str(code)
            break

    return {
        'n_commodities': n_total,
        'klp_rokok': klp_rokok,
        'sheet': blok41,
    }


# ── Resolver: temukan variabel yang ada di metadata ──────────────────────────

def resolve_concepts(value_labels: dict[str, dict[int, str]]) -> dict[str, str | None]:
    """
    Untuk setiap konsep, temukan nama variabel yang tersedia di metadata.
    Returns: { 'roof': 'R1806', 'wall': 'R1807', ... }
    """
    vl_upper = {k.upper(): k for k in value_labels}
    resolved = {}
    for concept, candidates in CONCEPT_CANDIDATES.items():
        found = None
        for cand in candidates:
            if cand.upper() in vl_upper:
                found = cand.upper()
                break
        resolved[concept] = found
    return resolved


# ── Code generator ────────────────────────────────────────────────────────────

def _vl_to_python(vl: dict[int, str], indent: int = 8) -> str:
    """Render value labels dict ke Python source."""
    pad = ' ' * indent
    items = ',\n'.join(f'{pad}{k}: {repr(v)}' for k, v in sorted(vl.items()))
    return '{\n' + items + f',\n{" " * (indent - 4)}}}'


def _runner_item(concept: str, col: str, vl: dict[int, str]) -> str:
    """Generate satu item RUNNER_RT."""
    out_name, kind = CONCEPT_OUTPUT[concept]
    map_str = '{' + ', '.join(f"'{k}': '{v}'" for k, v in sorted(vl.items())) + '}'
    # Potong label panjang
    clean_map = {}
    for k, v in sorted(vl.items()):
        clean_map[str(k)] = v[:40].replace("'", "\\'")
    map_py = '{' + ', '.join(f"'{k}': '{v}'" for k, v in clean_map.items()) + '}'
    return (f"    dict(kind='{kind}', out='{out_name}', col='{col.lower()}',\n"
            f"         map={map_py}),")


def generate_adapter(
    year: int,
    kor_path: str | Path,
    kp_path: Optional[str | Path] = None,
    *,
    base_year: int = 2020,
    notes: str = '',
    author: str = 'adapter_generator',
) -> str:
    """
    Generate kode adapter Python dari metadata Excel BPS.

    Parameters
    ----------
    year       : Tahun survei (mis. 2026)
    kor_path   : Path ke file metadata KOR (.xlsx atau .xls)
    kp_path    : Path ke file metadata KP (.xlsx atau .xls) — opsional
    base_year  : Tahun basis untuk perbandingan (default 2020)
    notes      : Catatan tambahan yang akan masuk ke docstring
    author     : Nama pembuat (untuk header)

    Returns
    -------
    str — kode Python adapter yang valid
    """
    yr2 = str(year)[-2:]  # '26' dari 2026

    # Parse KOR metadata
    print(f"[generator] Membaca metadata KOR: {kor_path}")
    vl = parse_metadata_excel(kor_path)
    print(f"[generator] Ditemukan {len(vl)} variabel dengan value labels")

    # Resolve konsep
    resolved = resolve_concepts(vl)
    found    = {k: v for k, v in resolved.items() if v}
    missing  = {k for k, v in resolved.items() if v is None}
    print(f"[generator] Konsep teridentifikasi: {sorted(found.keys())}")
    if missing:
        print(f"[generator] Tidak ditemukan: {sorted(missing)} — akan pakai base.py default")

    # Parse KP metadata
    kp_info = {'n_commodities': 188, 'klp_rokok': '183'}
    if kp_path:
        print(f"[generator] Membaca metadata KP: {kp_path}")
        kp_info = parse_kp_metadata(kp_path)
        print(f"[generator] KP: {kp_info['n_commodities']} komoditi, KLP rokok={kp_info['klp_rokok']}")

    # Deteksi hh_id: jika ada kolom URUT tapi tidak RENUM
    # (heuristic: metadata 2022 dan 2018 pakai URUT)
    hh_id = 'renum'  # default
    if any('URUT' in k for k in vl) and not any('RENUM' in k for k in vl):
        hh_id = 'urut'

    # Deteksi design cols: ada PSU/SSU/STRATA?
    has_psu = any('PSU' in k or 'SSU' in k or 'STRATA' in k for k in vl)
    has_wi3 = 'WI3' in vl or 'WI2' in vl

    # ── Build kode Python ──────────────────────────────────────────────────

    lines = []

    # Header docstring
    changed_concepts = []
    for concept, col in found.items():
        # Bandingkan dengan base (2020) kolom default
        base_cols = {'roof':'r1806','wall':'r1807','floor':'r1808',
                     'ownership':'r1802','sanitation':'r1809a',
                     'toilet_type':'r1809b','water':'r1810a',
                     'electricity':'r1816','fuel':'r1817'}
        base_col = base_cols.get(concept, '')
        if base_col and col.lower() != base_col:
            changed_concepts.append(f"  {concept}: {base_col} → {col.lower()}")

    doc_changes = '\n'.join(changed_concepts) if changed_concepts else '  (tidak ada perubahan kolom dari 2020)'
    doc_notes   = f'\n{notes}' if notes else ''

    lines.append(f'''"""
surveyprep.adapters.susenas_{year}
====================================
Adapter Susenas {year} Maret — di-generate otomatis oleh adapter_generator.py

Generated : {datetime.now().strftime("%Y-%m-%d %H:%M")}
Generator : {author}
Sumber KOR: {Path(kor_path).name}
Sumber KP : {Path(kp_path).name if kp_path else "—"}

STATUS: ⚠ AUTO-GENERATED — verifikasi manual diperlukan sebelum production.
        Periksa terutama: hh_id_col, design_cols, employment col shifts,
        dan value labels yang mungkin berbeda dari yang di-generate.

Perubahan kolom terdeteksi vs base (2020):
{doc_changes}

KP: {kp_info["n_commodities"]} komoditi, KLP rokok start = {kp_info["klp_rokok"]}{doc_notes}
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
''')

    # CONFIG
    wi3_flag = 'True' if has_wi3 else 'False'
    lines.append(f"# ── CONFIG ──────────────────────────────────────────────────────────────────")
    lines.append(f"CONFIG = make_config('{yr2}', has_wi3={wi3_flag})")
    if hh_id != 'renum':
        lines.append(f"CONFIG['hh_id_col'] = '{hh_id}'  # ⚠ tahun ini pakai URUT bukan RENUM")
    if has_psu:
        lines.append(f"# CONFIG['design_cols'] sudah berisi PSU/SSU/STRATA dari make_config")
    else:
        lines.append(f"# ⚠ PSU/SSU/STRATA tidak terdeteksi — design_cols mungkin perlu disesuaikan")
    lines.append("")

    # VALUE_LABELS
    lines.append("# ── VALUE_LABELS — override dari base.py ──────────────────────────────────")
    lines.append("VALUE_LABELS = copy.deepcopy(BASE_VALUE_LABELS)")
    lines.append("")

    # Generate value labels untuk tiap konsep yang ditemukan
    vl_generated = set()
    for concept, col in found.items():
        if concept not in CONCEPT_OUTPUT:
            continue
        col_up = col.upper()
        if col_up not in vl:
            continue
        out_name = CONCEPT_OUTPUT[concept][0]
        col_lower = col.lower()
        vl_data = vl[col_up]
        if not vl_data:
            continue

        vl_generated.add(col_lower)
        vl_py = _vl_to_python(vl_data, indent=4)
        lines.append(f"VALUE_LABELS['{col_lower}'] = {vl_py}")
        lines.append("")

    # Edu cert (ijazah)
    edu_col = found.get('edu_cert')
    if edu_col and edu_col in vl:
        edu_lower = edu_col.lower()
        vl_edu = vl[edu_col]
        n_edu = len(vl_edu)
        lines.append(f"# Ijazah tertinggi — {n_edu} kode")
        lines.append(f"VALUE_LABELS['{edu_lower}'] = {_vl_to_python(vl_edu, 4)}")
        lines.append("")
        # Band mapping
        band = _make_edu_band(vl_edu)
        if band:
            lines.append(f"VALUE_LABELS['{edu_lower}_band'] = {_vl_to_python(band, 4)}")
            lines.append("")

    # KLP — override jika berbeda dari base
    lines.append("# ── KLP komoditi pangan ─────────────────────────────────────────────────────")
    n_comm = kp_info['n_commodities']
    klp_rokok = kp_info['klp_rokok']
    if n_comm == 188 and klp_rokok == '183':
        lines.append("KLP = copy.deepcopy(BASE_KLP)  # sama dengan 2020 — 188 komoditi")
    else:
        lines.append(f"KLP = copy.deepcopy(BASE_KLP)")
        lines.append(f"KLP['rokok'] = {{'{klp_rokok}'}}  # KLP rokok berubah ({n_comm} komoditi)")
    lines.append("ALL14           = set(BASE_ALL14)")
    lines.append("NO_TOB          = set(BASE_NO_TOB)")
    lines.append("NO_TOB_PREP     = set(BASE_NO_TOB_PREP)")
    lines.append("PREPARED_RANGE  = BASE_PREPARED_RANGE")
    lines.append("PROC_CODES      = set(BASE_PROC_CODES)")
    lines.append("FOOD_GROUP_HEADERS = dict(BASE_FOOD_GROUP_HEADERS)")
    lines.append("")

    # RUNNER_RT
    lines.append("# ── RUNNER_RT ─────────────────────────────────────────────────────────────────")
    runner_changes = False
    for concept, col in found.items():
        if concept not in CONCEPT_OUTPUT:
            continue
        base_col_map = {
            'urban_rural': 'r105', 'ownership': 'r1802', 'roof': 'r1806',
            'wall': 'r1807', 'floor': 'r1808', 'sanitation': 'r1809a',
            'toilet_type': 'r1809b', 'water': 'r1810a',
            'electricity': 'r1816', 'fuel': 'r1817',
        }
        base_col = base_col_map.get(concept, '')
        if col.lower() != base_col:
            runner_changes = True
            break

    if not runner_changes:
        lines.append("RUNNER_RT = list(BASE_RUNNER_RT)  # sama dengan 2020")
    else:
        lines.append("RUNNER_RT = []")
        for concept, col in found.items():
            if concept not in CONCEPT_OUTPUT:
                continue
            col_up = col.upper()
            if col_up not in vl or not vl[col_up]:
                continue
            lines.append(_runner_item(concept, col, vl[col_up]))
        lines.append("")
        lines.append("# FIES — sesuaikan blok R14xx/R15xx/R17xx berdasarkan tahun")
        fies_vars = [v for v in vl if re.match(r'R1[457]0[1-8]$', v)]
        if fies_vars:
            fies_base = sorted(fies_vars)[0][:4].lower()  # mis. 'r170'
            fies_map  = {'1': 'Ya', '5': 'Tidak', '8': 'Tidak tahu', '9': 'Menolak'}
            fies_map_py = str(fies_map)
            for i, fies_sfx in enumerate(['1','2','3','4','5','6','7','8'], 1):
                fies_col = f"{fies_base}{fies_sfx}"
                fies_names = ['FoodInsecurity_Worry','FoodInsecurity_NoHealthy',
                              'FoodInsecurity_FewKinds','FoodInsecurity_SkipMeal',
                              'FoodInsecurity_EatLess','FoodInsecurity_RanOut',
                              'FoodInsecurity_Hungry','FoodInsecurity_NoBowl']
                lines.append(f"    dict(kind='from_rt', out='{fies_names[i-1]}', col='{fies_col}',")
                lines.append(f"         map={fies_map_py}),")
    lines.append("")

    # RUNNER_ART
    lines.append("# ── RUNNER_ART ────────────────────────────────────────────────────────────────")
    lines.append("RUNNER_ART = list(BASE_RUNNER_ART)  # override jika ada perubahan kolom ART")
    lines.append("")

    # EMPLOYMENT
    emp_col   = found.get('activity',   'r703')
    stat_col  = found.get('emp_status', 'r706')
    wflag_col = found.get('working_flag', None)
    edu_col   = found.get('edu_cert',   'r615')
    kip_col   = found.get('kip',        None)

    lines.append("# ── EMPLOYMENT — kolom ketenagakerjaan ──────────────────────────────────────")
    lines.append("EMPLOYMENT = {")
    lines.append(f"    'education_col'   : '{edu_col.lower() if edu_col else 'r615'}',")
    lines.append(f"    'kip_col'         : {repr(kip_col.lower()) if kip_col else 'None'},")
    lines.append(f"    'activity_col'    : '{emp_col.lower() if emp_col else 'r703'}',")

    # Derive temp_notwork, sector, status, hours dari activity col
    act_num = re.search(r'\d+', emp_col or 'r703')
    if act_num:
        n = int(act_num.group())
        lines.append(f"    'temp_notwork_col': 'r{n+1:03d}',   # ⚠ perlu verifikasi")
        lines.append(f"    'sector_col'      : 'r{n+2:03d}',   # ⚠ perlu verifikasi")
        lines.append(f"    'status_col'      : '{stat_col.lower() if stat_col else f'r{n+3:03d}'}',")
        lines.append(f"    'hours_col'       : 'r{n+4:03d}',   # ⚠ perlu verifikasi")
    else:
        lines.append( "    'temp_notwork_col': None,   # ⚠ tidak terdeteksi")
        lines.append( "    'sector_col'      : None,   # ⚠ tidak terdeteksi")
        lines.append(f"    'status_col'      : '{stat_col.lower() if stat_col else 'None'}',")
        lines.append( "    'hours_col'       : None,   # ⚠ tidak terdeteksi")

    if wflag_col:
        lines.append(f"    'working_flag_col': '{wflag_col.lower()}',")
    else:
        lines.append( "    'working_flag_col': None,   # ⚠ tidak terdeteksi — cek manual")

    lines.append("}")

    # Footer warning
    lines.append("""
# ── PERLU VERIFIKASI MANUAL ───────────────────────────────────────────────────
# Setelah generate, periksa hal-hal berikut:
# 1. CONFIG['hh_id_col'] — pastikan 'renum' atau 'urut' sesuai data aktual
# 2. CONFIG['design_cols'] — PSU/SSU/STRATA tersedia?
# 3. EMPLOYMENT dict — semua kolom r7xx/r8xx sudah benar
# 4. RUNNER_RT — mapping kode sudah sesuai metadata
# 5. Jalankan: python surveyprep/test_surveyprep.py susenas
# ─────────────────────────────────────────────────────────────────────────────
""")

    return '\n'.join(lines)


def _make_edu_band(vl_edu: dict[int, str]) -> dict[int, str]:
    """Buat band mapping ijazah berdasarkan label."""
    band = {}
    for code, label in vl_edu.items():
        lbl = label.lower()
        if any(x in lbl for x in ['tidak punya','tidak tamat','belum','tdk']):
            band[code] = 'Tidak_Tamat_SD'
        elif any(x in lbl for x in ['paket a','sdlb','sd','mi']):
            band[code] = 'SD'
        elif any(x in lbl for x in ['paket b','smplb','smp','mts']):
            band[code] = 'SMP'
        elif any(x in lbl for x in ['paket c','smlb','sma','ma','smk','mak']):
            band[code] = 'SMA'
        elif any(x in lbl for x in ['d1','d2','d3','diploma']):
            band[code] = 'Diploma'
        elif any(x in lbl for x in ['d4','s1','profesi','sarjana']):
            band[code] = 'S1'
        elif any(x in lbl for x in ['s2','s3','master','doktor','magister']):
            band[code] = 'S2_S3'
        else:
            band[code] = 'Lainnya'
    return band


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Generate SurveyPrep adapter dari metadata Excel BPS'
    )
    parser.add_argument('--kor',  required=True, help='Path metadata KOR (.xlsx/.xls)')
    parser.add_argument('--kp',   default=None,  help='Path metadata KP (.xlsx/.xls)')
    parser.add_argument('--year', required=True, type=int, help='Tahun survei (mis. 2026)')
    parser.add_argument('--out',  default=None,  help='Path output .py (default: print ke stdout)')
    parser.add_argument('--notes', default='',   help='Catatan tambahan di docstring')
    args = parser.parse_args()

    code = generate_adapter(
        year=args.year,
        kor_path=args.kor,
        kp_path=args.kp,
        notes=args.notes,
        author='adapter_generator CLI',
    )

    if args.out:
        Path(args.out).write_text(code, encoding='utf-8')
        print(f"\n[generator] ✅ Adapter ditulis ke: {args.out}")
        print(f"[generator] Baris: {code.count(chr(10))}")
        print(f"[generator] Selanjutnya: verifikasi manual, lalu jalankan test suite")
    else:
        print(code)


if __name__ == '__main__':
    main()
