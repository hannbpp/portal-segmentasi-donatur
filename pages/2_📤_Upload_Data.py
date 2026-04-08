"""
Page 2: Upload Data Baru
Upload file CSV/Excel data donasi baru ke database.
"""

import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.data_uploader import validate_upload, process_upload, REQUIRED_COLUMNS

st.set_page_config(page_title="Upload Data", page_icon="📤", layout="wide")

st.markdown("# 📤 Upload Data Donasi Baru")
st.markdown("Upload file CSV atau Excel berisi data donasi terbaru untuk ditambahkan ke database.")
st.divider()

# ---- Panduan Format ----
with st.expander("📋 Panduan Format File Upload", expanded=False):
    st.markdown(f"""
    **Kolom Wajib:**
    | Kolom | Tipe | Contoh |
    |-------|------|--------|
    | `id_donatur` | Teks | DU-2401.001 |
    | `nama_lengkap` | Teks | Ahmad Yani |
    | `tgl_bersih` | Tanggal | 2024-01-15 |
    | `nominal_valid` | Angka | 500000 |
    
    **Kolom Opsional:**
    `tipe`, `alamat`, `metode_bayar`, `cara_donasi`, `id_program_donasi`
    """)
    
    # Tombol download template
    template_df = pd.DataFrame({
        "id_donatur": ["DU-2601.001", "DU-2601.002"],
        "nama_lengkap": ["Ahmad Yani", "Siti Aminah"],
        "tgl_bersih": ["2026-01-15", "2026-01-20"],
        "nominal_valid": [500000, 250000],
        "tipe": ["Individu", "Individu"],
        "cara_donasi": ["Transfer", "Jemput Donasi"],
    })
    csv_template = template_df.to_csv(index=False)
    st.download_button(
        "⬇️ Download Template CSV",
        data=csv_template,
        file_name="template_upload_donasi.csv",
        mime="text/csv",
    )

st.markdown("---")

# ---- File Uploader ----
uploaded_file = st.file_uploader(
    "Pilih file CSV atau Excel",
    type=["csv", "xlsx", "xls"],
    help="File harus mengandung kolom wajib: id_donatur, nama_lengkap, tgl_bersih, nominal_valid"
)

if uploaded_file is not None:
    # Read file
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success(f"✅ File berhasil dibaca: **{len(df)} baris**, **{len(df.columns)} kolom**")
        
        # Validasi
        st.markdown("### 🔍 Hasil Validasi")
        result = validate_upload(df)
        
        if result["errors"]:
            for err in result["errors"]:
                st.error(f"❌ {err}")
        
        if result["warnings"]:
            for warn in result["warnings"]:
                st.warning(f"⚠️ {warn}")
        
        if result["is_valid"]:
            st.success("✅ File valid! Siap untuk di-upload ke database.")
        
        # Preview data
        st.markdown("### 📋 Preview Data")
        st.dataframe(result["preview_df"].head(20), hide_index=True, use_container_width=True)
        
        st.markdown(f"""
        **Ringkasan:**
        - Total baris: **{len(df)}**
        - Donatur unik: **{df['id_donatur'].nunique()}** 
        - Total nominal: **Rp {df['nominal_valid'].sum():,.0f}**
        - Periode: **{df['tgl_bersih'].min()}** s/d **{df['tgl_bersih'].max()}**
        """)
        
        # Tombol Upload
        st.markdown("---")
        if result["is_valid"]:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚀 Upload ke Database", type="primary", use_container_width=True):
                    with st.spinner("Memproses upload..."):
                        upload_result = process_upload(result["preview_df"])
                    
                    if upload_result["success"]:
                        st.balloons()
                        st.success(f"""
                        ✅ **Upload Berhasil!**
                        - Donatur baru ditambahkan: **{upload_result['new_donors']}**
                        - Transaksi baru ditambahkan: **{upload_result['new_transactions']}**
                        - Total nominal: **Rp {upload_result['total_nominal']:,.0f}**
                        """)
                        st.info("💡 Buka halaman **🎯 Analisis RFM** untuk menjalankan clustering ulang dengan data terbaru.")
                    else:
                        st.error(f"❌ Upload gagal: {upload_result.get('error', 'Unknown error')}")
            
            with col2:
                st.info("⚠️ Data yang di-upload akan **ditambahkan** ke database, bukan menimpa data lama.")
        else:
            st.warning("Perbaiki error di atas sebelum upload.")
    
    except Exception as e:
        st.error(f"❌ Gagal membaca file: {str(e)}")
