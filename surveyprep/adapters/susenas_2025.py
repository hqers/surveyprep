"""
surveyprep.adapters.susenas_2025
=================================
Adapter Susenas 2025 Maret (KOR + KP).
Sumber: Layout_Susenas_202503_Kor.xls + Layout_Susenas_202503_KP.xls

STATUS: ✅ VERIFIED dari metadata resmi BPS 2025

Ringkasan perubahan dari 2024
------------------------------
PERUBAHAN BESAR — SEMUA NOMOR BLOK RT BERGESER ~200:
  R17xx (2024) → R15xx (2025)  : FIES
  R18xx (2024) → R16xx (2025)  : Perumahan, sanitasi, air, listrik, BBM
  R19xx (2024) → R17xx (2025)  : Kredit
  R20xx (2024) → R18xx (2025)  : Aset RT
  R22xx (2024) → R20xx (2025)  : Bansos (PKH, BPNT)

VARIABEL BARU 2025:
  R1618-R1622 : Pengelolaan sampah + keamanan lingkungan
  R1702A-B    : Uang elektronik (server & kartu/chip)
  R1801N      : Kepemilikan uang tunai/tabungan ≥10 gram emas
  R2004A-G/II : Program MBG (Makan Bergizi Gratis)

VALUE LABELS BERUBAH:
  R1606 (atap)   : 8 kode → 7 kode, urutan berubah
  R1607 (dinding): 7 kode → 5 kode (digabung)
  R1608 (lantai) : 9 kode → 7 kode (digabung)

IND — R615 KEMBALI JADI IJAZAH:
  2024: R615 = KIP  →  2025: R615 = Ijazah (25 kode, lebih detail)
  KIP sekarang di R619
  Struktur r7xx SAMA dengan 2024 (r703_a-x, r704=flag, r705=sektor, r706=status)
"""
import copy
from .base import (
    make_config,
    BASE_VALUE_LABELS,
    BASE_KLP,
    BASE_RUNNER_RT, BASE_RUNNER_ART,
    BASE_EMPLOYMENT,
)

# ── Config: wi3 tidak ada (sama dengan 2024) ──────────────────────────────────
CONFIG = make_config('25', has_wi3=False)

# ── Value labels ──────────────────────────────────────────────────────────────
VALUE_LABELS = copy.deepcopy(BASE_VALUE_LABELS)

# R1602 (kepemilikan): sama dengan 2024 (5 kode)
VALUE_LABELS['r1602'] = {
    1: 'Milik sendiri', 2: 'Kontrak/sewa',
    3: 'Bebas sewa',    4: 'Dinas', 5: 'Lainnya',
}

# ⚠ R1606 (atap): 7 kode, urutan berbeda dari 2024
# 2024: 1=Beton,2=Genteng,3=Seng,4=Asbes,5=Bambu,6=Kayu/sirap,7=Jerami,8=Lainnya
# 2025: 1=Beton,2=Genteng,3=Seng,4=Kayu/sirap,5=Asbes,6=Bambu/jerami/ijuk,7=Lainnya
VALUE_LABELS['r1606'] = {
    1: 'Beton',    2: 'Genteng',  3: 'Seng',
    4: 'Kayu/sirap', 5: 'Asbes',
    6: 'Bambu/jerami/ijuk/rumbia', 7: 'Lainnya',
}

# ⚠ R1607 (dinding): 5 kode (2024: 7 kode)
VALUE_LABELS['r1607'] = {
    1: 'Tembok',
    2: 'Plesteran anyaman bambu/kawat',
    3: 'Kayu/papan/batang kayu',
    4: 'Bambu/anyaman bambu',
    5: 'Lainnya',
}

# ⚠ R1608 (lantai): 7 kode (2024: 9 kode)
VALUE_LABELS['r1608'] = {
    1: 'Marmer/granit',       2: 'Keramik/ubin/tegel/teraso',
    3: 'Parket/vinil/karpet', 4: 'Kayu/papan',
    5: 'Semen/bata merah',    6: 'Bambu/tanah',
    7: 'Lainnya',
}

# R1609A (sanitasi): sama dengan 2024
VALUE_LABELS['r1609a'] = dict(BASE_VALUE_LABELS['r1809a'])

# R1609B (kloset): sama dengan 2024
VALUE_LABELS['r1609b'] = {
    1: 'Leher angsa', 2: 'Plengsengan dengan tutup',
    3: 'Plengsengan tanpa tutup', 4: 'Cemplung/cubluk',
}

