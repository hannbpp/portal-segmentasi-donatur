# ============================================================
# KONFIGURASI DATABASE & APLIKASI
# Portal Segmentasi Donatur — Dompet Ummat Kalimantan Barat
# ============================================================

# --- MySQL (MAMP) ---
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 8889,
    "user": "root",
    "password": "root",
    "database": "dompet_ummat_dw",
}

# --- Aplikasi ---
APP_TITLE = "Portal Segmentasi Donatur"
APP_SUBTITLE = "Dompet Ummat Kalimantan Barat"
APP_ICON = "🎯"

# --- RFM Defaults ---
RFM_SEGMENT_LABELS = {
    "Champions":        "Donatur terbaik — sering donasi, nominal besar, baru-baru ini.",
    "Loyal":            "Donatur setia — frekuensi tinggi, nominal cukup baik.",
    "Potential Loyalist": "Donatur baru yang menunjukkan potensi loyalitas tinggi.",
    "New Donors":       "Donatur baru — baru pertama kali atau beberapa kali donasi.",
    "Promising":        "Donatur yang menunjukkan tanda-tanda positif, perlu nurturing.",
    "Need Attention":   "Donatur yang mulai menurun aktivitasnya, perlu follow-up.",
    "About to Sleep":   "Donatur yang hampir tidak aktif, perlu re-engagement segera.",
    "At Risk":          "Donatur yang dulu aktif tapi sudah lama tidak donasi.",
    "Hibernating":      "Donatur yang sudah sangat lama tidak aktif.",
    "Lost":             "Donatur yang kemungkinan besar sudah tidak akan kembali.",
}
