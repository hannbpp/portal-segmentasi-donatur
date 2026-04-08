"""
Portal Segmentasi Donatur — Dompet Ummat Kalimantan Barat
=========================================================
Penerapan Algoritma K-Means Clustering Berbasis Metode RFM
untuk Segmentasi Donatur.

Jalankan dengan:
    streamlit run app.py
"""

import streamlit as st
import sys
import os

# Tambahkan root project ke path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import APP_TITLE, APP_SUBTITLE, APP_ICON

# ---- Page Config ----
st.set_page_config(
    page_title=f"{APP_TITLE} — {APP_SUBTITLE}",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- Custom CSS ----
st.markdown("""
<style>
    /* Main header */
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #1a5276, #2ecc71);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #7f8c8d;
        margin-top: -10px;
        margin-bottom: 20px;
    }
    
    /* Metric cards */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        border-radius: 12px;
        padding: 16px;
        border-left: 4px solid #2ecc71;
    }
    [data-testid="stMetric"] label {
        font-size: 0.85rem;
        color: #6c757d;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a252f, #2c3e50);
    }
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown li {
        color: #ecf0f1;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        font-weight: 600;
    }
    
    /* Table */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# ---- Sidebar ----
with st.sidebar:
    st.markdown(f"## {APP_ICON} {APP_TITLE}")
    st.markdown(f"*{APP_SUBTITLE}*")
    st.divider()
    
    st.markdown("### 📄 Navigasi")
    st.markdown("""
    - **📊 Overview** — Ringkasan data donatur
    - **📤 Upload Data** — Upload data donasi baru
    - **🎯 Analisis RFM** — RFM scoring, clustering (K-Means / K-Medoids / DBSCAN), silhouette analysis, hyperparameter tuning
    - **👥 Profil Segmen** — Hasil & rekomendasi strategi
    """)
    
    st.divider()
    st.caption("Dzaky Farhan — MBSI Untan 2026")
    st.caption("Magang di Dompet Ummat KalBar")

# ---- Main Page (Home) ----
st.markdown('<p class="main-title">🎯 Portal Segmentasi Donatur</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Dompet Ummat Kalimantan Barat — Analisis RFM & K-Means Clustering</p>', unsafe_allow_html=True)

st.markdown("""
> **Selamat datang!** Portal ini digunakan untuk menganalisis dan mengelompokkan donatur 
> Dompet Ummat Kalimantan Barat berdasarkan perilaku donasi mereka menggunakan metode 
> **RFM (Recency, Frequency, Monetary)** dan algoritma **K-Means Clustering**.
""")

# Quick overview
st.markdown("---")
col1, col2, col3 = st.columns(3)

try:
    from utils.db_connection import run_query
    
    stats = run_query("""
        SELECT 
            (SELECT COUNT(*) FROM dim_donatur) AS total_donatur,
            (SELECT COUNT(*) FROM fact_donasi) AS total_transaksi,
            (SELECT COALESCE(SUM(nominal_valid), 0) FROM fact_donasi) AS total_donasi
    """)
    
    with col1:
        st.metric("👤 Total Donatur", f"{stats['total_donatur'].iloc[0]:,}")
    with col2:
        st.metric("📋 Total Transaksi", f"{stats['total_transaksi'].iloc[0]:,}")
    with col3:
        total = float(stats['total_donasi'].iloc[0])
        if total >= 1_000_000_000:
            st.metric("💰 Total Donasi", f"Rp {total/1_000_000_000:.1f} M")
        else:
            st.metric("💰 Total Donasi", f"Rp {total/1_000_000:.0f} Juta")

except Exception as e:
    st.error(f"⚠️ Gagal koneksi ke database: {str(e)}")
    st.info("Pastikan MySQL (MAMP) sudah berjalan di port 8889.")

# Cara pakai
st.markdown("---")
st.markdown("### 🚀 Cara Menggunakan Portal")

col_a, col_b, col_c, col_d = st.columns(4)
with col_a:
    st.markdown("""
    **1️⃣ Overview**  
    Lihat ringkasan data donatur dan trend donasi.
    """)
with col_b:
    st.markdown("""
    **2️⃣ Upload Data**  
    Upload file CSV/Excel data donasi terbaru.
    """)
with col_c:
    st.markdown("""
    **3️⃣ Analisis RFM**  
    Hitung skor RFM dan jalankan clustering.
    """)
with col_d:
    st.markdown("""
    **4️⃣ Profil Segmen**  
    Lihat hasil segmentasi dan rekomendasi strategi.
    """)

# Info teknis
with st.expander("ℹ️ Informasi Teknis"):
    st.markdown("""
    | Komponen | Detail |
    |----------|--------|
    | **Database** | MySQL (MAMP) — `dompet_ummat_dw` |
    | **Metode Analisis** | RFM (Recency, Frequency, Monetary) |
    | **Algoritma Clustering** | K-Means, K-Medoids, DBSCAN |
    | **Evaluasi** | Silhouette Score, Davies-Bouldin Index, Calinski-Harabasz Index |
    | **Fitur Lanjutan** | Hyperparameter Tuning, Silhouette Plot, K-Distance Graph |
    | **Sumber Data** | Data Warehouse Dompet Ummat KalBar |
    """)
