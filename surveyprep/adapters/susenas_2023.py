"""
surveyprep.adapters.susenas_2023
=================================
Adapter Susenas 2023 Maret (KOR + KP).
Sumber: Layout_data_Susenas_202303_Kor.xlsx + Layout_data_Susenas_202303_KP.xlsx

STATUS: ✅ VERIFIED dari layout resmi BPS 2023

Ringkasan perubahan dari 2020 (basis)
--------------------------------------
RT — STRUKTUR:
  Sama dengan 2024: R17xx, R18xx, R19xx, R20xx, R22xx
  wi3 tidak ada di RT (sama dengan 2024)

RT — VALUE LABELS BERUBAH:
  R1802 (kepemilikan) : 7 kode (2020) → 5 kode (mulai 2022/2023)
  R1806 (atap)        : 7 kode (2020) → 8 kode (Bambu dipisah, Jerami lebih detail)
  R1809B (kloset)     : 4 kode, kode 4 berubah (Cemplung cubluk, bukan Tidak ada)
  R1810A (air minum)  : 12 kode (2020) → 11 kode (Leding eceran hilang)
  R1816 (penerangan)  : label kode 2 berubah (PLN tanpa meteran)
  R1817 (bahan bakar) : 11 kode (sama dengan 2024, 0-11, Elpiji 12kg kode 3)

IND — PERUBAHAN:
  R614 = ijazah tertinggi (25 kode, bukan r615!)
  R615 = KIP (bukan ijazah)
  R703_A-X: multi-flag (sama 2024)
  R704    : kegiatan utama (sama 2024)
  R705    : flag sementara tidak bekerja (sama 2024)
  R706    : lapangan usaha 26 kode (sama 2024)
  R707    : status pekerjaan 6 kode (sama 2024)
  R701/R702/R802: 1=Ya, 5=Tidak (sama 2024)

KP41 2023: 197 komoditi (sama dengan 2024)
KLP headers: sama dengan 2024
  Daging=55, Telur=65, Sayur=75, Kacang=102, Buah=110,
  Minyak=126, BhnMinum=131, Bumbu=139, Lainnya=154, MknJadi=159, Rokok=192

Perbedaan dengan 2024:
  - R1806 (atap): 2023=8 kode (Bambu TERPISAH dari Jerami), 2024=8 kode SAMA
  - R1807 (dinding): 2023=7 kode, 2024=7 kode SAMA
  - R1808 (lantai): 2023=9 kode, 2024=9 kode SAMA
  - Education col: 2023=R614 (ijazah), 2024=R613 (ijazah)
    [Di 2023: R614=ijazah, R615=KIP]
    [Di 2024: R613=ijazah (5 kode kasar), R615=KIP]
  - R1901J: 2023=Lainnya (bukan PNM-Mekaar), 2024=PNM-Mekaar ada di R1901J
    [2023 tidak ada R1901K; 2024 ada R1901J=PNM-Mekaar + R1901K=Lainnya]
  - FIES (R1701-R1708): ada di 2023, nilai: 1=Ya, 5=Tidak, 8=Tidak tahu, 9=Menolak
"""
import copy
from .base import (
    make_config,
    BASE_VALUE_LABELS,
    BASE_KLP,
    BASE_RUNNER_RT, BASE_RUNNER_ART,
    BASE_EMPLOYMENT,
)

# ── Config: wi3 tidak ada ─────────────────────────────────────────────────────
CONFIG = make_config('23', has_wi3=False)

# ── Value labels ──────────────────────────────────────────────────────────────
VALUE_LABELS = copy.deepcopy(BASE_VALUE_LABELS)

# ⚠ R1802: 5 kode (sama dengan 2024)
VALUE_LABELS['r1802'] = {
    1: 'Milik sendiri', 2: 'Kontrak/sewa',
    3: 'Bebas sewa',    4: 'Dinas', 5: 'Lainnya',
}

