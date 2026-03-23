"""
surveyprep.adapters.base
========================
Definisi lengkap Susenas yang dijadikan basis semua adapter tahun spesifik.

Arsitektur inheritance:
    base.py          ← definisi penuh, default 2020
    susenas_2020.py  ← from .base import *  (tidak ada override = identik 2020)
    susenas_2021.py  ← from .base import *  + override bagian yang berubah
    susenas_2022.py  ← from .base import *  + override bagian yang berubah
    ...dst.

Cara membuat adapter tahun baru:
    1. Buat file susenas_202X.py
    2. from .base import (BASE_CONFIG, BASE_VALUE_LABELS, BASE_KLP,
                          BASE_RUNNER_RT, BASE_RUNNER_ART,
                          BASE_ALL14, BASE_NO_TOB, BASE_NO_TOB_PREP,
                          BASE_PREPARED_RANGE, BASE_PROC_CODES)
    3. import copy; CONFIG = copy.deepcopy(BASE_CONFIG); CONFIG['rt_file'] = '...'
    4. VALUE_LABELS = copy.deepcopy(BASE_VALUE_LABELS)
       VALUE_LABELS['r1817'] = {...}  # hanya yang berubah
    5. Tambahkan konstanta baru jika ada variabel baru

Apa yang SELALU berubah antar tahun:
    - CONFIG['rt_file'], 'art_a_file', 'art_b_file'  ← prefix tahun (kor21, kor22, dst.)
    - CONFIG['design_cols']                           ← wi3 hilang di 2024+

Apa yang SERING berubah:
    - VALUE_LABELS['r1817']   ← kode Elpiji kerap berubah
    - VALUE_LABELS['r1802']   ← kategori kepemilikan dikonsolidasi di 2024
    - BASE_KLP                ← bergeser saat ada komoditi baru disisipkan

Apa yang JARANG berubah:
    - VALUE_LABELS['r105'], 'r403', 'r405', 'r1807', 'r1808'
    - BASE_RUNNER_RT (kecuali nama kolom berubah seperti r1806 → r1806a di 2024)
"""
import copy

# ─── Konfigurasi file (2020 sebagai default) ──────────────────────────────────
BASE_CONFIG = {
    'rt_file'   : 'kor20rt_diseminasi.csv',
    'art_a_file': 'kor20ind_1_diseminasi.csv',
    'art_b_file': 'kor20ind_2_diseminasi.csv',
    'kp41_glob' : 'Blok41_gab*.csv',
    'kp42_glob' : 'blok42*.csv',
    'kp43_glob' : 'blok43*.csv',
    'sep'       : ';',
    'encoding'  : 'latin-1',
    'decimal'   : ',',
    'thousands' : '.',
    'hh_id_col' : 'renum',
    'design_cols': ['psu', 'ssu', 'strata', 'fwt', 'wi1', 'wi2', 'wi3'],
}

