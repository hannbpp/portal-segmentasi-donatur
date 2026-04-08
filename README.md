# 🎯 Portal Segmentasi Donatur — Dompet Ummat Kalimantan Barat

Penerapan Algoritma K-Means, K-Medoids, dan DBSCAN Clustering Berbasis Metode RFM (Recency, Frequency, Monetary) untuk Segmentasi Donatur Lembaga Filantropi.

## 📋 Tentang Proyek

Portal web berbasis **Streamlit** yang mengimplementasikan pipeline Business Intelligence end-to-end untuk segmentasi donatur Dompet Ummat Kalimantan Barat. Sistem ini memungkinkan analisis perilaku donasi menggunakan metode RFM yang dikombinasikan dengan beberapa algoritma clustering untuk menghasilkan segmen donatur yang bermakna secara bisnis.

### Fitur Utama

| Fitur | Deskripsi |
|-------|-----------|
| 📊 **Dashboard Overview** | Ringkasan statistik donatur, trend donasi, dan distribusi metode donasi |
| 📤 **Upload Data** | Upload CSV/Excel donasi baru dengan validasi & cleaning otomatis |
| 🎯 **Analisis RFM & Clustering** | Hitung skor RFM, jalankan 3 metode clustering, bandingkan hasil |
| 🔬 **Silhouette Analysis** | Analisis mendalam kualitas cluster per sample |
| ⚡ **Hyperparameter Tuning** | Grid search untuk K-Means dan DBSCAN |
| 👥 **Profil Segmen** | Visualisasi profil cluster + rekomendasi strategi retensi |

### Algoritma Clustering

- **K-Means** — Partitioning berbasis centroid, optimal untuk cluster berbentuk spherical
- **K-Medoids (PAM)** — Lebih robust terhadap outlier, menggunakan medoid sebagai pusat cluster
- **DBSCAN** — Density-based, otomatis menemukan jumlah cluster dan mendeteksi noise/outlier

### Metrik Evaluasi

- Silhouette Score (kualitas separasi cluster)
- Davies-Bouldin Index (kompaktness & separasi)
- Calinski-Harabasz Index (rasio dispersi antar/intra cluster)
- Elbow Method (penentuan K optimal)
- K-Distance Graph (estimasi parameter eps DBSCAN)

## 🛠️ Teknologi

| Komponen | Teknologi |
|----------|-----------|
| Frontend | Streamlit |
| Backend | Python 3.13 |
| Database | MySQL (MAMP) |
| ML/Analytics | Scikit-learn, Scikit-learn-extra |
| Visualisasi | Plotly |
| Data Processing | Pandas, NumPy |

## 📁 Struktur Proyek

```
portal_segmentasi_donatur/
├── app.py                    # Entry point Streamlit
├── config.py                 # Konfigurasi database & aplikasi
├── requirements.txt          # Dependencies Python
├── .gitignore
├── README.md
├── pages/
│   ├── 1_📊_Overview.py      # Dashboard overview
│   ├── 2_📤_Upload_Data.py   # Upload data baru
│   ├── 3_🎯_Analisis_RFM.py  # RFM scoring & clustering
│   └── 4_👥_Profil_Segmen.py # Profil segmen & rekomendasi
└── utils/
    ├── __init__.py
    ├── db_connection.py       # Helper koneksi MySQL
    ├── rfm_engine.py          # Mesin penghitung RFM
    ├── clustering_engine.py   # K-Means, K-Medoids, DBSCAN
    └── data_uploader.py       # Validasi & upload data
```

## 🚀 Cara Menjalankan

### 1. Clone repository
```bash
git clone https://github.com/dzakyfarhan/portal-segmentasi-donatur.git
cd portal-segmentasi-donatur
```

### 2. Setup virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Konfigurasi database
Edit `config.py` sesuai dengan setup MySQL Anda:
```python
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 8889,        # Sesuaikan port MySQL
    "user": "root",
    "password": "root",
    "database": "dompet_ummat_dw",
}
```

### 4. Jalankan aplikasi
```bash
streamlit run app.py
```

Portal akan terbuka di `http://localhost:8501`.

## 📊 Alur Kerja

```
Data Donasi (CSV/Excel)
        │
        ▼
   [Upload & Validasi]
        │
        ▼
   [Data Cleaning Otomatis]
        │
        ▼
   [Insert ke Data Warehouse]
        │
        ▼
   [Hitung Skor RFM]
        │
        ▼
   [Clustering: K-Means / K-Medoids / DBSCAN]
        │
        ▼
   [Evaluasi & Perbandingan Metode]
        │
        ▼
   [Profil Segmen & Rekomendasi Strategi]
```

## 👤 Penulis

**Dzaky Farhan** — Program Studi Manajemen dan Bisnis Sistem Informasi (MBSI), Universitas Tanjungpura, 2026.

Proyek ini merupakan bagian dari kegiatan magang di **Dompet Ummat Kalimantan Barat**.

## 📄 Lisensi

Proyek ini dibuat untuk keperluan akademis dan tidak untuk distribusi komersial.
