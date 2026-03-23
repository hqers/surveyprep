"""
surveyprep.adapters.susenas_2022
=================================
Adapter Susenas 2022 Maret (KOR + KP).
Sumber: Metadata_Susenas_202203_Kor.xls + Metadata_Susenas_202203_KP.xls

STATUS: ✅ VERIFIED dari metadata resmi BPS 2022

Posisi 2022 dalam kronologi
-----------------------------
2022 adalah TAHUN TRANSISI LANJUTAN — sangat mirip 2021 dengan satu
perbedaan kritis: R614 = IJAZAH (bukan R615 lagi).

Perubahan dari 2021
--------------------
IND:
  R614 = ijazah 25 kode  ← BARU di 2022 (2021: R615=ijazah, R614=tingkat kelas)
  R615 = subsidi kuota internet (1=Ya, 5=Tidak)  ← BARU dan UNIK 2022
  R616 = KIP (bukan R615 spt 2021, bukan R619 spt 2025)
  Struktur r702_A-X, r703, r704, r705, r706: SAMA dengan 2021
  Tidak ada r702 (layanan keuangan digital) — belum muncul di 2022

RT:
  URUT (bukan RENUM) = kunci join  ← BERUBAH dari 2021!
  wi3 tidak ada (sama 2021)
  Semua value labels RT: SAMA persis dengan 2021
  FIES R1701-R1708: ada, nilai 1/5/8/9 (sama 2021)

KP41:
  197 komoditi — SAMA dengan 2023 (bukan 188 seperti 2020/2021)
  KLP: 55=Daging, 65=Telur, 75=Sayur, 192=Rokok
  ⚠ Berbeda dari 2021 (rokok=183) — lompatan KLP terjadi di 2022!

Ringkasan perubahan dari 2021
------------------------------
| Aspek             | 2021             | 2022              |
|-------------------|------------------|-------------------|
| Kunci join RT     | RENUM            | URUT              |
| R614              | Tingkat kelas    | Ijazah 25 kode    |
| R615              | Ijazah 22 kode   | Subsidi kuota     |
| R616              | KIP              | KIP               |
| R702              | Belum ada        | Belum ada         |
| KLP rokok         | 183              | 192               |
| Jumlah komoditi   | 188              | 197               |
"""
import copy
from .base import (
    make_config,
    BASE_VALUE_LABELS,
    BASE_KLP,
    BASE_RUNNER_RT, BASE_RUNNER_ART,
    BASE_EMPLOYMENT,
)

# ── Config: URUT bukan RENUM, wi3 tidak ada ───────────────────────────────────
# ⚠ 2022: kunci join adalah 'urut', bukan 'renum' seperti 2021
CONFIG = make_config('22', has_wi3=False)
CONFIG['hh_id_col'] = 'urut'   # override: 2022 pakai URUT, bukan renum

# ── Value labels RT: sama persis dengan 2021 ─────────────────────────────────
VALUE_LABELS = copy.deepcopy(BASE_VALUE_LABELS)

VALUE_LABELS['r1802'] = {
    1: 'Milik sendiri', 2: 'Kontrak/sewa',
    3: 'Bebas sewa',    4: 'Dinas', 5: 'Lainnya',
}
VALUE_LABELS['r1806'] = {
    1: 'Beton',    2: 'Genteng',  3: 'Seng',
    4: 'Asbes',    5: 'Bambu',    6: 'Kayu/sirap',
    7: 'Jerami/ijuk/daun-daunan/rumbia', 8: 'Lainnya',
}
VALUE_LABELS['r1809b'] = {
    1: 'Leher angsa', 2: 'Plengsengan dengan tutup',
    3: 'Plengsengan tanpa tutup', 4: 'Cemplung cubluk',
}
VALUE_LABELS['r1810a'] = {
    1:  'Air kemasan bermerk', 2:  'Air isi ulang',
    3:  'Leding',              4:  'Sumur bor/pompa',
    5:  'Sumur terlindung',    6:  'Sumur tak terlindung',
    7:  'Mata air terlindung', 8:  'Mata air tak terlindung',
    9:  'Air permukaan',       10: 'Air hujan',
    11: 'Lainnya',
}
VALUE_LABELS['r1816'] = {
    1: 'PLN dengan meteran', 2: 'PLN tanpa meteran',
    3: 'Non-PLN',            4: 'Bukan listrik',
}
VALUE_LABELS['r1817'] = {
    0:  'Tidak memasak',        1:  'Listrik',
    2:  'Elpiji 5.5kg/bluegaz', 3:  'Elpiji 12kg',
    4:  'Elpiji 3kg',           5:  'Gas kota',
    6:  'Biogas',               7:  'Minyak tanah',
    8:  'Briket',               9:  'Arang',
    10: 'Kayu bakar',           11: 'Lainnya',
}
VALUE_LABELS['r1701_fies'] = {1:'Ya', 5:'Tidak', 8:'Tidak tahu', 9:'Menolak'}