# ─── Value labels (2020 sebagai default) ──────────────────────────────────────
BASE_VALUE_LABELS = {

    'r105': {1: 'Perkotaan', 2: 'Perdesaan'},

    'r403': {
        1: 'Kepala rumah tangga', 2: 'Istri/suami',
        3: 'Anak',                4: 'Menantu',
        5: 'Cucu',                6: 'Orang tua/mertua',
        7: 'Famili lain',         8: 'Pembantu rumah tangga',
        9: 'Lainnya',
    },

    'r405': {1: 'Laki-laki', 2: 'Perempuan'},

    # Ijazah tertinggi — berlaku 2017–2023 (r615 berubah makna di 2024)
    'r615_ijazah': {
        1:  'Tidak punya ijazah SD',  2:  'SD/MI tamat',
        3:  'SD/MI tidak tamat',      4:  'Paket A',
        5:  'SMP/MTs',                6:  'Paket B',
        7:  'SMA/MA',                 8:  'Paket C',
        9:  'SMK',
        13: 'DI',                     14: 'DII',
        15: 'DIII/Akademi',           16: 'DIII (kode lama)',
        17: 'DIV/S1',                 18: 'DIV/S1 (kode lama)',
        19: 'Profesi',                20: 'S2/Master',
        21: 'S3/Doktor',              22: 'Tidak punya ijazah',
    },

    'r703': {1: 'Bekerja', 2: 'Sekolah', 3: 'Mengurus RT', 4: 'Lainnya'},

    # Status pekerjaan — berlaku 2017–2023 (pindah ke r707 di 2024)
    'r706_status': {
        1: 'Berusaha sendiri',
        2: 'Berusaha + buruh tidak tetap',
        3: 'Berusaha + buruh tetap',
        4: 'Buruh/karyawan/pegawai',
        5: 'Pekerja bebas',
        6: 'Pekerja keluarga/tidak dibayar',
    },

    # Rekening tabungan: 2020–2023 = 1/2; 2024+ = 1/5
    'r701': {1: 'Ya', 2: 'Tidak'},
    'r802': {1: 'Ya', 2: 'Tidak'},

    # ── Variabel RT fisik ──
    'r1802': {
        1: 'Milik sendiri',       2: 'Kontrak',
        3: 'Sewa',                4: 'Bebas sewa (orang lain)',
        5: 'Bebas sewa (orang tua/saudara)',
        6: 'Dinas',               7: 'Lainnya',
    },

    'r1806': {
        1: 'Beton', 2: 'Genteng', 3: 'Sirap',
        4: 'Seng',  5: 'Asbes',   6: 'Ijuk/Rumbia', 7: 'Lainnya',
    },

    'r1807': {
        1: 'Tembok',          2: 'Plesteran anyaman',
        3: 'Kayu/papan',      4: 'Anyaman bambu',
        5: 'Batang kayu',     6: 'Bambu',      7: 'Lainnya',
    },

    'r1808': {
        1: 'Marmer/Granit', 2: 'Keramik',      3: 'Parket/Vinil',
        4: 'Ubin/Tegel',    5: 'Kayu/Papan',   6: 'Semen/Bata merah',
        7: 'Bambu',         8: 'Tanah',         9: 'Lainnya',
    },

    'r1809a': {
        1: 'Sendiri',              2: 'Bersama RT tertentu',
        3: 'MCK komunal',          4: 'MCK/WC umum',
        5: 'Ada tapi tidak digunakan', 6: 'Tidak ada',
    },

    'r1809b': {
        1: 'Leher angsa', 2: 'Plengsengan',
        3: 'Cemplung/cubluk', 4: 'Tidak ada kloset',
    },

    'r1810a': {
        1:  'Air kemasan bermerk',    2:  'Air isi ulang',
        3:  'Leding meteran',         4:  'Leding eceran',
        5:  'Sumur bor/pompa',        6:  'Sumur terlindung',
        7:  'Sumur tak terlindung',   8:  'Mata air terlindung',
        9:  'Mata air tak terlindung',10: 'Air permukaan',
        11: 'Air hujan',              12: 'Lainnya',
    },

    'r1816': {
        1: 'PLN meteran sendiri',
        2: 'PLN meteran bersama/menumpang',
        3: 'Non-PLN',
        4: 'Bukan listrik',
    },

    # ⚠ Bahan bakar — paling sering berubah antar tahun
    # Ini versi 2020. Override di adapter tahun spesifik jika berbeda.
    'r1817': {
        0:  'Tidak memasak',
        1:  'Listrik',
        2:  'Gas/elpiji ≥5.5 kg',
        3:  'Gas/elpiji 3 kg',
        4:  'Gas kota',
        5:  'Biogas',
        6:  'Minyak tanah',
        7:  'Briket',
        8:  'Arang/batok kelapa',
        9:  'Kayu bakar',
        10: 'Lainnya',
    },
}

# ─── KLP pangan 2020 ──────────────────────────────────────────────────────────
# ⚠ Bergeser di 2024 karena sisipan komoditi baru. Override jika perlu.
BASE_KLP = {
    'padi_umbi'  : {'1', '8'},
    'ikan'       : {'16'},
    'daging'     : {'52'},
    'telur_susu' : {'62'},
    'sayur'      : {'72'},
    'kacang'     : {'98'},
    'buah'       : {'106'},
    'minyak'     : {'120'},
    'bhn_minuman': {'125'},
    'bumbu'      : {'133'},
    'lainnya'    : {'146'},
    'mkn_jadi'   : {'151'},
    'rokok'      : {'183'},
}

BASE_ALL14          = {'1','8','16','52','62','72','98','106',
                       '120','125','133','146','151','183'}
BASE_NO_TOB         = BASE_ALL14 - {'183'}
BASE_NO_TOB_PREP    = BASE_ALL14 - {'183','151'}
BASE_PREPARED_RANGE = (151, 182)
BASE_PROC_CODES     = {'167','168','177','178','180','181'}

BASE_FOOD_GROUP_HEADERS = {
    '1':   'PADI-PADIAN',    '8':   'UMBI-UMBIAN',
    '16':  'IKAN',           '52':  'DAGING',
    '62':  'TELUR DAN SUSU', '72':  'SAYUR-SAYURAN',
    '98':  'KACANG-KACANGAN','106': 'BUAH-BUAHAN',
    '120': 'MINYAK DAN KELAPA','125':'BAHAN MINUMAN',
    '133': 'BUMBU-BUMBUAN',  '146': 'BAHAN MAKANAN LAINNYA',
    '151': 'MAKANAN MINUMAN JADI', '183': 'ROKOK DAN TEMBAKAU',
}

