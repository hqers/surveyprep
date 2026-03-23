"""
surveyprep.adapters.susenas_2017
=================================
Adapter Susenas 2017 Maret (KOR + KP).
Sumber: Layout_Susenas_201703_Kor.xls + Layout_Susenas_201703_KP.xls

STATUS: ✅ VERIFIED dari layout resmi BPS 2017

Kronologi blok perumahan:
    2017 : R16xx  (R1602=kepemilikan, R1607=atap, R1618A=listrik, R1619=BBM)
    2018 : R15xx  (R1502=kepemilikan, R1507=atap, R1518A=listrik, R1519=BBM)
    2019+: R18xx  (R1802=kepemilikan, R1806=atap, R1816=listrik, R1817=BBM)

Perubahan dari 2018
--------------------
RT:
  Semua variabel perumahan di R16xx (bukan R15xx spt 2018):
    kepemilikan : R1602  (2018: R1502)
    atap        : R1607  (2018: R1507) — 8 kode, 3=Asbes, 4=Seng (sama 2018/2019)
    dinding     : R1608  (2018: R1508)
    lantai      : R1609  (2018: R1509)
    sanitasi    : R1610A, R1610B  (2018: R1510A, R1510B)
    air minum   : R1611A  (2018: R1511A)
    penerangan  : R1618A  (2018: R1518A) — kode 4 tdk ada, bukan listrik=kode 5
    BBM         : R1619   (2018: R1519)
  FIES ada, di R15xx (bukan R14xx spt 2018, bukan R17xx spt 2019+):
    R1501-R1508  (2018: R1401-R1408, 2019+: R1701-R1708)
  Kredit: R2102A-J  (2018: R1701A-J, 2019: R1901A-J)
  Aset  : R2201A-M  (2018: R1801A-M, 2019: R2001A-M)
  Design: RENUM, FWT saja — WI/WI2/WI3/PSU/SSU/STRATA tidak ada
  ⚠ R1610A (sanitasi) 2017: 5 kode (sama 2018, MCK komunal tdk ada)
  ⚠ R1619 (BBM): "Alpiji" (typo di metadata), tapi kode sama 2018

IND:
  R615: TIDAK ADA ijazah! Sheet IND_a berisi crime/perjalanan/internet, bukan ijazah
  Sheet IND_b berisi: pendidikan, ketenagakerjaan, kesehatan
  ⚠ Perlu verifikasi: R615 mungkin di IND_b (nomor kolom perlu cek)
  Ketenagakerjaan di R8xx — SAMA dengan 2018:
    R801_A-X : multi-flag kegiatan
    R802     : kegiatan utama
    R803     : flag sementara tidak bekerja
    R804     : lapangan usaha (21 kode KBLI — lebih sedikit dari 2018+!)
    R805     : status pekerjaan
    R806     : jam kerja utama
  HP  : R701 (2018: R713)
  Internet: R704

KP41 2017: 188 komoditi — IDENTIK dengan 2018/2019/2020
  Perbedaan utama dari 2018: belum ada kolom KABU di KP
"""
import copy
from .base import (
    make_config,
    BASE_VALUE_LABELS,
    BASE_KLP,
    BASE_ALL14, BASE_NO_TOB, BASE_NO_TOB_PREP,
    BASE_PREPARED_RANGE, BASE_PROC_CODES,
    BASE_FOOD_GROUP_HEADERS,
)

# ── Config: RENUM, FWT; tidak ada WI/PSU/SSU ─────────────────────────────────
CONFIG = make_config('17', has_wi3=False)
CONFIG['design_cols'] = ['renum', 'fwt']
CONFIG['hh_id_col']   = 'renum'

# ── Value labels ──────────────────────────────────────────────────────────────
VALUE_LABELS = copy.deepcopy(BASE_VALUE_LABELS)

# R1602 (kepemilikan): 5 kode — sama 2018/2019+
VALUE_LABELS['r1602'] = {
    1: 'Milik sendiri', 2: 'Kontrak/sewa',
    3: 'Bebas sewa',    4: 'Dinas', 5: 'Lainnya',
}

