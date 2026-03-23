"""
surveyprep.adapters.susenas_2021
=================================
Adapter Susenas 2021 Maret (KOR + KP).
Sumber: Metadata_Susenas_202103_Kor.xlsx + Metadata_Susenas_202103_KP.xls

STATUS: ✅ VERIFIED dari metadata resmi BPS 2021

Posisi 2021 dalam kronologi perubahan
---------------------------------------
2021 adalah TAHUN TRANSISI antara 2020 dan 2023/2024.
Sebagian besar sudah berubah dari 2020, tetapi BELUM ke format 2023+.

Perubahan dari 2020
--------------------
RT:
  R1802  : 7 kode → 5 kode (Kontrak+Sewa digabung, mulai 2021)
  R1806  : 7 kode → 8 kode (Bambu dipisah dari Sirap)
  R1809B : 4 kode, kode 4 = Cemplung cubluk (bukan "Tidak ada" spt 2020)
  R1810A : 12 kode → 11 kode (Leding eceran hilang, digabung ke Leding)
  R1816  : label kode 2 berubah ("PLN tanpa meteran")
  R1817  : 11 kode (0-11), Elpiji 12kg = kode 3 (sama dengan 2023+)
  FIES   : R1701-R1708 ADA di 2021 (sama dengan 2023)
           Nilai: 1=Ya, 5=Tidak, 8=Tidak tahu, 9=Menolak
  wi3    : TIDAK ADA di RT (sudah hilang sejak 2021)
  PSU/SSU/STRATA: ada (sama 2020)
  RENUM  : kunci join (sama dengan 2020, bukan URUT seperti 2024+)

IND — PERBEDAAN BESAR dari 2023+:
  R615   : IJAZAH (22 kode, bukan 25)!  ← sama seperti 2020
           [2021: R615=ijazah, R616=KIP]
           [2023: R614=ijazah, R615=KIP]
           [2025: R615=ijazah kembali (25 kode)]
  R616   : KIP (1=Ya ditunjukkan, 2=Ya tdk ditunjukkan, 5=Tidak)
  R702_A-X: multi-flag kegiatan (bukan R703_A-X seperti 2023+!)
  R703   : kegiatan utama (1 kolom, bukan R704 seperti 2023+)
  R704   : flag sementara tidak bekerja (bukan R705 seperti 2023+)
  R705   : lapangan usaha 26 kode (bukan R706 seperti 2023+)
  R706   : status pekerjaan 6 kode (bukan R707 seperti 2023+)
  R701   : rekening tabungan (1=Ya, 5=Tidak — sama 2023+)
  R802   : HP (1=Ya, 5=Tidak — sama 2023+)
  R702   : BELUM ADA di 2021 (layanan keuangan digital, muncul di 2023)

KP41 2021: 188 komoditi — SAMA dengan 2020!
  KLP rokok = 183, KLP daging = 52 (belum bergeser)
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

# ── Config: wi3 tidak ada, renum masih ada ───────────────────────────────────
CONFIG = make_config('21', has_wi3=False)

# ── Value labels ──────────────────────────────────────────────────────────────
VALUE_LABELS = copy.deepcopy(BASE_VALUE_LABELS)

# ⚠ R1802: 5 kode (mulai 2021, sama dengan 2023+)
VALUE_LABELS['r1802'] = {
    1: 'Milik sendiri', 2: 'Kontrak/sewa',
    3: 'Bebas sewa',    4: 'Dinas', 5: 'Lainnya',
}

# ⚠ R1806 (atap): 8 kode, Bambu dipisah — sama dengan 2023
VALUE_LABELS['r1806'] = {
    1: 'Beton',    2: 'Genteng',  3: 'Seng',
    4: 'Asbes',    5: 'Bambu',    6: 'Kayu/sirap',
    7: 'Jerami/ijuk/daun-daunan/rumbia', 8: 'Lainnya',
}

# R1807 (dinding): 7 kode — sama dengan 2020 dan 2023
# (tidak berubah dari base)

# R1808 (lantai): 9 kode — sama dengan 2020 dan 2023
# (tidak berubah dari base)

# R1809A: sama dengan 2023
VALUE_LABELS['r1809a'] = {
    1: 'Sendiri',              2: 'Bersama RT tertentu',
    3: 'MCK komunal',          4: 'MCK/WC umum',
    5: 'Ada tapi tidak digunakan', 6: 'Tidak ada',
}

# ⚠ R1809B: kode 4 = Cemplung cubluk (bukan "Tidak ada" seperti 2020)
VALUE_LABELS['r1809b'] = {
    1: 'Leher angsa', 2: 'Plengsengan dengan tutup',
    3: 'Plengsengan tanpa tutup', 4: 'Cemplung cubluk',
}

# ⚠ R1810A: 11 kode (Leding eceran hilang) — sama dengan 2023+
VALUE_LABELS['r1810a'] = {
    1:  'Air kemasan bermerk', 2:  'Air isi ulang',
    3:  'Leding',              4:  'Sumur bor/pompa',
    5:  'Sumur terlindung',    6:  'Sumur tak terlindung',
    7:  'Mata air terlindung', 8:  'Mata air tak terlindung',
    9:  'Air permukaan',       10: 'Air hujan',
    11: 'Lainnya',
}

# ⚠ R1816: label kode 2 berubah — sama dengan 2023+
VALUE_LABELS['r1816'] = {
    1: 'PLN dengan meteran', 2: 'PLN tanpa meteran',
    3: 'Non-PLN',            4: 'Bukan listrik',
}

# ⚠ R1817: 11 kode, Elpiji 12kg = kode 3 — sama dengan 2023+
VALUE_LABELS['r1817'] = {
    0:  'Tidak memasak',       1:  'Listrik',
    2:  'Elpiji 5.5kg/bluegaz',3:  'Elpiji 12kg',
    4:  'Elpiji 3kg',          5:  'Gas kota',
    6:  'Biogas',              7:  'Minyak tanah',
    8:  'Briket',              9:  'Arang',
    10: 'Kayu bakar',          11: 'Lainnya',
}

# FIES 2021: 1=Ya, 5=Tidak, 8=Tidak tahu, 9=Menolak (sama 2023)
VALUE_LABELS['r1701_fies'] = {1: 'Ya', 5: 'Tidak', 8: 'Tidak tahu', 9: 'Menolak'}

# ⚠ R615 di 2021 = IJAZAH (22 kode, sama persis 2020!)
VALUE_LABELS['r615'] = dict(BASE_VALUE_LABELS['r615_ijazah'])

# ⚠ R616 di 2021 = KIP (bukan R615 seperti 2023, bukan R619 seperti 2025)
VALUE_LABELS['r616'] = {1: 'Ya, ditunjukkan', 2: 'Ya, tdk ditunjukkan', 5: 'Tidak'}

# R701: rekening tabungan (1=Ya, 5=Tidak — sama 2023+)
VALUE_LABELS['r701'] = {1: 'Ya', 5: 'Tidak'}
VALUE_LABELS['r802'] = {1: 'Ya', 5: 'Tidak'}

# ⚠ R703-R706 di 2021: SATU POSISI LEBIH AWAL dari 2023+
# 2021: R703=aktivitas utama, R704=flag, R705=lapangan, R706=status
# 2023: R704=aktivitas utama, R705=flag, R706=lapangan, R707=status
VALUE_LABELS['r703'] = {1: 'Bekerja', 2: 'Sekolah', 3: 'Mengurus RT', 4: 'Lainnya'}
VALUE_LABELS['r704'] = {1: 'Ya', 5: 'Tidak'}   # flag sementara tidak bekerja
VALUE_LABELS['r705'] = {                          # lapangan usaha 26 kode
    1:'Pertanian padi/palawija', 2:'Hortikultura', 3:'Perkebunan',
    4:'Perikanan', 5:'Peternakan', 6:'Kehutanan', 7:'Pertambangan',
    8:'Industri pengolahan', 9:'Listrik/gas/uap', 10:'Air/limbah/daur ulang',
    11:'Konstruksi', 12:'Perdagangan', 13:'Transportasi', 14:'Akomodasi/makan',
    15:'Informasi/komunikasi', 16:'Keuangan', 17:'Real estate',
    18:'Profesional/teknis', 19:'Penyewaan/bisnis', 20:'Pemerintahan',
    21:'Pendidikan', 22:'Kesehatan/sosial', 23:'Kesenian/rekreasi',
    24:'Jasa lainnya', 25:'RT pemberi kerja', 26:'Badan internasional',
}
VALUE_LABELS['r706'] = {                          # status pekerjaan 6 kode
    1: 'Berusaha sendiri',
    2: 'Berusaha + buruh tidak tetap',
    3: 'Berusaha + buruh tetap',
    4: 'Buruh/karyawan/pegawai',
    5: 'Pekerja bebas',
    6: 'Pekerja keluarga/tidak dibayar',
}

# ── KLP pangan 2021: SAMA dengan 2020 (188 komoditi) ─────────────────────────
KLP               = copy.deepcopy(BASE_KLP)   # semua sama dengan 2020
ALL14             = set(BASE_ALL14)
NO_TOB            = set(BASE_NO_TOB)
NO_TOB_PREP       = set(BASE_NO_TOB_PREP)
PREPARED_RANGE    = BASE_PREPARED_RANGE        # (151, 182)
PROC_CODES        = set(BASE_PROC_CODES)
FOOD_GROUP_HEADERS = dict(BASE_FOOD_GROUP_HEADERS)

# ── RUNNER RT 2021 ────────────────────────────────────────────────────────────
# Nama kolom SAMA dengan 2020/2023 (r1806, r1802, dst.)
# Hanya mapping yang berubah (r1802, r1806, r1809b, r1810a, r1816, r1817)
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
        item['map'] = {
            '1':'Beton', '2':'Genteng', '3':'Seng', '4':'Asbes',
            '5':'Bambu', '6':'Kayu/sirap',
            '7':'Jerami/ijuk/daun-daunan/rumbia', '8':'Lainnya',
        }
    elif out == 'ToiletType':
        item['map'] = {
            '1':'Leher angsa', '2':'Plengsengan dengan tutup',
            '3':'Plengsengan tanpa tutup', '4':'Cemplung cubluk',
        }
    elif out == 'WaterSource':
        item['map'] = {
            '1': 'Air kemasan bermerk', '2': 'Air isi ulang',
            '3': 'Leding',              '4': 'Sumur bor/pompa',
            '5': 'Sumur terlindung',    '6': 'Sumur tak terlindung',
            '7': 'Mata air terlindung', '8': 'Mata air tak terlindung',
            '9': 'Air permukaan',       '10':'Air hujan',
            '11':'Lainnya',
        }
    elif out == 'AccessEnergy':
        item['map'] = {
            '1': 'PLN_dengan_meteran', '2': 'PLN_tanpa_meteran',
            '3': 'Non_PLN',            '4': 'Bukan_listrik',
        }
    elif out == 'CookingFuel':
        item['map'] = {
            '0': 'Tidak memasak',       '1': 'Listrik',
            '2': 'Elpiji 5.5kg/bluegaz','3': 'Elpiji 12kg',
            '4': 'Elpiji 3kg',          '5': 'Gas kota',
            '6': 'Biogas',              '7': 'Minyak tanah',
            '8': 'Briket',              '9': 'Arang',
            '10':'Kayu bakar',          '11':'Lainnya',
        }
    RUNNER_RT.append(item)

# Tambah FIES (ada di 2021, nilai 1/5/8/9)
_FIES_MAP = {'1':'Ya', '5':'Tidak', '8':'Tidak tahu', '9':'Menolak'}
for col, out in [
    ('r1701','FoodInsecurity_Worry'),   ('r1702','FoodInsecurity_NoHealthy'),
    ('r1703','FoodInsecurity_FewKinds'),('r1704','FoodInsecurity_SkipMeal'),
    ('r1705','FoodInsecurity_EatLess'), ('r1706','FoodInsecurity_RanOut'),
    ('r1707','FoodInsecurity_Hungry'),  ('r1708','FoodInsecurity_NoBowl'),
]:
    RUNNER_RT.append(dict(kind='from_rt', out=out, col=col, map=_FIES_MAP))

# ── RUNNER ART 2021 ───────────────────────────────────────────────────────────
# ⚠ Perbedaan dari 2023+:
#   - Status pekerjaan di r706 (bukan r707)
#   - HP masih 1=Ya, 5=Tidak (sudah sama sejak 2021)
#   - Tidak ada r702 (layanan keuangan digital belum ada di 2021)
RUNNER_ART = []
for item in BASE_RUNNER_ART:
    item = dict(item)
    # BASE sudah pakai r706 untuk StatusPekerjaanKRT — benar untuk 2021
    # (2023+ pakai r707, tapi 2021 masih r706)
    RUNNER_ART.append(item)

# ── Kolom ketenagakerjaan 2021 ────────────────────────────────────────────────
# ⚠ BERBEDA dari 2020 DAN 2023+:
#   R702_A/B/C/D/X = multi-flag kegiatan (bukan R703_A-X seperti 2023+)
#   R703 = kegiatan utama (bukan R704 seperti 2023+)
#   R704 = flag tidak bekerja (bukan R705)
#   R705 = lapangan usaha (bukan R706)
#   R706 = status pekerjaan (bukan R707)
EMPLOYMENT = {
    'education_col'   : 'r615',    # ijazah 22 kode (sama 2020)
    'kip_col'         : 'r616',    # KIP di r616 (2023: r615; 2025: r619)
    'activity_col'    : 'r703',    # kegiatan utama (2023+: r704)
    'temp_notwork_col': 'r704',    # flag sementara tidak bekerja (2023+: r705)
    'sector_col'      : 'r705',    # lapangan usaha (2023+: r706)
    'status_col'      : 'r706',    # status pekerjaan (2023+: r707)
    'hours_col'       : 'r707',    # jam kerja utama (2023+: r708)
    'working_flag_col': 'r702_a',  # ⚠ 2021: r702_a (bukan r703_a seperti 2023+)
}