# ── IND: perbedaan kritis dari 2021 ──────────────────────────────────────────

# ⚠ R614 = IJAZAH 25 kode (2021: R614=tingkat kelas, R615=ijazah)
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

# ⚠ R615 = subsidi kuota internet (UNIK 2022 saja!)
VALUE_LABELS['r615'] = {1: 'Ya', 5: 'Tidak'}

# R616 = KIP (sama posisinya dengan 2021)
VALUE_LABELS['r616'] = {1: 'Ya, ditunjukkan', 2: 'Ya, tdk ditunjukkan', 5: 'Tidak'}

# r701/r802: 1=Ya, 5=Tidak (sama 2021)
VALUE_LABELS['r701'] = {1: 'Ya', 5: 'Tidak'}
VALUE_LABELS['r802'] = {1: 'Ya', 5: 'Tidak'}

# r703-r706: sama dengan 2021 (satu posisi sebelum 2023+)
VALUE_LABELS['r703'] = {1:'Bekerja', 2:'Sekolah', 3:'Mengurus RT', 4:'Lainnya'}
VALUE_LABELS['r704'] = {1: 'Ya', 5: 'Tidak'}
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
    1:'Berusaha sendiri', 2:'Berusaha + buruh tidak tetap',
    3:'Berusaha + buruh tetap', 4:'Buruh/karyawan/pegawai',
    5:'Pekerja bebas', 6:'Pekerja keluarga/tidak dibayar',
}

# ── KLP pangan 2022: SAMA dengan 2023 (197 komoditi) ─────────────────────────
# ⚠ Lompatan dari 2021 (188→197 komoditi, rokok 183→192)
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
    '1':  'PADI-PADIAN',       '8':  'UMBI-UMBIAN',
    '16': 'IKAN',              '55': 'DAGING',
    '65': 'TELUR DAN SUSU',    '75': 'SAYUR-SAYURAN',
    '102':'KACANG-KACANGAN',   '110':'BUAH-BUAHAN',
    '126':'MINYAK DAN KELAPA', '131':'BAHAN MINUMAN',
    '139':'BUMBU-BUMBUAN',     '154':'KONSUMSI LAINNYA',
    '159':'MAKANAN DAN MINUMAN JADI', '192':'ROKOK DAN TEMBAKAU',
}

# ── RUNNER RT 2022: sama dengan 2021 (nama kolom r1806, r1802, r1817 berubah) ─
from .susenas_2021 import RUNNER_RT as _RT_2021
RUNNER_RT = list(_RT_2021)  # identik — mapping sama

# ── RUNNER ART 2022: sama dengan 2021 (r706=status, r702_a=working_flag) ──────
from .susenas_2021 import RUNNER_ART as _ART_2021
RUNNER_ART = list(_ART_2021)

# ── Kolom ketenagakerjaan 2022 ────────────────────────────────────────────────
# ⚠ R614=ijazah (bukan R615 spt 2021)
# ⚠ R615=subsidi kuota (unik 2022, bukan ijazah, bukan KIP)
# ⚠ R616=KIP (sama 2021)
# ⚠ r703/r704/r705/r706: sama dengan 2021
EMPLOYMENT = {
    'education_col'   : 'r614',    # ⚠ 2022: R614=ijazah 25 kode
    'kip_col'         : 'r616',    # KIP di r616 (sama 2021)
    'activity_col'    : 'r703',    # sama 2021
    'temp_notwork_col': 'r704',    # sama 2021
    'sector_col'      : 'r705',    # sama 2021
    'status_col'      : 'r706',    # sama 2021
    'hours_col'       : 'r707',    # sama 2021
    'working_flag_col': 'r702_a',  # sama 2021
}
