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

st.set_page_config(page_title="Profil Segmen", page_icon="👥", layout="wide")

st.markdown("# 👥 Profil Segmen & Rekomendasi Strategi")
st.markdown("Hasil segmentasi donatur dan rekomendasi strategi retensi per segmen.")
st.divider()

# Cek apakah sudah ada hasil clustering
if "df_rfm" not in st.session_state or "chosen_labels" not in st.session_state:
    st.warning("⚠️ Belum ada hasil clustering. Silakan jalankan analisis di halaman **🎯 Analisis RFM** terlebih dahulu.")
    st.stop()

df_rfm = st.session_state["df_rfm"]
labels = st.session_state["chosen_labels"]
chosen_result = st.session_state["chosen_result"]
chosen_k = st.session_state["chosen_k"]

# ---- Profil Cluster ----
profiles = get_cluster_profiles(df_rfm, labels)
recommendations = get_segment_recommendations()

# ---- Overview metrik ----
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("🎯 Jumlah Cluster", chosen_k)
with col2:
    st.metric("📊 Metode", chosen_result["method"])
with col3:
    sil = chosen_result.get("silhouette_score", "N/A")
    st.metric("⭐ Silhouette Score", sil if sil else "N/A")
with col4:
    noise = chosen_result.get("n_noise", 0)
    st.metric("🔇 Noise Points", noise)

st.divider()

# ---- Radar Chart per Cluster ----
st.markdown("### 🕸️ Profil RFM per Cluster (Radar Chart)")

fig_radar = go.Figure()

colors = px.colors.qualitative.Set1
for i, row in profiles.iterrows():
    # Skip noise cluster in radar
    if int(row['cluster']) == -1:
        continue
    fig_radar.add_trace(go.Scatterpolar(
        r=[row["avg_r_score"], row["avg_f_score"], row["avg_m_score"], row["avg_r_score"]],
        theta=["Recency", "Frequency", "Monetary", "Recency"],
        fill="toself",
        name=f"Cluster {int(row['cluster'])} — {row['label_segmen']} ({int(row['jumlah_donatur'])} donatur)",
        line=dict(color=colors[i % len(colors)]),
        opacity=0.6,
    ))

fig_radar.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
    height=500,
    margin=dict(l=80, r=80, t=20, b=20),
)
st.plotly_chart(fig_radar, use_container_width=True)

# ---- Distribusi Donatur per Cluster ----
st.markdown("### 📊 Distribusi Donatur per Cluster")

col_pie, col_bar = st.columns(2)

with col_pie:
    fig_pie = px.pie(
        profiles, 
        values="jumlah_donatur", 
        names=profiles.apply(lambda x: f"Cluster {int(x['cluster'])} ({x['label_segmen']})", axis=1),
        color_discrete_sequence=px.colors.qualitative.Set2,
        hole=0.4,
    )
    fig_pie.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_pie, use_container_width=True)

with col_bar:
    fig_bar = px.bar(
        profiles,
        x="cluster",
        y=["avg_recency", "avg_frequency", "avg_monetary"],
        barmode="group",
        labels={"cluster": "Cluster", "value": "Rata-rata", "variable": "Metrik"},
        color_discrete_sequence=["#3498db", "#2ecc71", "#e74c3c"],
    )
    fig_bar.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_bar, use_container_width=True)

# ---- Tabel Profil Detail ----
st.markdown("### 📋 Detail Profil per Cluster")
st.dataframe(profiles, hide_index=True, use_container_width=True)

# ---- Rekomendasi Strategi per Segmen ----
st.divider()
st.markdown("### 💡 Rekomendasi Strategi Retensi per Segmen")

for _, row in profiles.iterrows():
    segment_name = row["label_segmen"]
    rec = recommendations.get(segment_name, None)
    
    if rec:
        emoji = rec["emoji"]
        color = rec["color"]
        
        with st.expander(
            f"{emoji} **Cluster {int(row['cluster'])} — {segment_name}** "
            f"({int(row['jumlah_donatur'])} donatur | "
            f"Avg RFM: R={row['avg_r_score']:.1f}, F={row['avg_f_score']:.1f}, M={row['avg_m_score']:.1f})",
            expanded=True
        ):
            col_info, col_action = st.columns([1, 1])
            
            with col_info:
                st.markdown(f"**Strategi:**")
                st.markdown(f"> {rec['strategi']}")
                st.markdown(f"""
                **Profil:**
                - Rata-rata Recency: **{row['avg_recency']:.0f} hari**
                - Rata-rata Frequency: **{row['avg_frequency']:.1f} transaksi**
                - Rata-rata Monetary: **Rp {row['avg_monetary']:,.0f}**
                """)
            
            with col_action:
                st.markdown("**Aksi yang Disarankan:**")
                for aksi in rec["aksi"]:
                    st.markdown(f"- ✅ {aksi}")
    else:
        with st.expander(f"📌 Cluster {int(row['cluster'])} — {segment_name} ({int(row['jumlah_donatur'])} donatur)"):
            st.info("Belum ada rekomendasi strategi untuk segmen ini.")

# ---- Export Results ----
st.divider()
st.markdown("### ⬇️ Export Hasil Segmentasi")

col_exp1, col_exp2 = st.columns(2)

with col_exp1:
    # Export per donatur
    df_export = df_rfm.copy()
    df_export["cluster"] = labels
    cluster_label_map = dict(zip(profiles["cluster"], profiles["label_segmen"]))
    df_export["label_segmen"] = df_export["cluster"].map(cluster_label_map)
    
    csv_full = df_export.to_csv(index=False)
    st.download_button(
        "⬇️ Download Data Donatur + Segmen (CSV)",
        data=csv_full,
        file_name="segmentasi_donatur_full.csv",
        mime="text/csv",
        use_container_width=True,
    )

with col_exp2:
    # Export profil cluster
    csv_profiles = profiles.to_csv(index=False)
    st.download_button(
        "⬇️ Download Profil Cluster (CSV)",
        data=csv_profiles,
        file_name="profil_cluster_donatur.csv",
        mime="text/csv",
        use_container_width=True,
    )