# ─── RUNNER RT default (2020) ─────────────────────────────────────────────────
# Perubahan antar tahun yang mungkin perlu override:
#   - col 'r1806' → 'r1806a' di 2024
#   - mapping 'r1802' dikurangi dari 7 → 5 kode di 2024
#   - mapping 'r1817' kode bergeser di 2024
BASE_RUNNER_RT = [
    dict(kind='from_rt', out='UrbanRural', col='r105',
         map={'1': 'Perkotaan', '2': 'Perdesaan'}),

    dict(kind='from_rt', out='HomeOwnership', col='r1802',
         map={
             '1': 'Milik sendiri',      '2': 'Kontrak',
             '3': 'Sewa',               '4': 'Bebas sewa (orang lain)',
             '5': 'Bebas sewa (orang tua/saudara)',
             '6': 'Dinas',              '7': 'Lainnya',
         }),

    dict(kind='from_rt', out='RoofMaterial', col='r1806',
         map={
             '1': 'Beton',   '2': 'Genteng', '3': 'Sirap',
             '4': 'Seng',    '5': 'Asbes',   '6': 'Ijuk/Rumbia', '7': 'Lainnya',
         }),

    dict(kind='from_rt', out='WallMaterial', col='r1807',
         map={
             '1': 'Tembok',         '2': 'Plesteran anyaman',
             '3': 'Kayu/papan',     '4': 'Anyaman bambu',
             '5': 'Batang kayu',    '6': 'Bambu', '7': 'Lainnya',
         }),

    dict(kind='from_rt', out='FloorMaterial', col='r1808',
         map={
             '1': 'Marmer/Granit', '2': 'Keramik',        '3': 'Parket/Vinil',
             '4': 'Ubin/Tegel',    '5': 'Kayu/Papan',     '6': 'Semen/Bata merah',
             '7': 'Bambu',         '8': 'Tanah',           '9': 'Lainnya',
         }),

    dict(kind='from_rt', out='Sanitation', col='r1809a',
         map={
             '1': 'Sendiri',              '2': 'Bersama (RT tertentu)',
             '3': 'MCK komunal',          '4': 'MCK/WC umum',
             '5': 'Ada tapi tidak digunakan', '6': 'Tidak ada',
         }),

    dict(kind='from_rt', out='ToiletType', col='r1809b',
         map={
             '1': 'Leher angsa', '2': 'Plengsengan',
             '3': 'Cemplung/cubluk', '4': 'Tidak ada',
         }),

    dict(kind='from_rt', out='WaterSource', col='r1810a',
         map={
             '1':  'Air kemasan bermerk', '2':  'Air isi ulang',
             '3':  'Leding meteran',      '4':  'Leding eceran',
             '5':  'Sumur bor/pompa',     '6':  'Sumur terlindung',
             '7':  'Sumur tak terlindung','8':  'Mata air terlindung',
             '9':  'Mata air tak terlindung','10':'Air permukaan',
             '11': 'Air hujan',           '12': 'Lainnya',
         }),

    dict(kind='from_rt', out='AccessEnergy', col='r1816',
         map={
             '1': 'PLN_meteran_sendiri', '2': 'PLN_meteran_bersama',
             '3': 'Non_PLN',             '4': 'Bukan_listrik',
         }),

    dict(kind='from_rt', out='CookingFuel', col='r1817',
         map={
             '0': 'Tidak memasak', '1': 'Listrik',
             '2': 'Elpiji ≥5.5kg', '3': 'Elpiji 3kg',
             '4': 'Gas kota',      '5': 'Biogas',
             '6': 'Minyak tanah',  '7': 'Briket',
             '8': 'Arang/batok',   '9': 'Kayu bakar',
             '10': 'Lainnya',
         }),
]

# ─── RUNNER ART default (2020) ────────────────────────────────────────────────
# Perubahan antar tahun:
#   - col 'r706' → 'r707' di 2024 (status pekerjaan geser)
#   - truthy r701/r802: '2'=Tidak di 2020; '5'=Tidak di 2024
BASE_RUNNER_ART = [
    dict(kind='from_art_head', out='StatusPekerjaanKRT', col='r706',
         map={
             '1': 'Berusaha sendiri',
             '2': 'Berusaha + buruh tidak tetap',
             '3': 'Berusaha + buruh tetap',
             '4': 'Buruh/karyawan/pegawai',
             '5': 'Pekerja bebas',
             '6': 'Pekerja keluarga/tidak dibayar',
         }),

    dict(kind='any_art', out='HasSavingsAccount', col='r701',
         truthy=('1', '01'), yes='Ya', no='Tidak'),

    dict(kind='any_art', out='AccessCommunication', col='r802',
         truthy=('1', '01'), yes='Ya', no='Tidak'),
]

