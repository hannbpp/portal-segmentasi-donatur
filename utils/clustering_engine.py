"""
clustering_engine.py
Mesin clustering (K-Means, K-Medoids, DBSCAN) untuk segmentasi donatur berbasis RFM.
Dilengkapi hyperparameter tuning dan perbandingan 3 metode.
"""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import silhouette_score, silhouette_samples, davies_bouldin_score, calinski_harabasz_score
from sklearn.neighbors import NearestNeighbors
import warnings
warnings.filterwarnings("ignore")


def prepare_features(df_rfm: pd.DataFrame) -> tuple:
    """
    Siapkan fitur RFM yang sudah dinormalisasi untuk clustering.
    
    Returns:
        (X_scaled, scaler, feature_names)
    """
    feature_cols = ["recency", "frequency", "monetary"]
    X = df_rfm[feature_cols].values
    
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)
    
    return X_scaled, scaler, feature_cols


# ============================================================
# PENENTUAN K OPTIMAL
# ============================================================
def find_optimal_k(X_scaled: np.ndarray, k_range: range = range(2, 11)) -> dict:
    """
    Cari jumlah cluster optimal menggunakan Elbow Method + Silhouette Score + DBI.
    
    Returns:
        dict dengan keys: k_values, inertias, silhouette_scores, 
        dbi_scores, chi_scores, optimal_k_silhouette, optimal_k_elbow
    """
    inertias = []
    silhouette_scores_list = []
    dbi_scores = []
    chi_scores = []
    
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
        labels = kmeans.fit_predict(X_scaled)
        
        inertias.append(kmeans.inertia_)
        silhouette_scores_list.append(round(silhouette_score(X_scaled, labels), 4))
        dbi_scores.append(round(davies_bouldin_score(X_scaled, labels), 4))
        chi_scores.append(round(calinski_harabasz_score(X_scaled, labels), 4))
    
    # Optimal K berdasarkan Silhouette Score tertinggi
    optimal_k_silhouette = list(k_range)[np.argmax(silhouette_scores_list)]
    
    # Optimal K berdasarkan Elbow (perubahan inertia terbesar)
    diffs = np.diff(inertias)
    diffs2 = np.diff(diffs)
    optimal_k_elbow = list(k_range)[np.argmax(np.abs(diffs2)) + 2] if len(diffs2) > 0 else 3
    
    return {
        "k_values": list(k_range),
        "inertias": inertias,
        "silhouette_scores": silhouette_scores_list,
        "dbi_scores": dbi_scores,
        "chi_scores": chi_scores,
        "optimal_k_silhouette": optimal_k_silhouette,
        "optimal_k_elbow": optimal_k_elbow,
    }


# ============================================================
# K-MEANS
# ============================================================
def run_kmeans(X_scaled: np.ndarray, n_clusters: int, n_init: int = 10, max_iter: int = 300) -> dict:
    """
    Jalankan K-Means clustering.
    """
    kmeans = KMeans(
        n_clusters=n_clusters, 
        random_state=42, 
        n_init=n_init, 
        max_iter=max_iter,
    )
    labels = kmeans.fit_predict(X_scaled)
    
    sil_score = silhouette_score(X_scaled, labels)
    dbi_score = davies_bouldin_score(X_scaled, labels)
    chi_score = calinski_harabasz_score(X_scaled, labels)
    sil_samples = silhouette_samples(X_scaled, labels)
    
    return {
        "method": "K-Means",
        "labels": labels,
        "centroids": kmeans.cluster_centers_,
        "inertia": kmeans.inertia_,
        "silhouette_score": round(sil_score, 4),
        "davies_bouldin_index": round(dbi_score, 4),
        "calinski_harabasz_score": round(chi_score, 4),
        "silhouette_samples": sil_samples,
        "n_clusters": n_clusters,
        "params": {"n_init": n_init, "max_iter": max_iter},
    }