# ⚠ R1806 (atap): 8 kode — Bambu TERPISAH dari Jerami
# [2024: urutan berbeda — 4=Asbes, 5=Bambu; 2023: 5=Bambu, 6=Kayu/sirap terpisah]
VALUE_LABELS['r1806'] = {
    1: 'Beton',    2: 'Genteng',  3: 'Seng',
    4: 'Asbes',    5: 'Bambu',    6: 'Kayu/sirap',
    7: 'Jerami/ijuk/daun-daunan/rumbia', 8: 'Lainnya',
}

# R1807 (dinding): 7 kode — sama dengan 2020
VALUE_LABELS['r1807'] = dict(BASE_VALUE_LABELS['r1807'])

# R1808 (lantai): 9 kode — sama dengan 2020
VALUE_LABELS['r1808'] = dict(BASE_VALUE_LABELS['r1808'])

# R1809A (sanitasi): sama dengan 2024
VALUE_LABELS['r1809a'] = {
    1: 'Sendiri',              2: 'Bersama RT tertentu',
    3: 'MCK komunal',          4: 'MCK/WC umum',
    5: 'Ada tapi tidak digunakan', 6: 'Tidak ada',
}

# ⚠ R1809B (kloset): 4 kode, kode 4=Cemplung (bukan "Tidak ada" seperti 2020)
VALUE_LABELS['r1809b'] = {
    1: 'Leher angsa', 2: 'Plengsengan dengan tutup',
    3: 'Plengsengan tanpa tutup', 4: 'Cemplung cubluk',
}

# ⚠ R1810A (air): 11 kode (Leding eceran hilang, sama dengan 2024)
VALUE_LABELS['r1810a'] = {
    1:  'Air kemasan bermerk', 2:  'Air isi ulang',
    3:  'Leding',              4:  'Sumur bor/pompa',
    5:  'Sumur terlindung',    6:  'Sumur tak terlindung',
    7:  'Mata air terlindung', 8:  'Mata air tak terlindung',
    9:  'Air permukaan',       10: 'Air hujan',
    11: 'Lainnya',
}

# ⚠ R1816 (penerangan): label kode 2 berubah (sama dengan 2024)
VALUE_LABELS['r1816'] = {
    1: 'PLN dengan meteran', 2: 'PLN tanpa meteran',
    3: 'Non-PLN',            4: 'Bukan listrik',
}

# ⚠ R1817 (bahan bakar): 11 kode, sama dengan 2024
VALUE_LABELS['r1817'] = {
    0:  'Tidak memasak',       1:  'Listrik',
    2:  'Elpiji 5.5kg/bluegaz',3:  'Elpiji 12kg',
    4:  'Elpiji 3kg',          5:  'Gas kota',
    6:  'Biogas',              7:  'Minyak tanah',
    8:  'Briket',              9:  'Arang',
    10: 'Kayu bakar',          11: 'Lainnya',
}

# FIES 2023: 1=Ya, 5=Tidak, 8=Tidak tahu, 9=Menolak
VALUE_LABELS['r1701_fies'] = {1: 'Ya', 5: 'Tidak', 8: 'Tidak tahu', 9: 'Menolak'}

# ⚠ R614 = ijazah 25 kode (di 2023, bukan R615!)
VALUE_LABELS['r614_ijazah'] = {
    1:  'Paket A',    2:  'SDLB',       3:  'SD',
    4:  'MI',         5:  'SPM/PDF Ula',6:  'Paket B',
    7:  'SMPLB',      8:  'SMP',        9:  'MTs',
    10: 'SPM/PDF Wustha', 11: 'Paket C',12: 'SMLB',
    13: 'SMA',        14: 'MA',         15: 'SMK',
    16: 'MAK',        17: 'SPM/PDF Ulya',18: 'D1/D2',
    19: 'D3',         20: 'D4',         21: 'S1',
    22: 'Profesi',    23: 'S2',         24: 'S3',
    25: 'Tidak Punya Ijazah SD',
}
# Band 7 level (sama dengan 2025)
VALUE_LABELS['r614_band'] = {
    1:  'Tidak_Tamat_SD', 2:  'SD',      3:  'SD',
    4:  'SD',             5:  'SD',      6:  'SMP',
    7:  'SMP',            8:  'SMP',     9:  'SMP',
    10: 'SMP',            11: 'SMA',     12: 'SMA',
    13: 'SMA',            14: 'SMA',     15: 'SMA',
    16: 'SMA',            17: 'SMA',     18: 'Diploma',
    19: 'Diploma',        20: 'S1',      21: 'S1',
    22: 'S1',             23: 'S2_S3',   24: 'S2_S3',
    25: 'Tidak_Tamat_SD',
}