# ─── Kolom ketenagakerjaan (2017–2023) ───────────────────────────────────────
# Di 2024 ini semua bergeser — lihat susenas_2024.py
BASE_EMPLOYMENT = {
    'education_col'  : 'r615',    # ijazah tertinggi (2024: berganti makna)
    'activity_col'   : 'r703',    # kegiatan utama (2024: r704)
    'temp_notwork_col': 'r704',   # sementara tidak bekerja (2024: r705)
    'sector_col'     : 'r705',    # lapangan usaha (2024: r706)
    'status_col'     : 'r706',    # status pekerjaan (2024: r707)
    'hours_col'      : 'r707',    # jam kerja utama (2024: r708)
}


# ─── Helper: buat CONFIG untuk tahun tertentu ─────────────────────────────────
def make_config(year2d: str, *, has_wi3: bool = True) -> dict:
    """
    Buat CONFIG untuk tahun tertentu dengan prefix file yang benar.

    Parameters
    ----------
    year2d : str
        Dua digit tahun, misal '21', '22', '23', '24', '25'.
    has_wi3 : bool
        False untuk 2024+ (wi3 tidak ada di RT).

    Returns
    -------
    dict CONFIG

    Contoh:
        CONFIG = make_config('22')           # Susenas 2022
        CONFIG = make_config('24', has_wi3=False)  # Susenas 2024
    """
    c = copy.deepcopy(BASE_CONFIG)
    c['rt_file']    = f'kor{year2d}rt_diseminasi.csv'
    c['art_a_file'] = f'kor{year2d}ind_1_diseminasi.csv'
    c['art_b_file'] = f'kor{year2d}ind_2_diseminasi.csv'
    if not has_wi3:
        c['design_cols'] = [x for x in c['design_cols'] if x != 'wi3']
    return c


# ═══════════════════════════════════════════════════════════════════════════════
# BAGIAN 2 — EHCVM (UEMOA / World Bank, 8 negara Afrika Barat)
# ═══════════════════════════════════════════════════════════════════════════════
#
# Referensi: Basic Information Document EHCVM2 Benin (Septembre 2023)
# Questionnaire: 20 sections (s00–s20), data per section = satu file .dta
# Format file  : Stata (.dta), dibaca dengan pandas read_stata()
# Join key     : grappe (cluster) + menage (household no.) → composite key
# Survey waves : EHCVM1=2018/19, EHCVM2=2021/22
# Negara UEMOA : ben, bfa, civ, gnb, mli, ner, sen, tgo
#
# Mapping konsep EHCVM → logical feature (untuk RUNNER):
#   s00  → identifikasi & geolokasi
#   s01  → sosiodemografi ART (sep kolom per ART)
#   s02  → pendidikan ART (≥3 tahun)
#   s04a → status ketenagakerjaan ART (≥5 tahun)
#   s04b → pekerjaan utama ART
#   s06  → tabungan & kredit ART (≥15 tahun)
#   s07b → konsumsi pangan 7 hari (analog Blok41 Susenas)
#   s08  → ketahanan pangan FIES (analog R1701-R1708 Susenas)
#   s09b–s09f → pengeluaran non-pangan (6 recall period)
#   s11  → karakteristik perumahan (analog R1802-R1817 Susenas)
#   s12  → aset RT (analog R2001A-M Susenas)
#   s15  → jaring pengaman sosial (analog R2202-R2211 Susenas)

EHCVM_COUNTRY_CODES = {
    'ben': 'Benin',
    'bfa': 'Burkina Faso',
    'civ': "Côte d'Ivoire",
    'gnb': 'Guinea-Bissau',
    'mli': 'Mali',
    'ner': 'Niger',
    'sen': 'Senegal',
    'tgo': 'Togo',
}

EHCVM_WAVE_YEARS = {
    '2018': 'EHCVM1 (2018/19)',
    '2021': 'EHCVM2 (2021/22)',
}