# ============================================================
# K-MEDOIDS
# ============================================================
def run_kmedoids(X_scaled: np.ndarray, n_clusters: int, max_iter: int = 300, metric: str = "euclidean") -> dict:
    """
    Jalankan K-Medoids clustering.
    Lebih robust terhadap outlier dibanding K-Means.
    """
    try:
        from sklearn_extra.cluster import KMedoids
        kmedoids = KMedoids(
            n_clusters=n_clusters, 
            random_state=42, 
            max_iter=max_iter,
            metric=metric,
        )
        labels = kmedoids.fit_predict(X_scaled)
        
        sil_score = silhouette_score(X_scaled, labels)
        dbi_score = davies_bouldin_score(X_scaled, labels)
        chi_score = calinski_harabasz_score(X_scaled, labels)
        sil_samples = silhouette_samples(X_scaled, labels)
        
        return {
            "method": "K-Medoids",
            "labels": labels,
            "centroids": kmedoids.cluster_centers_,
            "inertia": kmedoids.inertia_,
            "silhouette_score": round(sil_score, 4),
            "davies_bouldin_index": round(dbi_score, 4),
            "calinski_harabasz_score": round(chi_score, 4),
            "silhouette_samples": sil_samples,
            "n_clusters": n_clusters,
            "params": {"max_iter": max_iter, "metric": metric},
        }
    except ImportError:
        return {
            "method": "K-Medoids",
            "error": "scikit-learn-extra belum terinstall. Jalankan: pip install scikit-learn-extra",
        }


# ============================================================
# DBSCAN
# ============================================================
def estimate_dbscan_eps(X_scaled: np.ndarray, min_samples: int = 5) -> float:
    """
    Estimasi parameter eps optimal untuk DBSCAN menggunakan k-distance graph.
    Menghitung jarak ke k-nearest neighbor dan mencari titik elbow.
    """
    nn = NearestNeighbors(n_neighbors=min_samples)
    nn.fit(X_scaled)
    distances, _ = nn.kneighbors(X_scaled)
    
    # Ambil jarak ke neighbor terjauh (kolom terakhir), sort ascending
    k_distances = np.sort(distances[:, -1])
    
    # Cari titik elbow menggunakan perbedaan turunan kedua
    diffs = np.diff(k_distances)
    diffs2 = np.diff(diffs)
    
    if len(diffs2) > 0:
        elbow_idx = np.argmax(diffs2) + 2
        eps_estimate = k_distances[elbow_idx]
    else:
        # Fallback: gunakan percentile 90
        eps_estimate = np.percentile(k_distances, 90)
    
    return round(float(eps_estimate), 4)


def get_kdistance_data(X_scaled: np.ndarray, min_samples: int = 5) -> dict:
    """
    Hitung k-distance data untuk plotting k-distance graph.
    """
    nn = NearestNeighbors(n_neighbors=min_samples)
    nn.fit(X_scaled)
    distances, _ = nn.kneighbors(X_scaled)
    
    k_distances = np.sort(distances[:, -1])
    eps_estimate = estimate_dbscan_eps(X_scaled, min_samples)
    
    return {
        "k_distances": k_distances.tolist(),
        "eps_estimate": eps_estimate,
        "min_samples": min_samples,
    }


def run_dbscan(X_scaled: np.ndarray, eps: float = None, min_samples: int = 5) -> dict:
    """
    Jalankan DBSCAN clustering.
    Tidak memerlukan jumlah cluster di awal — otomatis menemukan cluster
    berdasarkan kepadatan data. Bisa mendeteksi noise/outlier.
    """
    # Auto-estimate eps jika tidak diberikan
    if eps is None:
        eps = estimate_dbscan_eps(X_scaled, min_samples)
    
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    labels = dbscan.fit_predict(X_scaled)
    
    # DBSCAN labels: -1 = noise, 0+ = cluster
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = (labels == -1).sum()
    
    result = {
        "method": "DBSCAN",
        "labels": labels,
        "n_clusters": n_clusters,
        "n_noise": n_noise,
        "noise_percentage": round(n_noise / len(labels) * 100, 2),
        "params": {"eps": round(eps, 4), "min_samples": min_samples},
    }
    
    # Hitung metrik hanya jika ada >= 2 cluster dan tidak semua noise
    non_noise_mask = labels != -1
    if n_clusters >= 2 and non_noise_mask.sum() > n_clusters:
        sil_score = silhouette_score(X_scaled[non_noise_mask], labels[non_noise_mask])
        dbi_score = davies_bouldin_score(X_scaled[non_noise_mask], labels[non_noise_mask])
        chi_score = calinski_harabasz_score(X_scaled[non_noise_mask], labels[non_noise_mask])
        sil_samples_full = np.zeros(len(labels))
        sil_samples_full[non_noise_mask] = silhouette_samples(X_scaled[non_noise_mask], labels[non_noise_mask])
        sil_samples_full[~non_noise_mask] = -1  # noise = -1
        
        result.update({
            "silhouette_score": round(sil_score, 4),
            "davies_bouldin_index": round(dbi_score, 4),
            "calinski_harabasz_score": round(chi_score, 4),
            "silhouette_samples": sil_samples_full,
        })
    else:
        result.update({
            "silhouette_score": None,
            "davies_bouldin_index": None,
            "calinski_harabasz_score": None,
            "silhouette_samples": None,
            "warning": f"DBSCAN hanya menemukan {n_clusters} cluster (noise: {n_noise}). Coba turunkan eps atau min_samples.",
        })
    
    return result


