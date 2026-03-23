"""
surveyprep.core.finder
======================
Auto-detect file Susenas dari folder data tanpa mengandalkan nama file.

Strategi deteksi: baca header CSV (baris pertama saja), cocokkan dengan
signature kolom yang khas untuk tiap jenis file — RT, ART, KP41, KP42.

Cara pakai:
    from surveyprep.core.finder import find_susenas_files, print_scan_report

    result = find_susenas_files("data/", year=2020)
    print_scan_report(result)

    # Atau langsung pakai hasilnya:
    df_rt = read_bps_csv(result['rt_file'], sep=result['sep'], ...)

CLI:
    python -m surveyprep.core.finder --dir data/ --year 2020
"""
from __future__ import annotations

import os
import csv
import argparse
from pathlib import Path
from typing import Optional


# ── Signature kolom per jenis file ───────────────────────────────────────────
# Minimal N kolom dari set ini harus ada agar file dianggap match.
# Kolom dipilih yang stabil lintas tahun dan tidak mungkin ada di file lain.

FILE_SIGNATURES = {
    'rt_file': {
        # KOR RT: punya kolom fisik bangunan (r1802+) dan tidak punya b41/b42/food/nonfood
        'required': {'r101', 'r102', 'r105'},
        'supporting': {'r201', 'r301', 'r401', 'r403', 'r1802', 'r1806', 'r1807', 'r1808'},
        'min_supporting': 2,
        'description': 'Household record (KOR RT)',
        'exclude_if': {'b41k5', 'b41k6', 'b42k3', 'b42k4', 'food', 'nonfood',
                       'kalori', 'coicop', 'klp', 'kode'},
    },
    'art_a_file': {
        # KOR ART: punya r407 (umur) dan tidak punya kolom fisik bangunan
        'required': {'r401', 'r403', 'r405', 'r407'},
        'supporting': {'r408', 'r409', 'r410', 'r412', 'r415'},
        'min_supporting': 1,
        'description': 'Individual record part A (KOR ART)',
        'exclude_if': {'r1802', 'r1806', 'r1807', 'b41k5', 'coicop'},
    },
    'art_b_file': {
        # KOR ART part B: punya blok 6 (pendidikan/ketenagakerjaan)
        'required': {'r401', 'r403'},
        'supporting': {'r601', 'r602', 'r603', 'r604', 'r605', 'r606', 'r607'},
        'min_supporting': 3,
        'description': 'Individual record part B (KOR ART blok 6+)',
        'exclude_if': {'r1802', 'b41k5', 'coicop'},
    },
    'kp41_files': {
        # KP41 food expenditure: punya b41k5/b41k6 dan kalori/protein
        'required': {'coicop', 'klp', 'kode'},
        'supporting': {'b41k5', 'b41k6', 'b41k7', 'b41k8', 'kalori', 'protein',
                       'lemak', 'karbo'},
        'min_supporting': 2,
        'description': 'Food expenditure (KP41)',
        'glob_patterns': ['*blok41*', '*kp41*', '*41_gab*', '*food*'],
        'multi': True,
        'exclude_if': {'b42k3', 'b42k4', 'food', 'nonfood', 'r401', 'r403',
                       'r1802', 'r1806'},
    },
    'kp42_files': {
        # KP42 non-food expenditure: punya b42k3/b42k4 dan sebulan
        'required': {'coicop', 'klp', 'kode'},
        'supporting': {'b42k3', 'b42k4', 'b42k5', 'b42k3a', 'b42k3b', 'sebulan'},
        'min_supporting': 2,
        'description': 'Non-food expenditure (KP42)',
        'glob_patterns': ['*blok42*', '*kp42*', '*42_gab*', '*nonfood*'],
        'multi': True,
        'exclude_if': {'b41k5', 'b41k6', 'kalori', 'food', 'nonfood', 'r401',
                       'r1802'},
    },
    'kp43_files': {
        # KP43 expenditure summary: punya food, nonfood, expend, kapita
        'required': {'food', 'nonfood', 'expend', 'kapita'},
        'supporting': {'kalori_kap', 'prote_kap', 'lemak_kap', 'karbo_kap'},
        'min_supporting': 1,
        'description': 'Expenditure summary (KP43)',
        'glob_patterns': ['*blok43*', '*kp43*'],
        'multi': True,
        'exclude_if': {'b41k5', 'b42k3', 'r401', 'r1802'},
    },
}

# Separator yang dicoba secara berurutan
SEPS = [';', ',', '\t', '|']


