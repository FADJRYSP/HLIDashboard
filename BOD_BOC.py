import pandas as pd
import streamlit as st

# Konfigurasi Halaman Dashboard
st.set_page_config(
    page_title="Dashboard Tindak Lanjut Rapat BOD-BOC",
    page_icon="📊",
    layout="wide",
)

# Judul Utama
st.title("📊 Dashboard Analisis Tindak Lanjut Rapat BOD-BOC")
st.markdown(
    "Dashboard ini digunakan untuk memantau status, kegiatan, serta progres "
    "strategis dari hasil rapat BOD-BOC."
)

# Nama File Excel sesuai dengan gambar
EXCEL_FILE = "24072026 Kirim Tim DH_Tindak Lanjut rapat BOD-BOC.xlsx"


# Fungsi untuk memuat data dengan caching (Perbaikan posisi @st.cache_data)
@st.cache_data
def load_data(file_path):
  return pd.read_excel(file_path)


# Memanggil fungsi load data dengan penanganan error
try:
  df = load_data(EXCEL_FILE)
except Exception as e:
  st.error(
      f"Gagal memuat file Excel '{EXCEL_FILE}'. Pastikan nama file dan "
      f"posisinya sudah benar di folder yang sama.\nDetail Error: {e}"
  )
  st.stop()

# --- SIDEBAR: FILTER DATA ---
st.sidebar.header("🔍 Filter Data")

# Filter Status
if "STATUS" in df.columns:
  status_options = df["STATUS"].dropna().unique().tolist()
  selected_status = st.sidebar.multiselect(
      "Pilih Status", options=status_options, default=status_options
  )
  df = df[df["STATUS"].isin(selected_status)]

# Filter Unit Pengusul / Lembaga
if "UNIT PENGUSUL/LEMBAGA" in df.columns:
  unit_options = df["UNIT PENGUSUL/LEMBAGA"].dropna().unique().tolist()
  selected_unit = st.sidebar.multiselect(
      "Pilih Unit Pengusul/Lembaga", options=unit_options, default=unit_options
  )
  df = df[df["UNIT PENGUSUL/LEMBAGA"].isin(selected_unit)]

# --- METRIK UTAMA (KPIs) ---
st.markdown("### 📈 Ringkasan Eksekutif")
col1, col2, col3 = st.columns(3)

total_kegiatan = len(df)
status_done_count = (
    len(df[df["STATUS"].str.lower() == "done"])
    if "STATUS" in df.columns
    else 0
)
persentase_done = (
    (status_done_count / total_kegiatan) * 100 if total_kegiatan > 0 else 0
)

with col1:
  st.metric(label="Total Kegiatan / Tindak Lanjut", value=total_kegiatan)
with col2:
  st.metric(label="Status Selesai (Done)", value=status_done_count)
with col3:
  st.metric(label="Persentase Penyelesaian", value=f"{persentase_done:.1f}%")

st.markdown("---")

# --- VISUALISASI GRAFIK ---
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
  st.subheader("📊 Distribusi Status Kegiatan")
  if "STATUS" in df.columns and not df.empty:
    status_counts = df["STATUS"].value_counts()
    st.bar_chart(status_counts)
  else:
    st.info("Data status tidak tersedia.")

with col_chart2:
  st.subheader("🏛️ Kegiatan Berdasarkan Unit Pengusul")
  if "UNIT PENGUSUL/LEMBAGA" in df.columns and not df.empty:
    unit_counts = df["UNIT PENGUSUL/LEMBAGA"].value_counts()
    st.bar_chart(unit_counts)
  else:
    st.info("Data unit pengusul tidak tersedia.")

st.markdown("---")

# --- TABEL DATA DETAIL ---
st.subheader("📋 Detail Data Tindak Lanjut Rapat")
st.dataframe(df, use_container_width=True)

# --- TOMBOL DOWNLOAD LAPORAN ---
st.download_button(
    label="📥 Download Data yang Difilter (CSV)",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name="filtered_tindak_lanjut_bod_boc.csv",
    mime="text/csv",
)