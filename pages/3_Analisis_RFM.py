"""
Page 3: Analisis RFM & Clustering
Hitung skor RFM, jalankan K-Means/K-Medoids/DBSCAN, bandingkan metode.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.rfm_engine import get_rfm_data, get_rfm_summary
from utils.clustering_engine import (
    prepare_features, find_optimal_k, run_kmeans, run_kmedoids, run_dbscan,
    compare_methods, get_cluster_profiles, get_silhouette_analysis,
    tune_kmeans, tune_dbscan, get_kdistance_data, estimate_dbscan_eps,
)
from utils.styles import get_global_css, kpi_card, section_header, icon_html, PLOTLY_LAYOUT, GREEN_PALETTE

st.set_page_config(page_title="Analisis RFM & Clustering", page_icon="", layout="wide")
st.markdown(get_global_css(), unsafe_allow_html=True)

# ---- Header ----
st.markdown("""
<div style="margin-bottom:8px;">
    <div style="font-size:1.8rem;font-weight:800;color:#1a252f;letter-spacing:-0.5px;">
        Analisis RFM & Clustering
    </div>
    <div style="font-size:0.88rem;color:#6c757d;margin-top:-2px;">
        Hitung skor RFM dan jalankan algoritma clustering untuk segmentasi donatur
    </div>