# ─── CONFIG default EHCVM (Benin 2021 sebagai referensi) ─────────────────────
EHCVM_BASE_CONFIG = {
    # ── survey_family: digunakan pipeline untuk memilih reader & join logic ──
    'survey_family'  : 'ehcvm',

    # ── format file ──
    'file_format'    : 'stata',     # 'stata' → pd.read_stata(); 'csv' → pd.read_csv()
    'encoding'       : 'utf-8',

    # ── join key ──
    # EHCVM: composite key grappe+menage → di-hash menjadi hhid oleh reader
    'hh_id_col'      : 'hhid',      # nama kolom setelah composite key dibuat
    'cluster_col'    : 'grappe',    # primary sampling unit
    'hh_num_col'     : 'menage',    # household number within cluster

    # ── variabel desain survei ──
    'design_cols'    : ['grappe', 'menage', 'hhweight', 'vague', 'milieu'],

    # ── File pattern (diisi oleh make_ehcvm_config) ──
    # Pola: s{section}_me_{country}{year}.dta
    # Contoh Benin 2021: s11_me_ben_2021.dta
    'country'        : 'ben',
    'year'           : '2021',

    # ── HH-level files ──
    'hh_ident_file'  : 's00_me_ben_2021.dta',    # identifikasi & GPS
    'hh_housing_file': 's11_me_ben_2021.dta',    # perumahan (analog RT Susenas)
    'hh_assets_file' : 's12_me_ben_2021.dta',    # aset RT
    'hh_safety_file' : 's15_me_ben_2021.dta',    # safety nets
    'hh_fies_file'   : 's08a_me_ben_2021.dta',   # FIES food security

    # ── IND-level files ──
    'ind_socdemo_file': 's01_me_ben_2021.dta',   # sosiodemografi ART
    'ind_educ_file'   : 's02_me_ben_2021.dta',   # pendidikan ART
    'ind_empl_a_file' : 's04a_me_ben_2021.dta',  # status pasar kerja
    'ind_empl_b_file' : 's04b_me_ben_2021.dta',  # pekerjaan utama
    'ind_savings_file': 's06_me_ben_2021.dta',   # tabungan & kredit

    # ── Food consumption (analog KP41 Susenas) ──
    'food_file'      : 's07b_me_ben_2021.dta',   # konsumsi pangan 7 hari

    # ── Non-food expenditure (analog KP42 Susenas) ──
    # Recall periods: 7d, 30d, 3m, 6m, 12m (+ ceremonies 12m)
    'nonfood_files'  : {
        'ceremonies_12m': 's09a_me_ben_2021.dta',
        'nonfood_7d'    : 's09b_me_ben_2021.dta',
        'nonfood_30d'   : 's09c_me_ben_2021.dta',
        'nonfood_3m'    : 's09d_me_ben_2021.dta',
        'nonfood_6m'    : 's09e_me_ben_2021.dta',
        'nonfood_12m'   : 's09f_me_ben_2021.dta',
    },

    # ── Auxiliary files ──
    'nsu_file'       : 'ehcvm_NSU_ben_2021.dta',      # non-standard unit conversion
    'prices_file'    : 'ehcvm_prix_ben_2021.dta',     # price data
    'weights_file'   : 'ehcvm_ponderations_ben2021.dta',
    'welfare_file'   : 'ehcvm_welfare_ben_2021.dta',  # poverty indicators
    'consumption_file': 'ehcvm_conso_ben_2021.dta',   # annual consumption per product
}

# ─── Value labels EHCVM (berdasarkan BID Benin 2021) ─────────────────────────
# Catatan: kode nilai EHCVM diverifikasi dari dokumen BID dan codebook EHCVM2.
# Variabel menggunakan skema s{section}q{question_number}.
# Contoh: s11q04 = Section 11, Question 4 (tipe atap)
#
# ⚠ Kode nilai EHCVM mungkin berbeda antar negara untuk beberapa variabel
#   (terutama material bangunan dan jenis toilet) — override di adapter negara.

