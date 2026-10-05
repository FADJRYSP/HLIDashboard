import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import streamlit as st

# Konfigurasi Halaman Web Menjadi Lebar
st.set_page_config(
    page_title="Dashboard Kegiatan HHI - PT KAI", page_icon="🚆", layout="wide"
)

# Custom CSS untuk Banner & Efek Card Timbul (Elevated Shadow)
st.markdown(
    """
    <style>
        .kai-banner {
            background: linear-gradient(90deg, #003366 75%, #FF6600 25%);
            padding: 15px 25px;
            border-radius: 10px;
            color: white;
            font-family: Arial, sans-serif;
            display: flex;
            align-items: center;
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
            margin-bottom: 25px;
        }
        .kai-logo {
            height: 45px;
            margin-right: 20px;
            background-color: white;
            padding: 4px 8px;
            border-radius: 6px;
        }
        .kai-title {
            font-size: 22px;
            font-weight: bold;
            margin: 0;
            line-height: 1.2;
        }
        .kai-subtitle {
            font-size: 12px;
            margin: 2px 0 0 0;
            opacity: 0.9;
        }
        .metric-card {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-left: 5px solid #003366;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 6px 12px rgba(0,0,0,0.1);
        }
        .metric-title {
            font-size: 11px;
            color: #666666;
            font-weight: bold;
            text-transform: uppercase;
            margin-bottom: 4px;
        }
        .metric-value {
            font-size: 20px;
            color: #003366;
            font-weight: bold;
            margin: 0;
        }
        /* Efek Card Timbul Berbayang Tegas */
        div[data-testid="stVerticalBlock"] > div[data-testid="stContainer"] {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            padding: 18px;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.12), 0 4px 10px rgba(0, 0, 0, 0.05);
            margin-bottom: 20px;
        }
    </style>
    <div class="kai-banner">
        <img src="http://keretaapikita.com/wp-content/uploads/2020/09/Logo-Baru-PT-KAI.jpg" class="kai-logo">
        <div>
            <div class="kai-title">REKAP DATA KEGIATAN HHI 2026</div>
            <div class="kai-subtitle">PT KERETA API INDONESIA (PERSERO) - LIVE INPUT DASHBOARD</div>
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

# Load Data dari Excel
file_excel = "Monev Kegiatan HHI.xlsx"


@st.cache_data
def load_data():
    try:
        xls = pd.ExcelFile(file_excel)
        sheet_names = xls.sheet_names

        if "Monev KRT" in sheet_names:
            df_test = pd.read_excel(file_excel, sheet_name="Monev KRT", nrows=5)
            header_row = (
                0 if "PEKERJAAN" in df_test.columns.astype(str).str.upper() else 1
            )
        else:
            header_row = 1

        df_krt = pd.read_excel(
            file_excel, sheet_name="Monev KRT", header=header_row
        )
        df_strategis = pd.read_excel(
            file_excel, sheet_name="Monev Strategis", header=header_row
        )
        df_kerjasama = pd.read_excel(
            file_excel, sheet_name="Monev Kerjasama", header=header_row
        )
    except Exception:
        df_krt = pd.read_excel(file_excel, sheet_name=0, header=0)
        df_strategis = pd.read_excel(file_excel, sheet_name=1, header=0)
        df_kerjasama = pd.read_excel(file_excel, sheet_name=2, header=0)

    df_krt["KATEGORI_MONEV"] = "MONEV KRT"
    df_strategis["KATEGORI_MONEV"] = "MONEV STRATEGIS"
    df_kerjasama["KATEGORI_MONEV"] = "MONEV KERJASAMA"

    df_all = pd.concat([df_krt, df_strategis, df_kerjasama], ignore_index=True)
    df_all.columns = df_all.columns.str.strip().str.upper()

    # Ubah nama kolom UNIT menjadi UNIT PENGUSUL/LEMBAGA jika ada
    if "UNIT" in df_all.columns:
        df_all = df_all.rename(columns={"UNIT": "UNIT PENGUSUL/LEMBAGA"})

    if "UPDATE TERKINI" not in df_all.columns:
        df_all["UPDATE TERKINI"] = "-"
    if "GOALS" not in df_all.columns:
        df_all["GOALS"] = "-"
    if "START" not in df_all.columns:
        df_all["START"] = "-"

    if "STATUS" in df_all.columns:
        df_all["STATUS"] = (
            df_all["STATUS"].astype(str).str.strip().str.upper()
        )
        df_all.loc[df_all["STATUS"] == "NAN", "STATUS"] = "ON PROGRES"

    return df_all


# Inisialisasi Session State supaya data inputan & hasil hapus tidak hilang
if "df_global" not in st.session_state:
    st.session_state.df_global = load_data()

df_all = st.session_state.df_global

if "STATUS" in df_all.columns:
    df_all["STATUS"] = df_all["STATUS"].astype(str).str.strip().str.upper()

# Konversi Tanggal yang Kuat
if "START" in df_all.columns:
    def parse_flexible_date(val):
        if pd.isna(val) or val == "-" or val == "":
            return pd.NaT
        try:
            if isinstance(val, (int, float)) or (
                isinstance(val, str) and val.replace(".", "", 1).isdigit()
            ):
                return pd.to_datetime("1899-12-30") + pd.to_timedelta(
                    float(val), unit="d"
                )
        except:
            pass
        try:
            return pd.to_datetime(val, errors="coerce")
        except:
            return pd.NaT

    df_all["START_DT"] = df_all["START"].apply(parse_flexible_date)
    df_all["BULAN"] = df_all["START_DT"].dt.strftime("%b")
else:
    df_all["BULAN"] = "-"

# Panel Kontrol Sidebar (Filter Kategori Monev)
st.sidebar.header("⚙️ Panel Kontrol")
pilihan_monev = st.sidebar.selectbox(
    "Pilih Kategori Monev",
    [
        "Semua Kategori",
        "MONEV KRT",
        "MONEV STRATEGIS",
        "MONEV KERJASAMA",
    ],
)

if pilihan_monev != "Semua Kategori":
    df_filtered = df_all[df_all["KATEGORI_MONEV"] == pilihan_monev]
else:
    df_filtered = df_all

# Perhitungan Metrik KPI Cards
total_kegiatan = len(df_filtered)
total_keseluruhan = len(df_all)
persen_dr_total = (
    f"{(total_kegiatan / total_keseluruhan) * 100:.0f}%"
    if total_keseluruhan > 0
    else "0%"
)

jumlah_selesai = (
    len(df_filtered[df_filtered["STATUS"] == "SELESAI"])
    if "STATUS" in df_filtered.columns
    else 0
)
jumlah_on_progres = (
    len(df_filtered[df_filtered["STATUS"] == "ON PROGRES"])
    if "STATUS" in df_filtered.columns
    else 0
)
jumlah_pending = (
    len(df_filtered[df_filtered["STATUS"] == "PENDING"])
    if "PENDING" in df_filtered["STATUS"].values
    else 0
)

# TAMPILAN KOTAK METRIK (KPI CARDS)
m1, m2, m3, m4, m5 = st.columns(5)

with m1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">Total Kegiatan</div>
            <div class="metric-value">{total_kegiatan}</div>
        </div>
    """,
        unsafe_allow_html=True,
    )

