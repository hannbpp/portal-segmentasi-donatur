"""
Page 1: Overview Dashboard
Dashboard ringkasan data donatur — premium UI.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.db_connection import run_query
from utils.rfm_engine import get_donation_trend, get_donation_method_stats
from utils.styles import get_global_css, kpi_card, section_header, icon_html, PLOTLY_LAYOUT, GREEN_PALETTE, GREEN_SEQUENTIAL

st.set_page_config(page_title="Dashboard Overview — Dompet Ummat", page_icon="", layout="wide")
st.markdown(get_global_css(), unsafe_allow_html=True)

# ========================================================
# SIDEBAR FILTERS
# ========================================================
with st.sidebar:
    st.markdown("## Dompet Ummat")
    st.markdown("*Dashboard Overview*")
    st.divider()

    st.markdown("##### FILTER DATA")

    # Date range filter
    try:
        date_range = run_query("""
            SELECT MIN(tgl_bersih) AS min_date, MAX(tgl_bersih) AS max_date
            FROM fact_donasi WHERE tgl_bersih > '1900-01-02'
        """)
        min_d = pd.to_datetime(date_range["min_date"].iloc[0]).date()
        max_d = pd.to_datetime(date_range["max_date"].iloc[0]).date()
    except:
        min_d = datetime(2012, 1, 1).date()
        max_d = datetime.now().date()

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        start_date = st.date_input("Dari", value=min_d, min_value=min_d, max_value=max_d)
    with col_d2:
        end_date = st.date_input("Sampai", value=max_d, min_value=min_d, max_value=max_d)

    # Tipe donatur filter
    try:
        tipe_list = run_query("SELECT DISTINCT tipe FROM dim_donatur WHERE tipe IS NOT NULL AND tipe != 'Tidak Ada Data' ORDER BY tipe")
        tipe_options = tipe_list["tipe"].tolist()
    except:
        tipe_options = ["Individu", "Lembaga"]
    
    selected_tipe = st.multiselect("Tipe Donatur", tipe_options, default=tipe_options)

    # Program filter
    try:
        prog_list = run_query("SELECT DISTINCT nama_program FROM dim_program_donasi WHERE nama_program IS NOT NULL ORDER BY nama_program LIMIT 20")
        prog_options = prog_list["nama_program"].tolist()
    except:
        prog_options = []
    
    if prog_options:
        selected_prog = st.multiselect("Program Donasi", prog_options, default=prog_options)
    else:
        selected_prog = []

    st.divider()
    st.caption("Data terakhir diperbarui:")
    st.caption(f"**{max_d.strftime('%d %B %Y')}**")

# ========================================================
# BUILD FILTER WHERE CLAUSE
# ========================================================
date_filter = f"f.tgl_bersih BETWEEN '{start_date}' AND '{end_date}' AND f.tgl_bersih > '1900-01-02'"
tipe_filter_list = ", ".join([f"'{t}'" for t in selected_tipe])
tipe_filter = f"d.tipe IN ({tipe_filter_list})" if selected_tipe else "1=1"

# ========================================================
# HEADER
# ========================================================
header_icon = icon_html("layout-dashboard", color="#2A6F2B", size=28)
st.markdown(f"""
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
    <div style="display:flex;align-items:center;gap:10px;">
        {header_icon}
        <div>
            <div style="font-size:1.8rem; font-weight:700; color:#1a252f; letter-spacing:-0.5px;">
                Dashboard Overview
            </div>
            <div style="font-size:0.88rem; color:#6c757d; margin-top:-2px;">
                Ringkasan data donatur & transaksi donasi Dompet Ummat Kalimantan Barat
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Date range badge
cal_icon = icon_html("calendar", color="#043F2E", size=14)
st.markdown(f"""
<div style="margin-bottom:16px;">
    <span style="
        display:inline-flex; align-items:center; gap:6px;
        background:#eafaf1; color:#043F2E;
        padding:6px 14px; border-radius:20px;
        font-size:0.78rem; font-weight:600;
        border:1px solid #d5f5e3;
    ">{cal_icon} {start_date.strftime('%d %b %Y')} — {end_date.strftime('%d %b %Y')}</span>
</div>
""", unsafe_allow_html=True)