# R615 di 2023 = KIP (bukan ijazah)
VALUE_LABELS['r615'] = {1: 'Ya, ditunjukkan', 2: 'Ya, tdk ditunjukkan', 5: 'Tidak'}

# r701/r702/r802: 1=Ya, 5=Tidak (sama 2024)
VALUE_LABELS['r701'] = {1: 'Ya', 5: 'Tidak'}
VALUE_LABELS['r702'] = {1: 'Ya', 5: 'Tidak'}
VALUE_LABELS['r802'] = {1: 'Ya', 5: 'Tidak'}

# r704, r705, r706, r707: sama dengan 2024
VALUE_LABELS['r704'] = {1: 'Bekerja', 2: 'Sekolah', 3: 'Mengurus RT', 4: 'Lainnya'}
VALUE_LABELS['r705'] = {1: 'Ya', 5: 'Tidak'}
VALUE_LABELS['r706'] = {
    1:'Pertanian padi/palawija', 2:'Hortikultura', 3:'Perkebunan',
    4:'Perikanan', 5:'Peternakan', 6:'Kehutanan', 7:'Pertambangan',
    8:'Industri pengolahan', 9:'Listrik/gas/uap', 10:'Air/limbah/daur ulang',
    11:'Konstruksi', 12:'Perdagangan', 13:'Transportasi', 14:'Akomodasi/makan',
    15:'Informasi/komunikasi', 16:'Keuangan', 17:'Real estate',
    18:'Profesional/teknis', 19:'Penyewaan/bisnis', 20:'Pemerintahan',
    21:'Pendidikan', 22:'Kesehatan/sosial', 23:'Kesenian/rekreasi',
    24:'Jasa lainnya', 25:'RT pemberi kerja', 26:'Badan internasional',
}
VALUE_LABELS['r707'] = {
    1: 'Berusaha sendiri',
    2: 'Berusaha + buruh tidak tetap',
    3: 'Berusaha + buruh tetap',
    4: 'Buruh/karyawan/pegawai',
    5: 'Pekerja bebas',
    6: 'Pekerja keluarga/tidak dibayar',
}

# ── KLP pangan 2023: SAMA persis dengan 2024 ─────────────────────────────────
# 197 komoditi, KLP headers: 55=Daging, 65=Telur, 75=Sayur, 102=Kacang,
# 110=Buah, 126=Minyak, 131=BhnMinum, 139=Bumbu, 154=Lainnya, 159=MknJadi, 192=Rokok
KLP = copy.deepcopy(BASE_KLP)
KLP.update({
    'daging'     : {'55'},
    'telur_susu' : {'65'},
    'sayur'      : {'75'},
    'kacang'     : {'102'},
    'buah'       : {'110'},
    'minyak'     : {'126'},
    'bhn_minuman': {'131'},
    'bumbu'      : {'139'},
    'lainnya'    : {'154'},
    'mkn_jadi'   : {'159'},
    'rokok'      : {'192'},
})

ALL14          = {'1','8','16','55','65','75','102','110',
                  '126','131','139','154','159','192'}
NO_TOB         = ALL14 - {'192'}
NO_TOB_PREP    = ALL14 - {'192','159'}
PREPARED_RANGE = (159, 191)
PROC_CODES     = {'176','177','186','187','189','190'}

