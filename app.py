"""
Portal Segmentasi Donatur — Dompet Ummat Kalimantan Barat
=========================================================
Jalankan dengan: streamlit run app.py
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import APP_TITLE, APP_SUBTITLE
from utils.styles import (
    get_global_css, kpi_card, section_header, icon_html,
    DU_GREEN_4, DU_GREEN_5, DU_GREEN_1,
)

# ---- Page Config ----
st.set_page_config(
    page_title=f"{APP_TITLE} — {APP_SUBTITLE}",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- Global CSS ----
st.markdown(get_global_css(), unsafe_allow_html=True)

# ---- Sidebar ----
with st.sidebar:
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
        {icon_html("hand-coins", color="#78C51C", size=24)}
        <span style="font-size:1.1rem;font-weight:700;color:#fff !important;">Dompet Ummat</span>
    </div>
    <div style="font-size:0.7rem;color:rgba(255,255,255,0.5) !important;margin-bottom:12px;">Portal Segmentasi Donatur</div>
    """, unsafe_allow_html=True)
    st.divider()

    # Credit
    st.markdown(f"""
    <div style="
        background: rgba(120,197,28,0.1);
        border-radius: 10px; padding: 12px;
        border: 1px solid rgba(120,197,28,0.2);
        margin-top: 8px;
    ">
        <div style="font-size:0.65rem;font-weight:600;color:rgba(255,255,255,0.5) !important;margin-bottom:3px;text-transform:uppercase;letter-spacing:0.5px;">
            Dibuat oleh
        </div>
        <div style="font-size:0.82rem;font-weight:600;color:#fff !important;">
            Dzaky Farhan
        </div>
        <div style="font-size:0.68rem;color:rgba(255,255,255,0.5) !important;margin-top:1px;">
            MBSI Untan — Magang 2026
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---- Main Page (Home) ----
header_icon = icon_html("hand-coins", color=DU_GREEN_4, size=32)
st.markdown(f"""
<div style="margin-bottom: 18px;">
    <div style="display:flex;align-items:center;gap:10px;">
        {header_icon}
        <div>
            <div style="font-size:1.7rem;font-weight:700;color:#1a252f;letter-spacing:-0.5px;line-height:1.2;">
                Portal Segmentasi Donatur
            </div>
            <div style="font-size:0.85rem;color:#6c757d;margin-top:2px;">
                Dompet Ummat Kalimantan Barat — Analisis RFM & K-Means Clustering
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Welcome card
st.markdown(f"""
<div style="
    background: linear-gradient(135deg, {DU_GREEN_1} 0%, #d5f5e3 100%);
    border-radius: 12px; padding: 16px 20px;
    border: 1px solid rgba(42,111,43,0.15);
    margin-bottom: 18px;
">
    <div style="font-size:0.85rem;color:#1a252f;line-height:1.6;">
        <strong>Selamat datang!</strong> Portal ini digunakan untuk menganalisis dan mengelompokkan donatur
        Dompet Ummat Kalimantan Barat berdasarkan perilaku donasi menggunakan metode
        <strong>RFM (Recency, Frequency, Monetary)</strong> dan algoritma <strong>K-Means / K-Medoids Clustering</strong>.
    </div>
</div>
""", unsafe_allow_html=True)

# Quick metrics
try:
    from utils.db_connection import run_query

    stats = run_query("""
        SELECT
            (SELECT COUNT(*) FROM dim_donatur) AS total_donatur,
            (SELECT COUNT(*) FROM fact_donasi) AS total_transaksi,
            (SELECT COALESCE(SUM(nominal_valid), 0) FROM fact_donasi WHERE nominal_valid > 0) AS total_donasi
    """)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(kpi_card("users", "Total Donatur", f"{stats['total_donatur'].iloc[0]:,}", "Di database", DU_GREEN_4), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("receipt", "Total Transaksi", f"{stats['total_transaksi'].iloc[0]:,}", "Seluruh periode", "#3498db"), unsafe_allow_html=True)
    with c3:
        total = float(stats['total_donasi'].iloc[0])
        if total >= 1_000_000_000:
            val = f"Rp {total/1_000_000_000:.2f} M"
        else:
            val = f"Rp {total/1_000_000:.0f} Juta"
        st.markdown(kpi_card("wallet", "Total Donasi", val, "Akumulasi", "#f39c12"), unsafe_allow_html=True)

except Exception as e:
    st.error(f"Gagal koneksi ke database: {str(e)}")
    st.info("Pastikan MySQL (MAMP) sudah berjalan di port 8889.")

# How to use
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
st.markdown(section_header("rocket", "Cara Menggunakan Portal"), unsafe_allow_html=True)

steps = st.columns(4)
step_data = [
    ("layout-dashboard", "Overview", "Lihat ringkasan data donatur, tren donasi, dan metrik kunci.", DU_GREEN_4),
    ("upload", "Upload Data", "Upload file CSV data donasi terbaru ke database.", "#3498db"),
    ("target", "Analisis RFM", "Hitung skor RFM dan jalankan clustering otomatis.", "#9b59b6"),
    ("users", "Profil Segmen", "Lihat hasil segmentasi dan rekomendasi strategi retensi.", "#e74c3c"),
]

for col, (ic, title, desc, color) in zip(steps, step_data):
    ic_svg = icon_html(ic, color=color, size=28)
    with col:
        st.markdown(f"""
        <div style="
            background: #ffffff;
            border-radius: 12px; padding: 16px;
            border: 1px solid #e9ecef;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            text-align: center;
            min-height: 140px;
        ">
            <div style="
                width:48px;height:48px;border-radius:12px;
                background:rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.08);
                display:flex;align-items:center;justify-content:center;
                margin:0 auto 8px auto;
            ">{ic_svg}</div>
            <div style="font-size:0.82rem;font-weight:700;color:{color};margin-bottom:4px;">
                {title}
            </div>
            <div style="font-size:0.72rem;color:#6c757d;line-height:1.4;">
                {desc}
            </div>
        </div>
        """, unsafe_allow_html=True)

# Info teknis
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
info_icon = icon_html("info", color="#6c757d", size=16)
with st.expander(f"Informasi Teknis"):
    st.markdown("""
    | Komponen | Detail |
    |----------|--------|
    | **Database** | MySQL (MAMP) — `dompet_ummat_dw` |
    | **Metode Analisis** | RFM (Recency, Frequency, Monetary) |
    | **Algoritma Clustering** | K-Means, K-Medoids (PAM), DBSCAN |
    | **Evaluasi** | Silhouette Score, Davies-Bouldin Index, Calinski-Harabasz |
    | **Tech Stack** | Python, Streamlit, pandas, scikit-learn, Plotly, MySQL |
    """)
