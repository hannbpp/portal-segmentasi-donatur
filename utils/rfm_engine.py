"""
rfm_engine.py
Mesin penghitung RFM (Recency, Frequency, Monetary) untuk setiap donatur.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from utils.db_connection import run_query


def get_rfm_data(reference_date: datetime = None) -> pd.DataFrame:
    """
    Hitung skor RFM untuk setiap donatur.
    
    Parameters:
        reference_date: Tanggal referensi untuk Recency.
                        Jika None, pakai tanggal terakhir data + 1 hari.
    
    Returns:
        DataFrame dengan kolom: id_donatur, nama_lengkap, tipe,
        recency, frequency, monetary, r_score, f_score, m_score,
        rfm_score, segment
    """
    # Ambil data donasi per donatur
    query = """
    SELECT 
        d.id_donatur,
        d.nama_lengkap,
        d.tipe,
        MAX(f.tgl_bersih)    AS last_donation_date,
        COUNT(f.id_fact)     AS frequency,
        SUM(f.nominal_valid) AS monetary
    FROM dim_donatur d
    INNER JOIN fact_donasi f ON d.id_donatur = f.id_donatur
    WHERE f.tgl_bersih IS NOT NULL 
      AND f.nominal_valid IS NOT NULL
      AND f.nominal_valid > 0
    GROUP BY d.id_donatur, d.nama_lengkap, d.tipe
    """
    df = run_query(query)
    
    if df.empty:
        return df
    
    # Tentukan tanggal referensi
    if reference_date is None:
        reference_date = df["last_donation_date"].max() + pd.Timedelta(days=1)
    
    # Hitung Recency (dalam hari)
    df["recency"] = (reference_date - pd.to_datetime(df["last_donation_date"])).dt.days
    
    # Pastikan tipe data benar
    df["frequency"] = df["frequency"].astype(int)
    df["monetary"] = df["monetary"].astype(float)
    
    # Drop kolom helper
    df = df.drop(columns=["last_donation_date"])
    
    # Hitung skor RFM (1-5, quintile)
    df["r_score"] = pd.qcut(df["recency"], q=5, labels=[5, 4, 3, 2, 1], duplicates="drop").astype(int)
    df["f_score"] = pd.qcut(df["frequency"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5], duplicates="drop").astype(int)
    df["m_score"] = pd.qcut(df["monetary"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5], duplicates="drop").astype(int)
    
    # RFM Score gabungan (rata-rata)
    df["rfm_score"] = ((df["r_score"] + df["f_score"] + df["m_score"]) / 3).round(2)
    
    # Assign segmen berdasarkan kombinasi skor
    df["segment"] = df.apply(_assign_segment, axis=1)
    
    return df


def _assign_segment(row) -> str:
    """
    Tentukan label segmen donatur berdasarkan skor R, F, M.
    Menggunakan logika segmentasi standar RFM.
    """
    r, f, m = row["r_score"], row["f_score"], row["m_score"]
    
    # Champions: R tinggi, F tinggi, M tinggi
    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    
    # Loyal: F tinggi
    if f >= 4 and m >= 3:
        return "Loyal"
    
    # Potential Loyalist: R tinggi, F sedang
    if r >= 4 and f >= 2 and f <= 4:
        return "Potential Loyalist"
    
    # New Donors: R tinggi, F rendah
    if r >= 4 and f <= 2:
        return "New Donors"
    
    # Promising: R sedang-tinggi, F rendah, M rendah
    if r >= 3 and f <= 2 and m <= 2:
        return "Promising"
    
    # Need Attention: R sedang, F sedang, M sedang
    if r >= 2 and r <= 4 and f >= 2 and f <= 4 and m >= 2 and m <= 4:
        return "Need Attention"
    
    # About to Sleep: R rendah-sedang, F rendah
    if r >= 2 and r <= 3 and f <= 2:
        return "About to Sleep"
    
    # At Risk: R rendah, F tinggi (dulu aktif)
    if r <= 2 and f >= 3:
        return "At Risk"
    
    # Hibernating: R sangat rendah, F rendah-sedang
    if r <= 2 and f >= 1 and f <= 3:
        return "Hibernating"
    
    # Lost: sisanya
    return "Lost"


def get_rfm_summary(df_rfm: pd.DataFrame) -> pd.DataFrame:
    """
    Buat ringkasan per segmen.
    """
    summary = df_rfm.groupby("segment").agg(
        jumlah_donatur=("id_donatur", "count"),
        avg_recency=("recency", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_monetary=("monetary", "mean"),
        avg_rfm_score=("rfm_score", "mean"),
    ).round(2).reset_index()
    
    summary = summary.sort_values("avg_rfm_score", ascending=False)
    return summary


def get_donation_trend() -> pd.DataFrame:
    """Ambil trend donasi per tahun."""
    query = """
    SELECT 
        YEAR(tgl_bersih) AS tahun,
        COUNT(*) AS jumlah_transaksi,
        SUM(nominal_valid) AS total_donasi,
        COUNT(DISTINCT id_donatur) AS jumlah_donatur
    FROM fact_donasi
    WHERE tgl_bersih IS NOT NULL AND tgl_bersih > '1900-01-02'
    GROUP BY YEAR(tgl_bersih)
    ORDER BY tahun
    """
    return run_query(query)


def get_donation_method_stats() -> pd.DataFrame:
    """Ambil statistik metode donasi."""
    query = """
    SELECT 
        cara_donasi,
        COUNT(*) AS jumlah,
        SUM(nominal_valid) AS total_nominal
    FROM fact_donasi
    WHERE cara_donasi IS NOT NULL AND cara_donasi != 'Tidak Ada Data'
    GROUP BY cara_donasi
    ORDER BY jumlah DESC
    """
    return run_query(query)