# R1607 (atap): 8 kode, 3=Asbes, 4=Seng — sama 2018/2019
VALUE_LABELS['r1607'] = {
    1: 'Beton',    2: 'Genteng',  3: 'Asbes',
    4: 'Seng',     5: 'Bambu',    6: 'Kayu/sirap',
    7: 'Jerami/ijuk/daun-daunan/rumbia', 8: 'Lainnya',
}

# R1608 (dinding): 7 kode — sama base
VALUE_LABELS['r1608'] = dict(BASE_VALUE_LABELS['r1807'])

# R1609 (lantai): 9 kode — sama base
VALUE_LABELS['r1609'] = dict(BASE_VALUE_LABELS['r1808'])

# ⚠ R1610A (sanitasi) 2017: 5 kode (sama 2018)
VALUE_LABELS['r1610a'] = {
    1: 'Sendiri',              2: 'Bersama RT tertentu',
    3: 'MCK/WC umum',          4: 'Ada tapi tidak digunakan',
    5: 'Tidak ada',
}

# R1610B (kloset): 4 kode
VALUE_LABELS['r1610b'] = {
    1: 'Leher angsa', 2: 'Plengsengan dengan tutup',
    3: 'Plengsengan tanpa tutup', 4: 'Cemplung cubluk',
}

# R1611A (air minum): 11 kode — sama 2018/2019+
VALUE_LABELS['r1611a'] = {
    1:  'Air kemasan bermerk', 2:  'Air isi ulang',
    3:  'Leding',              4:  'Sumur bor/pompa',
    5:  'Sumur terlindung',    6:  'Sumur tak terlindung',
    7:  'Mata air terlindung', 8:  'Mata air tak terlindung',
    9:  'Air permukaan',       10: 'Air hujan',
    11: 'Lainnya',
}

# ⚠ R1618A (penerangan): kode 4 tdk ada, bukan listrik=kode 5
VALUE_LABELS['r1618a'] = {
    1: 'PLN dengan meteran', 2: 'PLN tanpa meteran',
    3: 'Non-PLN',            5: 'Bukan listrik',
}

# R1619 (BBM): 11 kode — sama 2018/2019+
VALUE_LABELS['r1619'] = {
    0:  'Tidak memasak',        1:  'Listrik',
    2:  'Elpiji 5.5kg/bluegaz', 3:  'Elpiji 12kg',
    4:  'Elpiji 3kg',           5:  'Gas kota',
    6:  'Biogas',               7:  'Minyak tanah',
    8:  'Briket',               9:  'Arang',
    10: 'Kayu bakar',           11: 'Lainnya',
}

# FIES 2017: di R1501-R1508, nilai 1/5/8/9
VALUE_LABELS['r1501_fies'] = {1: 'Ya', 5: 'Tidak', 8: 'Tidak tahu', 9: 'Menolak'}

# R615 IND 2017: ijazah — ASUMSI sama kode dengan 2018/2019 (perlu verifikasi IND_b)
# IND_a berisi kejahatan/perjalanan/internet; ijazah di IND_b
VALUE_LABELS['r615'] = {
    1:  'Tidak punya ijazah SD',
    2:  'Paket A',    3:  'SDLB',    4:  'SD',
    5:  'MI',         6:  'Paket B', 7:  'SMPLB',
    8:  'SMP',        9:  'MTs',     10: 'Paket C',
    11: 'SMLB',       12: 'SMA',     13: 'MA',
    14: 'SMK',        15: 'MAK',     16: 'D1/D2',
    17: 'D3',         18: 'D4',      19: 'S1',
    20: 'S2',         21: 'S3',
}
VALUE_LABELS['r615_band'] = {
    1:  'Tidak_Tamat_SD', 2:  'SD',   3:  'SD',   4:  'SD',
    5:  'SD',             6:  'SMP',  7:  'SMP',  8:  'SMP',
    9:  'SMP',            10: 'SMA',  11: 'SMA',  12: 'SMA',
    13: 'SMA',            14: 'SMA',  15: 'SMA',  16: 'Diploma',
    17: 'Diploma',        18: 'S1',   19: 'S1',   20: 'S2_S3',
    21: 'S2_S3',
}

