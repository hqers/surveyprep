"""
surveyprep.adapters.susenas_2018
=================================
Adapter Susenas 2018 Maret (KOR + KP).
Sumber: Metadata_Susenas_201803_Kor.xls + Metadata_Susenas_201803_KP.xls

STATUS: ✅ VERIFIED dari metadata resmi BPS 2018

Kronologi blok perumahan (KRITIS):
    2017 : R16xx  (R1602=kepemilikan, R1607=atap, R1618A=listrik, R1619=BBM)
    2018 : R15xx  (R1502=kepemilikan, R1507=atap, R1518A=listrik, R1519=BBM)
    2019+ : R18xx (R1802=kepemilikan, R1806=atap, R1816=listrik, R1817=BBM)

Perubahan dari 2019 (basis terdekat)
--------------------------------------
RT:
  Semua variabel perumahan bergeser ~300 ke bawah vs 2019:
    kepemilikan : R1502  (2019: R1802)
    atap        : R1507  (2019: R1806)
    dinding     : R1508  (2019: R1807)
    lantai      : R1509  (2019: R1808)
    sanitasi    : R1510A, R1510B  (2019: R1809A, R1809B)
    air minum   : R1511A  (2019: R1810A)
    penerangan  : R1518A  (2019: R1816) — kode 4 tidak ada (bukan listrik=kode 5)
    BBM         : R1519   (2019: R1817)
  FIES ada, tapi di blok R14xx (bukan R17xx spt 2019+):
    R1401-R1408  (2019+: R1701-R1708)
  Kredit: R1701A-J  (2019: R1901A-J)
  Aset  : R1801A-M  (2019: R2001A-M)
  Design: URUT, WI, WI2, WI3, FWT  — RENUM/PSU/SSU/STRATA tidak ada
  ⚠ R1510A (sanitasi) 2018: hanya 5 kode (MCK komunal hilang dibanding 2019+)
    1=Sendiri, 2=Bersama RT tertentu, 3=MCK Umum, 4=Tdk digunakan, 5=Tdk ada

IND:
  R615: ijazah 22 kode, KODE SAMA dengan 2019 (1=Tdk punya, 4=SD, 12=SMA)
  R616: KIP (sama posisi dengan 2019)
  R717: rekening tabungan (bukan R701 spt 2021+)
  Ketenagakerjaan di R8xx (bukan R7xx!):
    R801_A-X : multi-flag kegiatan   (2019: R701_A-X)
    R802     : kegiatan utama        (2019: R702)
    R803     : flag sementara tdk bk (2019: R703)
    R804     : lapangan usaha 26 kode(2019: R704)
    R805     : status pekerjaan      (2019: R705)
    R806     : jam kerja utama       (2019: R706)
  HP : R713 (bukan R802 spt 2019)  — 1=Ya, 5=Tidak
  Internet: R716

KP41 2018: 188 komoditi — IDENTIK dengan 2017/2019/2020
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

# ── Config: WI/WI2/WI3, URUT, tidak ada PSU/SSU/STRATA/RENUM ─────────────────
CONFIG = make_config('18', has_wi3=False)
CONFIG['design_cols'] = ['wi', 'wi2', 'wi3', 'fwt']
CONFIG['hh_id_col']   = 'urut'   # 2018 pakai URUT (bukan renum spt 2019)

# ── Value labels ──────────────────────────────────────────────────────────────
VALUE_LABELS = copy.deepcopy(BASE_VALUE_LABELS)

# R1502 (kepemilikan): 5 kode — sama dengan 2019+
VALUE_LABELS['r1502'] = {
    1: 'Milik sendiri', 2: 'Kontrak/sewa',
    3: 'Bebas sewa',    4: 'Dinas', 5: 'Lainnya',
}

# R1507 (atap): 8 kode, kode 3=Asbes, 4=Seng — sama dengan 2019
VALUE_LABELS['r1507'] = {
    1: 'Beton',    2: 'Genteng',  3: 'Asbes',
    4: 'Seng',     5: 'Bambu',    6: 'Kayu/sirap',
    7: 'Jerami/ijuk/daun-daunan/rumbia', 8: 'Lainnya',
}

# R1508 (dinding): 7 kode — sama dengan base
VALUE_LABELS['r1508'] = dict(BASE_VALUE_LABELS['r1807'])

# R1509 (lantai): 9 kode — sama dengan base
VALUE_LABELS['r1509'] = dict(BASE_VALUE_LABELS['r1808'])

# ⚠ R1510A (sanitasi) 2018: 5 kode (MCK komunal tidak ada!)
# 2019+: 6 kode (ada MCK komunal = kode 3)
VALUE_LABELS['r1510a'] = {
    1: 'Sendiri',              2: 'Bersama RT tertentu',
    3: 'MCK/WC umum',          4: 'Ada tapi tidak digunakan',
    5: 'Tidak ada',
}

# R1510B (kloset): 4 kode — sama dengan 2019+
VALUE_LABELS['r1510b'] = {
    1: 'Leher angsa', 2: 'Plengsengan dengan tutup',
    3: 'Plengsengan tanpa tutup', 4: 'Cemplung cubluk',
}

# R1511A (air minum): 11 kode — sama dengan 2019+
VALUE_LABELS['r1511a'] = {
    1:  'Air kemasan bermerk', 2:  'Air isi ulang',
    3:  'Leding',              4:  'Sumur bor/pompa',
    5:  'Sumur terlindung',    6:  'Sumur tak terlindung',
    7:  'Mata air terlindung', 8:  'Mata air tak terlindung',
    9:  'Air permukaan',       10: 'Air hujan',
    11: 'Lainnya',
}

# ⚠ R1518A (penerangan): kode 4 tidak ada, bukan listrik=kode 5 — sama 2017/2019
VALUE_LABELS['r1518a'] = {
    1: 'PLN dengan meteran', 2: 'PLN tanpa meteran',
    3: 'Non-PLN',            5: 'Bukan listrik',
}

# R1519 (BBM): 11 kode — sama dengan 2019+
VALUE_LABELS['r1519'] = {
    0:  'Tidak memasak',        1:  'Listrik',
    2:  'Elpiji 5.5kg/bluegaz', 3:  'Elpiji 12kg',
    4:  'Elpiji 3kg',           5:  'Gas kota',
    6:  'Biogas',               7:  'Minyak tanah',
    8:  'Briket',               9:  'Arang',
    10: 'Kayu bakar',           11: 'Lainnya',
}

# FIES 2018: di R1401-R1408 (bukan R1701 spt 2019+), nilai 1/5/8/9
VALUE_LABELS['r1401_fies'] = {1: 'Ya', 5: 'Tidak', 8: 'Tidak tahu', 9: 'Menolak'}

# R615: ijazah 22 kode, KODE SAMA dengan 2019
VALUE_LABELS['r615'] = dict(BASE_VALUE_LABELS['r615_ijazah'])
# Override kode 2019 (1=Tdk punya, 4=SD, ...) — Catatan: di 2018 kodenya sama 2019
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
# Catatan: 2018 hanya 21 kode (tidak ada kode 20=Profesi seperti 2019)

VALUE_LABELS['r615_band'] = {
    1:  'Tidak_Tamat_SD', 2:  'SD',   3:  'SD',   4:  'SD',
    5:  'SD',             6:  'SMP',  7:  'SMP',  8:  'SMP',
    9:  'SMP',            10: 'SMA',  11: 'SMA',  12: 'SMA',
    13: 'SMA',            14: 'SMA',  15: 'SMA',  16: 'Diploma',
    17: 'Diploma',        18: 'S1',   19: 'S1',   20: 'S2_S3',
    21: 'S2_S3',
}

VALUE_LABELS['r616'] = {1: 'Ya, ditunjukkan', 2: 'Ya, tdk ditunjukkan', 5: 'Tidak'}
VALUE_LABELS['r717'] = {1: 'Ya', 5: 'Tidak'}   # rekening tabungan (2018: r717)
VALUE_LABELS['r713'] = {1: 'Ya', 5: 'Tidak'}   # HP (2018: r713)

# r8xx ketenagakerjaan 2018
VALUE_LABELS['r802'] = {1:'Bekerja',2:'Sekolah',3:'Mengurus RT',4:'Lainnya'}
VALUE_LABELS['r803'] = {1:'Ya', 5:'Tidak'}
VALUE_LABELS['r804'] = {   # lapangan usaha 26 kode (sama 2019+)
    1:'Pertanian padi/palawija', 2:'Hortikultura', 3:'Perkebunan',
    4:'Perikanan', 5:'Peternakan', 6:'Kehutanan', 7:'Pertambangan',
    8:'Industri pengolahan', 9:'Listrik/gas/uap', 10:'Air/limbah',
    11:'Konstruksi', 12:'Perdagangan', 13:'Transportasi', 14:'Akomodasi',
    15:'Informasi/komunikasi', 16:'Keuangan', 17:'Real estate',
    18:'Profesional/teknis', 19:'Penyewaan/bisnis', 20:'Pemerintahan',
    21:'Pendidikan', 22:'Kesehatan', 23:'Kesenian', 24:'Jasa lainnya',
    25:'RT pemberi kerja', 26:'Badan internasional',
}
VALUE_LABELS['r805'] = {
    1:'Berusaha sendiri', 2:'Berusaha+buruh tdk tetap',
    3:'Berusaha+buruh tetap', 4:'Buruh/karyawan/pegawai',
    5:'Pekerja bebas', 6:'Pekerja keluarga',
}

# ── KLP pangan 2018: SAMA dengan 2020 (188 komoditi) ─────────────────────────
KLP               = copy.deepcopy(BASE_KLP)
ALL14             = set(BASE_ALL14)
NO_TOB            = set(BASE_NO_TOB)
NO_TOB_PREP       = set(BASE_NO_TOB_PREP)
PREPARED_RANGE    = BASE_PREPARED_RANGE
PROC_CODES        = set(BASE_PROC_CODES)
FOOD_GROUP_HEADERS = dict(BASE_FOOD_GROUP_HEADERS)

# ── RUNNER RT 2018: nama kolom BERBEDA dari 2019+ ────────────────────────────
# Semua kolom perumahan bergeser ~300 ke bawah dibanding 2019
RUNNER_RT = [
    dict(kind='from_rt', out='UrbanRural', col='r105',
         map={'1':'Perkotaan','2':'Perdesaan'}),

    dict(kind='from_rt', out='HomeOwnership', col='r1502',
         map={'1':'Milik sendiri','2':'Kontrak/sewa','3':'Bebas sewa',
              '4':'Dinas','5':'Lainnya'}),

    dict(kind='from_rt', out='RoofMaterial', col='r1507',
         map={'1':'Beton','2':'Genteng','3':'Asbes','4':'Seng',
              '5':'Bambu','6':'Kayu/sirap',
              '7':'Jerami/ijuk/daun-daunan/rumbia','8':'Lainnya'}),

    dict(kind='from_rt', out='WallMaterial', col='r1508',
         map={'1':'Tembok','2':'Plesteran anyaman','3':'Kayu/papan',
              '4':'Anyaman bambu','5':'Batang kayu','6':'Bambu','7':'Lainnya'}),

    dict(kind='from_rt', out='FloorMaterial', col='r1509',
         map={'1':'Marmer/Granit','2':'Keramik','3':'Parket/Vinil',
              '4':'Ubin/Tegel','5':'Kayu/Papan','6':'Semen/Bata merah',
              '7':'Bambu','8':'Tanah','9':'Lainnya'}),

    # ⚠ 5 kode (MCK komunal tidak ada di 2018)
    dict(kind='from_rt', out='Sanitation', col='r1510a',
         map={'1':'Sendiri','2':'Bersama (RT tertentu)',
              '3':'MCK/WC umum','4':'Ada tapi tidak digunakan','5':'Tidak ada'}),

    dict(kind='from_rt', out='ToiletType', col='r1510b',
         map={'1':'Leher angsa','2':'Plengsengan dengan tutup',
              '3':'Plengsengan tanpa tutup','4':'Cemplung cubluk'}),

    dict(kind='from_rt', out='WaterSource', col='r1511a',
         map={'1':'Air kemasan bermerk','2':'Air isi ulang','3':'Leding',
              '4':'Sumur bor/pompa','5':'Sumur terlindung','6':'Sumur tak terlindung',
              '7':'Mata air terlindung','8':'Mata air tak terlindung',
              '9':'Air permukaan','10':'Air hujan','11':'Lainnya'}),

    # ⚠ kode 4 tidak ada, bukan listrik=kode 5
    dict(kind='from_rt', out='AccessEnergy', col='r1518a',
         map={'1':'PLN_dengan_meteran','2':'PLN_tanpa_meteran',
              '3':'Non_PLN','5':'Bukan_listrik'}),

    dict(kind='from_rt', out='CookingFuel', col='r1519',
         map={'0':'Tidak memasak','1':'Listrik','2':'Elpiji 5.5kg/bluegaz',
              '3':'Elpiji 12kg','4':'Elpiji 3kg','5':'Gas kota','6':'Biogas',
              '7':'Minyak tanah','8':'Briket','9':'Arang',
              '10':'Kayu bakar','11':'Lainnya'}),
]

# FIES 2018: di R1401-R1408
_FIES_MAP = {'1':'Ya','5':'Tidak','8':'Tidak tahu','9':'Menolak'}
for col, out in [
    ('r1401','FoodInsecurity_Worry'),    ('r1402','FoodInsecurity_NoHealthy'),
    ('r1403','FoodInsecurity_FewKinds'), ('r1404','FoodInsecurity_SkipMeal'),
    ('r1405','FoodInsecurity_EatLess'),  ('r1406','FoodInsecurity_RanOut'),
    ('r1407','FoodInsecurity_Hungry'),   ('r1408','FoodInsecurity_NoBowl'),
]:
    RUNNER_RT.append(dict(kind='from_rt', out=out, col=col, map=_FIES_MAP))

# ── RUNNER ART 2018: ketenagakerjaan di r8xx ──────────────────────────────────
RUNNER_ART = [
    # ⚠ Status pekerjaan di r805 (2019: r705)
    dict(kind='from_art_head', out='StatusPekerjaanKRT', col='r805',
         map={'1':'Berusaha sendiri','2':'Berusaha+buruh tdk tetap',
              '3':'Berusaha+buruh tetap','4':'Buruh/karyawan/pegawai',
              '5':'Pekerja bebas','6':'Pekerja keluarga'}),

    # ⚠ Tabungan di r717 (bukan r701 spt 2021+)
    dict(kind='any_art', out='HasSavingsAccount', col='r717',
         truthy=('1','01'), yes='Ya', no='Tidak'),

    # ⚠ HP di r713 (bukan r802 spt 2019+)
    dict(kind='any_art', out='AccessCommunication', col='r713',
         truthy=('1','01'), yes='Ya', no='Tidak'),
]

# ── Kolom ketenagakerjaan 2018 ────────────────────────────────────────────────
EMPLOYMENT = {
    'education_col'   : 'r615',    # ijazah 21 kode (kode sama dengan 2019)
    'kip_col'         : 'r616',    # KIP di r616 (sama 2019)
    'savings_col'     : 'r717',    # ⚠ rekening tabungan di r717 (2019: belum ada; 2021+: r701)
    'activity_col'    : 'r802',    # ⚠ kegiatan utama di r802 (2019: r702)
    'temp_notwork_col': 'r803',    # ⚠ flag tdk bekerja di r803 (2019: r703)
    'sector_col'      : 'r804',    # ⚠ lapangan usaha di r804 (2019: r704)
    'status_col'      : 'r805',    # ⚠ status pekerjaan di r805 (2019: r705)
    'hours_col'       : 'r806',    # ⚠ jam kerja di r806 (2019: r706)
    'working_flag_col': 'r801_a',  # ⚠ multi-flag r801_a (2019: r701_a)
    'hp_col'          : 'r713',    # HP di r713 (2019: r802)
    'internet_col'    : 'r716',    # internet di r716
}