EHCVM_BASE_VALUE_LABELS = {

    # ── Identifikasi & geografis ──
    'milieu': {1: 'Urbain', 2: 'Rural'},   # area of residence

    # ── Sosiodemografi (s01) ──
    's01q01': {  # lien de parenté (hubungan dengan KRT)
        1: 'Chef de ménage',  2: 'Époux/Épouse',
        3: 'Fils/Fille',      4: 'Père/Mère',
        5: 'Beau-fils/Belle-fille', 6: 'Petit-fils/Petite-fille',
        7: 'Frère/Sœur',     8: 'Autre parent',
        9: 'Sans lien de parenté',
    },
    's01q02': {1: 'Masculin', 2: 'Féminin'},  # sexe

    # ── Pendidikan (s02) ──
    's02q05': {   # niveau d'instruction le plus élevé
        0: 'Aucun',
        1: 'Primaire',
        2: 'Secondaire 1er cycle',
        3: 'Secondaire 2ème cycle',
        4: 'Supérieur',
        5: 'Alphabétisation/non-formel',
    },

    # ── Ketenagakerjaan (s04a) ──
    's04aq06': {   # situation dans l'emploi (status pekerjaan utama)
        1: 'Employeur',
        2: 'Salarié permanent',
        3: 'Salarié temporaire',
        4: 'Travailleur pour compte propre',
        5: 'Travailleur familial non rémunéré',
        6: 'Apprenti',
        7: 'Autre',
    },
    's04aq02': {   # activité 7 derniers jours (kegiatan 7 hari terakhir)
        1: 'Travail',
        2: 'École',
        3: 'Ménage',
        4: 'Retraite',
        5: 'Chômeur',
        6: 'Inactif autre',
    },

    # ── Perumahan (s11) ──
    's11q01': {   # statut occupation logement (kepemilikan)
        1: 'Propriétaire',
        2: 'Locataire',
        3: 'Logé gratuitement',
        4: 'Logement de fonction',
        5: 'Autre',
    },
    's11q04': {   # matériau toit (atap)
        1: 'Tôle/Zinc',
        2: 'Béton/Dalle',
        3: 'Tuile',
        4: 'Bois/Planche',
        5: 'Paille/Chaume',
        6: 'Autre',
    },
    's11q05': {   # matériau mur (dinding)
        1: 'Béton/Parpaing/Pierre',
        2: 'Brique cuite',
        3: 'Brique crue/Banco',
        4: 'Bois/Planches',
        5: 'Paille/Tige',
        6: 'Autre',
    },
    's11q06': {   # matériau sol (lantai)
        1: 'Carrelage/Marbre',
        2: 'Ciment',
        3: 'Terre battue',
        4: 'Bois/Parquet',
        5: 'Autre',
    },
    's11q12': {   # source eau potable saison sèche (sumber air musim kering)
        1: "Eau courante dans logement",
        2: "Eau courante dans cour",
        3: "Borne fontaine/robinet public",
        4: "Puits protégé",
        5: "Puits non protégé",
        6: "Source protégée",
        7: "Source non protégée",
        8: "Eau de pluie",
        9: "Camion citerne/revendeur",
        10: "Eau de surface",
        11: "Autre",
    },
    's11q18': {   # type aisances (jenis toilet)
        1: "WC avec chasse d'eau",
        2: 'Latrines améliorées (VTIP)',
        3: 'Latrines ordinaires',
        4: 'Pas de toilettes',
    },
    's11q21': {   # source éclairage (sumber penerangan)
        1: 'Électricité réseau',
        2: 'Groupe électrogène',
        3: 'Panneau solaire',
        4: 'Lampe-torche/Piles',
        5: 'Bougie',
        6: 'Pétrole/Gaz lampant',
        7: 'Autre',
    },
    's11q26': {   # combustible cuisine (bahan bakar memasak)
        1: 'Gaz butane',
        2: 'Électricité',
        3: 'Pétrole lampant/Kérosène',
        4: 'Charbon de bois',
        5: 'Bois de chauffe',
        6: 'Autre',
    },

    # ── FIES food security (s08a) ──
    # Nilai: 1=Oui (Ya), 2=Non (Tidak) — periode 12 bulan
    's08aq01': {1: 'Oui', 2: 'Non'},  # inquiet nourriture insuffisante
    's08aq02': {1: 'Oui', 2: 'Non'},  # pas manger aliments sains
    's08aq03': {1: 'Oui', 2: 'Non'},  # peu de variété
    's08aq04': {1: 'Oui', 2: 'Non'},  # sauter repas
    's08aq05': {1: 'Oui', 2: 'Non'},  # manger moins
    's08aq06': {1: 'Oui', 2: 'Non'},  # manquer nourriture
    's08aq07': {1: 'Oui', 2: 'Non'},  # faim pas manger
    's08aq08': {1: 'Oui', 2: 'Non'},  # passer journée sans manger
}

