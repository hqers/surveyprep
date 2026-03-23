# SurveyPrep

**Modular preprocessing framework untuk data survei pengeluaran rumah tangga bertipe campuran.**

Diorganisasi berdasarkan **tipe modul survei** (bukan nama file), sehingga dapat diadaptasi ke survei negara lain hanya dengan mendefinisikan ulang mapping variabel.

---

## Struktur Paket

```
surveyprep/
├── core/
│   ├── reader.py       ← Pembaca CSV adaptif (format BPS & generik)
│   ├── runner.py       ← Mesin eksekusi RUNNER pattern
│   ├── imputer.py      ← Imputasi tipe-sadar (median/mode, no encoding)
│   └── exporter.py     ← Dual output: profiling-ready & clustering-ready
├── susenas/
│   ├── hh_record.py    ← Modul RT: karakteristik RT, akses layanan
│   ├── individual.py   ← Modul ART: merge A+B, ekstraksi KRT, sosiodem
│   ├── food_exp.py     ← Modul KP41: konversi W2M, DDS, kelompok pangan
│   ├── nonfood_exp.py  ← Modul KP42/43: ANNUAL_CODES, breakdown tematik
│   └── integrator.py   ← Merge semua modul + hitung shares/burdens
├── adapters/
│   └── susenas_2020.py ← Konfigurasi resmi Susenas 2020 (mapping BPS)
└── pipeline.py         ← Entry point: run_susenas_pipeline()
```

---

## Penggunaan Cepat (Susenas)

```python
from surveyprep.pipeline import run_susenas_pipeline

df = run_susenas_pipeline(
    data_dir   = "data/",        # direktori berisi semua CSV Susenas
    output_dir = "outputs/",     # opsional: simpan dual output
    verbose    = True,
)
# df: 334.229 RT × ~34 kolom (22 numerik + 12 kategorik)
```

Output otomatis:
- `HH_PROFILING_with_weights.csv` — lengkap dengan bobot survei
- `HH_CLUSTERING_ready.csv` — fitur konten saja, siap untuk AUFS-Samba/MixClust
- `HH_WEIGHTS_sidecar.csv` — HHID + bobot untuk post-clustering merge

---

## Tiga Inovasi Desain

### 1. Abstraksi Empat Tipe Modul Survei

| Tipe Modul | Fungsi | Susenas | LSMS | EU-HBS |
|---|---|---|---|---|
| HH-Record | Data RT: akses layanan, karakteristik fisik | `kor20rt_*` | `hh_sec_a` | `HBS_HH` |
| Individual-Record | Data individu: demografi, pendidikan, kerja | `kor20ind_1/2_*` | `hh_sec_b` | `HBS_IND` |
| Food-Expenditure | Konsumsi pangan per komoditas, mingguan | `Blok41_gab*.csv` | `hh_sec_j1` | `HBS_FOOD` |
| NonFood-Expenditure | Pengeluaran non-pangan, bulanan+tahunan | `blok42*.csv` | `hh_sec_j2` | `HBS_NFOOD` |

### 2. RUNNER Pattern

Tambahkan variabel baru ke pipeline tanpa mengubah kode — cukup tambahkan satu entri di daftar:

```python
from surveyprep.pipeline import run_susenas_pipeline

extra = [
    # Tambah luas lantai (r1804) dari RT
    dict(kind='from_rt', out='FloorArea_m2', col='r1804'),
    
    # Tambah status disabilitas KRT (r1009 dari ART)
    dict(kind='from_art_head', out='DisabilityHead', col='r1009',
         map={'1':'Tidak ada', '2':'Ringan', '3':'Sedang', '4':'Berat'}),
    
    # Flag: ada ART yang pernah rawat inap (r1201)
    dict(kind='any_art', out='AnyHospitalized', col='r1201',
         truthy=('1','01'), yes='Ya', no='Tidak'),
]

df = run_susenas_pipeline(
    data_dir="data/",
    extra_runner_rt=[extra[0]],
    extra_runner_art=extra[1:],
)
```

Tiga jenis sumber RUNNER:
- `from_rt` — variabel langsung dari file RT (satu baris per RT)
- `from_art_head` — variabel dari baris KRT di file ART
- `any_art` — flag True jika ada anggota RT yang memenuhi kondisi

### 3. Dual Output (Profiling vs Clustering)

```
Profiling-ready  = semua kolom + PSU + strata + bobot
                   → untuk analisis berbobot, tabulasi BPS

Clustering-ready = fitur konten saja (tanpa bobot/desain)  
                   → input langsung ke AUFS-Samba + MixClust

Sidecar weights  = HHID + semua variabel desain
                   → untuk merge bobot setelah klasterisasi
```

---

## Fitur yang Dihasilkan (Susenas 2020)

| Kategori | Fitur | Tipe |
|---|---|---|
| Share pangan | FoodShare, PlantProteinShare, FVShare, TobaccoShare, PreparedFoodShare, ... | Numerik [0,1] |
| Burden pengeluaran | EnergyBurden, HealthShare, EducationShare, HousingShare, TransportShare, ... | Numerik [0,1] |
| Dietary Diversity | DDS14_norm, DDS13_noTob_norm, DDS12_noTobPrep_norm | Numerik [0,1] |
| Karakteristik RT | HouseholdSize, WorkerShare, DependencyRatio, AgeHead | Numerik |
| Akses layanan | AccessEnergy, Sanitation, CookingFuel, WaterSource, HomeOwnership | Kategorik |
| Sosio-demografi KRT | EducationHead, OccupationHeadSector, SexHead, UrbanRural | Kategorik |
| Komunikasi & keuangan | AccessCommunication, HasSavingsAccount | Kategorik |
| Status pekerjaan | StatusPekerjaanKRT | Kategorik |

---

## Adaptasi ke Tahun Lain

Untuk Susenas 2022, 2023, dst.:

```python
# 1. Salin adapter
cp surveyprep/adapters/susenas_2020.py surveyprep/adapters/susenas_2022.py

# 2. Edit nama file dan mapping yang berubah
# 3. Gunakan:
from surveyprep.adapters.susenas_2022 import CONFIG
df = run_susenas_pipeline(data_dir="data/2022/", config=CONFIG)
```

Variabel yang paling sering berubah antar tahun:
- `r1817` (bahan bakar memasak) — kode Elpiji dapat berubah
- `r701` (rekening tabungan) — baru muncul di 2020
- Variabel inklusi keuangan — bervariasi per tahun

---

## Dependensi

```
numpy  >= 1.24
pandas >= 2.0
```

Tidak membutuhkan scikit-learn untuk preprocessing (hanya numpy + pandas).
scikit-learn dibutuhkan untuk tahap klasterisasi hilir (AUFS-Samba, MixClust).

---

## Catatan Data

Data mentah Susenas tidak dapat dibagikan secara publik (restriksi BPS).
Kode pipeline ini open-source — peneliti dengan akses data yang sama
dapat mereplikasi hasil dengan sempurna menggunakan kode ini.

---

## Lisensi

MIT License — bebas digunakan untuk penelitian dan pendidikan.

## Sitasi

Jika menggunakan SurveyPrep dalam penelitian, mohon sitasi:

> Pratama, H., Lubis, F.F., Sembiring, J. (2026). *A Survey-Module-Aware 
> Modular Preprocessing Framework for Mixed-Type Household Expenditure Data*.
> SoftwareX (submitted).
