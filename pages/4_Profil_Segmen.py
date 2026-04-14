"""
Page 4: Profil Segmen & Rekomendasi Strategi
Menampilkan profil setiap segmen donatur dan saran strategi retensi.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.clustering_engine import get_cluster_profiles, get_segment_recommendations
from utils.styles import get_global_css, kpi_card, section_header, icon_html, PLOTLY_LAYOUT, GREEN_PALETTE

st.set_page_config(page_title="Profil Segmen", page_icon="", layout="wide")
st.markdown(get_global_css(), unsafe_allow_html=True)

# ---- Header ----
st.markdown("""
<div style="margin-bottom:8px;">
    <div style="font-size:1.8rem;font-weight:800;color:#1a252f;letter-spacing:-0.5px;">
        Profil Segmen & Rekomendasi
    </div>
    <div style="font-size:0.88rem;color:#6c757d;margin-top:-2px;">
        Hasil segmentasi donatur dan rekomendasi strategi retensi per segmen
    </div>
</div>
""", unsafe_allow_html=True)

# ---- Sidebar ----
with st.sidebar:
    st.markdown("## Dompet Ummat")
    st.markdown("*Profil Segmen*")
    st.divider()

# Cek apakah sudah ada hasil clustering
if "df_rfm" not in st.session_state or "chosen_labels" not in st.session_state:
    st.markdown("""
    <div style="
        background:#fff;border-radius:14px;padding:40px;
        border:1px solid #e9ecef;box-shadow:0 2px 8px rgba(0,0,0,0.04);
        text-align:center;margin-top:20px;
    ">
        <div style="font-size:3rem;margin-bottom:12px;">⚠️</div>
        <div style="font-size:1.1rem;font-weight:700;color:#1a252f;margin-bottom:6px;">Belum Ada Hasil Clustering</div>
        <div style="font-size:0.85rem;color:#6c757d;line-height:1.5;max-width:500px;margin:0 auto;">
            Silakan jalankan analisis di halaman <strong>Analisis RFM</strong> terlebih dahulu
            untuk melihat profil segmen donatur.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

df_rfm = st.session_state["df_rfm"]
labels = st.session_state["chosen_labels"]
chosen_result = st.session_state["chosen_result"]
chosen_k = st.session_state["chosen_k"]

# ---- Profil Cluster ----
profiles = get_cluster_profiles(df_rfm, labels)
recommendations = get_segment_recommendations()

# ---- KPI Cards ----
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(kpi_card("target", "Jumlah Cluster", str(chosen_k), color="#2A6F2B"), unsafe_allow_html=True)
with c2:
    st.markdown(kpi_card("brain", "Metode", str(chosen_result["method"]), color="#3498db"), unsafe_allow_html=True)
with c3:
    sil = chosen_result.get("silhouette_score", "N/A")
    st.markdown(kpi_card("star", "Silhouette Score", str(sil) if sil else "N/A", color="#f39c12"), unsafe_allow_html=True)
with c4:
    noise = chosen_result.get("n_noise", 0)
    st.markdown(kpi_card("volume-x", "Noise Points", str(noise), color="#e74c3c"), unsafe_allow_html=True)

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ---- Radar Chart per Cluster ----
st.markdown(section_header("radar", "Profil RFM per Cluster (Radar Chart)", "Perbandingan skor R, F, M antar cluster"), unsafe_allow_html=True)

fig_radar = go.Figure()

for i, row in profiles.iterrows():
    if int(row['cluster']) == -1:
        continue
    fig_radar.add_trace(go.Scatterpolar(
        r=[row["avg_r_score"], row["avg_f_score"], row["avg_m_score"], row["avg_r_score"]],
        theta=["Recency", "Frequency", "Monetary", "Recency"],
        fill="toself",
        name=f"Cluster {int(row['cluster'])} — {row['label_segmen']} ({int(row['jumlah_donatur'])})",
        line=dict(color=GREEN_PALETTE[i % len(GREEN_PALETTE)], width=2),
        opacity=0.65,
    ))

fig_radar.update_layout(
    **PLOTLY_LAYOUT,
    polar=dict(
        radialaxis=dict(visible=True, range=[0, 5], gridcolor="#e9ecef"),
        bgcolor="rgba(0,0,0,0)",
    ),
    height=480,
)
st.plotly_chart(fig_radar, use_container_width=True)

# ---- Distribusi Donatur per Cluster ----
st.markdown(section_header("bar-chart", "Distribusi Donatur per Cluster"), unsafe_allow_html=True)

col_pie, col_bar = st.columns(2)

