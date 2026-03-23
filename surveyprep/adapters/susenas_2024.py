"""
surveyprep.adapters.susenas_2024
=================================
Adapter Susenas 2024 Maret (KOR).
Sumber: Metadata_KOR_202403.xlsx + Metadata_Susenas_202403_KP.xlsx

Override dari base: lihat bagian ⚠ di bawah.

Ringkasan perubahan dari 2020:
  - r1802: 7 kode → 5 kode (Kontrak+Sewa digabung, Bebas sewa digabung)
  - r1806 → r1806a (nama kolom berubah + 8 kode)
  - r1810a: kode 4 (Leding eceran) hilang, kode 4+ bergeser
  - r1816: label kode 2 berubah
  - r1817: kode 3=Elpiji 12kg baru, kode 3–10 semua geser +1
  - r703 dipecah → r703_a/b/c/d/x
  - r704–r707 semua bergeser makna
  - r615 berubah menjadi KIP (ijazah → r613)
  - KLP pangan bergeser akibat 9 komoditi baru
  - wi3 tidak ada di RT
  - r701/r802: 2=Tidak → 5=Tidak
  - Variabel baru: FIES (r1701-r1708), r702 (layanan keuangan)
"""
import copy
from .base import (
    make_config,
    BASE_VALUE_LABELS,
    BASE_KLP,
    BASE_RUNNER_RT, BASE_RUNNER_ART,
    BASE_EMPLOYMENT,
)

# ── Config: wi3 tidak ada di 2024 ─────────────────────────────────────────────
CONFIG = make_config('24', has_wi3=False)

# ── Value labels: override bagian yang berubah ────────────────────────────────
VALUE_LABELS = copy.deepcopy(BASE_VALUE_LABELS)

# ⚠ r1802: 7 → 5 kode
VALUE_LABELS['r1802'] = {
    1: 'Milik sendiri', 2: 'Kontrak/sewa',
    3: 'Bebas sewa',    4: 'Dinas', 5: 'Lainnya',
}

# ⚠ r1806 → r1806a (nama kolom berubah, mapping ada di RUNNER_RT_2024)
# Tidak perlu override VALUE_LABELS karena akses via RUNNER

# ⚠ r1810a: kode 4 (Leding eceran) hilang
VALUE_LABELS['r1810a'] = {
    1:  'Air kemasan bermerk', 2:  'Air isi ulang',
    3:  'Leding',              4:  'Sumur bor/pompa',
    5:  'Sumur terlindung',    6:  'Sumur tak terlindung',
    7:  'Mata air terlindung', 8:  'Mata air tak terlindung',
    9:  'Air permukaan',       10: 'Air hujan',
    11: 'Lainnya',
}

# ⚠ r1816: label kode 2 berubah
VALUE_LABELS['r1816'] = {
    1: 'PLN dengan meteran', 2: 'PLN tanpa meteran',
    3: 'Non-PLN',            4: 'Bukan listrik',
}

# ⚠ r1817: kode 3=Elpiji 12kg baru, kode 3–10 semua geser +1
VALUE_LABELS['r1817'] = {
    0:  'Tidak memasak',       1:  'Listrik',
    2:  'Elpiji 5.5kg/bluegaz',3:  'Elpiji 12kg',
    4:  'Elpiji 3kg',          5:  'Gas kota',
    6:  'Biogas',              7:  'Minyak tanah',
    8:  'Briket',              9:  'Arang',
    10: 'Kayu bakar',          11: 'Lainnya',
}

# ⚠ r615 berubah makna (KIP, bukan ijazah)
VALUE_LABELS['r615'] = {1: 'Ya, ditunjukkan', 2: 'Ya, tdk ditunjukkan', 5: 'Tidak'}
# Ijazah di 2024 ada di r613
VALUE_LABELS['r613'] = {
    1: 'Tidak/Belum Sekolah', 2: 'SD', 3: 'SMP', 4: 'SMA', 5: 'Perguruan Tinggi',
}