def tune_dbscan(X_scaled: np.ndarray, eps_range: list = None, min_samples_range: list = None) -> pd.DataFrame:
    """
    Hyperparameter tuning untuk DBSCAN.
    Coba berbagai kombinasi eps dan min_samples, evaluasi hasilnya.
    """
    if eps_range is None:
        base_eps = estimate_dbscan_eps(X_scaled, 5)
        eps_range = [round(base_eps * m, 4) for m in [0.5, 0.75, 1.0, 1.25, 1.5]]
    
    if min_samples_range is None:
        min_samples_range = [3, 5, 7, 10]
    
    results = []
    for eps in eps_range:
        for ms in min_samples_range:
            res = run_dbscan(X_scaled, eps=eps, min_samples=ms)
            results.append({
                "eps": eps,
                "min_samples": ms,
                "n_clusters": res["n_clusters"],
                "n_noise": res["n_noise"],
                "noise_%": res["noise_percentage"],
                "Silhouette": res.get("silhouette_score"),
                "DBI": res.get("davies_bouldin_index"),
                "CH": res.get("calinski_harabasz_score"),
            })
    
    return pd.DataFrame(results)


# ============================================================
# HYPERPARAMETER TUNING K-MEANS
# ============================================================
def tune_kmeans(X_scaled: np.ndarray, k: int) -> pd.DataFrame:
    """
    Hyperparameter tuning untuk K-Means.
    Variasi: n_init dan inisialisasi.
    """
    configs = [
        {"n_init": 10, "init": "k-means++", "label": "k-means++ (n_init=10)"},
        {"n_init": 20, "init": "k-means++", "label": "k-means++ (n_init=20)"},
        {"n_init": 50, "init": "k-means++", "label": "k-means++ (n_init=50)"},
        {"n_init": 10, "init": "random", "label": "random (n_init=10)"},
        {"n_init": 20, "init": "random", "label": "random (n_init=20)"},
    ]
    
    results = []
    for cfg in configs:
        km = KMeans(n_clusters=k, n_init=cfg["n_init"], init=cfg["init"], 
                    random_state=42, max_iter=300)
        labels = km.fit_predict(X_scaled)
        
        results.append({
            "Konfigurasi": cfg["label"],
            "Inertia": round(km.inertia_, 2),
            "Silhouette": round(silhouette_score(X_scaled, labels), 4),
            "DBI": round(davies_bouldin_score(X_scaled, labels), 4),
            "CH": round(calinski_harabasz_score(X_scaled, labels), 4),
        })
    
    return pd.DataFrame(results)


# ============================================================
# PERBANDINGAN 3 METODE
# ============================================================
def compare_methods(X_scaled: np.ndarray, n_clusters: int, dbscan_eps: float = None, dbscan_min_samples: int = 5) -> pd.DataFrame:
    """
    Bandingkan K-Means vs K-Medoids vs DBSCAN.
    
    Returns:
        DataFrame perbandingan metrik ketiga metode.
    """
    results = []
    
    # K-Means
    km_result = run_kmeans(X_scaled, n_clusters)
    results.append({
        "Metode": "K-Means",
        "Jumlah Cluster": n_clusters,
        "Noise Points": 0,
        "Silhouette Score": km_result["silhouette_score"],
        "Davies-Bouldin Index": km_result["davies_bouldin_index"],
        "Calinski-Harabasz": km_result["calinski_harabasz_score"],
        "Inertia": round(km_result["inertia"], 2),
    })
    
    # K-Medoids
    kmed_result = run_kmedoids(X_scaled, n_clusters)
    if "error" not in kmed_result:
        results.append({
            "Metode": "K-Medoids",
            "Jumlah Cluster": n_clusters,
            "Noise Points": 0,
            "Silhouette Score": kmed_result["silhouette_score"],
            "Davies-Bouldin Index": kmed_result["davies_bouldin_index"],
            "Calinski-Harabasz": kmed_result["calinski_harabasz_score"],
            "Inertia": round(kmed_result["inertia"], 2),
        })
    
    # DBSCAN
    db_result = run_dbscan(X_scaled, eps=dbscan_eps, min_samples=dbscan_min_samples)
    results.append({
        "Metode": f"DBSCAN (eps={db_result['params']['eps']}, ms={dbscan_min_samples})",
        "Jumlah Cluster": db_result["n_clusters"],
        "Noise Points": db_result["n_noise"],
        "Silhouette Score": db_result.get("silhouette_score", "N/A"),
        "Davies-Bouldin Index": db_result.get("davies_bouldin_index", "N/A"),
        "Calinski-Harabasz": db_result.get("calinski_harabasz_score", "N/A"),
        "Inertia": "N/A",
    })
    
    return pd.DataFrame(results)


