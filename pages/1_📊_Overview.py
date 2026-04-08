"""
Page 1: Overview Donatur
Ringkasan data donatur dan trend donasi.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.db_connection import run_query
from utils.rfm_engine import get_donation_trend, get_donation_method_stats

st.set_page_config(page_title="Overview Donatur", page_icon="📊", layout="wide")

st.markdown("# 📊 Overview Donatur")
st.markdown("Ringkasan data donatur dan transaksi donasi Dompet Ummat Kalimantan Barat.")
st.divider()

try:
    # ---- Metric Cards ----
    stats = run_query("""
        SELECT 
            (SELECT COUNT(*) FROM dim_donatur) AS total_donatur,
            (SELECT COUNT(*) FROM fact_donasi) AS total_transaksi,
            (SELECT COALESCE(SUM(nominal_valid), 0) FROM fact_donasi) AS total_donasi,
            (SELECT COUNT(DISTINCT id_donatur) FROM fact_donasi) AS donatur_aktif
    """)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("👤 Total Donatur", f"{stats['total_donatur'].iloc[0]:,}")
    with c2:
        st.metric("🟢 Donatur Aktif", f"{stats['donatur_aktif'].iloc[0]:,}")
    with c3:
        st.metric("📋 Total Transaksi", f"{stats['total_transaksi'].iloc[0]:,}")
    with c4:
        total = float(stats['total_donasi'].iloc[0])
        st.metric("💰 Total Donasi", f"Rp {total:,.0f}")
    
    st.divider()
    
    # ---- Trend Donasi per Tahun ----
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("### 📈 Trend Donasi per Tahun")
        df_trend = get_donation_trend()
        
        if not df_trend.empty:
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Bar(
                x=df_trend["tahun"],
                y=df_trend["total_donasi"],
                name="Total Donasi (Rp)",
                marker_color="#2ecc71",
                opacity=0.7,
            ))
            fig_trend.add_trace(go.Scatter(
                x=df_trend["tahun"],
                y=df_trend["jumlah_donatur"],
                name="Jumlah Donatur",
                yaxis="y2",
                line=dict(color="#e74c3c", width=3),
                mode="lines+markers",
            ))
            fig_trend.update_layout(
                yaxis=dict(title="Total Donasi (Rp)", side="left"),
                yaxis2=dict(title="Jumlah Donatur", side="right", overlaying="y"),
                legend=dict(orientation="h", y=-0.2),
                height=400,
                margin=dict(l=20, r=20, t=20, b=20),
            )
            st.plotly_chart(fig_trend, use_container_width=True)
    
    with col_right:
        st.markdown("### 🏦 Cara Donasi")
        df_method = get_donation_method_stats()
        
        if not df_method.empty:
            fig_method = px.pie(
                df_method.head(8), 
                values="jumlah", 
                names="cara_donasi",
                color_discrete_sequence=px.colors.qualitative.Set2,
                hole=0.4,
            )
            fig_method.update_layout(
                height=400,
                margin=dict(l=20, r=20, t=20, b=20),
            )
            st.plotly_chart(fig_method, use_container_width=True)
    
    # ---- Tipe Donatur ----
    st.divider()
    st.markdown("### 👥 Distribusi Tipe Donatur")
    
    df_tipe = run_query("""
        SELECT tipe, COUNT(*) AS jumlah FROM dim_donatur
        WHERE tipe IS NOT NULL AND tipe != 'Tidak Ada Data'
        GROUP BY tipe ORDER BY jumlah DESC
    """)
    
    if not df_tipe.empty:
        col_t1, col_t2 = st.columns([1, 2])
        with col_t1:
            st.dataframe(df_tipe, hide_index=True, use_container_width=True)
        with col_t2:
            fig_tipe = px.bar(
                df_tipe, x="tipe", y="jumlah", 
                color="tipe",
                color_discrete_sequence=["#3498db", "#e74c3c", "#f39c12", "#2ecc71"],
            )
            fig_tipe.update_layout(
                showlegend=False, 
                height=300,
                margin=dict(l=20, r=20, t=20, b=20),
            )
            st.plotly_chart(fig_tipe, use_container_width=True)
    
    # ---- Top Donatur ----
    st.divider()
    st.markdown("### 🏅 Top 10 Donatur (Berdasarkan Total Donasi)")
    
    df_top = run_query("""
        SELECT 
            d.id_donatur,
            d.nama_lengkap,
            d.tipe,
            COUNT(f.id_fact) AS frekuensi,
            SUM(f.nominal_valid) AS total_donasi,
            MAX(f.tgl_bersih) AS donasi_terakhir
        FROM dim_donatur d
        JOIN fact_donasi f ON d.id_donatur = f.id_donatur
        GROUP BY d.id_donatur, d.nama_lengkap, d.tipe
        ORDER BY total_donasi DESC
        LIMIT 10
    """)
    
    if not df_top.empty:
        df_top["total_donasi"] = df_top["total_donasi"].apply(lambda x: f"Rp {x:,.0f}")
        st.dataframe(df_top, hide_index=True, use_container_width=True)

except Exception as e:
    st.error(f"⚠️ Error: {str(e)}")
    st.info("Pastikan MySQL (MAMP) sudah berjalan di port 8889.")