# ⚠ r703–r707 bergeser makna
VALUE_LABELS['r704'] = {1: 'Bekerja', 2: 'Sekolah', 3: 'Mengurus RT', 4: 'Lainnya'}
VALUE_LABELS['r705'] = {1: 'Ya', 5: 'Tidak'}
VALUE_LABELS['r706'] = {
    1:'Pertanian padi/palawija', 2:'Hortikultura', 3:'Perkebunan',
    4:'Perikanan', 5:'Peternakan', 6:'Kehutanan', 7:'Pertambangan',
    8:'Industri pengolahan', 9:'Listrik/gas/uap',10:'Air/limbah/daur ulang',
    11:'Konstruksi', 12:'Perdagangan', 13:'Transportasi', 14:'Akomodasi/makan',
    15:'Informasi/komunikasi', 16:'Keuangan', 17:'Real estate',
    18:'Profesional/teknis', 19:'Penyewaan/bisnis', 20:'Pemerintahan',
    21:'Pendidikan', 22:'Kesehatan/sosial', 23:'Kesenian/rekreasi',
    24:'Jasa lainnya', 25:'RT pemberi kerja', 26:'Badan internasional',
}
VALUE_LABELS['r707'] = VALUE_LABELS.get('r706_status', {
    1:'Berusaha sendiri', 2:'Berusaha+buruh tdk tetap',
    3:'Berusaha+buruh tetap', 4:'Buruh/karyawan',
    5:'Pekerja bebas', 6:'Pekerja keluarga',
})

# ⚠ r701/r802: 5=Tidak (bukan 2=Tidak)
VALUE_LABELS['r701'] = {1: 'Ya', 5: 'Tidak'}
VALUE_LABELS['r802'] = {1: 'Ya', 5: 'Tidak'}

# Variabel baru 2024
VALUE_LABELS['r702'] = {1: 'Ya', 5: 'Tidak'}   # layanan keuangan digital
VALUE_LABELS['r1701_r1708'] = {1: 'Ya', 2: 'Tidak', 5: 'Tidak'}  # FIES

# ── KLP pangan 2024: bergeser akibat 9 komoditi baru ─────────────────────────
KLP = copy.deepcopy(BASE_KLP)
KLP.update({
    'daging'     : {'55'},   # 2020: 52
    'telur_susu' : {'65'},   # 2020: 62
    'sayur'      : {'75'},   # 2020: 72
    'kacang'     : {'102'},  # 2020: 98
    'buah'       : {'110'},  # 2020: 106
    'minyak'     : {'126'},  # 2020: 120
    'bhn_minuman': {'131'},  # 2020: 125
    'bumbu'      : {'139'},  # 2020: 133
    'lainnya'    : {'154'},  # 2020: 146
    'mkn_jadi'   : {'159'},  # 2020: 151
    'rokok'      : {'192'},  # 2020: 183
})

ALL14          = {'1','8','16','55','65','75','102','110',
                  '126','131','139','154','159','192'}
NO_TOB         = ALL14 - {'192'}
NO_TOB_PREP    = ALL14 - {'192','159'}
PREPARED_RANGE = (159, 191)
PROC_CODES     = {'176','177','186','187','189','190'}

FOOD_GROUP_HEADERS = {
    '1':'PADI-PADIAN',    '8':'UMBI-UMBIAN',   '16':'IKAN',
    '55':'DAGING',        '65':'TELUR DAN SUSU','75':'SAYUR-SAYURAN',
    '102':'KACANG-KACANGAN','110':'BUAH-BUAHAN','126':'MINYAK DAN KELAPA',
    '131':'BAHAN MINUMAN','139':'BUMBU-BUMBUAN','154':'KONSUMSI LAINNYA',
    '159':'MAKANAN DAN MINUMAN JADI','192':'ROKOK DAN TEMBAKAU',
}