with col_pie:
    fig_pie = go.Figure(go.Pie(
        labels=profiles.apply(lambda x: f"C{int(x['cluster'])} ({x['label_segmen']})", axis=1),
        values=profiles["jumlah_donatur"],
        hole=0.55,
        textinfo="percent+label",
        textfont=dict(size=11, family="Poppins"),
        marker=dict(colors=GREEN_PALETTE[:len(profiles)]),
        hovertemplate="<b>%{label}</b><br>%{value:,} donatur (%{percent})<extra></extra>",
    ))
    fig_pie.update_layout(**PLOTLY_LAYOUT, height=400, showlegend=False)
    fig_pie.add_annotation(
        text=f"<b>{profiles['jumlah_donatur'].sum():,}</b><br><span style='font-size:10px;color:#6c757d'>Donatur</span>",
        showarrow=False, font=dict(size=16, family="Poppins"),
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col_bar:
    fig_bar = px.bar(
        profiles, x="cluster",
        y=["avg_recency", "avg_frequency", "avg_monetary"],
        barmode="group",
        labels={"cluster": "Cluster", "value": "Rata-rata", "variable": "Metrik"},
        color_discrete_sequence=["#3498db", "#2A6F2B", "#e74c3c"],
    )
    fig_bar.update_layout(**PLOTLY_LAYOUT, height=400)
    st.plotly_chart(fig_bar, use_container_width=True)

# ---- Tabel Profil Detail ----
st.markdown(section_header("file-text", "Detail Profil per Cluster"), unsafe_allow_html=True)
st.dataframe(profiles, hide_index=True, use_container_width=True)

# ---- Rekomendasi Strategi per Segmen ----
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
st.divider()
st.markdown(section_header("lightbulb", "Rekomendasi Strategi Retensi per Segmen", "Saran aksi berdasarkan profil masing-masing cluster"), unsafe_allow_html=True)

# Color map for segments
SEGMENT_COLORS = {
    "Champions": "#2A6F2B",
    "Loyal Donors": "#2ecc71",
    "Potential Loyalists": "#3498db",
    "Recent Donors": "#1abc9c",
    "Promising": "#f39c12",
    "Need Attention": "#e67e22",
    "About to Sleep": "#e74c3c",
    "Hibernating": "#95a5a6",
    "Lost": "#7f8c8d",
    "Whale Donors": "#8e44ad",
}

for _, row in profiles.iterrows():
    segment_name = row["label_segmen"]
    rec = recommendations.get(segment_name, None)
    seg_color = SEGMENT_COLORS.get(segment_name, "#6c757d")

    r_hex = int(seg_color[1:3], 16)
    g_hex = int(seg_color[3:5], 16)
    b_hex = int(seg_color[5:7], 16)

    if rec:
        emoji = rec["emoji"]

        st.markdown(f"""
        <div style="
            background:#fff;border-radius:14px;padding:20px;
            border:1px solid #e9ecef;box-shadow:0 2px 8px rgba(0,0,0,0.04);
            border-left:5px solid {seg_color};margin-bottom:12px;
        ">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                <div>
                    <span style="font-size:1.1rem;font-weight:700;color:#1a252f;">
                        {emoji} Cluster {int(row['cluster'])} — {segment_name}
                    </span>
                    <span style="
                        display:inline-block;margin-left:10px;
                        background:rgba({r_hex},{g_hex},{b_hex},0.1);color:{seg_color};
                        padding:3px 10px;border-radius:12px;font-size:0.72rem;font-weight:600;
                    ">{int(row['jumlah_donatur'])} donatur</span>
                </div>
                <div style="font-size:0.75rem;color:#6c757d;">
                    R={row['avg_r_score']:.1f} | F={row['avg_f_score']:.1f} | M={row['avg_m_score']:.1f}
                </div>
            </div>
            <div style="font-size:0.82rem;color:#343a40;margin-bottom:10px;line-height:1.5;">
                <strong>Strategi:</strong> {rec['strategi']}
            </div>
            <div style="font-size:0.78rem;color:#6c757d;margin-bottom:6px;font-weight:600;">Profil:</div>
            <div style="font-size:0.78rem;color:#343a40;line-height:1.6;margin-bottom:10px;">
                Avg Recency: <strong>{row['avg_recency']:.0f} hari</strong> &nbsp;|&nbsp;
                Avg Frequency: <strong>{row['avg_frequency']:.1f}x</strong> &nbsp;|&nbsp;
                Avg Monetary: <strong>Rp {row['avg_monetary']:,.0f}</strong>
            </div>
            <div style="font-size:0.78rem;color:#6c757d;margin-bottom:4px;font-weight:600;">Aksi yang Disarankan:</div>
            <div style="font-size:0.78rem;color:#343a40;line-height:1.7;">
                {"".join(f"<span style='display:block;'>✅ {aksi}</span>" for aksi in rec['aksi'])}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="
            background:#fff;border-radius:14px;padding:18px;
            border:1px solid #e9ecef;border-left:5px solid #95a5a6;margin-bottom:12px;
        ">
            <span style="font-size:0.95rem;font-weight:600;color:#1a252f;">
                Cluster {int(row['cluster'])} — {segment_name}
            </span>
            <span style="font-size:0.78rem;color:#6c757d;margin-left:10px;">
                ({int(row['jumlah_donatur'])} donatur) — Belum ada rekomendasi
            </span>
        </div>
        """, unsafe_allow_html=True)

# ---- Export Results ----
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
st.divider()
st.markdown(section_header("download", "Export Hasil Segmentasi"), unsafe_allow_html=True)

col_exp1, col_exp2, col_exp3 = st.columns(3)

with col_exp1:
    df_export = df_rfm.copy()
    df_export["cluster"] = labels
    cluster_label_map = dict(zip(profiles["cluster"], profiles["label_segmen"]))
    df_export["label_segmen"] = df_export["cluster"].map(cluster_label_map)

    csv_full = df_export.to_csv(index=False)
    st.download_button(
        "Donatur + Segmen (CSV)",
        data=csv_full,
        file_name="segmentasi_donatur_full.csv",
        mime="text/csv",
        use_container_width=True,
    )

with col_exp2:
    csv_profiles = profiles.to_csv(index=False)
    st.download_button(
        "Profil Cluster (CSV)",
        data=csv_profiles,
        file_name="profil_cluster_donatur.csv",
        mime="text/csv",
        use_container_width=True,
    )

with col_exp3:
    st.markdown("""
    <button onclick="window.print()" style="
        width:100%;padding:10px;cursor:pointer;
        background:#f8f9fa;border:1px solid #dee2e6;
        border-radius:8px;font-family:Poppins;font-weight:600;
        font-size:0.85rem;color:#343a40;transition:all 0.2s;
    " onmouseover="this.style.background='#e9ecef'"
      onmouseout="this.style.background='#f8f9fa'">
        Print / Save as PDF
    </button>
    """, unsafe_allow_html=True)