# ─── RUNNER HH (household-level) untuk EHCVM ─────────────────────────────────
# Setiap item memetakan satu kolom dari satu file ke satu fitur output.
# 'file' menunjuk ke kunci di CONFIG (mis. 'hh_housing_file').
# Ini berbeda dari Susenas di mana semua RT ada di satu file.
EHCVM_BASE_RUNNER_HH = [
    dict(kind='from_hh', out='UrbanRural', file='hh_ident_file',
         col='milieu', map={'1': 'Urbain', '2': 'Rural'}),

    dict(kind='from_hh', out='HomeOwnership', file='hh_housing_file',
         col='s11q01',
         map={'1':'Propriétaire','2':'Locataire','3':'Logé gratuitement',
              '4':'Logement de fonction','5':'Autre'}),

    dict(kind='from_hh', out='RoofMaterial', file='hh_housing_file',
         col='s11q04',
         map={'1':'Tôle/Zinc','2':'Béton/Dalle','3':'Tuile',
              '4':'Bois/Planche','5':'Paille/Chaume','6':'Autre'}),

    dict(kind='from_hh', out='WallMaterial', file='hh_housing_file',
         col='s11q05',
         map={'1':'Béton/Parpaing','2':'Brique cuite','3':'Brique crue/Banco',
              '4':'Bois/Planches','5':'Paille/Tige','6':'Autre'}),

    dict(kind='from_hh', out='FloorMaterial', file='hh_housing_file',
         col='s11q06',
         map={'1':'Carrelage/Marbre','2':'Ciment','3':'Terre battue',
              '4':'Bois/Parquet','5':'Autre'}),

    dict(kind='from_hh', out='WaterSource', file='hh_housing_file',
         col='s11q12',
         map={'1':'Eau courante logement','2':'Eau courante cour',
              '3':'Borne fontaine','4':'Puits protégé','5':'Puits non protégé',
              '6':'Source protégée','7':'Source non protégée',
              '8':'Eau de pluie','9':'Camion/revendeur',
              '10':'Eau de surface','11':'Autre'}),

    dict(kind='from_hh', out='ToiletType', file='hh_housing_file',
         col='s11q18',
         map={'1':'WC chasse','2':'Latrines améliorées',
              '3':'Latrines ordinaires','4':'Pas de toilettes'}),

    dict(kind='from_hh', out='AccessEnergy', file='hh_housing_file',
         col='s11q21',
         map={'1':'Électricité_réseau','2':'Groupe_électrogène',
              '3':'Panneau_solaire','4':'Lampe_torche',
              '5':'Bougie','6':'Pétrole/Gaz','7':'Autre'}),

    dict(kind='from_hh', out='CookingFuel', file='hh_housing_file',
         col='s11q26',
         map={'1':'Gaz butane','2':'Électricité','3':'Pétrole/Kérosène',
              '4':'Charbon de bois','5':'Bois de chauffe','6':'Autre'}),

    # ── FIES (s08a) — 8 items, nilai 1=Oui/2=Non ──
    dict(kind='from_hh', out='FoodInsecurity_Worry',    file='hh_fies_file',
         col='s08aq01', map={'1':'Oui','2':'Non'}),
    dict(kind='from_hh', out='FoodInsecurity_NoHealthy',file='hh_fies_file',
         col='s08aq02', map={'1':'Oui','2':'Non'}),
    dict(kind='from_hh', out='FoodInsecurity_FewKinds', file='hh_fies_file',
         col='s08aq03', map={'1':'Oui','2':'Non'}),
    dict(kind='from_hh', out='FoodInsecurity_SkipMeal', file='hh_fies_file',
         col='s08aq04', map={'1':'Oui','2':'Non'}),
    dict(kind='from_hh', out='FoodInsecurity_EatLess',  file='hh_fies_file',
         col='s08aq05', map={'1':'Oui','2':'Non'}),
    dict(kind='from_hh', out='FoodInsecurity_RanOut',   file='hh_fies_file',
         col='s08aq06', map={'1':'Oui','2':'Non'}),
    dict(kind='from_hh', out='FoodInsecurity_Hungry',   file='hh_fies_file',
         col='s08aq07', map={'1':'Oui','2':'Non'}),
    dict(kind='from_hh', out='FoodInsecurity_NoBowl',   file='hh_fies_file',
         col='s08aq08', map={'1':'Oui','2':'Non'}),
]

# ─── RUNNER IND untuk EHCVM ───────────────────────────────────────────────────
EHCVM_BASE_RUNNER_IND = [
    # Status pekerjaan KRT dari s04a
    dict(kind='from_ind_head', out='StatusPekerjaanKRT',
         file='ind_empl_a_file', col='s04aq06',
         map={'1':'Employeur','2':'Salarié permanent','3':'Salarié temporaire',
              '4':'Compte propre','5':'Familial non rémunéré',
              '6':'Apprenti','7':'Autre'}),

    # Tabungan dari s06 (any ART in HH)
    dict(kind='any_ind', out='HasSavingsAccount',
         file='ind_savings_file', col='s06q01',
         truthy=('1',), yes='Oui', no='Non'),

    # HP dari s01 (telpor — mobile phone)
    dict(kind='any_ind', out='AccessCommunication',
         file='ind_socdemo_file', col='s01q22',
         truthy=('1',), yes='Oui', no='Non'),
]

# ─── Kolom ketenagakerjaan EHCVM ─────────────────────────────────────────────
EHCVM_BASE_EMPLOYMENT = {
    'socdemo_file'    : 'ind_socdemo_file',  # s01
    'education_file'  : 'ind_educ_file',     # s02
    'education_col'   : 's02q05',            # niveau instruction
    'activity_file'   : 'ind_empl_a_file',   # s04a
    'activity_col'    : 's04aq02',           # kegiatan 7 hari terakhir
    'empstatus_file'  : 'ind_empl_a_file',   # s04a
    'empstatus_col'   : 's04aq06',           # status pekerjaan
    'sector_file'     : 'ind_empl_b_file',   # s04b
    'sector_col'      : 's04bq03',           # lapangan usaha (branche d'activité)
    'savings_file'    : 'ind_savings_file',  # s06
    'savings_col'     : 's06q01',            # a un compte bancaire
}