def _read_header(path: Path, n_rows: int = 3) -> tuple[list[str], str]:
    """
    Baca header CSV — coba beberapa separator, return (kolom_lowercase, sep).
    Hanya membaca n_rows baris pertama — sangat cepat bahkan untuk file besar.
    """
    for sep in SEPS:
        try:
            with open(path, encoding='latin-1', errors='replace') as f:
                reader = csv.reader(f, delimiter=sep)
                rows = []
                for i, row in enumerate(reader):
                    if i >= n_rows:
                        break
                    rows.append(row)
            if not rows:
                continue
            header = [c.strip().lower() for c in rows[0]]
            # Minimal harus ada beberapa kolom (bukan satu string panjang)
            if len(header) >= 3:
                return header, sep
        except Exception:
            continue
    return [], ','


def _score_file(header: set[str], sig: dict) -> int:
    """
    Hitung skor kecocokan file terhadap satu signature.
    Return -1 jika ada kolom exclude_if yang ditemukan.
    """
    # Cek kolom yang harus tidak ada
    exclude = sig.get('exclude_if', set())
    if exclude & header:
        return -1

    # Cek required
    required = sig.get('required', set())
    if required and not required.issubset(header):
        return 0

    # Hitung supporting
    supporting = sig.get('supporting', set())
    n_sup = len(supporting & header)
    if n_sup < sig.get('min_supporting', 0):
        return 0

    return len(required) * 3 + n_sup


def _detect_file_type(path: Path) -> tuple[Optional[str], str, str]:
    """
    Deteksi jenis file Susenas dari isinya.
    Return (file_type, separator, info_string).
    """
    header_list, sep = _read_header(path)
    if not header_list:
        return None, sep, 'cannot read'

    header = set(header_list)
    best_type, best_score = None, 0

    for ftype, sig in FILE_SIGNATURES.items():
        score = _score_file(header, sig)
        if score > best_score:
            best_score = score
            best_type = ftype

    info = f'score={best_score}, sep={repr(sep)}, cols={len(header)}'
    return best_type, sep, info


def find_susenas_files(
    data_dir: str | Path,
    year: Optional[int] = None,
    verbose: bool = True,
) -> dict:
    """
    Scan folder data_dir dan deteksi file-file Susenas secara otomatis.

    Parameters
    ----------
    data_dir : str | Path
        Folder yang berisi file-file Susenas
    year : int, optional
        Tahun survei — digunakan untuk validasi silang nama file jika tersedia
    verbose : bool
        Print progress saat scanning

    Returns
    -------
    dict dengan keys:
        rt_file       : Path | None
        art_a_file    : Path | None
        art_b_file    : Path | None
        kp41_files    : list[Path]
        kp42_files    : list[Path]
        sep           : str  (separator yang terdeteksi dari rt_file)
        status        : dict  (per file: 'found' | 'missing' | 'ambiguous')
        all_csv       : list[Path]  (semua CSV yang ditemukan)
        unmatched     : list[Path]  (CSV yang tidak teridentifikasi)
        warnings      : list[str]
    """
    data_dir = Path(data_dir)
    if not data_dir.exists():
        raise FileNotFoundError(f"Folder tidak ditemukan: {data_dir}")

    # Kumpulkan semua CSV (case-insensitive)
    all_csv = sorted([
        p for p in data_dir.rglob('*')
        if p.suffix.lower() in ('.csv', '.sav', '.dta')
        and not p.name.startswith('.')
        and not p.name.startswith('~')
    ])

    if verbose:
        print(f"📁 Scanning: {data_dir}")
        print(f"   {len(all_csv)} file CSV/SAV/DTA ditemukan\n")

    # Scan tiap file
    candidates: dict[str, list[tuple[Path, str]]] = {k: [] for k in FILE_SIGNATURES}
    unmatched: list[Path] = []
    sep_detected = ';'

    for path in all_csv:
        if verbose:
            print(f"   checking {path.name}...", end=' ', flush=True)

        ftype, sep, info = _detect_file_type(path)

        if ftype:
            candidates[ftype].append((path, info))
            if ftype == 'rt_file':
                sep_detected = sep
            if verbose:
                print(f"→ {ftype} ({info})")
        else:
            unmatched.append(path)
            if verbose:
                print(f"→ (tidak dikenali)")

    # Pilih file terbaik per jenis (skor tertinggi, atau nama paling cocok dengan tahun)
    result: dict = {
        'rt_file': None,
        'art_a_file': None,
        'art_b_file': None,
        'kp41_files': [],
        'kp42_files': [],
        'kp43_files': [],
        'sep': sep_detected,
        'status': {},
        'all_csv': all_csv,
        'unmatched': unmatched,
        'warnings': [],
        'data_dir': data_dir,
    }

    yr2 = str(year)[-2:] if year else None

    for ftype, matches in candidates.items():
        sig = FILE_SIGNATURES[ftype]
        is_multi = sig.get('multi', False)

        if not matches:
            result['status'][ftype] = 'missing'
            if ftype in ('rt_file', 'art_a_file'):
                result['warnings'].append(f"⚠ {ftype} tidak ditemukan di {data_dir}")
            continue

        if is_multi:
            result[ftype] = [p for p, _ in matches]
            result['status'][ftype] = 'found'
        else:
            if len(matches) == 1:
                result[ftype] = matches[0][0]
                result['status'][ftype] = 'found'
            else:
                # Ambiguitas — prioritaskan yang namanya mengandung tahun
                if yr2:
                    yr_matches = [(p, i) for p, i in matches if yr2 in p.name.lower()]
                    if len(yr_matches) == 1:
                        result[ftype] = yr_matches[0][0]
                        result['status'][ftype] = 'found'
                        result['warnings'].append(
                            f"ℹ {ftype}: {len(matches)} kandidat, dipilih berdasarkan tahun {year}: {yr_matches[0][0].name}"
                        )
                        continue
                # Ambil yang pertama, beri warning
                result[ftype] = matches[0][0]
                result['status'][ftype] = 'ambiguous'
                names = [p.name for p, _ in matches]
                result['warnings'].append(
                    f"⚠ {ftype}: {len(matches)} kandidat — {names}. Dipilih: {matches[0][0].name}"
                )

    return result