# ============================================================
# SILHOUETTE ANALYSIS (Per-Sample)
# ============================================================
def get_silhouette_analysis(X_scaled: np.ndarray, labels: np.ndarray) -> dict:
    """
    Analisis silhouette per sample dan per cluster.
    Untuk membuat Silhouette Plot yang detail.
    """
    unique_labels = sorted(set(labels))
    # Filter noise for DBSCAN
    non_noise = labels != -1
    
    if non_noise.sum() < 2:
        return {"error": "Tidak cukup data non-noise untuk analisis silhouette."}
    
    sil_vals = silhouette_samples(X_scaled[non_noise], labels[non_noise])
    avg_score = silhouette_score(X_scaled[non_noise], labels[non_noise])
    
    cluster_analysis = []
    for label in sorted(set(labels[non_noise])):
        mask = labels[non_noise] == label
        cluster_sil = sil_vals[mask]
        cluster_analysis.append({
            "cluster": int(label),
            "n_samples": int(mask.sum()),
            "avg_silhouette": round(float(cluster_sil.mean()), 4),
            "min_silhouette": round(float(cluster_sil.min()), 4),
            "max_silhouette": round(float(cluster_sil.max()), 4),
            "negative_count": int((cluster_sil < 0).sum()),
            "negative_pct": round(float((cluster_sil < 0).mean() * 100), 1),
        })
    
    return {
        "avg_silhouette": round(avg_score, 4),
        "sample_values": sil_vals,
        "sample_labels": labels[non_noise],
        "cluster_analysis": pd.DataFrame(cluster_analysis),
    }


