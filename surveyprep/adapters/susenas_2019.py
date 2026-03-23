"""
surveyprep.adapters.susenas_2019
=================================
Adapter Susenas 2019 Maret (KOR + KP).
Sumber: Layout_Data_Susenas_201903_Kor.xlsx
        Layout_Data_Susenas_201703_KP.xlsx  ← KP 2017 = identik dengan 2019/2020

STATUS: ✅ VERIFIED dari layout resmi BPS 2019 + KP 2017

Konfirmasi KP 2017 = berlaku untuk 2019
-----------------------------------------
KP 2017 memiliki 188 komoditi dengan KLP yang identik dengan 2020:
  KLP 52=Daging, 62=Telur, 72=Sayur, 98=Kacang, 106=Buah, 183=Rokok
Ini mengkonfirmasi bahwa KP tidak berubah antara 2017-2020.
Perubahan KLP baru terjadi di 2022 (188→197 komoditi, rokok 183→192).

Perubahan dari 2020 (basis)
-----------------------------
RT:
  PSU/SSU/STRATA : TIDAK ADA di 2019 (ada di 2020)
  WI             : ADA (Wealth Index — tidak ada di 2020)
  wi3            : TIDAK ADA (sama dengan 2021+)
  RENUM          : ada (kunci join, sama 2020)
  FWT            : ada (penimbang)
  FIES           : R1701-R1708 ADA (nilai: 1/5/8/9, sama 2021/2022/2023)
  R1802 (kepemilikan): 5 kode (1-5) — sudah berubah dari era sebelumnya
  R1806 (atap)   : 8 kode, tapi urutan berbeda dari 2021+
                   ⚠ kode 3=Asbes, kode 4=Seng (2021+: 3=Seng, 4=Asbes)
  R1809B (kloset): 4 kode, kode 4=Cemplung cubluk (sama 2021+)
  R1810A (air)   : 11 kode (Leding eceran sudah tidak ada — sama 2021+)
  R1816          : label kode 2 = "PLN tanpa meteran" (sama 2021+)
                   ⚠ kode 4 tidak ada! Kode "Bukan listrik" = kode 5
  R1817          : 11 kode (0-11), Elpiji 12kg = kode 3 (sama 2021+)

IND — PERBEDAAN BESAR dari 2020 dan 2021:
  R615  = IJAZAH (22 kode, kode berbeda dari 2021+!)
          1=Tidak punya ijazah SD, 4=SD, 8=SMP, 12=SMA, 19=S1, ...
          [2019: kode 1=Tidak punya, kode 4=SD]
          [2021: kode 1=Paket A, kode 3=SD, kode 22=Tidak punya]
  R616  = KIP (sama posisinya dengan 2021)
  R701_A-X: multi-flag kegiatan ← prefix R701 (bukan R702 spt 2021/2022!)
  R702  = kegiatan utama (bukan R703 seperti 2021/2022)
  R703  = flag sementara tidak bekerja (bukan R704)
  R704  = lapangan usaha (bukan R705)
  R705  = status pekerjaan (bukan R706)
  R701  = tidak ada (rekening tabungan belum ada di 2019)
  R802  = HP (1=Ya, 5=Tidak — sama 2021+)

KP: 188 komoditi, identik dengan 2020 (KLP rokok=183)
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

# ── Config ────────────────────────────────────────────────────────────────────
# 2019: tidak ada PSU/SSU/STRATA, ada WI (Wealth Index)
# wi3 tidak ada, wi1/wi2 ada, RENUM ada
CONFIG = make_config('19', has_wi3=False)
CONFIG['design_cols'] = ['wi', 'wi1', 'wi2', 'fwt']  # PSU/SSU/STRATA tidak ada

# ── Value labels RT ───────────────────────────────────────────────────────────
VALUE_LABELS = copy.deepcopy(BASE_VALUE_LABELS)

# R1802: 5 kode (sama 2021+)
VALUE_LABELS['r1802'] = {
    1: 'Milik sendiri', 2: 'Kontrak/sewa',
    3: 'Bebas sewa',    4: 'Dinas', 5: 'Lainnya',
}

# ⚠ R1806 (atap): 8 kode, TAPI urutan kode 3 dan 4 terbalik vs 2021+
# 2019: 1=Beton, 2=Genteng, 3=ASBES, 4=SENG, 5=Bambu, 6=Kayu/sirap, 7=Jerami, 8=Lainnya
# 2021: 1=Beton, 2=Genteng, 3=SENG, 4=ASBES, 5=Bambu, 6=Kayu/sirap, 7=Jerami, 8=Lainnya
VALUE_LABELS['r1806'] = {
    1: 'Beton',    2: 'Genteng',  3: 'Asbes',
    4: 'Seng',     5: 'Bambu',    6: 'Kayu/sirap',
    7: 'Jerami/ijuk/daun-daunan/rumbia', 8: 'Lainnya',
}

# R1807/R1808: sama dengan base (2020)
# R1809A: sama 2021+
VALUE_LABELS['r1809a'] = {
    1: 'Sendiri',              2: 'Bersama RT tertentu',
    3: 'MCK komunal',          4: 'MCK/WC umum',
    5: 'Ada tapi tidak digunakan', 6: 'Tidak ada',
}
# R1809B: 4 kode (sama 2021+)
VALUE_LABELS['r1809b'] = {
    1: 'Leher angsa', 2: 'Plengsengan dengan tutup',
    3: 'Plengsengan tanpa tutup', 4: 'Cemplung cubluk',
}
# R1810A: 11 kode (sama 2021+)
VALUE_LABELS['r1810a'] = {
    1:  'Air kemasan bermerk', 2:  'Air isi ulang',
    3:  'Leding',              4:  'Sumur bor/pompa',
    5:  'Sumur terlindung',    6:  'Sumur tak terlindung',
    7:  'Mata air terlindung', 8:  'Mata air tak terlindung',
    9:  'Air permukaan',       10: 'Air hujan',
    11: 'Lainnya',
}
# ⚠ R1816: label kode 2 berubah + kode 4 tidak ada, bukan listrik = kode 5
VALUE_LABELS['r1816'] = {
    1: 'PLN dengan meteran', 2: 'PLN tanpa meteran',
    3: 'Non-PLN',            5: 'Bukan listrik',
}
# R1817: 11 kode (sama 2021+)
VALUE_LABELS['r1817'] = {
    0:  'Tidak memasak',        1:  'Listrik',
    2:  'Elpiji 5.5kg/bluegaz', 3:  'Elpiji 12kg',
    4:  'Elpiji 3kg',           5:  'Gas kota',
    6:  'Biogas',               7:  'Minyak tanah',
    8:  'Briket',               9:  'Arang',
    10: 'Kayu bakar',           11: 'Lainnya',
}
VALUE_LABELS['r1701_fies'] = {1: 'Ya', 5: 'Tidak', 8: 'Tidak tahu', 9: 'Menolak'}

# ⚠ R615 2019: ijazah 22 kode dengan KODE BERBEDA dari 2021+
# 2019: 1=Tdk punya, 4=SD, 8=SMP, 12=SMA, 19=S1 dst.
# 2021: 1=Paket A, 3=SD, 8=SMP, 13=SMA, 21=S1, 22=Tdk punya
VALUE_LABELS['r615'] = {
    1:  'Tidak punya ijazah SD',
    2:  'Paket A',
    3:  'SDLB',
    4:  'SD',
    5:  'MI',
    6:  'Paket B',
    7:  'SMPLB',
    8:  'SMP',
    9:  'MTs',
    10: 'Paket C',
    11: 'SMLB',
    12: 'SMA',
    13: 'MA',
    14: 'SMK',
    15: 'MAK',
    16: 'D1/D2',
    17: 'D3',
    18: 'D4',
    19: 'S1',
    20: 'Profesi',
    21: 'S2',
    22: 'S3',
}
# Band 7 level untuk 2019 (kode berbeda, band sama)
VALUE_LABELS['r615_band'] = {
    1:  'Tidak_Tamat_SD', 2:  'SD',        3:  'SD',
    4:  'SD',             5:  'SD',         6:  'SMP',
    7:  'SMP',            8:  'SMP',        9:  'SMP',
    10: 'SMA',            11: 'SMA',        12: 'SMA',
    13: 'SMA',            14: 'SMA',        15: 'SMA',
    16: 'Diploma',        17: 'Diploma',    18: 'S1',
    19: 'S1',             20: 'S1',         21: 'S2_S3',
    22: 'S2_S3',
}

# R616 = KIP (sama posisi dengan 2021)
VALUE_LABELS['r616'] = {1: 'Ya, ditunjukkan', 2: 'Ya, tdk ditunjukkan', 5: 'Tidak'}

# R802: HP (1=Ya, 5=Tidak — sama 2021+)
VALUE_LABELS['r802'] = {1: 'Ya', 5: 'Tidak'}
# ⚠ R701 (rekening tabungan) BELUM ADA di 2019

# ── KLP pangan 2019: SAMA dengan 2020 (identik KP 2017) ──────────────────────
KLP               = copy.deepcopy(BASE_KLP)
ALL14             = set(BASE_ALL14)
NO_TOB            = set(BASE_NO_TOB)
NO_TOB_PREP       = set(BASE_NO_TOB_PREP)
PREPARED_RANGE    = BASE_PREPARED_RANGE    # (151, 182)
PROC_CODES        = set(BASE_PROC_CODES)
FOOD_GROUP_HEADERS = dict(BASE_FOOD_GROUP_HEADERS)

# ── RUNNER RT 2019: sama kolom dengan 2020, mapping r1806 berbeda ─────────────
RUNNER_RT = []
for item in BASE_RUNNER_RT:
    item = dict(item)
    out = item['out']
    if out == 'HomeOwnership':
        item['map'] = {
            '1': 'Milik sendiri', '2': 'Kontrak/sewa',
            '3': 'Bebas sewa',    '4': 'Dinas', '5': 'Lainnya',
        }
    elif out == 'RoofMaterial':
        # ⚠ Kode 3=Asbes, 4=Seng (terbalik dari 2021+)
        item['map'] = {
            '1': 'Beton',    '2': 'Genteng',  '3': 'Asbes',
            '4': 'Seng',     '5': 'Bambu',    '6': 'Kayu/sirap',
            '7': 'Jerami/ijuk/daun-daunan/rumbia', '8': 'Lainnya',
        }
    elif out == 'ToiletType':
        item['map'] = {
            '1': 'Leher angsa', '2': 'Plengsengan dengan tutup',
            '3': 'Plengsengan tanpa tutup', '4': 'Cemplung cubluk',
        }
    elif out == 'WaterSource':
        item['map'] = {
            '1':  'Air kemasan bermerk', '2':  'Air isi ulang',
            '3':  'Leding',              '4':  'Sumur bor/pompa',
            '5':  'Sumur terlindung',    '6':  'Sumur tak terlindung',
            '7':  'Mata air terlindung', '8':  'Mata air tak terlindung',
            '9':  'Air permukaan',       '10': 'Air hujan',
            '11': 'Lainnya',
        }
    elif out == 'AccessEnergy':
        # ⚠ Kode 4 tidak ada, bukan listrik = kode 5
        item['map'] = {
            '1': 'PLN_dengan_meteran', '2': 'PLN_tanpa_meteran',
            '3': 'Non_PLN',            '5': 'Bukan_listrik',
        }
    elif out == 'CookingFuel':
        item['map'] = {
            '0':  'Tidak memasak',        '1':  'Listrik',
            '2':  'Elpiji 5.5kg/bluegaz', '3':  'Elpiji 12kg',
            '4':  'Elpiji 3kg',           '5':  'Gas kota',
            '6':  'Biogas',               '7':  'Minyak tanah',
            '8':  'Briket',               '9':  'Arang',
            '10': 'Kayu bakar',           '11': 'Lainnya',
        }
    RUNNER_RT.append(item)

# Tambah FIES (ada di 2019, nilai 1/5/8/9)
_FIES_MAP = {'1': 'Ya', '5': 'Tidak', '8': 'Tidak tahu', '9': 'Menolak'}
for col, out in [
    ('r1701', 'FoodInsecurity_Worry'),    ('r1702', 'FoodInsecurity_NoHealthy'),
    ('r1703', 'FoodInsecurity_FewKinds'), ('r1704', 'FoodInsecurity_SkipMeal'),
    ('r1705', 'FoodInsecurity_EatLess'),  ('r1706', 'FoodInsecurity_RanOut'),
    ('r1707', 'FoodInsecurity_Hungry'),   ('r1708', 'FoodInsecurity_NoBowl'),
]:
    RUNNER_RT.append(dict(kind='from_rt', out=out, col=col, map=_FIES_MAP))

# ── RUNNER ART 2019 ───────────────────────────────────────────────────────────
# ⚠ Status pekerjaan di R705 (bukan R706 seperti 2021/2022)
# ⚠ R701 (rekening tabungan) belum ada di 2019
RUNNER_ART = []
for item in BASE_RUNNER_ART:
    item = dict(item)
    out = item['out']
    if out == 'StatusPekerjaanKRT':
        item['col'] = 'r705'   # ⚠ 2019: r705, bukan r706
    elif out == 'HasSavingsAccount':
        continue   # ⚠ r701 belum ada di 2019, skip
    RUNNER_ART.append(item)

# AccessCommunication (HP) tetap via r802 — sama
# ⚠ Tidak ada r702 (layanan keuangan digital) di 2019

# ── Kolom ketenagakerjaan 2019 ────────────────────────────────────────────────
# Semua bergeser satu posisi lebih awal dari 2021/2022:
# 2019: R701_A-X=multi-flag, R702=aktivitas, R703=flag, R704=lapangan, R705=status
# 2021: R702_A-X=multi-flag, R703=aktivitas, R704=flag, R705=lapangan, R706=status
EMPLOYMENT = {
    'education_col'   : 'r615',    # ijazah 22 kode (kode berbeda dari 2021+)
    'kip_col'         : 'r616',    # KIP di r616 (sama 2021/2022)
    'savings_col'     : None,      # ⚠ tidak ada di 2019
    'activity_col'    : 'r702',    # kegiatan utama (2021: r703; 2023+: r704)
    'temp_notwork_col': 'r703',    # flag sementara tidak bekerja (2021: r704)
    'sector_col'      : 'r704',    # lapangan usaha (2021: r705; 2023+: r706)
    'status_col'      : 'r705',    # status pekerjaan (2021: r706; 2023+: r707)
    'hours_col'       : 'r706',    # jam kerja (2021: r707; 2023+: r708)
    'working_flag_col': 'r701_a',  # ⚠ 2019: r701_a (2021: r702_a; 2023+: r703_a)
}
