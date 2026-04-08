"""
data_uploader.py
Fungsi untuk validasi dan upload data donasi baru ke database.
"""

import pandas as pd
import numpy as np
from utils.db_connection import get_connection, run_query


# Kolom wajib di file upload
REQUIRED_COLUMNS = ["id_donatur", "nama_lengkap", "tgl_bersih", "nominal_valid"]
OPTIONAL_COLUMNS = ["tipe", "alamat", "metode_bayar", "cara_donasi", "id_program_donasi"]


def validate_upload(df: pd.DataFrame) -> dict:
    """
    Validasi file CSV/Excel yang di-upload.
    
    Returns:
        dict: is_valid, errors, warnings, preview_df
    """
    errors = []
    warnings = []
    
    # Cek kolom wajib
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        errors.append(f"Kolom wajib tidak ditemukan: {', '.join(missing_cols)}")
        return {"is_valid": False, "errors": errors, "warnings": warnings, "preview_df": df}
    
    # Cek apakah ada data
    if df.empty:
        errors.append("File tidak berisi data (kosong).")
        return {"is_valid": False, "errors": errors, "warnings": warnings, "preview_df": df}
    
    # Validasi tgl_bersih bisa diparsing
    try:
        df["tgl_bersih"] = pd.to_datetime(df["tgl_bersih"], errors="coerce")
        null_dates = df["tgl_bersih"].isna().sum()
        if null_dates > 0:
            warnings.append(f"{null_dates} baris memiliki tanggal yang tidak valid (akan diisi 1900-01-01).")
            df["tgl_bersih"] = df["tgl_bersih"].fillna(pd.Timestamp("1900-01-01"))
    except Exception as e:
        errors.append(f"Gagal parsing kolom tgl_bersih: {str(e)}")
    
    # Validasi nominal_valid numerik
    try:
        df["nominal_valid"] = pd.to_numeric(df["nominal_valid"], errors="coerce")
        null_nominal = df["nominal_valid"].isna().sum()
        if null_nominal > 0:
            warnings.append(f"{null_nominal} baris memiliki nominal tidak valid (akan diisi 0).")
            df["nominal_valid"] = df["nominal_valid"].fillna(0)
        
        neg_nominal = (df["nominal_valid"] < 0).sum()
        if neg_nominal > 0:
            warnings.append(f"{neg_nominal} baris memiliki nominal negatif.")
    except Exception as e:
        errors.append(f"Gagal parsing kolom nominal_valid: {str(e)}")
    
    # Cek duplikat
    dup_count = df.duplicated(subset=["id_donatur", "tgl_bersih", "nominal_valid"]).sum()
    if dup_count > 0:
        warnings.append(f"{dup_count} baris kemungkinan duplikat (id + tanggal + nominal sama).")
    
    is_valid = len(errors) == 0
    return {"is_valid": is_valid, "errors": errors, "warnings": warnings, "preview_df": df}


def process_upload(df: pd.DataFrame) -> dict:
    """
    Proses upload data ke database.
    
    1. Cek donatur baru vs existing
    2. Insert donatur baru ke dim_donatur
    3. Insert transaksi donasi ke fact_donasi
    
    Returns:
        dict: new_donors, new_transactions, total_nominal
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Ambil ID donatur yang sudah ada
        existing_donors = run_query("SELECT id_donatur FROM dim_donatur")
        existing_ids = set(existing_donors["id_donatur"].tolist()) if not existing_donors.empty else set()
        
        # Pisahkan donatur baru
        new_donor_ids = set(df["id_donatur"].unique()) - existing_ids
        new_donors_df = df[df["id_donatur"].isin(new_donor_ids)].drop_duplicates(subset=["id_donatur"])
        
        # Insert donatur baru ke dim_donatur
        new_donor_count = 0
        for _, row in new_donors_df.iterrows():
            cursor.execute(
                """INSERT INTO dim_donatur (id_donatur, nama_lengkap, alamat, perusahaan, tipe, kontak_utama) 
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (
                    row["id_donatur"],
                    row.get("nama_lengkap", "Tidak Ada Data"),
                    row.get("alamat", "Tidak Ada Data"),
                    "Tidak Ada Data",
                    row.get("tipe", "Individu"),
                    "Tidak Ada Data",
                )
            )
            new_donor_count += 1
        
        # Generate ID transaksi baru
        max_id_result = run_query("SELECT MAX(CAST(id_transaksi_donasi AS UNSIGNED)) AS max_id FROM fact_donasi")
        max_id = int(max_id_result["max_id"].iloc[0]) if not max_id_result.empty and max_id_result["max_id"].iloc[0] else 0
        
        # Insert transaksi donasi ke fact_donasi
        new_tx_count = 0
        total_nominal = 0
        for _, row in df.iterrows():
            max_id += 1
            cursor.execute(
                """INSERT INTO fact_donasi 
                   (id_transaksi_donasi, id_donatur, tgl_bersih, nominal_valid, metode_bayar, cara_donasi)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (
                    str(max_id),
                    row["id_donatur"],
                    row["tgl_bersih"],
                    row["nominal_valid"],
                    row.get("metode_bayar", "Tidak Ada Data"),
                    row.get("cara_donasi", "Tidak Ada Data"),
                )
            )
            new_tx_count += 1
            total_nominal += float(row["nominal_valid"])
        
        conn.commit()
        
        return {
            "success": True,
            "new_donors": new_donor_count,
            "new_transactions": new_tx_count,
            "total_nominal": total_nominal,
        }
    
    except Exception as e:
        conn.rollback()
        return {
            "success": False,
            "error": str(e),
        }
    finally:
        cursor.close()
        conn.close()