FOOD_GROUP_HEADERS = {
    '1':  'PADI-PADIAN',      '8':  'UMBI-UMBIAN',
    '16': 'IKAN',             '55': 'DAGING',
    '65': 'TELUR DAN SUSU',   '75': 'SAYUR-SAYURAN',
    '102':'KACANG-KACANGAN',  '110':'BUAH-BUAHAN',
    '126':'MINYAK DAN KELAPA','131':'BAHAN MINUMAN',
    '139':'BUMBU-BUMBUAN',    '154':'KONSUMSI LAINNYA',
    '159':'MAKANAN DAN MINUMAN JADI','192':'ROKOK DAN TEMBAKAU',
}

# ── RUNNER RT 2023: nama kolom sama dengan 2024 (R18xx, R17xx) ───────────────
# Gunakan RUNNER dari 2024 sebagai basis, hanya update mapping r1806 (atap)
from .susenas_2024 import RUNNER_RT as _RT_2024

RUNNER_RT = []
for item in _RT_2024:
    item = dict(item)
    out = item['out']
    if out == 'RoofMaterial':
        # 2023: Bambu terpisah dari Jerami (8 kode, urutan sama seperti 2024 tapi kode 5=Bambu)
        item['col'] = 'r1806'   # 2023: r1806 (bukan r1806a seperti di 2024)
        item['map'] = {
            '1':'Beton',   '2':'Genteng', '3':'Seng',
            '4':'Asbes',   '5':'Bambu',   '6':'Kayu/sirap',
            '7':'Jerami/ijuk/daun-daunan/rumbia', '8':'Lainnya',
        }
    elif out == 'WallMaterial':
        # 2023: 7 kode (sama 2020, bukan 5 kode seperti 2025)
        item['map'] = {
            '1':'Tembok',          '2':'Plesteran anyaman bambu/kawat',
            '3':'Kayu/papan',      '4':'Anyaman bambu',
            '5':'Batang kayu',     '6':'Bambu', '7':'Lainnya',
        }
    elif out == 'FloorMaterial':
        # 2023: 9 kode (sama 2020, bukan 7 kode seperti 2025)
        item['map'] = {
            '1':'Marmer/Granit', '2':'Keramik',        '3':'Parket/Vinil',
            '4':'Ubin/Tegel',    '5':'Kayu/Papan',     '6':'Semen/Bata merah',
            '7':'Bambu',         '8':'Tanah',           '9':'Lainnya',
        }
    elif out in ('FoodInsecurity_Worry','FoodInsecurity_NoHealthy',
                 'FoodInsecurity_FewKinds','FoodInsecurity_SkipMeal',
                 'FoodInsecurity_EatLess','FoodInsecurity_RanOut',
                 'FoodInsecurity_Hungry','FoodInsecurity_NoBowl'):
        # FIES 2023: 1=Ya, 5=Tidak, 8=Tidak tahu, 9=Menolak
        item['map'] = {'1':'Ya','5':'Tidak','8':'Tidak tahu','9':'Menolak'}
    RUNNER_RT.append(item)

# ── RUNNER ART 2023: sama dengan 2024 (r707=status, r706=lapangan) ───────────
from .susenas_2024 import RUNNER_ART as _ART_2024
RUNNER_ART = list(_ART_2024)

# ── Kolom ketenagakerjaan 2023 ────────────────────────────────────────────────
# ⚠ Perbedaan dari 2024: ijazah di R614 (bukan R613)
EMPLOYMENT = {
    'education_col'  : 'r614',    # ⚠ 2023: R614 = ijazah (25 kode)
    'kip_col'        : 'r615',    # KIP di R615
    'activity_col'   : 'r704',    # sama 2024
    'temp_notwork_col': 'r705',   # sama 2024
    'sector_col'     : 'r706',    # sama 2024
    'status_col'     : 'r707',    # sama 2024
    'hours_col'      : 'r708',    # sama 2024
    'working_flag_col': 'r703_a', # sama 2024
}