def print_scan_report(result: dict, year: Optional[int] = None) -> None:
    """Print laporan hasil scan ke stdout."""
    print("\n" + "="*60)
    print("  SurveyPrep — File Scan Report")
    if year:
        print(f"  Tahun: {year}")
    print("="*60)

    STATUS_ICON = {'found': '✅', 'missing': '❌', 'ambiguous': '⚠️ '}

    single_files = ['rt_file', 'art_a_file', 'art_b_file']
    multi_files  = ['kp41_files', 'kp42_files', 'kp43_files']

    for ftype in single_files:
        sig = FILE_SIGNATURES[ftype]
        status = result['status'].get(ftype, 'missing')
        icon = STATUS_ICON.get(status, '?')
        path = result.get(ftype)
        name = path.name if path else '(not found)'
        print(f"  {icon} {sig['description']}")
        print(f"     {ftype}: {name}")

    for ftype in multi_files:
        sig = FILE_SIGNATURES[ftype]
        files = result.get(ftype, [])
        icon = '✅' if files else '❌'
        print(f"  {icon} {sig['description']}")
        if files:
            for f in files[:3]:
                print(f"     {f.name}")
            if len(files) > 3:
                print(f"     ... +{len(files)-3} lainnya")
        else:
            print(f"     (not found)")

    print(f"\n  Separator terdeteksi: {repr(result['sep'])}")

    if result['unmatched']:
        print(f"\n  File tidak dikenali ({len(result['unmatched'])}):")
        for p in result['unmatched'][:5]:
            print(f"     {p.name}")

    if result['warnings']:
        print("\n  Warnings:")
        for w in result['warnings']:
            print(f"  {w}")

    print("="*60 + "\n")


def assert_files_found(result: dict, require_kp41: bool = True) -> None:
    """
    Raise FileNotFoundError jika file penting tidak ditemukan.
    Panggil ini di awal notebook sebelum mulai load data.
    """
    missing = []
    if not result['rt_file']:
        missing.append('rt_file (KOR RT)')
    if not result['art_a_file']:
        missing.append('art_a_file (KOR ART part A)')
    if require_kp41 and not result['kp41_files']:
        missing.append('kp41_files (food expenditure KP41)')
    if missing:
        raise FileNotFoundError(
            f"File berikut tidak ditemukan di {result['data_dir']}:\n" +
            "\n".join(f"  - {m}" for m in missing) +
            "\n\nPastikan semua file ada di folder data/ dan coba jalankan ulang cell ini."
        )


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Scan folder data Susenas dan deteksi file secara otomatis'
    )
    parser.add_argument('--dir',  default='data/', help='Folder data (default: data/)')
    parser.add_argument('--year', type=int,        help='Tahun survei (opsional, untuk validasi)')
    args = parser.parse_args()

    result = find_susenas_files(args.dir, year=args.year, verbose=True)
    print_scan_report(result, year=args.year)


if __name__ == '__main__':
    main()
