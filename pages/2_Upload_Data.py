"""
Page 2: Upload Data Baru
Upload file CSV/Excel data donasi baru ke database.
"""

import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.data_uploader import validate_upload, process_upload, REQUIRED_COLUMNS
from utils.styles import get_global_css, kpi_card, section_header, icon_html, PLOTLY_LAYOUT

st.set_page_config(page_title="Upload Data", page_icon="", layout="wide")
st.markdown(get_global_css(), unsafe_allow_html=True)

# ---- Header ----
st.markdown("""
<div style="margin-bottom:8px;">
    <div style="font-size:1.8rem;font-weight:800;color:#1a252f;letter-spacing:-0.5px;">
        Upload Data Donasi Baru
    </div>
    <div style="font-size:0.88rem;color:#6c757d;margin-top:-2px;">
        Upload file CSV atau Excel berisi data donasi terbaru untuk ditambahkan ke database
    </div>
</div>
""", unsafe_allow_html=True)

# ---- Sidebar ----
with st.sidebar:
    st.markdown("## Dompet Ummat")
    st.markdown("*Upload Data*")
    st.divider()

# ---- Panduan Format ----
st.markdown("""
<div style="
    background:#fff;border-radius:14px;padding:20px;
    border:1px solid #e9ecef;box-shadow:0 2px 8px rgba(0,0,0,0.04);
    margin-bottom:20px;
">
    <div style="font-size:0.95rem;font-weight:700;color:#1a252f;margin-bottom:12px;">
        Format File Upload
    </div>
    <div style="font-size:0.82rem;color:#343a40;line-height:1.7;">
        <strong>Kolom Wajib:</strong>
        <table style="width:100%;border-collapse:collapse;margin:8px 0;font-size:0.78rem;">
            <tr style="background:#f5f7fa;">
                <th style="padding:8px 12px;text-align:left;border-bottom:2px solid #e9ecef;font-weight:600;color:#6c757d;">Kolom</th>
                <th style="padding:8px 12px;text-align:left;border-bottom:2px solid #e9ecef;font-weight:600;color:#6c757d;">Tipe</th>
                <th style="padding:8px 12px;text-align:left;border-bottom:2px solid #e9ecef;font-weight:600;color:#6c757d;">Contoh</th>
            </tr>
            <tr><td style="padding:6px 12px;border-bottom:1px solid #f0f0f0;"><code>id_donatur</code></td><td style="padding:6px 12px;border-bottom:1px solid #f0f0f0;">Teks</td><td style="padding:6px 12px;border-bottom:1px solid #f0f0f0;">DU-2401.001</td></tr>
            <tr><td style="padding:6px 12px;border-bottom:1px solid #f0f0f0;"><code>nama_lengkap</code></td><td style="padding:6px 12px;border-bottom:1px solid #f0f0f0;">Teks</td><td style="padding:6px 12px;border-bottom:1px solid #f0f0f0;">Ahmad Yani</td></tr>
            <tr><td style="padding:6px 12px;border-bottom:1px solid #f0f0f0;"><code>tgl_bersih</code></td><td style="padding:6px 12px;border-bottom:1px solid #f0f0f0;">Tanggal</td><td style="padding:6px 12px;border-bottom:1px solid #f0f0f0;">2024-01-15</td></tr>
            <tr><td style="padding:6px 12px;"><code>nominal_valid</code></td><td style="padding:6px 12px;">Angka</td><td style="padding:6px 12px;">500000</td></tr>
        </table>
        <span style="color:#6c757d;font-size:0.75rem;">
            <strong>Opsional:</strong> tipe, alamat, metode_bayar, cara_donasi, id_program_donasi
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# Template download
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
    "Download Template CSV",
    data=csv_template,
    file_name="template_upload_donasi.csv",
    mime="text/csv",
)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ---- File Uploader ----
st.markdown(section_header("file-text", "Upload File", "Pilih file CSV atau Excel untuk diupload"), unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Pilih file CSV atau Excel",
    type=["csv", "xlsx", "xls"],
    help="File harus mengandung kolom wajib: id_donatur, nama_lengkap, tgl_bersih, nominal_valid",
    label_visibility="collapsed",
)

if uploaded_file is not None:
    # Read file
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # Success message
        st.markdown(f"""
        <div style="
            background:linear-gradient(135deg,#eafaf1,#d5f5e3);
            border-radius:12px;padding:14px 18px;
            border:1px solid #abebc6;margin:12px 0;
        ">
            <span style="font-size:0.88rem;font-weight:600;color:#043F2E;">
                ✅ File berhasil dibaca: <strong>{len(df)} baris</strong>, <strong>{len(df.columns)} kolom</strong>
            </span>
        </div>
        """, unsafe_allow_html=True)

        # Validasi
        st.markdown(section_header("search", "Hasil Validasi"), unsafe_allow_html=True)
        result = validate_upload(df)

        if result["errors"]:
            for err in result["errors"]:
                st.error(f"❌ {err}")

        if result["warnings"]:
            for warn in result["warnings"]:
                st.warning(f"⚠️ {warn}")

        if result["is_valid"]:
            st.markdown("""
            <div style="
                background:linear-gradient(135deg,#eafaf1,#d5f5e3);
                border-radius:12px;padding:12px 16px;
                border:1px solid #abebc6;margin-bottom:12px;
            ">
                <span style="font-size:0.85rem;font-weight:600;color:#043F2E;">
                    ✅ File valid! Siap untuk di-upload ke database.
                </span>
            </div>
            """, unsafe_allow_html=True)

        # Preview data
        st.markdown(section_header("file-text", "Preview Data"), unsafe_allow_html=True)
        st.dataframe(result["preview_df"].head(20), hide_index=True, use_container_width=True)

        # Summary KPI cards
        s1, s2, s3, s4 = st.columns(4)
        with s1:
            st.markdown(kpi_card("file-text", "Total Baris", f"{len(df):,}", color="#2A6F2B"), unsafe_allow_html=True)
        with s2:
            st.markdown(kpi_card("user", "Donatur Unik", f"{df['id_donatur'].nunique():,}", color="#3498db"), unsafe_allow_html=True)
        with s3:
            total_nom = df["nominal_valid"].sum()
            if total_nom >= 1_000_000_000:
                nom_str = f"Rp {total_nom/1_000_000_000:.2f} M"
            else:
                nom_str = f"Rp {total_nom/1_000_000:.1f} Jt"
            st.markdown(kpi_card("wallet", "Total Nominal", nom_str, color="#f39c12"), unsafe_allow_html=True)
        with s4:
            periode = f"{df['tgl_bersih'].min()} — {df['tgl_bersih'].max()}"
            st.markdown(kpi_card("calendar", "Periode", periode[:20], color="#9b59b6"), unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        # Upload buttons
        if result["is_valid"]:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Upload ke Database", type="primary", use_container_width=True):
                    with st.spinner("Memproses upload..."):
                        upload_result = process_upload(result["preview_df"])

                    if upload_result["success"]:
                        st.balloons()
                        st.markdown(f"""
                        <div style="
                            background:linear-gradient(135deg,#eafaf1,#d5f5e3);
                            border-radius:14px;padding:20px;
                            border:1px solid #abebc6;margin:12px 0;
                        ">
                            <div style="font-size:1rem;font-weight:700;color:#043F2E;margin-bottom:8px;">
                                ✅ Upload Berhasil!
                            </div>
                            <div style="font-size:0.82rem;color:#343a40;line-height:1.7;">
                                • Donatur baru ditambahkan: <strong>{upload_result['new_donors']}</strong><br>
                                • Transaksi baru ditambahkan: <strong>{upload_result['new_transactions']}</strong><br>
                                • Total nominal: <strong>Rp {upload_result['total_nominal']:,.0f}</strong>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.info("Buka halaman **Analisis RFM** untuk menjalankan clustering ulang dengan data terbaru.")
                    else:
                        st.error(f"❌ Upload gagal: {upload_result.get('error', 'Unknown error')}")

            with col2:
                st.markdown("""
                <div style="
                    background:rgba(52,152,219,0.06);border-radius:12px;padding:14px 16px;
                    border:1px solid rgba(52,152,219,0.15);
                ">
                    <span style="font-size:0.82rem;color:#2c3e50;line-height:1.5;">
                        ⚠️ Data yang di-upload akan <strong>ditambahkan</strong> ke database, bukan menimpa data lama.
                    </span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Perbaiki error di atas sebelum upload.")

    except Exception as e:
        st.error(f"❌ Gagal membaca file: {str(e)}")

else:
    # Idle state
    st.markdown("""
    <div style="
        background:#fff;border-radius:14px;padding:40px;
        border:2px dashed #dee2e6;
        text-align:center;margin-top:8px;
    ">
        <div style="font-size:3rem;margin-bottom:12px;"></div>
        <div style="font-size:1rem;font-weight:700;color:#1a252f;margin-bottom:6px;">
            Drag & drop file atau klik untuk browse
        </div>
        <div style="font-size:0.82rem;color:#6c757d;">
            Format: CSV, XLSX, XLS — Maksimal 200MB
        </div>
    </div>
    """, unsafe_allow_html=True)