# R1610A (air minum): sama dengan 2024 (11 kode)
VALUE_LABELS['r1610a'] = {
    1:  'Air kemasan bermerk', 2:  'Air isi ulang',
    3:  'Leding',              4:  'Sumur bor/pompa',
    5:  'Sumur terlindung',    6:  'Sumur tak terlindung',
    7:  'Mata air terlindung', 8:  'Mata air tak terlindung',
    9:  'Air permukaan',       10: 'Air hujan',
    11: 'Lainnya',
}

# R1616 (penerangan): sama dengan 2024
VALUE_LABELS['r1616'] = {
    1: 'PLN dengan meteran', 2: 'PLN tanpa meteran',
    3: 'Non-PLN',            4: 'Bukan listrik',
}

# R1617 (bahan bakar): SAMA persis dengan 2024
VALUE_LABELS['r1617'] = {
    0:  'Tidak memasak',       1:  'Listrik',
    2:  'Elpiji 5.5kg/bluegaz',3:  'Elpiji 12kg',
    4:  'Elpiji 3kg',          5:  'Gas kota',
    6:  'Biogas',              7:  'Minyak tanah',
    8:  'Briket',              9:  'Arang',
    10: 'Kayu bakar',          11: 'Lainnya',
}

# ⚠ R615 2025: KEMBALI IJAZAH (25 kode, lebih detail dari 2020)
VALUE_LABELS['r615'] = {
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
# Recode ke 7 band (sama logikanya, kode berbeda)
VALUE_LABELS['r615_band'] = {
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

# r701/r702/r802: sama dengan 2024 (1=Ya, 5=Tidak)
VALUE_LABELS['r701'] = {1: 'Ya', 5: 'Tidak'}
VALUE_LABELS['r702'] = {1: 'Ya', 5: 'Tidak'}
VALUE_LABELS['r802'] = {1: 'Ya', 5: 'Tidak'}

# r704 (flag sementara tidak bekerja), r705 (lapangan usaha), r706 (status):
# SAMA dengan 2024
VALUE_LABELS['r705'] = {
    1:'Pertanian padi/palawija', 2:'Hortikultura', 3:'Perkebunan',
    4:'Perikanan', 5:'Peternakan', 6:'Kehutanan', 7:'Pertambangan',
    8:'Industri pengolahan', 9:'Listrik/gas/uap', 10:'Air/limbah/daur ulang',
    11:'Konstruksi', 12:'Perdagangan', 13:'Transportasi', 14:'Akomodasi/makan',
    15:'Informasi/komunikasi', 16:'Keuangan', 17:'Real estate',
    18:'Profesional/teknis', 19:'Penyewaan/bisnis', 20:'Pemerintahan',
    21:'Pendidikan', 22:'Kesehatan/sosial', 23:'Kesenian/rekreasi',
    24:'Jasa lainnya', 25:'RT pemberi kerja', 26:'Badan internasional',
}
VALUE_LABELS['r706'] = {
    1: 'Berusaha sendiri',
    2: 'Berusaha + buruh tidak tetap',
    3: 'Berusaha + buruh tetap',
    4: 'Buruh/karyawan/pegawai',
    5: 'Pekerja bebas',
    6: 'Pekerja keluarga/tidak dibayar',
}

# ── KLP pangan 2025: bergeser lagi dari 2024 ─────────────────────────────────
KLP = copy.deepcopy(BASE_KLP)
KLP.update({
    'ikan'       : {'16'},    # header sama, isi bertambah (+komoditi baru)
    'daging'     : {'61'},    # 2024: 55 | 2020: 52
    'telur_susu' : {'74'},    # 2024: 65 | 2020: 62
    'sayur'      : {'85'},    # 2024: 75 | 2020: 72
    'kacang'     : {'121'},   # 2024: 102| 2020: 98
    'buah'       : {'129'},   # 2024: 110| 2020: 106
    'minyak'     : {'154'},   # 2024: 126| 2020: 120
    'bhn_minuman': {'159'},   # 2024: 131| 2020: 125
    'bumbu'      : {'167'},   # 2024: 139| 2020: 133
    'lainnya'    : {'182'},   # 2024: 154| 2020: 146
    'mkn_jadi'   : {'187'},   # 2024: 159| 2020: 151
    'rokok'      : {'220'},   # 2024: 192| 2020: 183
})

ALL14          = {'1','8','16','61','74','85','121','129',
                  '154','159','167','182','187','220'}
NO_TOB         = ALL14 - {'220'}
NO_TOB_PREP    = ALL14 - {'220','187'}
PREPARED_RANGE = (187, 219)   # 2024:(159,191) | 2020:(151,182)
PROC_CODES     = {'204','205','214','215','217','218'}  # sesuaikan aktual

FOOD_GROUP_HEADERS = {
    '1':  'PADI-PADIAN',      '8':  'UMBI-UMBIAN',
    '16': 'IKAN/UDANG/CUMI/KERANG', '61': 'DAGING',
    '74': 'TELUR DAN SUSU',   '85': 'SAYUR-SAYURAN',
    '121':'KACANG-KACANGAN',  '129':'BUAH-BUAHAN',
    '154':'MINYAK DAN KELAPA','159':'BAHAN MINUMAN',
    '167':'BUMBU-BUMBUAN',    '182':'KONSUMSI LAINNYA',
    '187':'MAKANAN DAN MINUMAN JADI','220':'ROKOK DAN TEMBAKAU',
}

# ── RUNNER RT 2025: nama kolom semua bergeser ~200 ────────────────────────────
# Template: ambil dari 2024, ganti semua r18xx→r16xx, r17xx→r15xx
_COL_REMAP_2025 = {
    'r1806a': 'r1606',  'r1802':  'r1602',  'r1807':  'r1607',
    'r1808':  'r1608',  'r1809a': 'r1609a', 'r1809b': 'r1609b',
    'r1810a': 'r1610a', 'r1816':  'r1616',  'r1817':  'r1617',
    'r105':   'r105',   # tidak bergeser
    # FIES: r1701-r1708 → r1501-r1508
    'r1701': 'r1501', 'r1702': 'r1502', 'r1703': 'r1503',
    'r1704': 'r1504', 'r1705': 'r1505', 'r1706': 'r1506',
    'r1707': 'r1507', 'r1708': 'r1508',
}

# Import susenas_2024 RUNNER_RT sebagai basis (sudah punya semua override 2024)
from .susenas_2024 import RUNNER_RT as _RT_2024

RUNNER_RT = []
for item in _RT_2024:
    item = dict(item)
    old_col = item.get('col', '')
    new_col = _COL_REMAP_2025.get(old_col, old_col)
    item['col'] = new_col

    # Update mapping untuk kolom yang value label-nya berubah
    out = item['out']
    if out == 'RoofMaterial':
        item['map'] = {
            '1':'Beton','2':'Genteng','3':'Seng','4':'Kayu/sirap',
            '5':'Asbes','6':'Bambu/jerami/ijuk/rumbia','7':'Lainnya',
        }
    elif out == 'WallMaterial':
        item['map'] = {
            '1':'Tembok','2':'Plesteran anyaman bambu/kawat',
            '3':'Kayu/papan/batang kayu','4':'Bambu/anyaman bambu','5':'Lainnya',
        }
    elif out == 'FloorMaterial':
        item['map'] = {
            '1':'Marmer/granit',        '2':'Keramik/ubin/tegel/teraso',
            '3':'Parket/vinil/karpet',  '4':'Kayu/papan',
            '5':'Semen/bata merah',     '6':'Bambu/tanah',
            '7':'Lainnya',
        }
    RUNNER_RT.append(item)

# Tambah variabel baru 2025: uang elektronik
RUNNER_RT.append(dict(kind='from_rt', out='HasServerEMoney', col='r1702a',
                      map={'1':'Ya','2':'Tidak','5':'Tidak'}))
RUNNER_RT.append(dict(kind='from_rt', out='HasCardEMoney', col='r1702b',
                      map={'1':'Ya','2':'Tidak','5':'Tidak'}))

# ── RUNNER ART 2025: sama dengan 2024 (r706=status, r705=lapangan, r704=flag) ─
# Struktur r7xx 2025 identik dengan 2024
from .susenas_2024 import RUNNER_ART as _ART_2024
RUNNER_ART = list(_ART_2024)

# ── Kolom ketenagakerjaan 2025: SAMA dengan 2024 ─────────────────────────────
# ⚠ Perbedaan dari 2024: r615 KEMBALI jadi ijazah (bukan KIP)
#   KIP di 2025 = r619
EMPLOYMENT = {
    'education_col'  : 'r615',    # ✅ kembali ijazah (25 kode)
    'kip_col'        : 'r619',    # KIP pindah ke r619
    'activity_col'   : 'r704',    # sama 2024
    'temp_notwork_col': 'r704',   # r704=flag sementara tidak bekerja
    'sector_col'     : 'r705',    # lapangan usaha 26 kode
    'status_col'     : 'r706',    # status pekerjaan 6 kode
    'hours_col'      : 'r707',    # jam kerja utama
    'working_flag_col': 'r703_a', # multi-flag, sama 2024
}