with m2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">% dari Total</div>
            <div class="metric-value">{persen_dr_total}</div>
        </div>
    """,
        unsafe_allow_html=True,
    )

with m3:
    st.markdown(
        f"""
        <div class="metric-card" style="border-left-color: #003366;">
            <div class="metric-title">Selesai</div>
            <div class="metric-value">{jumlah_selesai}</div>
        </div>
    """,
        unsafe_allow_html=True,
    )

with m4:
    st.markdown(
        f"""
        <div class="metric-card" style="border-left-color: #FF9900;">
            <div class="metric-title">On Progress</div>
            <div class="metric-value">{jumlah_on_progres}</div>
        </div>
    """,
        unsafe_allow_html=True,
    )

with m5:
    st.markdown(
        f"""
        <div class="metric-card" style="border-left-color: #A6A6A6;">
            <div class="metric-title">Pending</div>
            <div class="metric-value">{jumlah_pending}</div>
        </div>
    """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)


# Fungsi Pembersih Progress agar aman dibaca dalam bentuk angka
def clean_progress(val):
    try:
        if isinstance(val, str):
            val_str = val.replace("%", "").strip()
            num = float(val_str)
        else:
            num = float(val)
        if 0.0 <= num <= 1.0:
            num = num * 100
        return num
    except:
        return 0.0


# --- GRAFIK DISTRIBUSI KEGIATAN MONEV ---
with st.container(border=True):
    st.subheader("📊 Distribusi Kegiatan Monev (KRT, Strategis, & Kerjasama)")
    dist_counts = df_all["KATEGORI_MONEV"].value_counts().reset_index()
    dist_counts.columns = ["KATEGORI", "JUMLAH"]

    fig_dist = px.bar(
        dist_counts,
        x="JUMLAH",
        y="KATEGORI",
        orientation="h",
        text="JUMLAH",
        color="KATEGORI",
        color_discrete_map={
            "MONEV KRT": "#003366",
            "MONEV STRATEGIS": "#FF9900",
            "MONEV KERJASAMA": "#D9534F",
        },
    )
    fig_dist.update_traces(textposition="outside")
    fig_dist.update_layout(
        xaxis=dict(range=[0, max(dist_counts["JUMLAH"], default=1) * 1.15]),
        yaxis={"categoryorder": "total ascending"},
        margin=dict(t=10, b=10, l=10, r=10),
        height=220,
        xaxis_title="Jumlah Pekerjaan",
        yaxis_title="",
        showlegend=False,
    )
    st.plotly_chart(fig_dist, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)


# --- TATA LETAK KOLOM KIRI & KANAN ---
col_left, col_right = st.columns(2)

with col_left:
    # 1. Status Kegiatan
    with st.container(border=True):
        st.subheader("📊 Status Kegiatan")
        if "STATUS" in df_filtered.columns:
            status_counts = df_filtered["STATUS"].value_counts().reset_index()
            status_counts.columns = ["STATUS", "JUMLAH"]

            fig_status = px.pie(
                status_counts,
                names="STATUS",
                values="JUMLAH",
                hole=0.4,
                color="STATUS",
                color_discrete_map={
                    "SELESAI": "#003366",
                    "ON PROGRES": "#FF9900",
                    "PENDING": "#A6A6A6",
                },
            )
            fig_status.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                height=240,
                legend=dict(font=dict(size=10)),
            )
            st.plotly_chart(fig_status, use_container_width=True)
        else:
            st.info("Kolom STATUS tidak tersedia.")

    # 2. Trend Jumlah Kegiatan per Bulan
    with st.container(border=True):
        st.subheader("📈 Trend Jumlah Kegiatan per Bulan")
        if not df_filtered.empty and "BULAN" in df_filtered.columns:
            trend_bulan = (
                df_filtered.dropna(subset=["BULAN"])
                .groupby("BULAN")["PEKERJAAN"]
                .count()
                .reset_index()
            )
            bulan_urut = [
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            ]
            trend_bulan["BULAN"] = pd.Categorical(
                trend_bulan["BULAN"], categories=bulan_urut, ordered=True
            )
            trend_bulan = trend_bulan.sort_values("BULAN")

            fig_trend = px.line(
                trend_bulan,
                x="BULAN",
                y="PEKERJAAN",
                markers=True,
                color_discrete_sequence=["#003366"],
            )
            fig_trend.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                height=240,
                xaxis_title="",
                yaxis_title="",
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Data bulan tidak tersedia.")

    # 3. KOTAK INFORMASI TAMBAHAN
    with st.container(border=True):
        st.subheader("📌 Ringkasan Status Operasional")
        st.markdown(
            f"""
        - **Kategori Aktif:** `{pilihan_monev}`
        - **Total Beban Tugas Aktif:** `{total_kegiatan} Pekerjaan`
        - **Pekerjaan Selesai:** `{jumlah_selesai} Kegiatan`
        - **Dalam Pengerjaan:** `{jumlah_on_progres} Kegiatan`
        """
        )

with col_right:
    # 1. Kegiatan per Unit Pengusul/Lembaga
    with st.container(border=True):
        st.subheader("🏢 Kegiatan per Unit Pengusul/Lembaga")
        col_unit_name = "UNIT PENGUSUL/LEMBAGA"
        if col_unit_name in df_filtered.columns and not df_filtered.empty:
            unit_counts = (
                df_filtered[col_unit_name]
                .dropna()
                .astype(str)
                .str.strip()
                .value_counts()
                .reset_index()
            )
            unit_counts.columns = [col_unit_name, "JUMLAH"]

            if not unit_counts.empty:
                fig_unit = px.bar(
                    unit_counts,
                    x="JUMLAH",
                    y=col_unit_name,
                    orientation="h",
                    color_discrete_sequence=["#003366"],
                )
                fig_unit.update_layout(
                    yaxis={"categoryorder": "total ascending"},
                    margin=dict(t=10, b=10, l=10, r=10),
                    height=280,
                    xaxis_title="",
                    yaxis_title="",
                )
                st.plotly_chart(fig_unit, use_container_width=True)
            else:
                st.info("Data Unit Pengusul/Lembaga kosong.")
        else:
            st.info("Kolom UNIT PENGUSUL/LEMBAGA tidak ditemukan.")

    # 2. Beban PIC - Status ON PROGRES
    with st.container(border=True):
        st.subheader("👷 Beban PIC - Status ON PROGRES")
        if "STATUS" in df_filtered.columns and "PIC" in df_filtered.columns:
            df_op = df_filtered[df_filtered["STATUS"] == "ON PROGRES"]
            if not df_op.empty:
                pic_counts = df_op["PIC"].value_counts().head(5).reset_index()
                pic_counts.columns = ["PIC", "JUMLAH"]

                fig_pic = px.bar(
                    pic_counts,
                    x="PIC",
                    y="JUMLAH",
                    color_discrete_sequence=["#FF9900"],
                )
                fig_pic.update_layout(
                    margin=dict(t=10, b=10, l=10, r=10),
                    height=260,
                    xaxis_title="",
                    yaxis_title="",
                )
                st.plotly_chart(fig_pic, use_container_width=True)
            else:
                st.info("Data On Progress tidak tersedia.")
        else:
            st.info("Kolom PIC/STATUS tidak tersedia.")

# --- GRAFIK PROGRESS SELURUH PEKERJAAN ---
with st.container(border=True):
    st.subheader("📈 Grafik Persentase Progress Seluruh Pekerjaan")

    if not df_filtered.empty and "% PROGRES" in df_filtered.columns:
        df_chart = df_filtered.copy()
        df_chart["PROGRES_NUM"] = df_chart["% PROGRES"].apply(clean_progress)
        df_chart["PEKERJAAN_PENDEK"] = df_chart["PEKERJAAN"].apply(
            lambda x: (str(x)[:45] + "...") if len(str(x)) > 45 else str(x)
        )

        total_data = len(df_chart)

        if total_data > 1:
            max_tampil = st.slider(
                "Tampilkan jumlah pekerjaan teratas pada grafik:",
                min_value=1,
                max_value=total_data,
                value=min(10, total_data),
            )
            df_chart_subset = df_chart.head(max_tampil)
        else:
            df_chart_subset = df_chart

        fig_height = max(4.0, len(df_chart_subset) * 0.35)
        fig, ax = plt.subplots(figsize=(10, fig_height))

        warna_bar = []
        for idx, row in df_chart_subset.iterrows():
            prog = row["PROGRES_NUM"]
            stat = (
                str(row["STATUS"]).strip().upper()
                if "STATUS" in df_chart_subset.columns
                else ""
            )
            if prog >= 100 or stat == "SELESAI":
                warna_bar.append("#28a745")
            else:
                warna_bar.append("#003366")

        bars = ax.barh(
            df_chart_subset["PEKERJAAN_PENDEK"],
            df_chart_subset["PROGRES_NUM"],
            color=warna_bar,
        )

        ax.set_xlabel("Persentase Progress (%)", fontweight="bold", fontsize=9)
        ax.set_ylabel("Nama Pekerjaan", fontweight="bold", fontsize=9)
        ax.tick_params(axis="both", labelsize=9)
        ax.set_xlim(0, 125)
        ax.invert_yaxis()
        ax.grid(axis="x", linestyle="--", alpha=0.5)

        for idx, bar in enumerate(bars):
            width = bar.get_width()
            row_data = df_chart_subset.iloc[idx]
            stat = (
                str(row_data["STATUS"]).strip().upper()
                if "STATUS" in df_chart_subset.columns
                else ""
            )

            if width >= 100 or stat == "SELESAI":
                label_text = f"{int(width)}% - SELESAI"
                label_color = "#28a745"
            else:
                label_text = (
                    f"{int(width)}% - {stat}" if stat else f"{int(width)}%"
                )
                label_color = "#003366"

            ax.text(
                width + 2,
                bar.get_y() + bar.get_height() / 2,
                label_text,
                va="center",
                ha="left",
                fontsize=8,
                fontweight="bold",
                color=label_color,
            )

        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.info("Data persentase progress tidak tersedia.")

# --- FITUR INTERAKTIF: EDIT, HAPUS & TAMBAH DATA (LIVE EDITOR) ---
st.markdown("<br>", unsafe_allow_html=True)
with st.container(border=True):
    st.subheader("📝 Edit, Hapus & Tambah Data Kegiatan (Live Editor)")
    st.info(
        "💡 **Cara Pakai:** Edit sel data langsung, centang kolom **Hapus** untuk menghapus baris,"
        " atau tambahkan baris baru langsung di bagian bawah tabel."
        " Klik tombol simpan untuk mengunci perubahan secara permanen ke Excel."
    )

    kolom_edit = [
        "PEKERJAAN",
        "PIC",
        "UNIT PENGUSUL/LEMBAGA",
        "START",
        "END",
        "% PROGRES",
        "STATUS",
        "UPDATE TERKINI",
        "GOALS",
        "KATEGORI_MONEV",
    ]
    kolom_tersedia = [col for col in kolom_edit if col in df_filtered.columns]

    df_editor_view = df_filtered[kolom_tersedia].copy()

    if "% PROGRES" in df_editor_view.columns:
        df_editor_view["% PROGRES"] = (
            df_editor_view["% PROGRES"]
            .apply(clean_progress)
            .astype(int)
            .astype(str)
            + "%"
        )

    # Sisipkan kolom checkbox Hapus
    df_editor_view.insert(0, "Hapus", False)

    edited_df = st.data_editor(
        df_editor_view,
        num_rows="dynamic",  # Diubah menjadi "dynamic" agar bisa menambah baris baru
        use_container_width=True,
        key="data_editor_kegiatan_v8",
    )

    if st.button("💾 Simpan Perubahan & Hapus Data Terpilih", type="primary"):
        # 1. PROSES HAPUS BERDASARKAN NAMA PEKERJAAN
        pekerjaan_to_delete = []
        for i in range(len(edited_df)):
            # Pastikan baris memiliki kolom Hapus dan bernilai True
            if "Hapus" in edited_df.columns and bool(edited_df.iloc[i]["Hapus"]) == True:
                pekr = str(edited_df.iloc[i]["PEKERJAAN"]).strip()
                pekerjaan_to_delete.append(pekr)

        if len(pekerjaan_to_delete) > 0:
            st.session_state.df_global = st.session_state.df_global[
                ~st.session_state.df_global["PEKERJAAN"]
                .astype(str)
                .str.strip()
                .isin(pekerjaan_to_delete)
            ].reset_index(drop=True)

        existing_jobs = set(
            st.session_state.df_global["PEKERJAAN"].astype(str).str.strip()
        )

        # 2. PROSES UPDATE & TAMBAH BARIS BARU
        for i in range(len(edited_df)):
            # Lewati baris yang ditandai hapus
            if "Hapus" in edited_df.columns and bool(edited_df.iloc[i]["Hapus"]) == True:
                continue

            nama_pekerjaan_ini = str(edited_df.iloc[i]["PEKERJAAN"]).strip()
            if not nama_pekerjaan_ini or nama_pekerjaan_ini == "nan" or nama_pekerjaan_ini == "None":
                continue

            # Jika pekerjaan sudah ada -> UPDATE data yang diedit
            if nama_pekerjaan_ini in existing_jobs:
                match_idx = st.session_state.df_global[
                    st.session_state.df_global["PEKERJAAN"]
                    .astype(str)
                    .str.strip()
                    == nama_pekerjaan_ini
                ].index

                if not match_idx.empty:
                    idx = match_idx[0]
                    for col in kolom_tersedia:
                        val_to_save = edited_df.iloc[i][col]
                        if col == "% PROGRES":
                            val_to_save = clean_progress(val_to_save) / 100.0
                        elif col == "STATUS":
                            val_to_save = str(val_to_save).strip().upper()
                        st.session_state.df_global.loc[idx, col] = val_to_save
            else:
                # Jika pekerjaan belum ada -> TAMBAH SEBAGAI DATA BARU
                new_row = {}
                for col in kolom_tersedia:
                    val_to_save = edited_df.iloc[i][col]
                    if col == "% PROGRES":
                        val_to_save = clean_progress(val_to_save) / 100.0
                    elif col == "STATUS":
                        val_to_save = str(val_to_save).strip().upper()
                    elif pd.isna(val_to_save) or val_to_save == "None":
                        val_to_save = "-"
                    new_row[col] = val_to_save

                # Set kategori default jika kosong
                if "KATEGORI_MONEV" not in new_row or not new_row["KATEGORI_MONEV"] or new_row["KATEGORI_MONEV"] == "-":
                    new_row["KATEGORI_MONEV"] = (
                        pilihan_monev if pilihan_monev != "Semua Kategori" else "MONEV KRT"
                    )

                df_new_row = pd.DataFrame([new_row])
                st.session_state.df_global = pd.concat(
                    [st.session_state.df_global, df_new_row], ignore_index=True
                )
                existing_jobs.add(nama_pekerjaan_ini)

        # Bersihkan duplikat murni berdasarkan nama pekerjaan
        st.session_state.df_global = (
            st.session_state.df_global.drop_duplicates(
                subset=["PEKERJAAN"], keep="first"
            ).reset_index(drop=True)
        )

        # Pastikan status bersih
        if "STATUS" in st.session_state.df_global.columns:
            st.session_state.df_global["STATUS"] = (
                st.session_state.df_global["STATUS"]
                .astype(str)
                .str.strip()
                .str.upper()
            )

        # 3. KUNCI PERUBAHAN KE FILE EXCEL
        try:
            with pd.ExcelWriter(file_excel, engine="openpyxl") as writer:
                df_to_save_global = st.session_state.df_global.rename(
                    columns={"UNIT PENGUSUL/LEMBAGA": "UNIT"}
                )

                df_krt_out = df_to_save_global[
                    df_to_save_global["KATEGORI_MONEV"] == "MONEV KRT"
                ].drop(columns=["KATEGORI_MONEV"], errors="ignore")
                df_strat_out = df_to_save_global[
                    df_to_save_global["KATEGORI_MONEV"] == "MONEV STRATEGIS"
                ].drop(columns=["KATEGORI_MONEV"], errors="ignore")
                df_kerj_out = df_to_save_global[
                    df_to_save_global["KATEGORI_MONEV"] == "MONEV KERJASAMA"
                ].drop(columns=["KATEGORI_MONEV"], errors="ignore")

                df_krt_out.to_excel(
                    writer, sheet_name="Monev KRT", index=False
                )
                df_strat_out.to_excel(
                    writer, sheet_name="Monev Strategis", index=False
                )
                df_kerj_out.to_excel(
                    writer, sheet_name="Monev Kerjasama", index=False
                )

            load_data.clear()
            st.success(
                "🔒 Perubahan (tambah, edit, & hapus) berhasil dikunci permanen ke file Excel!"
            )
            st.rerun()
        except Exception as e:
            st.error(
                f"⚠️ Gagal menyimpan ke file Excel (Pastikan file Excel tidak sedang terbuka): {e}"
            )