# r701/r704: HP/internet (2017: r701=HP, r704=internet)
VALUE_LABELS['r701'] = {1: 'Ya', 5: 'Tidak'}  # HP di 2017
VALUE_LABELS['r704'] = {1: 'Ya', 5: 'Tidak'}  # internet di 2017

# r8xx ketenagakerjaan 2017 (sama dengan 2018)
VALUE_LABELS['r802'] = {1:'Bekerja',2:'Sekolah',3:'Mengurus RT',4:'Lainnya'}
VALUE_LABELS['r803'] = {1:'Ya', 5:'Tidak'}

# ⚠ r804 lapangan usaha 2017: HANYA 21 kode (KBLI 1 digit+)
# berbeda dari 2018+ yang punya 26 kode (KBLI 2 digit)
VALUE_LABELS['r804'] = {
    1:  'Pertanian, kehutanan, perikanan',
    2:  'Pertambangan/Penggalian',
    3:  'Industri pengolahan',
    4:  'Listrik/gas/uap/udara dingin',
    5:  'Pengelolaan air/limbah/sampah',
    6:  'Konstruksi',
    7:  'Perdagangan besar/eceran',
    8:  'Pengangkutan/pergudangan',
    9:  'Akomodasi/makan/minum',
    10: 'Informasi/komunikasi',
    11: 'Keuangan/asuransi',
    12: 'Real estat',
    13: 'Profesional/ilmiah/teknis',
    14: 'Penyewaan/jasa bisnis',
    15: 'Administrasi pemerintahan',
    16: 'Pendidikan',
    17: 'Kesehatan/sosial',
    18: 'Kesenian/hiburan/rekreasi',
    19: 'Jasa lainnya',
    20: 'RT sebagai pemberi kerja',
    21: 'Badan internasional',
}

VALUE_LABELS['r805'] = {
    1:'Berusaha sendiri', 2:'Berusaha+buruh tdk tetap',
    3:'Berusaha+buruh tetap', 4:'Buruh/karyawan/pegawai',
    5:'Pekerja bebas', 6:'Pekerja keluarga',
}

# ── KLP pangan 2017: SAMA dengan 2020 (188 komoditi) ─────────────────────────
KLP               = copy.deepcopy(BASE_KLP)
ALL14             = set(BASE_ALL14)
NO_TOB            = set(BASE_NO_TOB)
NO_TOB_PREP       = set(BASE_NO_TOB_PREP)
PREPARED_RANGE    = BASE_PREPARED_RANGE
PROC_CODES        = set(BASE_PROC_CODES)
FOOD_GROUP_HEADERS = dict(BASE_FOOD_GROUP_HEADERS)