# ========================================================
# MAIN CONTENT
# ========================================================
try:
    # ---- QUERY: Main KPIs ----
    stats = run_query(f"""
        SELECT 
            COUNT(DISTINCT d.id_donatur) AS total_donatur,
            COUNT(f.id_fact) AS total_transaksi,
            COALESCE(SUM(f.nominal_valid), 0) AS total_donasi,
            COALESCE(AVG(f.nominal_valid), 0) AS avg_nominal,
            COUNT(DISTINCT YEAR(f.tgl_bersih)) AS tahun_aktif
        FROM dim_donatur d
        INNER JOIN fact_donasi f ON d.id_donatur = f.id_donatur
        WHERE {date_filter} AND {tipe_filter}
          AND f.nominal_valid IS NOT NULL AND f.nominal_valid > 0
    """)
    
    total_donatur = int(stats["total_donatur"].iloc[0])
    total_tx = int(stats["total_transaksi"].iloc[0])
    total_donasi = float(stats["total_donasi"].iloc[0])
    avg_nominal = float(stats["avg_nominal"].iloc[0])
    tahun_aktif = int(stats["tahun_aktif"].iloc[0])
    avg_per_donatur = total_donasi / total_donatur if total_donatur > 0 else 0

    # ---- KPI CARDS (Row 1) ----
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(kpi_card("users", "Total Donatur", f"{total_donatur:,}", f"Periode {tahun_aktif} tahun", "#2A6F2B"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("receipt", "Total Transaksi", f"{total_tx:,}", f"Avg {total_tx/total_donatur:.1f}x/donatur" if total_donatur > 0 else "", "#3498db"), unsafe_allow_html=True)
    with c3:
        if total_donasi >= 1_000_000_000:
            donasi_str = f"Rp {total_donasi/1_000_000_000:.2f} M"
        else:
            donasi_str = f"Rp {total_donasi/1_000_000:.0f} Jt"
        st.markdown(kpi_card("wallet", "Total Donasi", donasi_str, "Akumulasi seluruh periode", "#f39c12"), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_card("bar-chart", "Avg per Transaksi", f"Rp {avg_nominal:,.0f}", "", "#9b59b6"), unsafe_allow_html=True)
    with c5:
        st.markdown(kpi_card("target", "Avg per Donatur", f"Rp {avg_per_donatur:,.0f}", "", "#e74c3c"), unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ================================================================
    # ROW 2: Trend + Donut
    # ================================================================
    col_trend, col_donut = st.columns([2, 1])

    with col_trend:
        st.markdown(section_header("trending-up", "Tren Donasi per Tahun", "Total donasi dan jumlah donatur aktif per tahun"), unsafe_allow_html=True)
        
        df_trend = run_query(f"""
            SELECT 
                YEAR(f.tgl_bersih) AS tahun,
                COUNT(*) AS jumlah_transaksi,
                SUM(f.nominal_valid) AS total_donasi,
                COUNT(DISTINCT f.id_donatur) AS jumlah_donatur
            FROM fact_donasi f
            INNER JOIN dim_donatur d ON f.id_donatur = d.id_donatur
            WHERE {date_filter} AND {tipe_filter}
              AND f.nominal_valid > 0
            GROUP BY YEAR(f.tgl_bersih)
            ORDER BY tahun
        """)

        if not df_trend.empty:
            fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Area chart - Total donasi
            fig_trend.add_trace(go.Scatter(
                x=df_trend["tahun"], y=df_trend["total_donasi"],
                fill="tozeroy", name="Total Donasi (Rp)",
                line=dict(color="#2A6F2B", width=2.5),
                fillcolor="rgba(39,174,96,0.12)",
                hovertemplate="<b>%{x}</b><br>Rp %{y:,.0f}<extra></extra>",
            ), secondary_y=False)

            # Line - Jumlah donatur
            fig_trend.add_trace(go.Scatter(
                x=df_trend["tahun"], y=df_trend["jumlah_donatur"],
                name="Donatur Aktif", mode="lines+markers",
                line=dict(color="#3498db", width=2.5, dash="dot"),
                marker=dict(size=7, color="#3498db"),
                hovertemplate="<b>%{x}</b><br>%{y:,} donatur<extra></extra>",
            ), secondary_y=True)

            fig_trend.update_layout(
                **PLOTLY_LAYOUT, height=380,
                yaxis=dict(title="Total Donasi (Rp)", gridcolor="#f0f0f0", gridwidth=1),
                yaxis2=dict(title="Jumlah Donatur", gridcolor="rgba(0,0,0,0)"),
                xaxis=dict(dtick=1),
            )
            st.plotly_chart(fig_trend, use_container_width=True)

    with col_donut:
        st.markdown(section_header("user", "Tipe Donatur", "Distribusi individu vs lembaga"), unsafe_allow_html=True)
        
        df_tipe = run_query(f"""
            SELECT d.tipe, COUNT(DISTINCT d.id_donatur) AS jumlah
            FROM dim_donatur d
            INNER JOIN fact_donasi f ON d.id_donatur = f.id_donatur
            WHERE {date_filter} AND {tipe_filter}
              AND d.tipe IS NOT NULL AND d.tipe != 'Tidak Ada Data'
            GROUP BY d.tipe ORDER BY jumlah DESC
        """)

        if not df_tipe.empty:
            fig_tipe = go.Figure(go.Pie(
                labels=df_tipe["tipe"], values=df_tipe["jumlah"],
                hole=0.55, textinfo="percent+label",
                textfont=dict(size=12, family="Poppins"),
                marker=dict(colors=["#2A6F2B", "#3498db", "#f39c12", "#e74c3c"]),
                hovertemplate="<b>%{label}</b><br>%{value:,} donatur (%{percent})<extra></extra>",
            ))
            fig_tipe.update_layout(**PLOTLY_LAYOUT, height=380, showlegend=False)
            
            # Center text
            fig_tipe.add_annotation(
                text=f"<b>{df_tipe['jumlah'].sum():,}</b><br><span style='font-size:11px;color:#6c757d'>Donatur</span>",
                showarrow=False, font=dict(size=18, family="Poppins"),
            )
            st.plotly_chart(fig_tipe, use_container_width=True)

    # ================================================================
    # ROW 3: Cara Donasi + Donasi per Bulan
    # ================================================================
    col_method, col_monthly = st.columns(2)

    with col_method:
        st.markdown(section_header("credit-card", "Cara Donasi", "Metode pembayaran yang digunakan donatur"), unsafe_allow_html=True)
        
        df_method = run_query(f"""
            SELECT f.cara_donasi, COUNT(*) AS jumlah, SUM(f.nominal_valid) AS total
            FROM fact_donasi f
            INNER JOIN dim_donatur d ON f.id_donatur = d.id_donatur
            WHERE {date_filter} AND {tipe_filter}
              AND f.cara_donasi IS NOT NULL AND f.cara_donasi != 'Tidak Ada Data'
              AND f.nominal_valid > 0
            GROUP BY f.cara_donasi
            ORDER BY jumlah DESC LIMIT 8
        """)

        if not df_method.empty:
            fig_method = go.Figure(go.Bar(
                x=df_method["jumlah"], y=df_method["cara_donasi"],
                orientation="h",
                marker=dict(
                    color=df_method["jumlah"],
                    colorscale=[[0, "#d5f5e3"], [1, "#2A6F2B"]],
                    cornerradius=4,
                ),
                text=[f"{v:,}" for v in df_method["jumlah"]],
                textposition="outside",
                textfont=dict(size=11, family="Poppins", color="#343a40"),
                hovertemplate="<b>%{y}</b><br>%{x:,} transaksi<extra></extra>",
            ))
            fig_method.update_layout(
                **PLOTLY_LAYOUT, height=360,
                yaxis=dict(autorange="reversed", tickfont=dict(size=11)),
                xaxis=dict(showgrid=False, showticklabels=False),
                bargap=0.25,
            )
            st.plotly_chart(fig_method, use_container_width=True)

    with col_monthly:
        st.markdown(section_header("calendar", "Tren Bulanan", "Pola donasi per bulan (seluruh tahun)"), unsafe_allow_html=True)

        df_monthly = run_query(f"""
            SELECT 
                MONTH(f.tgl_bersih) AS bulan,
                SUM(f.nominal_valid) AS total_donasi,
                COUNT(*) AS jumlah_tx
            FROM fact_donasi f
            INNER JOIN dim_donatur d ON f.id_donatur = d.id_donatur
            WHERE {date_filter} AND {tipe_filter}
              AND f.nominal_valid > 0 AND f.tgl_bersih > '1900-01-02'
            GROUP BY MONTH(f.tgl_bersih)
            ORDER BY bulan
        """)

        if not df_monthly.empty:
            bulan_names = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
                           "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
            df_monthly["bulan_nama"] = df_monthly["bulan"].apply(
                lambda x: bulan_names[int(x)-1] if 1 <= int(x) <= 12 else str(x)
            )

            fig_monthly = go.Figure()
            fig_monthly.add_trace(go.Bar(
                x=df_monthly["bulan_nama"], y=df_monthly["total_donasi"],
                name="Total Donasi",
                marker=dict(color="#2A6F2B", cornerradius=4, opacity=0.7),
                hovertemplate="<b>%{x}</b><br>Rp %{y:,.0f}<extra></extra>",
            ))
            fig_monthly.add_trace(go.Scatter(
                x=df_monthly["bulan_nama"], y=df_monthly["jumlah_tx"],
                name="Jumlah Transaksi", yaxis="y2",
                mode="lines+markers",
                line=dict(color="#e74c3c", width=2.5),
                marker=dict(size=6),
                hovertemplate="<b>%{x}</b><br>%{y:,} transaksi<extra></extra>",
            ))
            fig_monthly.update_layout(
                **PLOTLY_LAYOUT, height=360,
                yaxis=dict(title="Total Donasi", gridcolor="#f0f0f0"),
                yaxis2=dict(title="Jumlah TX", overlaying="y", side="right", gridcolor="rgba(0,0,0,0)"),
            )
            st.plotly_chart(fig_monthly, use_container_width=True)

    # ================================================================
    # ROW 4: Top Donatur + Distribusi Nominal
    # ================================================================
    col_top, col_dist = st.columns([1.2, 0.8])

    with col_top:
        st.markdown(section_header("award", "Top 10 Donatur", "Berdasarkan total akumulasi donasi"), unsafe_allow_html=True)

        df_top = run_query(f"""
            SELECT 
                d.nama_lengkap AS Nama,
                d.tipe AS Tipe,
                COUNT(f.id_fact) AS Frekuensi,
                SUM(f.nominal_valid) AS Total_Donasi,
                MAX(f.tgl_bersih) AS Terakhir
            FROM dim_donatur d
            INNER JOIN fact_donasi f ON d.id_donatur = f.id_donatur
            WHERE {date_filter} AND {tipe_filter}
              AND f.nominal_valid > 0
            GROUP BY d.id_donatur, d.nama_lengkap, d.tipe
            ORDER BY Total_Donasi DESC
            LIMIT 10
        """)

        if not df_top.empty:
            df_display = df_top.copy()
            df_display.insert(0, "#", range(1, len(df_display)+1))
            df_display["Total_Donasi"] = df_display["Total_Donasi"].apply(lambda x: f"Rp {x:,.0f}")
            df_display["Terakhir"] = pd.to_datetime(df_display["Terakhir"]).dt.strftime("%d %b %Y")
            st.dataframe(df_display, hide_index=True, use_container_width=True, height=390)

    with col_dist:
        st.markdown(section_header("bar-chart", "Distribusi Nominal", "Sebaran nilai donasi per transaksi"), unsafe_allow_html=True)

        df_nom = run_query(f"""
            SELECT f.nominal_valid
            FROM fact_donasi f
            INNER JOIN dim_donatur d ON f.id_donatur = d.id_donatur
            WHERE {date_filter} AND {tipe_filter}
              AND f.nominal_valid > 0 AND f.nominal_valid <= 10000000
        """)

        if not df_nom.empty:
            fig_hist = go.Figure(go.Histogram(
                x=df_nom["nominal_valid"], nbinsx=40,
                marker=dict(color="#2A6F2B", opacity=0.75, line=dict(width=0.5, color="#043F2E")),
                hovertemplate="Rp %{x:,.0f}<br>%{y:,} transaksi<extra></extra>",
            ))
            fig_hist.update_layout(
                **PLOTLY_LAYOUT, height=390,
                xaxis=dict(title="Nominal (Rp)", gridcolor="#f0f0f0"),
                yaxis=dict(title="Jumlah Transaksi", gridcolor="#f0f0f0"),
            )
            st.plotly_chart(fig_hist, use_container_width=True)

    # ================================================================
    # ROW 5: YoY Growth
    # ================================================================
    st.markdown(section_header("trending-up", "Pertumbuhan Year-over-Year", "Perbandingan penghimpunan antar tahun"), unsafe_allow_html=True)

    if not df_trend.empty and len(df_trend) >= 2:
        df_growth = df_trend.copy()
        df_growth["growth_pct"] = df_growth["total_donasi"].pct_change() * 100
        df_growth["growth_donatur"] = df_growth["jumlah_donatur"].pct_change() * 100
        df_growth = df_growth.dropna()

        if not df_growth.empty:
            c_g1, c_g2, c_g3 = st.columns(3)

            latest = df_growth.iloc[-1]
            prev = df_growth.iloc[-2] if len(df_growth) >= 2 else latest

            with c_g1:
                yr = int(latest["tahun"])
                g = latest["growth_pct"]
                st.metric(
                    f"Donasi {yr} vs {yr-1}",
                    f"Rp {latest['total_donasi']:,.0f}",
                    f"{g:+.1f}%"
                )
            with c_g2:
                gd = latest["growth_donatur"]
                st.metric(
                    f"Donatur {yr} vs {yr-1}",
                    f"{int(latest['jumlah_donatur']):,}",
                    f"{gd:+.1f}%"
                )
            with c_g3:
                avg_tx = latest["total_donasi"] / latest["jumlah_donatur"] if latest["jumlah_donatur"] > 0 else 0
                st.metric(
                    f"Avg/Donatur {yr}",
                    f"Rp {avg_tx:,.0f}",
                )

    # ================================================================
    # EXPORT SECTION
    # ================================================================
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.divider()

    exp1, exp2, exp3 = st.columns(3)

    with exp1:
        # Export as CSV
        try:
            df_export = run_query(f"""
                SELECT d.id_donatur, d.nama_lengkap, d.tipe,
                       COUNT(f.id_fact) AS frekuensi,
                       SUM(f.nominal_valid) AS total_donasi,
                       MAX(f.tgl_bersih) AS donasi_terakhir
                FROM dim_donatur d
                INNER JOIN fact_donasi f ON d.id_donatur = f.id_donatur
                WHERE {date_filter} AND {tipe_filter} AND f.nominal_valid > 0
                GROUP BY d.id_donatur, d.nama_lengkap, d.tipe
                ORDER BY total_donasi DESC
            """)
            csv_data = df_export.to_csv(index=False)
            st.download_button(
                "Download Data Donatur (CSV)",
                data=csv_data,
                file_name=f"donatur_overview_{start_date}_{end_date}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        except:
            pass

    with exp2:
        # Export trend as CSV
        if not df_trend.empty:
            csv_trend = df_trend.to_csv(index=False)
            st.download_button(
                "Download Tren Tahunan (CSV)",
                data=csv_trend,
                file_name=f"trend_donasi_{start_date}_{end_date}.csv",
                mime="text/csv",
                use_container_width=True,
            )

    with exp3:
        # Print / PDF button
        st.markdown("""
        <button onclick="window.print()" style="
            width:100%; padding:10px; cursor:pointer;
            background:#f8f9fa; border:1px solid #dee2e6;
            border-radius:8px; font-family:Poppins; font-weight:600;
            font-size:0.85rem; color:#343a40;
            transition: all 0.2s;
        " onmouseover="this.style.background='#e9ecef'" 
          onmouseout="this.style.background='#f8f9fa'">
            Print / Save as PDF
        </button>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Error: {str(e)}")
    st.info("Pastikan MySQL (MAMP) sudah berjalan di port 8889 dan database `dompet_ummat_dw` tersedia.")
