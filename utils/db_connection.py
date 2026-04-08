"""
db_connection.py
Helper untuk koneksi ke MySQL (MAMP) dan menjalankan query.
"""

import pandas as pd
import mysql.connector
from config import DB_CONFIG


def get_connection():
    """Buat koneksi baru ke MySQL."""
    return mysql.connector.connect(**DB_CONFIG)


def run_query(query: str, params: tuple = None) -> pd.DataFrame:
    """Jalankan SELECT query dan kembalikan hasilnya sebagai DataFrame."""
    conn = get_connection()
    try:
        df = pd.read_sql(query, conn, params=params)
        return df
    finally:
        conn.close()


def execute_query(query: str, params: tuple = None):
    """Jalankan INSERT/UPDATE/DELETE query."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def execute_many(query: str, data: list):
    """Jalankan INSERT batch (executemany)."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.executemany(query, data)
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def get_table_stats() -> pd.DataFrame:
    """Ambil statistik jumlah rows untuk tabel utama."""
    query = """
    SELECT 'dim_donatur' AS tabel, COUNT(*) AS jumlah FROM dim_donatur
    UNION ALL
    SELECT 'fact_donasi', COUNT(*) FROM fact_donasi
    UNION ALL
    SELECT 'dim_program_donasi', COUNT(*) FROM dim_program_donasi
    """
    return run_query(query)
