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

st.set_page_config(page_title="Analisis RFM & Clustering", page_icon="🎯", layout="wide")

st.markdown("# 🎯 Analisis RFM & Clustering")
st.markdown("Hitung skor RFM dan jalankan algoritma clustering untuk segmentasi donatur.")
st.divider()

# ---- Sidebar Settings ----
with st.sidebar:
    st.markdown("### ⚙️ Pengaturan")
    
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
        st.caption(f"📅 Referensi: {ref_date.strftime('%d %B %Y')}")
    elif date_mode == "Manual":
        ref_date = st.date_input("Pilih tanggal", value=datetime.now())
        ref_date = datetime.combine(ref_date, datetime.min.time())
    # Statis = None (akan otomatis pakai tanggal terakhir data)
    
    st.divider()
    
    # Clustering method
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
        st.markdown("#### 🔍 Parameter DBSCAN")
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
if st.button("🚀 Jalankan Analisis RFM & Clustering", type="primary", use_container_width=True):
    
    # Step 1: Hitung RFM
    with st.spinner("🔄 Menghitung skor RFM..."):
        df_rfm = get_rfm_data(reference_date=ref_date)
    
    if df_rfm.empty:
        st.error("Tidak ada data donasi yang valid di database.")
        st.stop()
    
    st.success(f"✅ RFM berhasil dihitung untuk **{len(df_rfm):,} donatur**")
    
    # Simpan ke session state
    st.session_state["df_rfm"] = df_rfm
    
    # ---- Tab Layout ----
    tab_titles = ["📊 Distribusi RFM", "🔬 Penentuan K Optimal", "🎯 Hasil Clustering", 
                  "🔬 Analisis Silhouette", "⚡ Hyperparameter Tuning", "📋 Data Lengkap"]
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(tab_titles)
    
    # ==== TAB 1: Distribusi RFM ====
    with tab1:
        st.markdown("### Distribusi Skor RFM")
        
        fig_dist = make_subplots(rows=1, cols=3, subplot_titles=("Recency (hari)", "Frequency (transaksi)", "Monetary (Rp)"))
        
        fig_dist.add_trace(
            go.Histogram(x=df_rfm["recency"], nbinsx=30, marker_color="#3498db", name="Recency"),
            row=1, col=1
        )
        fig_dist.add_trace(
            go.Histogram(x=df_rfm["frequency"], nbinsx=30, marker_color="#2ecc71", name="Frequency"),
            row=1, col=2
        )
        fig_dist.add_trace(
            go.Histogram(x=df_rfm["monetary"], nbinsx=30, marker_color="#e74c3c", name="Monetary"),
            row=1, col=3
        )
        fig_dist.update_layout(height=350, showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_dist, use_container_width=True)
        
        # Statistik deskriptif
        st.markdown("### Statistik Deskriptif")
        desc_cols = ["recency", "frequency", "monetary"]
        st.dataframe(
            df_rfm[desc_cols].describe().round(2).T,
            use_container_width=True
        )
        
        # Segmentasi RFM (tanpa clustering)
        st.markdown("### Segmentasi RFM (Rule-Based)")
        rfm_summary = get_rfm_summary(df_rfm)
        st.dataframe(rfm_summary, hide_index=True, use_container_width=True)
        
        fig_seg = px.bar(
            rfm_summary, x="segment", y="jumlah_donatur",
            color="avg_rfm_score",
            color_continuous_scale="RdYlGn",
            labels={"jumlah_donatur": "Jumlah Donatur", "segment": "Segmen"},
        )
        fig_seg.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_seg, use_container_width=True)
    
    # ==== TAB 2: Penentuan K Optimal ====
    with tab2:
        st.markdown("### Penentuan Jumlah Cluster Optimal")
        
        with st.spinner("🔄 Menghitung metrik untuk K=2 sampai K=10..."):
            X_scaled, scaler, feature_names = prepare_features(df_rfm)
            optimal_results = find_optimal_k(X_scaled)
        
        st.session_state["X_scaled"] = X_scaled
        st.session_state["scaler"] = scaler
        
        col_e, col_s = st.columns(2)
        
        with col_e:
            st.markdown("#### Elbow Method (Inertia)")
            fig_elbow = go.Figure()
            fig_elbow.add_trace(go.Scatter(
                x=optimal_results["k_values"],
                y=optimal_results["inertias"],
                mode="lines+markers",
                line=dict(color="#3498db", width=3),
                marker=dict(size=8),
            ))
            fig_elbow.add_vline(
                x=optimal_results["optimal_k_elbow"],
                line_dash="dash", line_color="red",
                annotation_text=f"Elbow: K={optimal_results['optimal_k_elbow']}"
            )
            fig_elbow.update_layout(
                xaxis_title="Jumlah Cluster (K)", yaxis_title="Inertia",
                height=350, margin=dict(l=20, r=20, t=20, b=20),
            )
            st.plotly_chart(fig_elbow, use_container_width=True)
        
        with col_s:
            st.markdown("#### Silhouette Score")
            colors = ["#2ecc71" if s == max(optimal_results["silhouette_scores"]) else "#bdc3c7" 
                      for s in optimal_results["silhouette_scores"]]
            fig_sil = go.Figure()
            fig_sil.add_trace(go.Bar(
                x=optimal_results["k_values"],
                y=optimal_results["silhouette_scores"],
                marker_color=colors,
                text=[f"{s:.4f}" for s in optimal_results["silhouette_scores"]],
                textposition="outside",
            ))
            fig_sil.add_vline(
                x=optimal_results["optimal_k_silhouette"],
                line_dash="dash", line_color="green",
                annotation_text=f"Best: K={optimal_results['optimal_k_silhouette']}"
            )
            fig_sil.update_layout(
                xaxis_title="Jumlah Cluster (K)", yaxis_title="Silhouette Score",
                height=350, margin=dict(l=20, r=20, t=20, b=20),
            )
            st.plotly_chart(fig_sil, use_container_width=True)
        
        # Davies-Bouldin & Calinski-Harabasz side by side
        col_d, col_c = st.columns(2)
        with col_d:
            st.markdown("#### Davies-Bouldin Index (↓ lebih baik)")
            fig_dbi = go.Figure()
            fig_dbi.add_trace(go.Scatter(
                x=optimal_results["k_values"],
                y=optimal_results["dbi_scores"],
                mode="lines+markers",
                line=dict(color="#e74c3c", width=3),
                marker=dict(size=8),
            ))
            fig_dbi.update_layout(
                xaxis_title="K", yaxis_title="DBI",
                height=300, margin=dict(l=20, r=20, t=20, b=20),
            )
            st.plotly_chart(fig_dbi, use_container_width=True)
        
        with col_c:
            st.markdown("#### Calinski-Harabasz Index (↑ lebih baik)")
            fig_chi = go.Figure()
            fig_chi.add_trace(go.Scatter(
                x=optimal_results["k_values"],
                y=optimal_results["chi_scores"],
                mode="lines+markers",
                line=dict(color="#9b59b6", width=3),
                marker=dict(size=8),
            ))
            fig_chi.update_layout(
                xaxis_title="K", yaxis_title="CH Index",
                height=300, margin=dict(l=20, r=20, t=20, b=20),
            )
            st.plotly_chart(fig_chi, use_container_width=True)
        
        # DBSCAN k-distance graph
        if cluster_method in ["DBSCAN", "Bandingkan Semua (3 Metode)"]:
            st.markdown("---")
            st.markdown("#### 📏 K-Distance Graph (untuk estimasi eps DBSCAN)")
            ms = dbscan_min_samples if 'dbscan_min_samples' in dir() else 5
            kdist = get_kdistance_data(X_scaled, min_samples=ms)
            
            fig_kdist = go.Figure()
            fig_kdist.add_trace(go.Scatter(
                y=kdist["k_distances"],
                mode="lines",
                line=dict(color="#3498db", width=2),
                name="k-distance"
            ))
            fig_kdist.add_hline(
                y=kdist["eps_estimate"],
                line_dash="dash", line_color="red",
                annotation_text=f"eps estimasi: {kdist['eps_estimate']}"
            )
            fig_kdist.update_layout(
                xaxis_title="Data Points (sorted)", yaxis_title=f"{ms}-distance",
                height=350, margin=dict(l=20, r=20, t=20, b=20),
            )
            st.plotly_chart(fig_kdist, use_container_width=True)
            st.info(f"📌 Estimasi eps optimal: **{kdist['eps_estimate']}** (min_samples={ms})")
        
        # Rekomendasi
        st.success(f"""
        **📌 Rekomendasi K Optimal:**
        - Elbow Method: **K = {optimal_results['optimal_k_elbow']}**
        - Silhouette Score terbaik: **K = {optimal_results['optimal_k_silhouette']}** (Score: {max(optimal_results['silhouette_scores']):.4f})
        """)
        
        st.session_state["optimal_results"] = optimal_results
    
    # ==== TAB 3: Hasil Clustering ====
    with tab3:
        st.markdown("### Hasil Clustering")
        
        X_scaled = st.session_state.get("X_scaled", prepare_features(df_rfm)[0])
        
        # Tentukan K
        if cluster_method != "DBSCAN":
            if k_mode == "Otomatis (Elbow + Silhouette)":
                chosen_k = optimal_results["optimal_k_silhouette"]
            else:
                chosen_k = manual_k
            st.info(f"🎯 Menggunakan **K = {chosen_k}** cluster")
        else:
            chosen_k = None
        
        # Jalankan clustering
        with st.spinner("🔄 Menjalankan clustering..."):
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
            st.markdown("#### 📊 Perbandingan K-Means vs K-Medoids vs DBSCAN")
            
            eps_val = manual_eps if (dbscan_eps_mode == "Manual" and manual_eps) else None
            comparison_df = compare_methods(X_scaled, chosen_k, dbscan_eps=eps_val, dbscan_min_samples=dbscan_min_samples)
            
            st.dataframe(comparison_df, hide_index=True, use_container_width=True)
            
            # Cari metode terbaik (berdasarkan Silhouette Score valid)
            valid_comparison = comparison_df[comparison_df["Silhouette Score"].apply(lambda x: isinstance(x, (int, float)))]
            if not valid_comparison.empty:
                best_method = valid_comparison.loc[valid_comparison["Silhouette Score"].idxmax(), "Metode"]
                best_sil = valid_comparison["Silhouette Score"].max()
                st.success(f"🏆 **Metode terbaik: {best_method}** (Silhouette Score: {best_sil})")
            
            # DBSCAN noise info
            db_res = all_results.get("DBSCAN", {})
            if db_res.get("n_noise", 0) > 0:
                st.warning(f"🔍 DBSCAN mendeteksi **{db_res['n_noise']} noise points** ({db_res['noise_percentage']}% dari total)")
            
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
            
            col_db1, col_db2, col_db3 = st.columns(3)
            with col_db1:
                st.metric("🔍 Cluster Ditemukan", chosen_result["n_clusters"])
            with col_db2:
                st.metric("🔇 Noise Points", f"{chosen_result['n_noise']} ({chosen_result['noise_percentage']}%)")
            with col_db3:
                sil = chosen_result.get("silhouette_score", "N/A")
                st.metric("⭐ Silhouette Score", sil if sil else "N/A")
            
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
        
        # Metrik (jika tersedia)
        if chosen_result.get("silhouette_score") is not None:
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric("Silhouette Score", chosen_result["silhouette_score"])
            with col_m2:
                st.metric("Davies-Bouldin Index", chosen_result["davies_bouldin_index"])
            with col_m3:
                st.metric("Calinski-Harabasz", f"{chosen_result['calinski_harabasz_score']:,.0f}")
        
        # Scatter plot 2D
        st.markdown("#### 🔵 Visualisasi Cluster (2D)")
        
        df_plot = df_rfm.copy()
        df_plot["Cluster"] = chosen_labels.astype(str)
        # Label noise as "Noise"
        df_plot.loc[df_plot["Cluster"] == "-1", "Cluster"] = "Noise"
        # Clamp recency to min 1 for marker size
        df_plot["recency_size"] = df_plot["recency"].clip(lower=1)
        
        fig_scatter = px.scatter(
            df_plot, x="frequency", y="monetary",
            color="Cluster",
            size="recency_size",
            hover_data=["id_donatur", "nama_lengkap", "recency", "r_score", "f_score", "m_score"],
            labels={"frequency": "Frequency (Jumlah Donasi)", "monetary": "Monetary (Total Rp)", "recency_size": "Recency (hari)"},
            color_discrete_sequence=px.colors.qualitative.Set1,
            opacity=0.7,
        )
        fig_scatter.update_layout(height=500, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Scatter plot 3D
        st.markdown("#### 🌐 Visualisasi Cluster (3D)")
        fig_3d = px.scatter_3d(
            df_plot, x="recency", y="frequency", z="monetary",
            color="Cluster",
            hover_data=["id_donatur", "nama_lengkap"],
            labels={"recency": "Recency", "frequency": "Frequency", "monetary": "Monetary"},
            color_discrete_sequence=px.colors.qualitative.Set1,
            opacity=0.6,
        )
        fig_3d.update_layout(height=600, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig_3d, use_container_width=True)
        
        # Cluster profiles
        st.markdown("#### 📋 Profil Cluster")
        profiles = get_cluster_profiles(df_rfm, chosen_labels)
        st.dataframe(profiles, hide_index=True, use_container_width=True)
    
    # ==== TAB 4: Analisis Silhouette ====
    with tab4:
        st.markdown("### 🔬 Analisis Silhouette (Per Cluster)")
        st.markdown("Analisis mendalam kualitas setiap cluster berdasarkan silhouette coefficient.")
        
        if "chosen_labels" in st.session_state and "X_scaled" in st.session_state:
            sil_analysis = get_silhouette_analysis(
                st.session_state["X_scaled"], 
                st.session_state["chosen_labels"]
            )
            
            if "error" in sil_analysis:
                st.error(sil_analysis["error"])
            else:
                st.metric("📊 Rata-rata Silhouette Score", sil_analysis["avg_silhouette"])
                
                # Tabel per cluster
                st.markdown("#### Detail per Cluster")
                st.dataframe(sil_analysis["cluster_analysis"], hide_index=True, use_container_width=True)
                
                # Silhouette plot
                st.markdown("#### Silhouette Plot")
                
                sil_vals = sil_analysis["sample_values"]
                sil_labels = sil_analysis["sample_labels"]
                
                fig_sil_plot = go.Figure()
                
                y_lower = 0
                unique_clusters = sorted(set(sil_labels))
                colors_sil = px.colors.qualitative.Set1
                
                for i, cluster in enumerate(unique_clusters):
                    cluster_sil = sorted(sil_vals[sil_labels == cluster])
                    cluster_size = len(cluster_sil)
                    y_upper = y_lower + cluster_size
                    
                    fig_sil_plot.add_trace(go.Bar(
                        x=cluster_sil,
                        y=list(range(y_lower, y_upper)),
                        orientation='h',
                        name=f"Cluster {cluster}",
                        marker_color=colors_sil[i % len(colors_sil)],
                        showlegend=True,
                    ))
                    y_lower = y_upper + 5  # gap between clusters
                
                # Average line
                fig_sil_plot.add_vline(
                    x=sil_analysis["avg_silhouette"], 
                    line_dash="dash", line_color="red",
                    annotation_text=f"Avg: {sil_analysis['avg_silhouette']}"
                )
                
                fig_sil_plot.update_layout(
                    xaxis_title="Silhouette Coefficient",
                    yaxis_title="Data Points",
                    height=500,
                    margin=dict(l=20, r=20, t=20, b=20),
                    barmode="stack",
                    yaxis=dict(showticklabels=False),
                )
                st.plotly_chart(fig_sil_plot, use_container_width=True)
                
                # Interpretasi
                bad_clusters = sil_analysis["cluster_analysis"][
                    sil_analysis["cluster_analysis"]["negative_pct"] > 20
                ]
                if not bad_clusters.empty:
                    st.warning(f"""
                    ⚠️ **{len(bad_clusters)} cluster** memiliki >20% anggota dengan silhouette negatif.
                    Ini berarti sebagian anggota cluster tersebut mungkin lebih cocok di cluster lain.
                    Pertimbangkan untuk mengubah jumlah K atau menggunakan metode clustering yang berbeda.
                    """)
                else:
                    st.success("✅ Semua cluster memiliki kualitas baik (< 20% silhouette negatif).")
    
    # ==== TAB 5: Hyperparameter Tuning ====
    with tab5:
        st.markdown("### ⚡ Hyperparameter Tuning")
        st.markdown("Eksperimen dengan berbagai konfigurasi parameter untuk menemukan kombinasi terbaik.")
        
        X_scaled = st.session_state.get("X_scaled", prepare_features(df_rfm)[0])
        
        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            st.markdown("#### 🔵 K-Means Tuning")
            if cluster_method != "DBSCAN":
                k_tune = chosen_k
            else:
                k_tune = optimal_results.get("optimal_k_silhouette", 4)
            
            with st.spinner("Tuning K-Means..."):
                km_tune_df = tune_kmeans(X_scaled, k_tune)
            
            st.dataframe(km_tune_df, hide_index=True, use_container_width=True)
            
            best_km = km_tune_df.loc[km_tune_df["Silhouette"].idxmax()]
            st.info(f"🏆 **Best config:** {best_km['Konfigurasi']} (Silhouette: {best_km['Silhouette']})")
        
        with col_t2:
            st.markdown("#### 🟠 DBSCAN Tuning")
            
            with st.spinner("Tuning DBSCAN..."):
                db_tune_df = tune_dbscan(X_scaled)
            
            # Filter out rows with no valid clusters
            db_valid = db_tune_df[db_tune_df["n_clusters"] >= 2].copy()
            
            if not db_valid.empty:
                st.dataframe(db_valid, hide_index=True, use_container_width=True)
                
                best_db = db_valid.loc[db_valid["Silhouette"].idxmax()]
                st.info(f"🏆 **Best config:** eps={best_db['eps']}, min_samples={int(best_db['min_samples'])} "
                        f"(Silhouette: {best_db['Silhouette']}, Clusters: {int(best_db['n_clusters'])})")
            else:
                st.dataframe(db_tune_df, hide_index=True, use_container_width=True)
                st.warning("⚠️ Tidak ada konfigurasi DBSCAN yang menghasilkan ≥ 2 cluster. "
                          "Data mungkin terlalu seragam atau parameter perlu disesuaikan.")
    
    # ==== TAB 6: Data Lengkap ====
    with tab6:
        st.markdown("### Data RFM Lengkap")
        
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
        
        # Export to CSV
        csv_data = df_filtered.to_csv(index=False)
        st.download_button(
            "⬇️ Download Data RFM (CSV)",
            data=csv_data,
            file_name="rfm_segmentasi_donatur.csv",
            mime="text/csv",
        )

else:
    st.info("👆 Klik tombol di atas untuk memulai analisis RFM dan clustering.")
    
    # Show cached results if available
    if "df_rfm" in st.session_state:
        st.success("📦 Data analisis sebelumnya tersedia. Klik tombol untuk refresh, atau lihat hasil di bawah.")