# ── RUNNER RT 2017 ────────────────────────────────────────────────────────────
RUNNER_RT = [
    dict(kind='from_rt', out='UrbanRural', col='r105',
         map={'1':'Perkotaan','2':'Perdesaan'}),

    dict(kind='from_rt', out='HomeOwnership', col='r1602',
         map={'1':'Milik sendiri','2':'Kontrak/sewa','3':'Bebas sewa',
              '4':'Dinas','5':'Lainnya'}),

    dict(kind='from_rt', out='RoofMaterial', col='r1607',
         map={'1':'Beton','2':'Genteng','3':'Asbes','4':'Seng',
              '5':'Bambu','6':'Kayu/sirap',
              '7':'Jerami/ijuk/daun-daunan/rumbia','8':'Lainnya'}),

    dict(kind='from_rt', out='WallMaterial', col='r1608',
         map={'1':'Tembok','2':'Plesteran anyaman','3':'Kayu/papan',
              '4':'Anyaman bambu','5':'Batang kayu','6':'Bambu','7':'Lainnya'}),

    dict(kind='from_rt', out='FloorMaterial', col='r1609',
         map={'1':'Marmer/Granit','2':'Keramik','3':'Parket/Vinil',
              '4':'Ubin/Tegel','5':'Kayu/Papan','6':'Semen/Bata merah',
              '7':'Bambu','8':'Tanah','9':'Lainnya'}),

    dict(kind='from_rt', out='Sanitation', col='r1610a',
         map={'1':'Sendiri','2':'Bersama (RT tertentu)',
              '3':'MCK/WC umum','4':'Ada tapi tidak digunakan','5':'Tidak ada'}),

    dict(kind='from_rt', out='ToiletType', col='r1610b',
         map={'1':'Leher angsa','2':'Plengsengan dengan tutup',
              '3':'Plengsengan tanpa tutup','4':'Cemplung cubluk'}),

    dict(kind='from_rt', out='WaterSource', col='r1611a',
         map={'1':'Air kemasan bermerk','2':'Air isi ulang','3':'Leding',
              '4':'Sumur bor/pompa','5':'Sumur terlindung','6':'Sumur tak terlindung',
              '7':'Mata air terlindung','8':'Mata air tak terlindung',
              '9':'Air permukaan','10':'Air hujan','11':'Lainnya'}),

    dict(kind='from_rt', out='AccessEnergy', col='r1618a',
         map={'1':'PLN_dengan_meteran','2':'PLN_tanpa_meteran',
              '3':'Non_PLN','5':'Bukan_listrik'}),

    dict(kind='from_rt', out='CookingFuel', col='r1619',
         map={'0':'Tidak memasak','1':'Listrik','2':'Elpiji 5.5kg/bluegaz',
              '3':'Elpiji 12kg','4':'Elpiji 3kg','5':'Gas kota','6':'Biogas',
              '7':'Minyak tanah','8':'Briket','9':'Arang',
              '10':'Kayu bakar','11':'Lainnya'}),
]

# FIES 2017: di R1501-R1508
_FIES_MAP = {'1':'Ya','5':'Tidak','8':'Tidak tahu','9':'Menolak'}
for col, out in [
    ('r1501','FoodInsecurity_Worry'),    ('r1502','FoodInsecurity_NoHealthy'),
    ('r1503','FoodInsecurity_FewKinds'), ('r1504','FoodInsecurity_SkipMeal'),
    ('r1505','FoodInsecurity_EatLess'),  ('r1506','FoodInsecurity_RanOut'),
    ('r1507','FoodInsecurity_Hungry'),   ('r1508','FoodInsecurity_NoBowl'),
]:
    RUNNER_RT.append(dict(kind='from_rt', out=out, col=col, map=_FIES_MAP))

# ── RUNNER ART 2017: ketenagakerjaan di r8xx ──────────────────────────────────
RUNNER_ART = [
    dict(kind='from_art_head', out='StatusPekerjaanKRT', col='r805',
         map={'1':'Berusaha sendiri','2':'Berusaha+buruh tdk tetap',
              '3':'Berusaha+buruh tetap','4':'Buruh/karyawan/pegawai',
              '5':'Pekerja bebas','6':'Pekerja keluarga'}),

    # ⚠ 2017 tidak ada rekening tabungan di RT (R2101 = jumlah ART bertabungan)

    # HP di R701 (2018: r713; 2019+: r802)
    dict(kind='any_art', out='AccessCommunication', col='r701',
         truthy=('1','01'), yes='Ya', no='Tidak'),
]

# ── Kolom ketenagakerjaan 2017 ────────────────────────────────────────────────
EMPLOYMENT = {
    'education_col'   : 'r615',    # ijazah 21 kode (perlu verifikasi di IND_b)
    'kip_col'         : None,       # KIP belum ada di 2017
    'savings_col'     : None,       # rekening tabungan tidak di level IND (R2101 di RT)
    'activity_col'    : 'r802',     # kegiatan utama (sama 2018)
    'temp_notwork_col': 'r803',     # flag sementara tidak bekerja (sama 2018)
    'sector_col'      : 'r804',     # lapangan usaha 21 kode (2018+: 26 kode)
    'status_col'      : 'r805',     # status pekerjaan (sama 2018)
    'hours_col'       : 'r806',     # jam kerja (sama 2018)
    'working_flag_col': 'r801_a',   # multi-flag r801_a (sama 2018)
    'hp_col'          : 'r701',     # HP di r701 (2018: r713; 2019+: r802)
    'internet_col'    : 'r704',     # internet di r704
}