# ============================================================
# PROFIL CLUSTER
# ============================================================
def get_cluster_profiles(df_rfm: pd.DataFrame, labels: np.ndarray) -> pd.DataFrame:
    """
    Buat profil rata-rata RFM per cluster.
    """
    df = df_rfm.copy()
    df["cluster"] = labels
    
    # Filter noise (label -1 dari DBSCAN)
    df_clean = df[df["cluster"] != -1]
    
    if df_clean.empty:
        return pd.DataFrame()
    
    profiles = df_clean.groupby("cluster").agg(
        jumlah_donatur=("id_donatur", "count"),
        avg_recency=("recency", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_monetary=("monetary", "mean"),
        avg_r_score=("r_score", "mean"),
        avg_f_score=("f_score", "mean"),
        avg_m_score=("m_score", "mean"),
        min_monetary=("monetary", "min"),
        max_monetary=("monetary", "max"),
        median_monetary=("monetary", "median"),
    ).round(2).reset_index()
    
    # Assign nama segmen berdasarkan profil cluster
    profiles["label_segmen"] = profiles.apply(_auto_label_cluster, axis=1)
    
    # Tambah noise info jika ada
    noise_count = (labels == -1).sum()
    if noise_count > 0:
        noise_row = pd.DataFrame([{
            "cluster": -1,
            "jumlah_donatur": noise_count,
            "avg_recency": df[df["cluster"] == -1]["recency"].mean(),
            "avg_frequency": df[df["cluster"] == -1]["frequency"].mean(),
            "avg_monetary": df[df["cluster"] == -1]["monetary"].mean(),
            "avg_r_score": df[df["cluster"] == -1]["r_score"].mean(),
            "avg_f_score": df[df["cluster"] == -1]["f_score"].mean(),
            "avg_m_score": df[df["cluster"] == -1]["m_score"].mean(),
            "min_monetary": df[df["cluster"] == -1]["monetary"].min(),
            "max_monetary": df[df["cluster"] == -1]["monetary"].max(),
            "median_monetary": df[df["cluster"] == -1]["monetary"].median(),
            "label_segmen": "Noise / Outlier",
        }]).round(2)
        profiles = pd.concat([profiles, noise_row], ignore_index=True)
    
    return profiles


def _auto_label_cluster(row) -> str:
    """
    Beri label otomatis ke cluster berdasarkan rata-rata skor RFM.
    """
    r = row["avg_r_score"]
    f = row["avg_f_score"]
    m = row["avg_m_score"]
    avg = (r + f + m) / 3
    
    if avg >= 4.0:
        return "Champions"
    elif avg >= 3.5:
        return "Loyal"
    elif r >= 3.5 and f <= 2.5:
        return "New Donors"
    elif r <= 2.0 and f >= 3.0:
        return "At Risk"
    elif avg >= 2.5:
        return "Need Attention"
    elif r <= 2.0 and f <= 2.0:
        return "Hibernating"
    else:
        return "About to Sleep"


# ============================================================
# REKOMENDASI STRATEGI
# ============================================================
def get_segment_recommendations() -> dict:
    """
    Saran strategi retensi per segmen donatur.
    """
    return {
        "Champions": {
            "emoji": "🏆",
            "color": "#2ecc71",
            "strategi": "Pertahankan hubungan premium. Berikan apresiasi khusus, undangan eksklusif, dan laporan impact donasi.",
            "aksi": ["Kirim laporan impact personal", "Undang ke acara eksklusif", "Berikan sertifikat apresiasi"],
        },
        "Loyal": {
            "emoji": "💎",
            "color": "#3498db",
            "strategi": "Tingkatkan engagement. Tawarkan program recurring donation dan program referral.",
            "aksi": ["Tawarkan auto-debit bulanan", "Program ajak teman berdonasi", "Update rutin via WhatsApp"],
        },
        "Potential Loyalist": {
            "emoji": "🌟",
            "color": "#9b59b6",
            "strategi": "Nurturing intensif. Bangun hubungan personal agar menjadi Loyal/Champions.",
            "aksi": ["Follow-up personal via telepon", "Kirim newsletter impact", "Ajak ke program sukarelawan"],
        },
        "New Donors": {
            "emoji": "🌱",
            "color": "#1abc9c",
            "strategi": "Welcome program. Bangun first impression yang kuat agar donatur kembali.",
            "aksi": ["Kirim welcome package/email", "Ucapan terima kasih personal", "Informasi program yang relevan"],
        },
        "Promising": {
            "emoji": "📈",
            "color": "#f39c12",
            "strategi": "Edukasi dan ajak berpartisipasi lebih aktif dalam program-program Dompet Ummat.",
            "aksi": ["Kirim cerita sukses penerima manfaat", "Tawarkan variasi program donasi", "Reminder berkala"],
        },
        "Need Attention": {
            "emoji": "⚠️",
            "color": "#e67e22",
            "strategi": "Re-engagement campaign. Ingatkan kembali pentingnya donasi dan impact yang dicapai.",
            "aksi": ["Campaign re-engagement via email/WA", "Berikan promo/match donation", "Survey kepuasan donatur"],
        },
        "About to Sleep": {
            "emoji": "😴",
            "color": "#e74c3c",
            "strategi": "Urgent re-activation! Hubungi segera sebelum hilang sepenuhnya.",
            "aksi": ["Telepon personal dari tim fundraising", "Campaign spesial Ramadhan/Qurban", "Diskon/cashback donasi"],
        },
        "At Risk": {
            "emoji": "🚨",
            "color": "#c0392b",
            "strategi": "Win-back campaign intensif. Donatur ini dulunya aktif, ada peluang kembali.",
            "aksi": ["Hubungi personal, tanyakan alasan berhenti", "Tawarkan fleksibilitas nominal", "Kirim laporan dampak"],
        },
        "Hibernating": {
            "emoji": "❄️",
            "color": "#7f8c8d",
            "strategi": "Low-cost re-engagement. Kirim komunikasi berkala tanpa terlalu agresif.",
            "aksi": ["Email/WA blast berkala", "Masukkan ke mailing list umum", "Campaign seasonal (Ramadhan)"],
        },
        "Lost": {
            "emoji": "👋",
            "color": "#95a5a6",
            "strategi": "Minimal effort. Simpan data untuk campaign besar saja (Ramadhan, bencana).",
            "aksi": ["Masukkan ke list campaign besar saja", "Jangan terlalu sering kontak", "Analisis alasan churn"],
        },
        "Noise / Outlier": {
            "emoji": "🔍",
            "color": "#bdc3c7",
            "strategi": "Data point yang tidak cocok masuk cluster manapun. Perlu investigasi individual.",
            "aksi": ["Periksa data apakah valid", "Analisis manual per donatur", "Kemungkinan donatur unik atau data error"],
        },
    }