</div>
""", unsafe_allow_html=True)

# ---- Sidebar Settings ----
with st.sidebar:
    st.markdown("## Dompet Ummat")
    st.markdown("*Analisis RFM*")
    st.divider()

    st.markdown("##### PENGATURAN")

    # Tanggal referensi
    date_mode = st.radio(
        "Tanggal Referensi RFM",
        ["Dinamis (Hari Ini)", "Statis (Tanggal Terakhir Data)", "Manual"],
        index=0,
        help="Tanggal referensi untuk menghitung Recency"
    )

    ref_date = None
    if date_mode == "Dinamis (Hari Ini)":
        ref_date = datetime.now()
        st.caption(f"Referensi: {ref_date.strftime('%d %B %Y')}")
    elif date_mode == "Manual":
        ref_date = st.date_input("Pilih tanggal", value=datetime.now())
        ref_date = datetime.combine(ref_date, datetime.min.time())
    # Statis = None (akan otomatis pakai tanggal terakhir data)

    st.divider()

    # Clustering method
    st.markdown("##### CLUSTERING")
    cluster_method = st.selectbox(
        "Metode Clustering",
        ["K-Means", "K-Medoids", "DBSCAN", "Bandingkan Semua (3 Metode)"],
        index=3,
    )

    # Number of clusters (untuk K-Means dan K-Medoids)
    if cluster_method != "DBSCAN":
        k_mode = st.radio(
            "Jumlah Cluster (K)",
            ["Otomatis (Elbow + Silhouette)", "Manual"],
            index=0,
        )
        manual_k = 4
        if k_mode == "Manual":
            manual_k = st.slider("Pilih K", min_value=2, max_value=10, value=4)

    # DBSCAN params
    if cluster_method in ["DBSCAN", "Bandingkan Semua (3 Metode)"]:
        st.divider()
        st.markdown("##### PARAMETER DBSCAN")
        dbscan_eps_mode = st.radio(
            "Epsilon (eps)",
            ["Otomatis (k-distance)", "Manual"],
            index=0,
        )
        manual_eps = None
        if dbscan_eps_mode == "Manual":
            manual_eps = st.number_input("Nilai eps", min_value=0.1, max_value=5.0, value=0.5, step=0.1)

        dbscan_min_samples = st.slider("min_samples", min_value=2, max_value=20, value=5)

# ---- Main Content ----
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

if st.button("Jalankan Analisis RFM & Clustering", type="primary", use_container_width=True):

    # Step 1: Hitung RFM
    with st.spinner("Menghitung skor RFM..."):
        df_rfm = get_rfm_data(reference_date=ref_date)

    if df_rfm.empty:
        st.error("Tidak ada data donasi yang valid di database.")
        st.stop()

    # Success banner
    st.markdown(f"""
    <div style="
        background:linear-gradient(135deg,#eafaf1,#d5f5e3);
        border-radius:12px;padding:14px 18px;
        border:1px solid #abebc6;margin:12px 0;
    ">
        <span style="font-size:0.9rem;font-weight:600;color:#043F2E;">
            ✅ RFM berhasil dihitung untuk <strong>{len(df_rfm):,} donatur</strong>
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Simpan ke session state
    st.session_state["df_rfm"] = df_rfm

    # ---- Tab Layout ----
    tab_titles = ["Distribusi RFM", "Penentuan K Optimal", "Hasil Clustering",
                  "Analisis Silhouette", "Hyperparameter Tuning", "Data Lengkap"]
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(tab_titles)

    # ==== TAB 1: Distribusi RFM ====
    with tab1:
        st.markdown(section_header("bar-chart", "Distribusi Skor RFM", "Sebaran nilai Recency, Frequency, dan Monetary dari seluruh donatur"), unsafe_allow_html=True)

        fig_dist = make_subplots(rows=1, cols=3, subplot_titles=("Recency (hari)", "Frequency (transaksi)", "Monetary (Rp)"))

        for col_idx, (col_name, color) in enumerate([
            ("recency", "#3498db"), ("frequency", "#2A6F2B"), ("monetary", "#e74c3c")
        ], 1):
            fig_dist.add_trace(
                go.Histogram(x=df_rfm[col_name], nbinsx=30, marker_color=color,
                             marker_line=dict(width=0.5, color="#fff"), opacity=0.85),
                row=1, col=col_idx
            )

        fig_dist.update_layout(**PLOTLY_LAYOUT, height=350, showlegend=False)
        st.plotly_chart(fig_dist, use_container_width=True)

        # Statistik deskriptif
        st.markdown(section_header("file-text", "Statistik Deskriptif"), unsafe_allow_html=True)
        desc_cols = ["recency", "frequency", "monetary"]
        st.dataframe(df_rfm[desc_cols].describe().round(2).T, use_container_width=True)

        # Segmentasi RFM (tanpa clustering)
        st.markdown(section_header("target", "Segmentasi RFM (Rule-Based)", "Pengelompokan berdasarkan aturan skor RFM"), unsafe_allow_html=True)
        rfm_summary = get_rfm_summary(df_rfm)
        st.dataframe(rfm_summary, hide_index=True, use_container_width=True)

        fig_seg = px.bar(
            rfm_summary, x="segment", y="jumlah_donatur",
            color="avg_rfm_score",
            color_continuous_scale=[[0, "#e74c3c"], [0.5, "#f39c12"], [1, "#2A6F2B"]],
            labels={"jumlah_donatur": "Jumlah Donatur", "segment": "Segmen"},
        )
        fig_seg.update_layout(**PLOTLY_LAYOUT, height=400)
        st.plotly_chart(fig_seg, use_container_width=True)

    # ==== TAB 2: Penentuan K Optimal ====
    with tab2:
        st.markdown(section_header("search", "Penentuan Jumlah Cluster Optimal", "Evaluasi K=2 sampai K=10 dengan 4 metrik"), unsafe_allow_html=True)

        with st.spinner("Menghitung metrik untuk K=2 sampai K=10..."):
            X_scaled, scaler, feature_names = prepare_features(df_rfm)
            optimal_results = find_optimal_k(X_scaled)

        st.session_state["X_scaled"] = X_scaled
        st.session_state["scaler"] = scaler

        col_e, col_s = st.columns(2)

        with col_e:
            st.markdown(section_header("trending-down", "Elbow Method (Inertia)"), unsafe_allow_html=True)
            fig_elbow = go.Figure()
            fig_elbow.add_trace(go.Scatter(
                x=optimal_results["k_values"], y=optimal_results["inertias"],
                mode="lines+markers",
                line=dict(color="#2A6F2B", width=3),
                marker=dict(size=8, color="#2A6F2B"),
                hovertemplate="K=%{x}<br>Inertia=%{y:,.0f}<extra></extra>",
            ))
            fig_elbow.add_vline(
                x=optimal_results["optimal_k_elbow"],
                line_dash="dash", line_color="#e74c3c",
                annotation_text=f"Elbow: K={optimal_results['optimal_k_elbow']}"
            )
            fig_elbow.update_layout(
                **PLOTLY_LAYOUT, height=350,
                xaxis=dict(title="Jumlah Cluster (K)", dtick=1),
                yaxis=dict(title="Inertia", gridcolor="#f0f0f0"),
            )
            st.plotly_chart(fig_elbow, use_container_width=True)

        with col_s:
            st.markdown(section_header("bar-chart", "Silhouette Score"), unsafe_allow_html=True)
            best_sil_val = max(optimal_results["silhouette_scores"])
            colors = ["#2A6F2B" if s == best_sil_val else "#d5f5e3" for s in optimal_results["silhouette_scores"]]
            fig_sil = go.Figure()
            fig_sil.add_trace(go.Bar(
                x=optimal_results["k_values"], y=optimal_results["silhouette_scores"],
                marker_color=colors, marker_line=dict(width=1, color="#043F2E"),
                text=[f"{s:.4f}" for s in optimal_results["silhouette_scores"]],
                textposition="outside", textfont=dict(size=10, family="Poppins"),
                hovertemplate="K=%{x}<br>Score=%{y:.4f}<extra></extra>",
            ))
            fig_sil.update_layout(
                **PLOTLY_LAYOUT, height=350,
                xaxis=dict(title="Jumlah Cluster (K)", dtick=1),
                yaxis=dict(title="Silhouette Score", gridcolor="#f0f0f0"),
            )
            st.plotly_chart(fig_sil, use_container_width=True)

        # Davies-Bouldin & Calinski-Harabasz
        col_d, col_c = st.columns(2)
        with col_d:
            st.markdown(section_header("trending-down", "Davies-Bouldin Index", "↓ Semakin rendah semakin baik"), unsafe_allow_html=True)
            fig_dbi = go.Figure()
            fig_dbi.add_trace(go.Scatter(
                x=optimal_results["k_values"], y=optimal_results["dbi_scores"],
                mode="lines+markers", line=dict(color="#e74c3c", width=3),
                marker=dict(size=8), hovertemplate="K=%{x}<br>DBI=%{y:.4f}<extra></extra>",
            ))
            fig_dbi.update_layout(**PLOTLY_LAYOUT, height=300, xaxis=dict(title="K", dtick=1), yaxis=dict(title="DBI", gridcolor="#f0f0f0"))
            st.plotly_chart(fig_dbi, use_container_width=True)

        with col_c:
            st.markdown(section_header("trending-up", "Calinski-Harabasz Index", "↑ Semakin tinggi semakin baik"), unsafe_allow_html=True)
            fig_chi = go.Figure()
            fig_chi.add_trace(go.Scatter(
                x=optimal_results["k_values"], y=optimal_results["chi_scores"],
                mode="lines+markers", line=dict(color="#9b59b6", width=3),
                marker=dict(size=8), hovertemplate="K=%{x}<br>CHI=%{y:,.0f}<extra></extra>",
            ))
            fig_chi.update_layout(**PLOTLY_LAYOUT, height=300, xaxis=dict(title="K", dtick=1), yaxis=dict(title="CH Index", gridcolor="#f0f0f0"))
            st.plotly_chart(fig_chi, use_container_width=True)

        # DBSCAN k-distance graph
        if cluster_method in ["DBSCAN", "Bandingkan Semua (3 Metode)"]:
            st.divider()
            st.markdown(section_header("bar-chart", "K-Distance Graph", "Estimasi parameter eps optimal untuk DBSCAN"), unsafe_allow_html=True)
            ms = dbscan_min_samples if 'dbscan_min_samples' in dir() else 5
            kdist = get_kdistance_data(X_scaled, min_samples=ms)

            fig_kdist = go.Figure()
            fig_kdist.add_trace(go.Scatter(
                y=kdist["k_distances"], mode="lines",
                line=dict(color="#3498db", width=2), name="k-distance"
            ))
            fig_kdist.add_hline(
                y=kdist["eps_estimate"], line_dash="dash", line_color="#e74c3c",
                annotation_text=f"eps estimasi: {kdist['eps_estimate']}"
            )
            fig_kdist.update_layout(**PLOTLY_LAYOUT, height=350,
                xaxis=dict(title="Data Points (sorted)", gridcolor="#f0f0f0"),
                yaxis=dict(title=f"{ms}-distance", gridcolor="#f0f0f0"),
            )
            st.plotly_chart(fig_kdist, use_container_width=True)

        # Rekomendasi
        st.markdown(f"""
        <div style="
            background:linear-gradient(135deg,#eafaf1,#d5f5e3);
            border-radius:12px;padding:16px 20px;border:1px solid #abebc6;margin-top:12px;
        ">
            <div style="font-size:0.85rem;font-weight:700;color:#043F2E;margin-bottom:6px;">Rekomendasi K Optimal</div>
            <div style="font-size:0.82rem;color:#1a252f;line-height:1.6;">
                • Elbow Method: <strong>K = {optimal_results['optimal_k_elbow']}</strong><br>
                • Silhouette Score terbaik: <strong>K = {optimal_results['optimal_k_silhouette']}</strong> (Score: {max(optimal_results['silhouette_scores']):.4f})
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.session_state["optimal_results"] = optimal_results

    # ==== TAB 3: Hasil Clustering ====
    with tab3:
        st.markdown(section_header("target", "Hasil Clustering", "Visualisasi dan evaluasi cluster yang terbentuk"), unsafe_allow_html=True)

        X_scaled = st.session_state.get("X_scaled", prepare_features(df_rfm)[0])

        # Tentukan K
        if cluster_method != "DBSCAN":
            if k_mode == "Otomatis (Elbow + Silhouette)":
                chosen_k = optimal_results["optimal_k_silhouette"]
            else:
                chosen_k = manual_k
        else:
            chosen_k = None

        # Jalankan clustering
        with st.spinner("Menjalankan clustering..."):
            all_results = {}

            if cluster_method in ["K-Means", "Bandingkan Semua (3 Metode)"]:
                all_results["K-Means"] = run_kmeans(X_scaled, chosen_k)

            if cluster_method in ["K-Medoids", "Bandingkan Semua (3 Metode)"]:
                all_results["K-Medoids"] = run_kmedoids(X_scaled, chosen_k)

            if cluster_method in ["DBSCAN", "Bandingkan Semua (3 Metode)"]:
                eps_val = manual_eps if (dbscan_eps_mode == "Manual" and manual_eps) else None
                all_results["DBSCAN"] = run_dbscan(X_scaled, eps=eps_val, min_samples=dbscan_min_samples)

        # Perbandingan metode
        if cluster_method == "Bandingkan Semua (3 Metode)":
            st.markdown(section_header("zap", "Perbandingan K-Means vs K-Medoids vs DBSCAN"), unsafe_allow_html=True)

            eps_val = manual_eps if (dbscan_eps_mode == "Manual" and manual_eps) else None
            comparison_df = compare_methods(X_scaled, chosen_k, dbscan_eps=eps_val, dbscan_min_samples=dbscan_min_samples)

            st.dataframe(comparison_df, hide_index=True, use_container_width=True)

            # Cari metode terbaik
            valid_comparison = comparison_df[comparison_df["Silhouette Score"].apply(lambda x: isinstance(x, (int, float)))]
            if not valid_comparison.empty:
                best_method = valid_comparison.loc[valid_comparison["Silhouette Score"].idxmax(), "Metode"]
                best_sil = valid_comparison["Silhouette Score"].max()

                st.markdown(f"""
                <div style="
                    background:linear-gradient(135deg,#fef9e7,#fdebd0);
                    border-radius:12px;padding:14px 18px;border:1px solid #f9e79f;margin:8px 0;
                ">
                    <span style="font-size:0.9rem;font-weight:700;color:#7d6608;">
                        Metode terbaik: <strong>{best_method}</strong> (Silhouette Score: {best_sil})
                    </span>
                </div>
                """, unsafe_allow_html=True)

            # DBSCAN noise info
            db_res = all_results.get("DBSCAN", {})
            if db_res.get("n_noise", 0) > 0:
                st.warning(f"DBSCAN mendeteksi **{db_res['n_noise']} noise points** ({db_res['noise_percentage']}% dari total)")

            # Pilih metode terbaik untuk visualisasi
            if "K-Means" in best_method:
                chosen_result = all_results["K-Means"]
            elif "K-Medoids" in best_method:
                chosen_result = all_results["K-Medoids"]
            else:
                chosen_result = all_results["DBSCAN"]
            chosen_labels = chosen_result["labels"]

        elif cluster_method == "DBSCAN":
            chosen_result = all_results["DBSCAN"]
            chosen_labels = chosen_result["labels"]

            c_db1, c_db2, c_db3 = st.columns(3)
            with c_db1:
                st.markdown(kpi_card("search", "Cluster Ditemukan", str(chosen_result["n_clusters"]), color="#3498db"), unsafe_allow_html=True)
            with c_db2:
                st.markdown(kpi_card("volume-x", "Noise Points", f"{chosen_result['n_noise']} ({chosen_result['noise_percentage']}%)", color="#e74c3c"), unsafe_allow_html=True)
            with c_db3:
                sil = chosen_result.get("silhouette_score", "N/A")
                st.markdown(kpi_card("star", "Silhouette Score", str(sil) if sil else "N/A", color="#f39c12"), unsafe_allow_html=True)

            if chosen_result.get("warning"):
                st.warning(chosen_result["warning"])
        else:
            chosen_result = list(all_results.values())[0]
            chosen_labels = chosen_result["labels"]

        # Simpan ke session
        st.session_state["chosen_labels"] = chosen_labels
        st.session_state["chosen_result"] = chosen_result
        st.session_state["chosen_k"] = chosen_result.get("n_clusters", chosen_k)
        st.session_state["all_results"] = all_results

        # Metrik cards
        if chosen_result.get("silhouette_score") is not None:
            cm1, cm2, cm3 = st.columns(3)
            with cm1:
                st.markdown(kpi_card("star", "Silhouette Score", str(chosen_result["silhouette_score"]), color="#2A6F2B"), unsafe_allow_html=True)
            with cm2:
                st.markdown(kpi_card("trending-down", "Davies-Bouldin Index", str(chosen_result["davies_bouldin_index"]), color="#e74c3c"), unsafe_allow_html=True)
            with cm3:
                st.markdown(kpi_card("trending-up", "Calinski-Harabasz", f"{chosen_result['calinski_harabasz_score']:,.0f}", color="#9b59b6"), unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        # Scatter plot 2D
        st.markdown(section_header("globe", "Visualisasi Cluster (2D)", "Scatter plot Frequency vs Monetary, ukuran = Recency"), unsafe_allow_html=True)

        df_plot = df_rfm.copy()
        df_plot["Cluster"] = chosen_labels.astype(str)
        df_plot.loc[df_plot["Cluster"] == "-1", "Cluster"] = "Noise"
        df_plot["recency_size"] = df_plot["recency"].clip(lower=1)

        fig_scatter = px.scatter(
            df_plot, x="frequency", y="monetary", color="Cluster",
            size="recency_size",
            hover_data=["id_donatur", "nama_lengkap", "recency", "r_score", "f_score", "m_score"],
            labels={"frequency": "Frequency (Jumlah Donasi)", "monetary": "Monetary (Total Rp)", "recency_size": "Recency (hari)"},
            color_discrete_sequence=GREEN_PALETTE,
            opacity=0.7,
        )
        fig_scatter.update_layout(**PLOTLY_LAYOUT, height=500, xaxis=dict(gridcolor="#f0f0f0"), yaxis=dict(gridcolor="#f0f0f0"))
        st.plotly_chart(fig_scatter, use_container_width=True)

        # Scatter plot 3D
        st.markdown(section_header("globe", "Visualisasi Cluster (3D)", "Poppinsaktif — geser untuk rotasi"), unsafe_allow_html=True)
        fig_3d = px.scatter_3d(
            df_plot, x="recency", y="frequency", z="monetary", color="Cluster",
            hover_data=["id_donatur", "nama_lengkap"],
            labels={"recency": "Recency", "frequency": "Frequency", "monetary": "Monetary"},
            color_discrete_sequence=GREEN_PALETTE,
            opacity=0.6,
        )
        layout_3d = {k: v for k, v in PLOTLY_LAYOUT.items() if k != "margin"}
        fig_3d.update_layout(**layout_3d, height=600, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig_3d, use_container_width=True)

        # Cluster profiles
        st.markdown(section_header("file-text", "Profil Cluster"), unsafe_allow_html=True)
        profiles = get_cluster_profiles(df_rfm, chosen_labels)
        st.dataframe(profiles, hide_index=True, use_container_width=True)

    # ==== TAB 4: Analisis Silhouette ====
    with tab4:
        st.markdown(section_header("search", "Analisis Silhouette (Per Cluster)", "Evaluasi kualitas setiap cluster berdasarkan silhouette coefficient"), unsafe_allow_html=True)

        if "chosen_labels" in st.session_state and "X_scaled" in st.session_state:
            sil_analysis = get_silhouette_analysis(
                st.session_state["X_scaled"],
                st.session_state["chosen_labels"]
            )

            if "error" in sil_analysis:
                st.error(sil_analysis["error"])
            else:
                st.markdown(kpi_card("bar-chart", "Rata-rata Silhouette Score", str(sil_analysis["avg_silhouette"]), color="#2A6F2B"), unsafe_allow_html=True)
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

                # Tabel per cluster
                st.markdown(section_header("file-text", "Detail per Cluster"), unsafe_allow_html=True)
                st.dataframe(sil_analysis["cluster_analysis"], hide_index=True, use_container_width=True)

                # Silhouette plot
                st.markdown(section_header("bar-chart", "Silhouette Plot"), unsafe_allow_html=True)

                sil_vals = sil_analysis["sample_values"]
                sil_labels = sil_analysis["sample_labels"]

                fig_sil_plot = go.Figure()

                y_lower = 0
                unique_clusters = sorted(set(sil_labels))

                for i, cluster in enumerate(unique_clusters):
                    cluster_sil = sorted(sil_vals[sil_labels == cluster])
                    cluster_size = len(cluster_sil)
                    y_upper = y_lower + cluster_size

                    fig_sil_plot.add_trace(go.Bar(
                        x=cluster_sil, y=list(range(y_lower, y_upper)),
                        orientation='h', name=f"Cluster {cluster}",
                        marker_color=GREEN_PALETTE[i % len(GREEN_PALETTE)],
                        showlegend=True,
                    ))
                    y_lower = y_upper + 5

                fig_sil_plot.add_vline(
                    x=sil_analysis["avg_silhouette"],
                    line_dash="dash", line_color="#e74c3c",
                    annotation_text=f"Avg: {sil_analysis['avg_silhouette']}"
                )
                fig_sil_plot.update_layout(
                    **PLOTLY_LAYOUT, height=500,
                    xaxis=dict(title="Silhouette Coefficient"),
                    yaxis=dict(title="Data Points", showticklabels=False),
                    barmode="stack",
                )
                st.plotly_chart(fig_sil_plot, use_container_width=True)

                # Poppinspretasi
                bad_clusters = sil_analysis["cluster_analysis"][
                    sil_analysis["cluster_analysis"]["negative_pct"] > 20
                ]
                if not bad_clusters.empty:
                    st.warning(f"⚠️ **{len(bad_clusters)} cluster** memiliki >20% anggota dengan silhouette negatif. "
                              "Pertimbangkan untuk mengubah jumlah K atau menggunakan metode clustering yang berbeda.")
                else:
                    st.markdown("""
                    <div style="background:linear-gradient(135deg,#eafaf1,#d5f5e3);border-radius:12px;padding:14px 18px;border:1px solid #abebc6;">
                        <span style="font-size:0.85rem;font-weight:600;color:#043F2E;">
                            ✅ Semua cluster memiliki kualitas baik (< 20% silhouette negatif).
                        </span>
                    </div>
                    """, unsafe_allow_html=True)

    # ==== TAB 5: Hyperparameter Tuning ====
    with tab5:
        st.markdown(section_header("zap", "Hyperparameter Tuning", "Eksperimen dengan berbagai konfigurasi parameter"), unsafe_allow_html=True)

        X_scaled = st.session_state.get("X_scaled", prepare_features(df_rfm)[0])

        col_t1, col_t2 = st.columns(2)

        with col_t1:
            st.markdown(section_header("globe", "K-Means Tuning"), unsafe_allow_html=True)
            if cluster_method != "DBSCAN":
                k_tune = chosen_k
            else:
                k_tune = optimal_results.get("optimal_k_silhouette", 4)

            with st.spinner("Tuning K-Means..."):
                km_tune_df = tune_kmeans(X_scaled, k_tune)

            st.dataframe(km_tune_df, hide_index=True, use_container_width=True)

            best_km = km_tune_df.loc[km_tune_df["Silhouette"].idxmax()]
            st.markdown(f"""
            <div style="background:rgba(39,174,96,0.08);border-radius:10px;padding:10px 14px;border:1px solid rgba(39,174,96,0.2);margin-top:8px;">
                <span style="font-size:0.8rem;font-weight:600;color:#043F2E;">
                    Best: {best_km['Konfigurasi']} (Silhouette: {best_km['Silhouette']})
                </span>
            </div>
            """, unsafe_allow_html=True)

        with col_t2:
            st.markdown(section_header("settings", "DBSCAN Tuning"), unsafe_allow_html=True)

            with st.spinner("Tuning DBSCAN..."):
                db_tune_df = tune_dbscan(X_scaled)

            db_valid = db_tune_df[db_tune_df["n_clusters"] >= 2].copy()

            if not db_valid.empty:
                st.dataframe(db_valid, hide_index=True, use_container_width=True)

                best_db = db_valid.loc[db_valid["Silhouette"].idxmax()]
                st.markdown(f"""
                <div style="background:rgba(243,156,18,0.08);border-radius:10px;padding:10px 14px;border:1px solid rgba(243,156,18,0.2);margin-top:8px;">
                    <span style="font-size:0.8rem;font-weight:600;color:#7d6608;">
                        Best: eps={best_db['eps']}, min_samples={int(best_db['min_samples'])}
                        (Silhouette: {best_db['Silhouette']}, Clusters: {int(best_db['n_clusters'])})
                    </span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.dataframe(db_tune_df, hide_index=True, use_container_width=True)
                st.warning("Tidak ada konfigurasi DBSCAN yang menghasilkan ≥ 2 cluster.")

    # ==== TAB 6: Data Lengkap ====
    with tab6:
        st.markdown(section_header("file-text", "Data RFM Lengkap", "Tabel lengkap dengan filter dan export"), unsafe_allow_html=True)

        df_display = df_rfm.copy()
        if "chosen_labels" in st.session_state:
            df_display["cluster"] = st.session_state["chosen_labels"]

        # Filter
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            segment_filter = st.multiselect(
                "Filter Segmen",
                options=df_display["segment"].unique(),
                default=df_display["segment"].unique(),
            )
        with col_f2:
            sort_by = st.selectbox(
                "Urutkan berdasarkan",
                ["rfm_score", "recency", "frequency", "monetary"],
                index=0,
            )

        df_filtered = df_display[df_display["segment"].isin(segment_filter)]
        df_filtered = df_filtered.sort_values(sort_by, ascending=(sort_by == "recency"))

        st.dataframe(df_filtered, hide_index=True, use_container_width=True)

        # Export
        csv_data = df_filtered.to_csv(index=False)
        st.download_button(
            "Download Data RFM (CSV)",
            data=csv_data,
            file_name="rfm_segmentasi_donatur.csv",
            mime="text/csv",
            use_container_width=True,
        )

else:
    # Idle state
    st.markdown("""
    <div style="
        background:#fff;border-radius:14px;padding:40px;
        border:1px solid #e9ecef;box-shadow:0 2px 8px rgba(0,0,0,0.04);
        text-align:center;margin-top:20px;
    ">
        <div style="font-size:3rem;margin-bottom:12px;">🎯</div>
        <div style="font-size:1.1rem;font-weight:700;color:#1a252f;margin-bottom:6px;">Siap untuk Analisis</div>
        <div style="font-size:0.85rem;color:#6c757d;line-height:1.5;max-width:500px;margin:0 auto;">
            Klik tombol <strong>"Jalankan Analisis RFM & Clustering"</strong> di atas untuk memulai.
            Pastikan database MySQL sudah berjalan.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if "df_rfm" in st.session_state:
        st.markdown("""
        <div style="
            background:linear-gradient(135deg,#eafaf1,#d5f5e3);
            border-radius:12px;padding:14px 18px;border:1px solid #abebc6;margin-top:16px;
        ">
            <span style="font-size:0.85rem;font-weight:600;color:#043F2E;">
                📦 Data analisis sebelumnya tersedia. Klik tombol untuk refresh.
            </span>
        </div>
        """, unsafe_allow_html=True)