# ── RUNNER RT 2024: override r1806, r1802, r1817, r1810a, r1816 ───────────────
RUNNER_RT = []
for item in BASE_RUNNER_RT:
    item = dict(item)
    out = item['out']

    if out == 'RoofMaterial':
        # ⚠ Nama kolom berubah r1806 → r1806a, mapping juga berubah
        item['col'] = 'r1806a'
        item['map'] = {
            '1':'Beton','2':'Genteng','3':'Seng','4':'Asbes',
            '5':'Bambu','6':'Kayu/sirap','7':'Jerami/ijuk/rumbia','8':'Lainnya',
        }
    elif out == 'HomeOwnership':
        item['map'] = {
            '1':'Milik sendiri','2':'Kontrak/sewa',
            '3':'Bebas sewa','4':'Dinas','5':'Lainnya',
        }
    elif out == 'WaterSource':
        item['map'] = {
            '1':'Air kemasan bermerk','2':'Air isi ulang','3':'Leding',
            '4':'Sumur bor/pompa','5':'Sumur terlindung','6':'Sumur tak terlindung',
            '7':'Mata air terlindung','8':'Mata air tak terlindung',
            '9':'Air permukaan','10':'Air hujan','11':'Lainnya',
        }
    elif out == 'AccessEnergy':
        item['map'] = {
            '1':'PLN_dengan_meteran','2':'PLN_tanpa_meteran',
            '3':'Non_PLN','4':'Bukan_listrik',
        }
    elif out == 'CookingFuel':
        item['map'] = {
            '0':'Tidak memasak','1':'Listrik','2':'Elpiji 5.5kg/bluegaz',
            '3':'Elpiji 12kg','4':'Elpiji 3kg','5':'Gas kota','6':'Biogas',
            '7':'Minyak tanah','8':'Briket','9':'Arang',
            '10':'Kayu bakar','11':'Lainnya',
        }
    elif out == 'ToiletType':
        item['map'] = {
            '1':'Leher angsa','2':'Plengsengan dengan tutup',
            '3':'Plengsengan tanpa tutup','4':'Cemplung/cubluk',
        }
    RUNNER_RT.append(item)

# Tambah FIES (baru 2024)
_FIES_MAP = {'1':'Ya','2':'Tidak','5':'Tidak'}
for col, out in [
    ('r1701','FoodInsecurity_Worry'),  ('r1702','FoodInsecurity_NoHealthy'),
    ('r1703','FoodInsecurity_FewKinds'),('r1704','FoodInsecurity_SkipMeal'),
    ('r1705','FoodInsecurity_EatLess'), ('r1706','FoodInsecurity_RanOut'),
    ('r1707','FoodInsecurity_Hungry'),  ('r1708','FoodInsecurity_NoBowl'),
]:
    RUNNER_RT.append(dict(kind='from_rt', out=out, col=col, map=_FIES_MAP))

# Layanan keuangan digital (baru 2024)
RUNNER_RT.append(dict(kind='from_rt', out='DigitalFinance', col='r702',
                      map={'1':'Ya','5':'Tidak'}))

# ── RUNNER ART 2024: status pekerjaan di r707, truthy r701/r802 berubah ───────
RUNNER_ART = []
for item in BASE_RUNNER_ART:
    item = dict(item)
    out = item['out']
    if out == 'StatusPekerjaanKRT':
        item['col'] = 'r707'   # ⚠ geser dari r706
    # r701/r802: 5=Tidak di 2024 — truthy tetap '1', tapi tidak perlu ubah
    # karena truthy=('1','01') sudah cukup: tidak memakai '2' sebagai truthy
    RUNNER_ART.append(item)

# Tambah layanan keuangan digital per ART
RUNNER_ART.append(dict(kind='any_art', out='UsesDigitalFinance', col='r702',
                        truthy=('1','01'), yes='Ya', no='Tidak'))

# ── Kolom ketenagakerjaan 2024 ────────────────────────────────────────────────
EMPLOYMENT = {
    'education_col'  : 'r613',    # ⚠ r615 = KIP di 2024, ijazah di r613
    'activity_col'   : 'r704',    # ⚠ geser dari r703
    'temp_notwork_col': 'r705',   # ⚠ geser dari r704
    'sector_col'     : 'r706',    # ⚠ geser dari r705
    'status_col'     : 'r707',    # ⚠ geser dari r706
    'hours_col'      : 'r708',    # ⚠ geser dari r707
    'working_flag_col': 'r703_a', # ⚠ baru (r703 dipecah jadi multi-flag)
}

# ── Alias konstanta untuk individual_2024.py ─────────────────────────────────
# individual_2024.py mengimport nama-nama ini secara eksplisit
EDUCATION_COL_2024      = EMPLOYMENT['education_col']       # 'r613'
WORKING_FLAG_COL_2024   = EMPLOYMENT['working_flag_col']    # 'r703_a'
ACTIVITY_COL_2024       = EMPLOYMENT['activity_col']        # 'r704'
TEMP_NOT_WORK_2024      = EMPLOYMENT['temp_notwork_col']    # 'r705'