# ─── Struktur konsumsi pangan EHCVM (s07b) ───────────────────────────────────
# s07b analog dengan Blok41 Susenas, tapi dengan nama kolom berbeda
# Kolom utama:
#   codpr    : kode produk (COICOP-based, harmonized across UEMOA)
#   s07bq01  : dikonsumsi? (1=oui)
#   s07bq02c : nilai konsumsi total (FCFA/minggu) — analog B41K10 Susenas
#   s07bq02e : dari pembelian (FCFA) — analog B41K6
#   s07bq02g : dari produksi sendiri/hadiah (FCFA) — analog B41K8
# Tidak ada kolom KLP di EHCVM — produk dikelompokkan via codpr COICOP range
EHCVM_FOOD_COL_MAP = {
    'product_code'  : 'codpr',
    'consumed_flag' : 's07bq01',
    'value_total'   : 's07bq02c',
    'value_purchase': 's07bq02e',
    'value_own_prod': 's07bq02g',
}

# ─── Helper: buat CONFIG EHCVM ────────────────────────────────────────────────
def make_ehcvm_config(country: str, year: str) -> dict:
    """
    Buat CONFIG untuk negara dan tahun EHCVM tertentu.

    Parameters
    ----------
    country : str
        Kode negara 3 huruf kecil. Nilai valid: 'ben','bfa','civ','gnb',
        'mli','ner','sen','tgo'.
    year : str
        Tahun survei 4 digit: '2018' (EHCVM1) atau '2021' (EHCVM2).

    Returns
    -------
    dict CONFIG dengan semua nama file yang sudah disesuaikan.

    Contoh:
        CONFIG = make_ehcvm_config('ben', '2021')  # Benin EHCVM2
        CONFIG = make_ehcvm_config('bfa', '2021')  # Burkina EHCVM2
    """
    if country not in EHCVM_COUNTRY_CODES:
        raise ValueError(f"country '{country}' tidak valid. Pilih: {list(EHCVM_COUNTRY_CODES)}")
    if year not in EHCVM_WAVE_YEARS:
        raise ValueError(f"year '{year}' tidak valid. Pilih: {list(EHCVM_WAVE_YEARS)}")

    c = copy.deepcopy(EHCVM_BASE_CONFIG)
    c['country'] = country
    c['year']    = year

    # Suffix untuk nama file
    sfx = f'{country}_{year}'          # mis. ben_2021
    sfx_short = f'{country}{year}'     # mis. ben2021 (untuk beberapa file aux)

    # HH-level files
    c['hh_ident_file']   = f's00_me_{sfx}.dta'
    c['hh_housing_file'] = f's11_me_{sfx}.dta'
    c['hh_assets_file']  = f's12_me_{sfx}.dta'
    c['hh_safety_file']  = f's15_me_{sfx}.dta'
    c['hh_fies_file']    = f's08a_me_{sfx}.dta'

    # IND-level files
    c['ind_socdemo_file'] = f's01_me_{sfx}.dta'
    c['ind_educ_file']    = f's02_me_{sfx}.dta'
    c['ind_empl_a_file']  = f's04a_me_{sfx}.dta'
    c['ind_empl_b_file']  = f's04b_me_{sfx}.dta'
    c['ind_savings_file'] = f's06_me_{sfx}.dta'

    # Food & non-food
    c['food_file'] = f's07b_me_{sfx}.dta'
    c['nonfood_files'] = {
        'ceremonies_12m': f's09a_me_{sfx}.dta',
        'nonfood_7d'    : f's09b_me_{sfx}.dta',
        'nonfood_30d'   : f's09c_me_{sfx}.dta',
        'nonfood_3m'    : f's09d_me_{sfx}.dta',
        'nonfood_6m'    : f's09e_me_{sfx}.dta',
        'nonfood_12m'   : f's09f_me_{sfx}.dta',
    }

    # Auxiliary files
    c['nsu_file']         = f'ehcvm_NSU_{sfx}.dta'
    c['prices_file']      = f'ehcvm_prix_{sfx}.dta'
    c['weights_file']     = f'ehcvm_ponderations_{sfx_short}.dta'
    c['welfare_file']     = f'ehcvm_welfare_{sfx}.dta'
    c['consumption_file'] = f'ehcvm_conso_{sfx}.dta'

    return c
