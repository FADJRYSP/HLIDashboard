# ==========================================================
# 📊 DASHBOARD MONITORING HHI PT KAI
# Version : 2.0
# Developer : Fadjry Sahrudin Putra
# ==========================================================

# ==========================
# IMPORT LIBRARY
# ==========================
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import re
import html as html_lib
import hashlib
from urllib.parse import quote
from urllib.request import Request, urlopen
from io import BytesIO
import textwrap
from typing import Protocol


class _UploadedDocument(Protocol):
    def getbuffer(self) -> memoryview:
        ...

# reportlab is an optional dependency; fall back to text download if missing
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    from reportlab.lib.utils import ImageReader
    HAS_REPORTLAB = True
except Exception:
    HAS_REPORTLAB = False

DEFAULT_SHEET_URL = "https://docs.google.com/spreadsheets/d/1yvdxDE1lnHAjEJQZlqYZqYlBa_ZjCz1k/edit?usp=sharing&ouid=104405218548143620607&rtpof=true&sd=true"
KAI_LOGO_URL = "https://images.seeklogo.com/logo-png/40/2/pt-kai-kereta-api-indonesia-2020-logo-png_seeklogo-407558.png"


def _get_sheet_url() -> str:
    """Resolve the configured spreadsheet URL used for reading and writing."""
    secret_url = st.secrets.get("GOOGLE_SHEETS_URL") if "GOOGLE_SHEETS_URL" in st.secrets else None
    connections = st.secrets.get("connections", {})
    gsheets = connections.get("gsheets", {}) if hasattr(connections, "get") else {}
    configured_url = gsheets.get("spreadsheet") if hasattr(gsheets, "get") else None
    return (
        os.environ.get("GOOGLE_SHEETS_URL")
        or secret_url
        or configured_url
        or DEFAULT_SHEET_URL
    )


KAI_NAVY = "#2D2A70"
KAI_ORANGE = "#E46A00"
KAI_SLATE = "#5E6A7D"
KAI_SOFT_BG = "#F5F7FB"
KAI_CARD = "#FFFFFF"
PLOT_TEMPLATE = "plotly_white"

# ==========================
# KONFIGURASI HALAMAN
# ==========================
st.set_page_config(
    page_title="Dashboard Monitoring HHI",
    page_icon=KAI_LOGO_URL,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================
# CSS
# ==========================
st.markdown("""
<style>
:root{
    --kai-navy:#2D2A70;
    --kai-orange:#E46A00;
    --kai-slate:#5E6A7D;
    --kai-soft:#F5F7FB;
    --kai-card:#FFFFFF;
}

.stApp{
    background:
        radial-gradient(circle at 92% 5%, rgba(228,106,0,0.10) 0%, rgba(228,106,0,0) 28%),
        radial-gradient(circle at 0% 42%, rgba(45,42,112,0.08) 0%, rgba(45,42,112,0) 32%),
        linear-gradient(135deg, #F8FAFD 0%, #EEF2F8 100%);
}

.block-container{
    padding-top:1rem;
    padding-bottom:1rem;
}

@keyframes kaiRiseIn{
    from{opacity:0; transform:translateY(10px);}
    to{opacity:1; transform:translateY(0);}
}

.kai-hero{
    animation:kaiRiseIn .55s ease-out both;
}

.kai-card-metric{
    animation:kaiRiseIn .5s ease-out both;
}

.kai-card-metric:nth-child(2){animation-delay:.06s;}
.kai-card-metric:nth-child(3){animation-delay:.12s;}
.kai-card-metric:nth-child(4){animation-delay:.18s;}
.kai-card-metric:nth-child(5){animation-delay:.24s;}

@media (prefers-reduced-motion: reduce){
    .kai-hero,
    .kai-card-metric,
    [data-testid="stPlotlyChart"]{
        animation:none;
        transition:none;
    }
}

[data-testid="stPlotlyChart"]{
    background:linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
    border:1px solid #D5DCE8;
    border-bottom:4px solid #C3CCDC;
    border-radius:12px;
    padding:8px 8px 2px;
    box-sizing:border-box;
    box-shadow:0 2px 0 rgba(255,255,255,0.95) inset, 0 7px 0 rgba(45,42,112,0.08), 0 16px 28px rgba(45,42,112,0.18), 0 5px 9px rgba(15,23,42,0.12);
    transition:transform .2s ease, box-shadow .2s ease;
    animation:kaiRiseIn .6s ease-out .16s both;
}

[data-testid="stPlotlyChart"]:hover{
    transform:translateY(-3px);
    box-shadow:0 2px 0 rgba(255,255,255,0.95) inset, 0 9px 0 rgba(45,42,112,0.10), 0 20px 34px rgba(45,42,112,0.22), 0 7px 12px rgba(15,23,42,0.14);
}

div[data-testid="metric-container"]{
    background:var(--kai-card);
    border-radius:12px;
    padding:15px;
    border:1px solid #E5E7EB;
    border-left:6px solid var(--kai-orange);
    box-shadow:0px 6px 18px rgba(17,24,39,.08);
}

[data-testid="stSidebar"]{
    background:linear-gradient(
        180deg,
        #FFFFFF 0,
        #FFFFFF 155px,
        #24205B 155px,
        #2D2A70 100%
    );
}

.sidebar-logo-panel{
    background:transparent;
    height:155px;
    box-sizing:border-box;
    display:block;
    padding:28px 12px 0;
    margin:-1rem -1rem 1.25rem;
    text-align:center;
}

.sidebar-logo-panel img{
    display:block;
    width:110px;
    height:auto;
    margin:0 auto;
    transform:translateY(-22px);
}

[data-testid="stSidebar"] *{
    color:#FFFFFF;
}

[data-testid="stSidebarCollapseButton"]{
    z-index:10;
}

[data-testid="stSidebarCollapseButton"] button{
    color:#FFFFFF !important;
    background:#2D2A70 !important;
    border:1px solid #2D2A70 !important;
}

[data-testid="stSidebarCollapseButton"] button svg{
    stroke:#FFFFFF !important;
}

/* Override warna teks untuk elemen input di sidebar agar terbaca
   (sidebar background gelap + input field putih sebelumnya membuat teks putih tidak terbaca) */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] .stTextInput>div>div>input,
[data-testid="stSidebar"] .stTextArea>div>div>textarea,
[data-testid="stSidebar"] .stSelectbox>div>div>div,
[data-testid="stSidebar"] .stMultiSelect>div>div>div,
[data-testid="stSidebar"] .stNumberInput>div>div>input {
    color: #0F172A !important; /* teks gelap untuk keterbacaan */
}

[data-testid="stSidebar"] input::placeholder,
[data-testid="stSidebar"] textarea::placeholder,
[data-testid="stSidebar"] .stTextInput>div>div>input::placeholder,
[data-testid="stSidebar"] .stTextArea>div>div>textarea::placeholder {
    color: #94A3B8 !important; /* warna placeholder abu */
}

.resume-shell {
    background: #F4F6F8;
    border: 1px solid #DDE3EA;
    border-radius: 18px;
    padding: 18px;
    margin-top: 12px;
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.05);
}

.resume-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 12px;
    padding: 4px 2px 10px;
    border-bottom: 1px solid #E0E7F0;
}

.resume-back {
    color: #1d4ed8;
    font-weight: 600;
    font-size: 0.95rem;
    text-decoration: none;
}

.resume-title {
    text-align: center;
    flex: 1;
    font-size: 2.1rem;
    font-weight: 800;
    color: #111827;
    letter-spacing: 0.02em;
}

.resume-button {
    padding: 8px 16px;
    border-radius: 10px;
    background: #f3f4f6;
    border: 1px solid #d1d5db;
    color: #111827;
    font-weight: 600;
    cursor: pointer;
}

.resume-card {
    background: #FFFFFF;
    border-radius: 16px;
    border: 1px solid #E2E8F0;
    padding: 20px 18px;
}

.resume-topbar {
    display: grid;
    grid-template-columns: 110px 1.7fr 1fr;
    gap: 18px;
    align-items: center;
    margin-bottom: 8px;
}

.resume-no-box {
    background: linear-gradient(135deg, #2E63C4, #214F9C);
    color: white;
    border-radius: 18px;
    min-height: 120px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    font-weight: 800;
    box-shadow: 0 6px 16px rgba(37, 99, 235, 0.25);
}

.resume-no-label {
    font-size: 1.0rem;
    opacity: 0.9;
    line-height: 1;
}

.resume-no-value {
    font-size: 2.6rem;
    line-height: 1.1;
    margin-top: 4px;
}

.resume-main-title {
    font-size: clamp(1.3rem, 2vw, 2.2rem);
    font-weight: 800;
    color: #0F172A;
    margin: 0;
    line-height: 1.2;
}

.resume-tag {
    display: inline-block;
    background: #F3E8FF;
    border: 1px solid #E9D5FF;
    color: #6D28D9;
    border-radius: 8px;
    padding: 5px 10px;
    font-size: 0.72rem;
    font-weight: 700;
    margin-top: 10px;
    letter-spacing: 0.02em;
}

.resume-meta {
    display: flex;
    flex-direction: column;
    gap: 10px;
    font-size: 0.95rem;
    color: #334155;
    align-items: flex-start;
}

.resume-meta-item {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    justify-content: flex-start;
}

.resume-meta-label {
    font-weight: 700;
    color: #0F172A;
    min-width: 100px;
}

.resume-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 16px;
    margin-top: 18px;
}

.resume-panel {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 14px 16px;
    min-height: 108px;
}

.resume-panel .panel-title {
    color: #0F172A;
    font-size: 0.75rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 10px;
    display: block;
}

.resume-panel .panel-value {
    font-size: 1.1rem;
    font-weight: 700;
    color: #0F172A;
}

.resume-panel .panel-sub {
    font-size: 0.9rem;
    color: #475569;
    margin-top: 5px;
}

.resume-section {
    margin-top: 18px;
    display: grid;
    grid-template-columns: 1.15fr 0.85fr;
    gap: 18px;
}

.resume-left,
.resume-right {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 16px 18px;
}

.resume-section-title {
    color: #0F172A;
    font-size: 1.02rem;
    font-weight: 800;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.resume-bullets {
    margin: 0;
    padding-left: 1.1rem;
    color: #334155;
}

.resume-bullets li {
    margin-bottom: 8px;
    line-height: 1.45;
}

.resume-info-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0 8px;
    color: #334155;
}

.resume-info-table td {
    padding: 4px 0;
    vertical-align: top;
}

.resume-info-table td:first-child {
    font-weight: 700;
    color: #0F172A;
    width: 42%;
    padding-right: 10px;
}

.resume-eval {
    margin-top: 18px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 18px;
}

.resume-alert {
    border-radius: 12px;
    padding: 14px 16px;
    border: 1px solid #FECACA;
    background: #FEF2F2;
    color: #991B1B;
    font-weight: 600;
}

.resume-warning {
    border-radius: 12px;
    padding: 14px 16px;
    border: 1px solid #FDE68A;
    background: #FFFBEB;
    color: #92400E;
    font-weight: 600;
}

.resume-success {
    border-radius: 12px;
    padding: 14px 16px;
    border: 1px solid #BBF7D0;
    background: #F0FDF4;
    color: #166534;
    font-weight: 600;
}

@media (max-width: 960px) {
    .resume-topbar {
        grid-template-columns: 1fr;
    }
    .resume-grid,
    .resume-section,
    .resume-eval {
        grid-template-columns: 1fr;
    }
}

.kai-hero{
    position:relative;
    overflow:hidden;
    background:linear-gradient(112deg, #11183F 0%, #20265F 56%, #344582 100%);
    color:#FFFFFF;
    border:1px solid rgba(255,255,255,0.16);
    border-bottom:4px solid #F28A2E;
    border-radius:16px;
    padding:20px 24px;
    min-height:128px;
    box-sizing:border-box;
    margin-bottom:14px;
    box-shadow:0 4px 0 rgba(255,255,255,0.10) inset, 0 12px 0 rgba(45,42,112,0.08), 0 18px 30px rgba(23,26,74,0.22);
}

.kai-hero::after{
    content:"";
    position:absolute;
    width:320px;
    height:320px;
    right:-120px;
    top:-190px;
    border:1px solid rgba(255,255,255,0.12);
    border-radius:50%;
    box-shadow:0 0 0 22px rgba(255,255,255,0.035), 0 0 0 44px rgba(255,255,255,0.025);
}

.kai-hero-brand{
    display:flex;
    align-items:center;
    gap:18px;
    min-height:76px;
    position:relative;
    z-index:1;
}

.kai-hero-brand > div:last-child{
    display:flex;
    flex-direction:column;
    justify-content:center;
    gap:3px;
}

.kai-logo{
    width:76px;
    height:76px;
    object-fit:contain;
    flex:0 0 76px;
    border-radius:14px;
    background:#FFFFFF;
    padding:7px;
    box-sizing:border-box;
    border:1px solid rgba(255,255,255,0.72);
    box-shadow:0 5px 0 rgba(255,255,255,0.35) inset, 0 8px 14px rgba(10,12,45,0.28);
}

.kai-hero-kicker{
    color:#FFD19E;
    font-size:.68rem;
    font-weight:800;
    letter-spacing:.14em;
    text-transform:uppercase;
}

.kai-hero h2{
    margin:1px 0 2px 0;
    font-size:1.6rem;
    font-weight:800;
    letter-spacing:.01em;
    line-height:1.1;
}

.kai-hero p{
    margin:1px 0 0 0;
    opacity:0.95;
    color:#E8EAF8;
    font-size:0.86rem;
    line-height:1.25;
}

.kai-pill{
    display:inline-block;
    align-self:flex-start;
    margin-top:7px;
    background:rgba(255,255,255,0.12);
    border:1px solid rgba(255,255,255,0.38);
    border-radius:999px;
    padding:4px 11px;
    color:#FFFFFF;
    font-size:0.72rem;
    font-weight:700;
    letter-spacing:.02em;
}

@media (max-width: 640px) {
    .kai-hero{
        padding:16px;
        min-height:112px;
    }
    .kai-hero-brand{
        gap:12px;
    }
    .kai-logo{
        width:62px;
        height:62px;
        flex-basis:62px;
    }
    .kai-hero h2{
        font-size:1.18rem;
    }
    .kai-hero p{
        font-size:.78rem;
    }
}
.kai-card-grid{
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(190px,1fr));
    gap:1rem;
    margin-bottom:1rem;
}

.kai-card-metric{
    background:linear-gradient(135deg, #FFFFFF 0%, var(--card-tint, #EEF2FF) 100%);
    border-radius:18px;
    padding:24px 22px;
    border:1px solid #E5E7EB;
    border-left:6px solid var(--card-accent, #2D2A70);
    min-height:142px;
    box-sizing:border-box;
    position:relative;
    overflow:hidden;
    box-shadow:0 3px 0 rgba(255,255,255,0.85) inset, 0 10px 18px rgba(45,42,112,0.12), 0 3px 5px rgba(15,23,42,0.08);
    transition:transform .2s ease, box-shadow .2s ease;
}

.kai-card-metric::after{
    content:"";
    position:absolute;
    top:0;
    left:12px;
    right:12px;
    height:1px;
    background:rgba(255,255,255,0.95);
}

.kai-card-metric:hover{
    transform:translateY(-3px);
    box-shadow:0 3px 0 rgba(255,255,255,0.9) inset, 0 16px 24px rgba(45,42,112,0.16), 0 5px 8px rgba(15,23,42,0.10);
}

.kai-card-metric:nth-child(1){
    --card-accent:#2D2A70;
    --card-tint:#DDE3FF;
}

.kai-card-metric:nth-child(2){
    --card-accent:#16803C;
    --card-tint:#D9F5E4;
}

.kai-card-metric:nth-child(3){
    --card-accent:#E46A00;
    --card-tint:#FFE8CC;
}

.kai-card-metric:nth-child(4){
    --card-accent:#1769AA;
    --card-tint:#D7EEFF;
}

.kai-card-metric:nth-child(5){
    --card-accent:#B4235A;
    --card-tint:#FFE0EA;
}

.kai-card-metric .metric-label{
    font-size:0.92rem;
    color:#5E6A7D;
    margin-bottom:0.5rem;
    font-weight:600;
}

.kai-card-metric .metric-value{
    font-size:2.5rem;
    font-weight:800;
    color:var(--card-accent, #2D2A70);
    line-height:1;
}

.kai-card-metric .metric-note{
    margin-top:0.75rem;
    color:#8B93A9;
    font-size:0.85rem;
}

.resume-action-panel{
    margin-top:1.25rem;
    padding:1.1rem 1.25rem;
    border:1px solid #D9E0EC;
    border-left:5px solid #E46A00;
    border-radius:14px;
    background:linear-gradient(110deg,#FFFFFF 0%,#F8FAFC 100%);
    box-shadow:0 8px 20px rgba(45,42,112,.07);
}
.resume-action-eyebrow{
    color:#E46A00;
    font-size:.7rem;
    font-weight:800;
    letter-spacing:.1em;
    text-transform:uppercase;
}
.resume-action-title{
    margin-top:3px;
    color:#172033;
    font-size:1.12rem;
    font-weight:800;
}
.resume-action-copy{
    margin-top:3px;
    color:#64748B;
    font-size:.86rem;
}
.resume-preview{
    margin-top:.85rem;
    padding:.75rem .9rem;
    border-radius:10px;
    background:#F1F5F9;
    color:#334155;
    font-size:.86rem;
}
.resume-preview strong{color:#0F172A;}
</style>
""",unsafe_allow_html=True)

# ==========================================================
# 🏠 NAVIGASI SECTION
# ==========================================================

LEGAL_SHEETS = {
    "PSO": "PSO 2",
    "TAC": "TAC",
    "Konsesi Perkeretaapian": "Konsesi Perkeretaapian",
    "Perlintasan Sebidang 2": "Perlintasan Sebidang 2",
    "BUPP 2": "BUPP 2",
    "BUPS": "BUPS",
    "IMO": "IMO",
    "KJCB": "KJCB",
    "LRT": "LRT",
}
LAW_TITLE_PREFIXES = (
    "undang-undang",
    "undang undang",
    "uu no.",
    "uu nomor",
    "peraturan",
    "perpres",
    "perpres nomor",
    "pp no.",
    "pp nomor",
    "pm no.",
    "pm nomor",
    "permen",
    "kepmen",
    "keputusan",
)
UU_23_2007_DOCUMENT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "static",
    "uu_23_2007_perkeretaapian.pdf",
)
LEGAL_DOCUMENT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "static",
    "legal_documents",
)
UU_23_2007_TITLE_PATTERN = re.compile(
    r"^(?:undang[\s-]+undang|uu)\b.*\b(?:nomor|no\.?)\s*23\b.*\b2007\b",
    flags=re.IGNORECASE,
)


def _law_document_filename(section_name: str, law_title: str) -> str:
    title_hash = hashlib.sha256(
        f"{section_name}\0{law_title}".casefold().encode("utf-8")
    ).hexdigest()[:12]
    return f"law_{title_hash}"


def _legacy_law_document_filename(section_name: str, law_title: str) -> str:
    return re.sub(
        r"[^a-z0-9]+",
        "_",
        f"{section_name}_{law_title}".casefold(),
    ).strip("_")


def _get_law_document_path(section_name: str, law_title: str) -> str | None:
    filenames = [_law_document_filename(section_name, law_title)]
    legacy_filename = _legacy_law_document_filename(section_name, law_title)
    if legacy_filename != filenames[0]:
        filenames.append(legacy_filename)
    for filename in filenames:
        uploaded_document = os.path.join(LEGAL_DOCUMENT_DIR, f"{filename}.pdf")
        if os.path.isfile(uploaded_document):
            return uploaded_document
    if UU_23_2007_TITLE_PATTERN.search(law_title):
        return UU_23_2007_DOCUMENT
    return None


def _save_law_document(
    section_name: str,
    law_title: str,
    document: _UploadedDocument,
) -> str:
    safe_title = _law_document_filename(section_name, law_title)
    if not safe_title:
        raise ValueError("Nama peraturan tidak dapat digunakan sebagai nama file.")

    document_path = os.path.join(LEGAL_DOCUMENT_DIR, f"{safe_title}.pdf")
    if os.path.exists(document_path):
        raise FileExistsError("Dokumen untuk peraturan ini sudah tersedia.")

    document_bytes = document.getbuffer()
    if not document_bytes:
        raise ValueError("File PDF kosong.")

    os.makedirs(LEGAL_DOCUMENT_DIR, exist_ok=True)
    try:
        with open(document_path, "wb") as document_file:
            document_file.write(document_bytes)
    except OSError as exc:
        raise OSError(f"Dokumen tidak dapat disimpan: {exc}") from exc
    return document_path


def _append_legal_regulation(
    section_name: str,
    law_title: str,
    article_entries: list[tuple[str, str]],
) -> None:
    credentials = st.secrets.get("gcp_service_account") if "gcp_service_account" in st.secrets else None
    if not credentials:
        raise ValueError(
            "Kredensial tulis belum dikonfigurasi. Tambahkan [gcp_service_account] "
            "di Streamlit secrets dan beri akun tersebut akses Editor ke spreadsheet."
        )

    import gspread

    sheet_url = _get_sheet_url()
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_url or "")
    if not match:
        raise ValueError("URL Google Sheets tidak valid.")

    client = gspread.service_account_from_dict(dict(credentials))
    spreadsheet = client.open_by_key(match.group(1))
    worksheet = spreadsheet.worksheet(LEGAL_SHEETS[section_name])
    existing_values = worksheet.get_all_values()
    existing_titles = {
        str(row[0]).strip().casefold()
        for row in existing_values
        if row and str(row[0]).strip()
    }
    if law_title.casefold() in existing_titles:
        raise ValueError("Nama hukum/peraturan tersebut sudah ada di worksheet.")

    if not article_entries:
        raise ValueError("Tambahkan minimal satu Pasal dan ringkasan/isi.")

    column_count = max(
        len(article_entries) + 1,
        max((len(row) for row in existing_values), default=1),
    )
    article_header_row = [""] * column_count
    article_content_row = [""] * column_count
    article_content_row[0] = law_title
    for index, (article_title, article_summary) in enumerate(article_entries, start=1):
        article_header_row[index] = article_title
        article_content_row[index] = article_summary
    end_column = ""
    column_number = column_count
    while column_number:
        column_number, remainder = divmod(column_number - 1, 26)
        end_column = chr(65 + remainder) + end_column
    start_row = len(existing_values) + 1
    worksheet.update(
        range_name=f"A{start_row}:{end_column}{start_row + 1}",
        values=[article_header_row, article_content_row],
        value_input_option="USER_ENTERED",
    )


@st.dialog("Tambah Dasar Hukum / Peraturan", width="large")
def _show_add_legal_data_dialog() -> None:
    section_name = st.selectbox("Kelompok peraturan", list(LEGAL_SHEETS))

    with st.form("add_legal_data_form"):
        st.caption("Isi data peraturan dan unggah dokumen PDF-nya.")
        law_title = st.text_input(
            "Nama hukum/peraturan",
            placeholder="Contoh: Peraturan Menteri Perhubungan Nomor ...",
        )
        article_count = st.number_input(
            "Jumlah Pasal",
            min_value=1,
            max_value=30,
            value=1,
            step=1,
            help="Setiap Pasal akan dibuat sebagai kolom tersendiri di baris header spreadsheet.",
        )
        article_entries: list[tuple[str, str]] = []
        st.markdown("**Pasal dan Ringkasan/Isi**")
        st.caption(
            "Pasal menjadi header kolom, sedangkan ringkasan/isi menjadi isi pada kolom tersebut."
        )
        for index in range(int(article_count)):
            pasal_column, summary_column = st.columns([1, 3])
            with pasal_column:
                article_title = st.text_input(
                    "Pasal",
                    placeholder="Pasal 1",
                    key=f"new_law_article_title_{section_name}_{index}",
                )
            with summary_column:
                article_summary = st.text_area(
                    "Ringkasan/Isi Pasal",
                    height=100,
                    key=f"new_law_article_summary_{section_name}_{index}",
                )
            article_title = article_title.strip()
            if article_title and re.fullmatch(r"\d+[a-z]?", article_title, flags=re.IGNORECASE):
                article_title = f"Pasal {article_title}"
            article_entries.append((article_title, article_summary.strip()))
        document = st.file_uploader(
            "Dokumen PDF (opsional)",
            type=["pdf"],
            accept_multiple_files=False,
        )
        submitted = st.form_submit_button(
            "Simpan Dasar Hukum",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    law_title = law_title.strip()
    if not law_title:
        st.error("Nama hukum/peraturan wajib diisi.")
        return
    if not law_title.casefold().startswith(LAW_TITLE_PREFIXES):
        st.error(
            "Nama hukum/peraturan harus diawali salah satu format: "
            + ", ".join(LAW_TITLE_PREFIXES)
            + "."
        )
        return
    invalid_entries = [
        index + 1
        for index, (article_title, article_summary) in enumerate(article_entries)
        if not article_title or not article_summary
    ]
    if invalid_entries:
        st.error(
            "Lengkapi Pasal dan Ringkasan/Isi pada baris: "
            + ", ".join(str(index) for index in invalid_entries)
        )
        return
    try:
        document_path = None
        if document is not None:
            document_path = _save_law_document(section_name, law_title, document)
        _append_legal_regulation(
            section_name,
            law_title,
            article_entries,
        )
    except Exception as exc:
        if document_path and os.path.isfile(document_path):
            os.remove(document_path)
        st.error(f"Data belum tersimpan: {exc}")
        return

    cached_loader = globals().get("load_law_sheet")
    if cached_loader is not None:
        cached_loader.clear()
    st.success(
        "Dasar hukum berhasil disimpan."
        + (" Dokumen PDF juga berhasil disimpan." if document is not None else "")
    )
    st.rerun()


@st.dialog("Dokumen Dasar Hukum", width="large")
def _show_law_document_dialog() -> None:
    document_path = st.session_state.get("law_document_path")
    document_title = st.session_state.get("law_document_title", "Dokumen")
    if not document_path or not os.path.isfile(document_path):
        st.error("File dokumen tidak ditemukan.")
        return

    with open(document_path, "rb") as document_file:
        document_bytes = document_file.read()

    st.subheader(document_title)
    st.caption(os.path.basename(document_path))
    st.pdf(document_path, height=780)
    st.download_button(
        "Unduh PDF",
        data=document_bytes,
        file_name=os.path.basename(document_path),
        mime="application/pdf",
        use_container_width=True,
    )


@st.cache_data(ttl=30)
def load_law_sheet(sheet_name: str) -> tuple[pd.DataFrame, str | None]:
    sheet_url = _get_sheet_url()
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_url or "")
    if not match:
        return pd.DataFrame(), "URL Google Sheets tidak valid atau belum dikonfigurasi."

    credentials = st.secrets.get("gcp_service_account") if "gcp_service_account" in st.secrets else None
    if credentials:
        try:
            import gspread

            client = gspread.service_account_from_dict(dict(credentials))
            worksheet = client.open_by_key(match.group(1)).worksheet(sheet_name)
            values = worksheet.get_all_values()
            return pd.DataFrame(values), None
        except Exception:
            pass

    sheet_csv_url = (
        f"https://docs.google.com/spreadsheets/d/{match.group(1)}/gviz/tq"
        f"?tqx=out:csv&sheet={quote(sheet_name)}"
    )
    try:
        sheet = pd.read_csv(sheet_csv_url, header=None, dtype=str).fillna("")
        return sheet, None
    except Exception as exc:
        return pd.DataFrame(), f"Sheet {sheet_name} tidak dapat dibaca: {exc}"


def _normalize_law_search_text(value: str) -> list[str]:
    normalized = str(value).casefold()
    aliases = (
        ("undang-undang", "undang undang uu"),
        ("undang undang", "undang undang uu"),
        ("peraturan pemerintah", "peraturan pemerintah pp"),
        ("peraturan presiden", "peraturan presiden perpres"),
        ("peraturan menteri perhubungan", "peraturan menteri perhubungan permenhub pm"),
        ("keputusan menteri perhubungan", "keputusan menteri perhubungan kepmenhub km"),
    )
    for phrase, expanded in aliases:
        normalized = normalized.replace(phrase, expanded)
    normalized = re.sub(r"\bno\.?\b", "nomor", normalized)
    return re.findall(r"[a-z0-9]+", normalized)


def _is_article_header(value: str) -> bool:
    normalized = str(value).strip()
    return bool(
        "pasal" in normalized.casefold()
        or re.fullmatch(
            r"\d+[a-z]?(?:\s+ayat\s*\(\d+\))?(?:\s+.*)?",
            normalized,
            flags=re.IGNORECASE,
        )
    )


def _search_legal_titles(query: str) -> list[tuple[str, str]]:
    query_tokens = _normalize_law_search_text(query)
    if not query_tokens:
        return []

    matches = []
    for section_name, sheet_name in LEGAL_SHEETS.items():
        law_sheet, error = load_law_sheet(sheet_name)
        if error or law_sheet.empty or law_sheet.shape[1] == 0:
            continue

        for raw_title in law_sheet.iloc[:, 0]:
            law_title = str(raw_title).strip()
            if not law_title.casefold().startswith(LAW_TITLE_PREFIXES):
                continue

            title_tokens = _normalize_law_search_text(law_title)
            if all(
                any(title_token.startswith(query_token) for title_token in title_tokens)
                for query_token in query_tokens
            ):
                matches.append((section_name, law_title))

    return matches


if "app_section" not in st.session_state:
    st.session_state.app_section = "home"

if st.session_state.app_section == "home":
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #FFFFFF !important;
            background-image: url("/app/static/kai_home_background.png");
            background-repeat: no-repeat;
            background-position: right 0 top 32px;
            background-size: auto 100%;
        }
        [data-testid="stSidebar"], [data-testid="stSidebarCollapseButton"] { display: none; }
        .block-container {
            max-width: none !important;
            width: 100% !important;
            min-height: calc(100vh - 2rem);
            padding: 12vh 0 1.5rem;
            display: flex;
            flex-direction: column;
            justify-content: center;
            box-sizing: border-box;
        }
        .kai-home-screen {
            width: min(54vw, 760px);
            margin-left: 7vw;
            text-align: center;
            padding: 8px 16px 20px;
            box-sizing: border-box;
        }
        .kai-home-logo {
            width: 420px;
            height: 250px;
            object-fit: contain;
        }
        .kai-home-title { color: #20265F; font-size: 2.2rem; font-weight: 800; margin: 18px 0 8px; }
        .kai-home-subtitle { color: #5E6A7D; font-size: 1.1rem; margin: 0; }
        div[data-testid="stHorizontalBlock"] {
            width: min(54vw, 760px);
            margin-left: 7vw;
            gap: 18px;
        }
        div[data-testid="stHorizontalBlock"] .stButton > button {
            min-height: 68px; border-radius: 8px; font-size: 1.05rem; font-weight: 700;
            border: 1px solid #2D2A70; color: #2D2A70; background: #FFFFFF;
        }
        div[data-testid="stHorizontalBlock"] .stButton > button:hover {
            color: #FFFFFF; background: #2D2A70; border-color: #2D2A70;
        }
        @media (max-width: 760px) {
            .stApp { background-size: auto 64vh; background-position: right bottom; }
            .block-container { justify-content: flex-start; padding-top: 5vh; padding-bottom: 45vh; }
            .kai-home-screen, div[data-testid="stHorizontalBlock"] {
                width: 92vw;
                margin-left: 4vw;
            }
            .kai-home-screen { background: rgba(255, 255, 255, 0.78); border-radius: 8px; }
            .kai-home-logo { width: 230px; height: 150px; }
        }
        @media (min-width: 761px) and (max-height: 560px) {
            .block-container { padding-top: 8vh; }
        }
        </style>
        <div class="kai-home-screen">
            <img class="kai-home-logo" src=""" + KAI_LOGO_URL + """ alt="Logo PT KAI">
            <h1 class="kai-home-title">Monitoring HHI PT KAI</h1>
            <p class="kai-home-subtitle">Pilih section yang ingin dibuka</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    home_dashboard, home_legal = st.columns(2)
    if home_dashboard.button("Dashboard", type="primary", use_container_width=True):
        st.session_state.app_section = "dashboard"
        st.rerun()
    if home_legal.button("Dasar Hukum / Peraturan", use_container_width=True):
        st.session_state.app_section = "legal"
        st.rerun()
    st.stop()

if st.session_state.app_section == "legal":
    st.markdown(
        f"""
        <style>
        .stApp {{ background: #FFFFFF !important; }}
        [data-testid="stSidebar"], [data-testid="stSidebarCollapseButton"] {{ display: none; }}
        .stApp::before {{
            content: "";
            position: fixed;
            inset: 0;
            z-index: 0;
            pointer-events: none;
            background-image: url("{KAI_LOGO_URL}");
            background-repeat: no-repeat;
            background-position: center 54%;
            background-size: min(68vw, 900px);
            opacity: 0.14;
            filter: blur(2px);
        }}
        .block-container {{
            position: relative;
            z-index: 1;
            max-width: 1600px !important;
            width: 96vw !important;
            padding-top: 2.5rem;
            padding-bottom: 3rem;
        }}
        [data-testid="stMain"] h1 {{ font-size: 2.5rem; }}
        [data-testid="stTextInput"] label {{ font-size: 1rem; }}
        [data-testid="stTextInput"] input {{ min-height: 52px; font-size: 1rem; }}
        [data-testid="stMain"] .stButton > button {{
            min-height: 64px;
            font-size: 1rem;
            font-weight: 700;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("Dasar Hukum / Peraturan")
    st.write("Daftar dasar hukum dan peraturan yang menjadi acuan monitoring HHI.")

    if st.button(
        "➕ Tambah Dasar Hukum / Peraturan",
        type="primary",
        use_container_width=True,
    ):
        _show_add_legal_data_dialog()

    search_query = st.text_input(
        "Cari Undang-Undang / Peraturan",
        placeholder="Contoh: UU Nomor 23, peraturan, atau tahun",
        key="legal_title_search",
    )
    if search_query.strip():
        with st.spinner("Mencari nama hukum/peraturan..."):
            search_results = _search_legal_titles(search_query)

        if search_results:
            st.caption(f"Ditemukan {len(search_results)} hasil")
            for result_index, (section_name, law_title) in enumerate(search_results):
                title_column, action_column = st.columns([5, 1])
                title_column.markdown(f"**{law_title}**")
                if action_column.button(
                    f"Buka {section_name}",
                    key=f"search_law_result_{result_index}",
                    use_container_width=True,
                ):
                    st.session_state.selected_law_title = law_title
                    st.session_state.app_section = f"law:{section_name}"
                    st.rerun()
        else:
            st.info("Tidak ditemukan. Coba kata kunci yang lebih singkat.")

    legal_columns = st.columns(3)
    for index, section_name in enumerate(LEGAL_SHEETS):
        if legal_columns[index % 3].button(
            section_name,
            key=f"open_law_section_{index}",
            use_container_width=True,
        ):
            st.session_state.pop("selected_law_title", None)
            st.session_state.app_section = f"law:{section_name}"
            st.rerun()
    if st.button("Kembali ke Beranda", type="primary"):
        st.session_state.app_section = "home"
        st.rerun()
    st.stop()

selected_law_section = None
if st.session_state.app_section == "pso":
    selected_law_section = "PSO"
elif st.session_state.app_section.startswith("law:"):
    selected_law_section = st.session_state.app_section.split(":", 1)[1]

if selected_law_section in LEGAL_SHEETS:
    st.markdown(
        f"""
        <style>
        .stApp {{ background: #FFFFFF !important; }}
        [data-testid="stSidebar"], [data-testid="stSidebarCollapseButton"] {{ display: none; }}
        .stApp::before {{
            content: "";
            position: fixed;
            inset: 0;
            z-index: 0;
            pointer-events: none;
            background-image: url("{KAI_LOGO_URL}");
            background-repeat: no-repeat;
            background-position: center 54%;
            background-size: min(68vw, 900px);
            opacity: 0.14;
            filter: blur(2px);
        }}
        .block-container {{
            position: relative;
            z-index: 1;
            max-width: 1600px !important;
            width: 96vw !important;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }}
        [data-testid="stMain"] h1 {{ font-size: 2.5rem; }}
        [data-testid="stExpander"] summary p {{ font-size: 1.08rem; font-weight: 700; }}
        [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p {{
            font-size: 1rem;
            line-height: 1.55;
        }}
        [data-testid="stMain"] .stButton > button {{ min-height: 56px; font-size: 1rem; }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    if st.button("← Kembali ke Dasar Hukum / Peraturan"):
        st.session_state.pop("selected_law_title", None)
        st.session_state.app_section = "legal"
        st.rerun()
    sheet_name = LEGAL_SHEETS[selected_law_section]
    st.title(f"Dasar Hukum / Peraturan {selected_law_section}")
    st.caption(f"Sumber data: sheet {sheet_name}")

    law_sheet, law_error = load_law_sheet(sheet_name)
    if law_error:
        st.error(law_error)
    else:
        law_rows = [
            (row_index, str(title).strip())
            for row_index, title in enumerate(law_sheet.iloc[:, 0])
            if str(title).strip().lower().startswith(LAW_TITLE_PREFIXES)
        ]

        if not law_rows:
            st.info(f"Belum ada nama hukum/peraturan yang dikenali di kolom A sheet {sheet_name}.")
        else:
            first_law_row = law_rows[0][0]
            explanation_notes = [
                str(value).strip()
                for value in law_sheet.iloc[:first_law_row, 0]
                if str(value).strip().lower().startswith("penjelasan pasal")
            ]

            def _pasal_reference(text: str) -> tuple[str, str] | None:
                reference = re.search(
                    r"pasal\s+(\d+[a-z]?)\s*(?:ayat\s*\((\d+)\))?",
                    text,
                    flags=re.IGNORECASE,
                )
                if not reference:
                    return None
                return reference.group(1).lower(), reference.group(2) or ""

            selected_law_title = st.session_state.get("selected_law_title")
            for row_index, law_title in law_rows:
                with st.expander(law_title, expanded=law_title == selected_law_title):
                    document_path = _get_law_document_path(selected_law_section, law_title)
                    if document_path:
                        if st.button(
                            "Lihat Dokumen",
                            key=f"view_law_document_{selected_law_section}_{row_index}",
                            use_container_width=True,
                        ):
                            st.session_state.law_document_path = document_path
                            st.session_state.law_document_title = law_title
                            _show_law_document_dialog()
                    else:
                        st.caption("Dokumen peraturan ini belum tersedia.")
                        uploaded_document = st.file_uploader(
                            "Upload dokumen PDF",
                            type=["pdf"],
                            accept_multiple_files=False,
                            key=f"upload_law_document_{selected_law_section}_{row_index}",
                        )
                        if st.button(
                            "Simpan Dokumen",
                            key=f"save_law_document_{selected_law_section}_{row_index}",
                            disabled=uploaded_document is None,
                            use_container_width=True,
                        ):
                            try:
                                _save_law_document(
                                    selected_law_section,
                                    law_title,
                                    uploaded_document,
                                )
                            except (FileExistsError, OSError, ValueError) as exc:
                                st.error(str(exc))
                            else:
                                st.success("Dokumen berhasil diunggah.")
                                st.rerun()

                    article_headers = (
                        law_sheet.iloc[row_index - 1, 1:]
                        if row_index > 0
                        else pd.Series(dtype=str)
                    )
                    has_article = False

                    for column_index, raw_header in enumerate(article_headers, start=1):
                        header = str(raw_header).strip()
                        content = str(law_sheet.iat[row_index, column_index]).strip()
                        if not header or not _is_article_header(header):
                            if content:
                                st.markdown("**Ringkasan**")
                                st.write(content)
                            continue

                        has_article = True
                        header_parts = re.split(r"\s*(?:→|->)\s*", header, maxsplit=1)
                        article_title = header_parts[0].strip()
                        article_summary = header_parts[1].strip() if len(header_parts) > 1 else ""
                        st.markdown(f"**{article_title}**")
                        if article_summary:
                            st.caption(article_summary)
                        if content:
                            st.write(content)

                        article_reference = _pasal_reference(article_title)
                        if article_reference:
                            for note in explanation_notes:
                                note_reference = _pasal_reference(note)
                                if note_reference and note_reference[0] == article_reference[0] and (
                                    not note_reference[1] or note_reference[1] == article_reference[1]
                                ):
                                    explanation_text = re.split(r"\s*(?:→|->)\s*", note, maxsplit=1)
                                    if len(explanation_text) > 1:
                                        st.caption("Penjelasan pasal")
                                        st.write(explanation_text[1].strip())

                    if not has_article and not any(
                        str(value).strip() for value in law_sheet.iloc[row_index, 1:]
                    ):
                        st.info("Belum ada data pasal untuk peraturan ini.")
    st.stop()

# ==========================================================
# 📂 LOAD DATA GOOGLE SHEETS
# ==========================================================

@st.cache_data(ttl=60)
def load_data():
    """Load three worksheets from a Google Spreadsheet.

    The loader uses the public CSV export endpoint first so the dashboard
    can update automatically from a shared spreadsheet without a service
    account. If the spreadsheet is still private, the read will fail until
    sharing is changed or authenticated access is restored.

    The spreadsheet URL can be provided via `st.secrets['GOOGLE_SHEETS_URL']`
    or environment variable `GOOGLE_SHEETS_URL`.
    """

    # Resolve spreadsheet URL / id
    sheet_url = _get_sheet_url()
    if not sheet_url:
        st.error("Google Sheets URL not configured. Set `GOOGLE_SHEETS_URL` in Streamlit secrets or environment.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_url)
    if not m:
        st.error("Google Sheets URL seems invalid. Paste the full share URL.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    ss_id = m.group(1)

    def _prepare_sheet(df: pd.DataFrame, kategori: str) -> pd.DataFrame:
        df = df.copy()
        if df.empty:
            df = pd.DataFrame(columns=["KATEGORI_MONEV"])
        else:
            df.columns = df.columns.astype(str).str.strip()
            df.dropna(how="all", inplace=True)
        df["KATEGORI_MONEV"] = kategori
        return df

    def _read_public_sheet(title: str, kategori: str) -> pd.DataFrame:
        sheet_csv_url = (
            f"https://docs.google.com/spreadsheets/d/{ss_id}/gviz/tq"
            f"?tqx=out:csv&sheet={quote(title)}"
        )
        try:
            df = pd.read_csv(sheet_csv_url)
            return _prepare_sheet(df, kategori)
        except Exception:
            return _prepare_sheet(pd.DataFrame(), kategori)

    df_krt = _read_public_sheet("Monev KRT", "KRT")
    df_strategis = _read_public_sheet("Update Monev Strategis", "STRATEGIS")
    df_kerjasama = _read_public_sheet("Monev Kerjasama", "KERJASAMA")

    if df_krt.empty and df_strategis.empty and df_kerjasama.empty:
        st.error(
            "Spreadsheet belum bisa dibaca secara publik. Buka Google Sheets lalu ubah Share ke 'Anyone with the link can view', "
            "atau lanjutkan memakai service account jika sheet tetap private."
        )

    return df_krt, df_strategis, df_kerjasama


def _append_strategic_activity(row: dict[str, object]) -> None:
    credentials = st.secrets.get("gcp_service_account") if "gcp_service_account" in st.secrets else None
    if not credentials:
        raise ValueError(
            "Kredensial tulis belum dikonfigurasi. Tambahkan [gcp_service_account] "
            "di Streamlit secrets dan beri akun tersebut akses Editor ke spreadsheet."
        )

    import gspread

    sheet_url = _get_sheet_url()
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_url or "")
    if not match:
        raise ValueError("URL Google Sheets tidak valid.")

    client = gspread.service_account_from_dict(dict(credentials))
    try:
        spreadsheet = client.open_by_key(match.group(1))
    except gspread.exceptions.APIError as exc:
        message = str(exc)
        if "must not be an Office file" in message:
            raise ValueError(
                "File pada URL tersebut adalah file Excel/Office. "
                "Buka file di Google Drive, pilih File > Simpan sebagai Google Spreadsheet, "
                "lalu ganti GOOGLE_SHEETS_URL di Streamlit secrets dengan URL spreadsheet baru."
            ) from exc
        raise

    worksheet = spreadsheet.worksheet("Update Monev Strategis")
    all_values = worksheet.get_all_values()
    header_index = next(
        (
            index
            for index, values in enumerate(all_values)
            if "NO" in {str(value).strip().upper() for value in values}
            and "KEGIATAN" in {str(value).strip().upper() for value in values}
        ),
        None,
    )
    if header_index is None:
        raise ValueError(
            "Header pada worksheet Update Monev Strategis tidak ditemukan. "
            "Pastikan satu baris header memiliki kolom NO dan KEGIATAN."
        )
    headers = all_values[header_index]

    worksheet.append_row(
        [row.get(header.strip(), "") if header.strip() else "" for header in headers],
        value_input_option="USER_ENTERED",
    )


@st.dialog("Tambah Data Isu Strategis", width="large")
def _show_add_strategic_data_dialog(df: pd.DataFrame) -> None:
    fields = [
        column for column in df.columns
        if column != "KATEGORI_MONEV" and not str(column).startswith("Unnamed:")
    ]
    if not fields:
        st.error("Kolom worksheet isu strategis belum dapat dibaca.")
        return

    next_no = 1
    if "NO" in df.columns:
        numbers = pd.to_numeric(df["NO"], errors="coerce").dropna()
        if not numbers.empty:
            next_no = int(numbers.max()) + 1

    values: dict[str, object] = {}
    with st.form("add_strategic_activity_form"):
        st.caption("Isi data kegiatan baru. Kolom yang tidak wajib boleh dikosongkan.")
        form_columns = st.columns(2)
        for index, field in enumerate(fields):
            label = str(field).strip()
            with form_columns[index % 2]:
                if label.upper() == "NO":
                    values[label] = st.text_input(label, value=str(next_no), disabled=True)
                elif "STATUS" in label.upper():
                    values[label] = st.selectbox(label, ["Pending", "On Progress", "Done"])
                elif "PROGRES" in label.upper() or "PROGRESS" in label.upper():
                    values[label] = f"{st.number_input(label, min_value=0, max_value=100, value=0)}%"
                elif "TERAKHIR DI UPDATE" in label.upper() or "TERAKHIR UPDATE" in label.upper():
                    values[label] = st.text_input(label, value=datetime.now().strftime("%Y-%m-%d"))
                elif any(term in label.upper() for term in ("KEGIATAN", "GOALS", "HAMBATAN", "DAMPAK", "EVALUASI", "TINDAK LANJUT", "DESKRIPSI")):
                    values[label] = st.text_area(label, height=100)
                else:
                    values[label] = st.text_input(label)

        submitted = st.form_submit_button("Simpan Data", type="primary", use_container_width=True)

    if submitted:
        required_fields = [field for field in ("UNIT PENGUSUL/LEMBAGA", "KEGIATAN") if field in values]
        missing_fields = [field for field in required_fields if not str(values[field]).strip()]
        if missing_fields:
            st.error("Lengkapi kolom wajib: " + ", ".join(missing_fields))
            return

        try:
            _append_strategic_activity(values)
        except Exception as exc:
            st.error(f"Data belum tersimpan ke spreadsheet: {exc}")
            return

        load_data.clear()
        st.success("Data isu strategis berhasil disimpan.")
        st.rerun()

# ==========================================================
# 📊 LOAD DATA
# ==========================================================

df_krt, df_strategis, df_kerjasama = load_data()


def get_activity_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Keep activity rows so dashboard matches spreadsheet structure.

    Some sheets (especially Strategis) have continuation lines where `NO` is
    empty but activity text still exists. Those lines must be retained.
    Trailing helper/blank lines from CSV export should still be removed.
    """
    if df.empty:
        return df.copy()

    # Prefer activity columns so continuation rows are preserved.
    activity_columns = ["KEGIATAN", "PEKERJAAN", "RINCIAN KEGIATAN"]
    for col in activity_columns:
        if col in df.columns:
            content = df[col].astype(str).str.strip().str.lower()
            valid_activity = content.ne("") & content.ne("nan")
            return df.loc[valid_activity].copy()

    if "NO" in df.columns:
        no_series = df["NO"].astype(str).str.strip().str.lower()
        valid_no = no_series.ne("") & no_series.ne("nan")
        return df.loc[valid_no].copy()

    return df.dropna(how="all").copy()


def get_activity_count(df: pd.DataFrame) -> int:
    cleaned = get_activity_rows(df)
    # Count every valid activity row, including continuation rows without NO.
    return int(len(cleaned))


def _pick_existing_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _split_group_values(value: str) -> list[str]:
    if pd.isna(value):
        return []
    raw = str(value).strip()
    if raw.lower() in {"", "nan", "none"}:
        return []

    # Split combined unit strings into individual parts.
    parts = re.split(r"\s*(?:/|;|,|&|\\band\\b|\\bdan\\b)\s*", raw, flags=re.IGNORECASE)
    normalized = []
    for part in parts:
        item = part.strip()
        if not item:
            continue

        # Extract prefix before parentheses, e.g. "ZL (Pendapat Hukum)" -> "ZL"
        if "(" in item:
            item = item.split("(", 1)[0].strip()

        normalized.append(item)

    return normalized


def _get_group_counts(df: pd.DataFrame, col: str, top_n: int | None = 10) -> pd.DataFrame:
    if col not in df.columns:
        return pd.DataFrame(columns=[col, "Jumlah"])

    # Filter to activity rows only to avoid counting continuation/blank rows
    df_clean = get_activity_rows(df)
    if df_clean.empty:
        return pd.DataFrame(columns=[col, "Jumlah"])

    series = df_clean[col].astype(str).str.strip().replace({"": pd.NA, "nan": pd.NA})
    if col in ["UNIT PENGUSUL/LEMBAGA", "UNIT", "LEMBAGA"]:
        series = series.ffill()

    exploded = series.apply(_split_group_values).explode().dropna().astype(str).str.strip()
    exploded = exploded[~exploded.isin(["", "nan", "None", "none"])]
    if exploded.empty:
        return pd.DataFrame(columns=[col, "Jumlah"])

    grouped = exploded.value_counts()
    if top_n is not None:
        grouped = grouped.head(top_n)
    grouped = grouped.sort_values(ascending=True).reset_index()
    grouped.columns = [col, "Jumlah"]
    return grouped


def _get_stakeholder_counts(df: pd.DataFrame, top_n: int = 12) -> pd.DataFrame:
    if "STAKEHOLDER" not in df.columns:
        return pd.DataFrame(columns=["Stakeholder", "Jumlah"])

    stakeholder_series = (
        get_activity_rows(df)["STAKEHOLDER"]
        .apply(_split_group_values)
        .explode()
        .dropna()
        .astype(str)
        .str.strip()
    )
    stakeholder_series = stakeholder_series[
        (stakeholder_series != "") & (stakeholder_series.str.lower() != "nan")
    ]
    stakeholder_series = stakeholder_series.apply(
        lambda value: "Kemenhub" if re.match(r"^Kemenhub\b", value, flags=re.IGNORECASE) else value
    )
    counts = stakeholder_series.value_counts().head(top_n).reset_index()
    counts.columns = ["Stakeholder", "Jumlah"]
    return counts


def filter_by_unit(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """Filter dataframe by a unit/layanan query across common unit columns.

    Matching is case-insensitive and performs substring matching.
    """
    if df.empty or not query:
        return df.copy()

    q = str(query).strip().lower()
    candidates = ["UNIT PENGUSUL/LEMBAGA", "UNIT", "LEMBAGA", "PIC"]

    # Buat salinan dan lakukan forward-fill pada kolom kandidat sehingga
    # baris lanjutan (continuation rows) yang kosong tetap diasosiasikan
    # dengan unit/lembaga sebelumnya.
    df2 = df.copy()
    for col in candidates:
        if col in df2.columns:
            df2[col] = (
                df2[col]
                .astype(str)
                .str.strip()
                .replace({"": pd.NA, "nan": pd.NA})
                .fillna(method="ffill")
            )

    masks = []
    for col in candidates:
        if col in df2.columns:
            masks.append(df2[col].astype(str).str.lower().str.contains(q, na=False))

    if not masks:
        return df.iloc[0:0].copy()

    mask = masks[0]
    for m in masks[1:]:
        mask = mask | m

    return df.loc[mask].copy()


def filter_by_stakeholder(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """Filter dataframe by a stakeholder query using case-insensitive substring matching."""
    if df.empty or not query or "STAKEHOLDER" not in df.columns:
        return df.copy() if not query else df.iloc[0:0].copy()

    stakeholder = (
        df["STAKEHOLDER"]
        .astype(str)
        .str.strip()
        .replace({"": pd.NA, "nan": pd.NA})
        .fillna(method="ffill")
    )
    mask = stakeholder.str.lower().str.contains(str(query).strip().lower(), na=False)
    return df.loc[mask].copy()


def filter_by_activity_keyword(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """Filter activities by a literal keyword across available activity columns."""
    if df.empty or not query:
        return df.copy()

    activity_columns = [
        column for column in ["KEGIATAN", "PEKERJAAN", "RINCIAN KEGIATAN"]
        if column in df.columns
    ]
    if not activity_columns:
        return df.iloc[0:0].copy()

    keyword = str(query).strip()
    mask = pd.Series(False, index=df.index)
    for column in activity_columns:
        mask = mask | df[column].astype(str).str.contains(
            keyword, case=False, na=False, regex=False
        )

    return df.loc[mask].copy()


def _parse_percent_value(val) -> float | None:
    try:
        if pd.isna(val):
            return None
        s = str(val).strip().replace("%", "").replace(",", ".")
        return float(re.search(r"(\d+(?:\.\d+)?)", s).group(1))
    except Exception:
        return None


def _normalize_column_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(name).lower()).strip()


def _match_row_value(row: pd.Series, candidates: list[str], default: str = "-") -> str:
    mapping = {_normalize_column_name(k): k for k in row.index}
    for candidate in candidates:
        key = mapping.get(_normalize_column_name(candidate))
        if key is None:
            continue
        val = row.get(key)
        if pd.isna(val):
            continue
        text = str(val).strip()
        if text and text.lower() not in {"nan", "none", "null", "-"}:
            return text
    return default


def _safe_resume_value(row: pd.Series, candidates: list[str], default: str = "-") -> str:
    return _match_row_value(row, candidates, default)


def _split_resume_items(value: str) -> list[str]:
    """Split spreadsheet text into display items without changing its wording."""
    if value == "-":
        return []

    items = []
    for line in str(value).splitlines():
        line = line.strip()
        if not line:
            continue
        parts = re.split(r"(?=\b\d+[.)]\s+)", line)
        items.extend(part.strip() for part in parts if part.strip())
    return items or [str(value).strip()]


def _remove_resume_number(value: str) -> str:
    return re.sub(r"^\d+[.)]\s*", "", value).strip()


def generate_resume_and_recommendations(row: pd.Series) -> tuple[str, list[str]]:
    """Generate a detailed textual resume and rule-based recommendations for a single activity row."""
    activity_cols = [c for c in ["KEGIATAN", "PEKERJAAN", "RINCIAN KEGIATAN"] if c in row.index]
    title = _safe_resume_value(row, activity_cols, "-")
    no = _safe_resume_value(row, ["NO"], "-")
    status = _safe_resume_value(row, ["STATUS"], "-")
    pic = _safe_resume_value(row, ["PIC"], "-")
    unit = _safe_resume_value(row, ["UNIT PENGUSUL/LEMBAGA", "UNIT", "LEMBAGA"], "-")
    stakeholder = _safe_resume_value(row, ["STAKEHOLDER"], "-")
    rincian = _safe_resume_value(row, ["RINCIAN KEGIATAN", "URAIAN KEGIATAN"], "-")
    deskripsi = _safe_resume_value(row, ["DESKRIPSI KEGIATAN"], "-")
    klasifikasi = _safe_resume_value(row, ["KLASIFIKASI STRATEGI", "KLASIFIKASI"], "-")
    keterangan = _safe_resume_value(row, ["KETERANGAN", "CATATAN", "CATATAN KEGIATAN"], "-")
    start = _safe_resume_value(row, ["START", "TANGGAL MULAI", "MULAI"], "-")
    end = _safe_resume_value(row, ["END", "TARGET SELESAI", "TANGGAL SELESAI", "SELESAI"], "-")
    last_update = _safe_resume_value(row, ["UPDATE TERKINI", "LAST UPDATE", "UPDATE", "TERAKHIR UPDATE", "TERAKHIR DI UPDATE", "TERAKHIR DIUPDATE", "LAST UPDATE TERKINI"], "-")
    progress = _parse_percent_value(_match_row_value(row, ["% PROGRES", "PROGRES (%)", "PROGRESS %", "PROGRES"], "-") if _match_row_value(row, ["% PROGRES", "PROGRES (%)", "PROGRESS %", "PROGRES"], "-") != "-" else row.get("% PROGRES", None))
    dampak = _safe_resume_value(row, ["DAMPAK", "DAMPAK / KONSEKUENSI", "DAMPAK KONSEKUENSI", "KONSEKUENSI"], "-")
    hambatan = _safe_resume_value(row, ["HAMBATAN", "HAMBATAN / KENDALA", "KENDALA", "RISIKO", "HAMBATAN KENDALA"], "-")
    hasil_eval = _safe_resume_value(row, ["HASIL EVALUASI & REKOMENDASI LANGKAH SELANJUTNYA", "HASIL EVALUASI DAN REKOMENDASI LANGKAH SELANJUTNYA", "HASIL EVALUASI & REKOMENDASI", "HASIL EVALUASI DAN REKOMENDASI", "HASIL EVALUASI", "EVALUASI & REKOMENDASI", "EVALUASI DAN REKOMENDASI"], "-")
    tindak_lanjut = _safe_resume_value(row, ["TINDAK LANJUT YANG DILAKUKAN", "TINDAK LANJUT", "TINDAK LANJUT YANG TELAH DILAKUKAN", "TINDAK LANJUT KEGIATAN"], "-")

    summary_lines = []
    summary_lines.append(f"**NO**: {no}")
    summary_lines.append(f"**Kegiatan**: {title}")
    if rincian != "-":
        summary_lines.append(f"**Rincian**: {rincian}")
    if deskripsi != "-":
        summary_lines.append(f"**Deskripsi Kegiatan**: {deskripsi}")
    summary_lines.append(f"**Unit / Lembaga Pengusul**: {unit}")
    if pic != "-":
        summary_lines.append(f"**PIC**: {pic}")
    if stakeholder != "-":
        summary_lines.append(f"**Stakeholder**: {stakeholder}")
    if klasifikasi != "-":
        summary_lines.append(f"**Klasifikasi**: {klasifikasi}")
    summary_lines.append(f"**Status**: {status}")
    summary_lines.append(f"**% Progres**: {progress if progress is not None else '-'}")
    if start != "-":
        summary_lines.append(f"**Tanggal Mulai**: {start}")
    if end != "-":
        summary_lines.append(f"**Target Selesai**: {end}")
    if last_update != "-":
        summary_lines.append(f"**Update Terakhir**: {last_update}")
    if hambatan != "-":
        summary_lines.append(f"**Hambatan / Kendala**: {hambatan}")
    if dampak != "-":
        summary_lines.append(f"**Dampak / Konsekuensi**: {dampak}")
    if hasil_eval != "-":
        summary_lines.append(f"**Hasil Evaluasi & Rekomendasi**: {hasil_eval}")
    if tindak_lanjut != "-":
        summary_lines.append(f"**Tindak Lanjut yang Dilakukan**: {tindak_lanjut}")
    if keterangan != "-":
        summary_lines.append(f"**Keterangan**: {keterangan}")

    summary = "\n\n".join(summary_lines)

    recs: list[str] = []
    st_upper = status.upper() if isinstance(status, str) else ""
    if st_upper in ("PENDING", "BELUM DIMULAI"):
        recs.append("Follow-up kepada PIC untuk klarifikasi hambatan dan jadwalkan penyelesaian.")
    if st_upper in ("ON PROGRES", "IN PROGRESS", "ONPROGRES", "BERJALAN"):
        recs.append("Tetapkan milestone singkat 1-2 minggu dan update % progres setiap minggu.")
    if st_upper in ("SELESAI", "DONE", "COMPLETED", "Selesai"):
        recs.append("Verifikasi hasil, tutup kegiatan di spreadsheet, dan arsipkan bukti pendukung.")

    if progress is None:
        recs.append("Minta update % progres dari PIC karena kolom '% PROGRES' belum terisi.")
    elif progress >= 100:
        recs.append("Proses penutupan dan buat laporan ringkas hasil serta pelajaran yang didapat.")
    elif progress >= 50:
        recs.append("Pertahankan fokus kerja, selesaikan blokir teknis, dan tetapkan due-date terperinci.")
    else:
        recs.append("Alokasikan sumber daya tambahan dan identifikasi kendala utama seperti jadwal, pendanaan, atau SDM.")

    if end != "-":
        try:
            end_dt = pd.to_datetime(end, dayfirst=True, errors="coerce")
            if pd.notna(end_dt):
                days_left = (end_dt.date() - datetime.now().date()).days
                if days_left < 0 and (progress is None or progress < 100):
                    recs.append(f"Target selesai terlewat {abs(days_left)} hari — prioritaskan percepatan dan laporkan resiko ke manajemen.")
                elif days_left <= 7 and (progress is None or progress < 100):
                    recs.append(f"Deadline dalam {days_left} hari — lakukan percepatan dan pastikan PIC siap melakukan aksi segera.")
        except Exception:
            pass

    if stakeholder != "-":
        parts = [s.strip() for s in re.split(r",|;", stakeholder) if s.strip()]
        if len(parts) >= 3:
            recs.append("Adakan koordinasi multi-stakeholder untuk menyelaraskan kebutuhan dan alur komunikasi.")
        else:
            recs.append("Konfirmasi peran stakeholder dan kirim update berkala.")

    if "strateg" in klasifikasi.lower():
        recs.append("Laporkan ringkasan ke tim strategis dan pertimbangkan langkah eskalasi bila berdampak besar.")

    recs.append("Pastikan dokumentasi lengkap: surat, PKS, notulen, bukti pelaksanaan, dan foto/arsip pendukung.")
    recs.append("Catat risiko dan tindak lanjutnya di spreadsheet agar status kegiatan tetap transparan.")

    seen = set()
    final_recs = []
    for r in recs:
        if r not in seen:
            final_recs.append(r)
            seen.add(r)

    return summary, final_recs


def build_resume_pdf_bytes(row: pd.Series, activity_label_col: str | None = None) -> bytes:
    """Generate a real PDF download from the resume content."""
    if activity_label_col is None:
        activity_label_col = _pick_existing_column(row.to_frame().T, ["KEGIATAN", "PEKERJAAN", "RINCIAN KEGIATAN"]) or "KEGIATAN"

    title = _safe_resume_value(row, [activity_label_col, "KEGIATAN", "PEKERJAAN", "RINCIAN KEGIATAN"], "-")
    status = _safe_resume_value(row, ["STATUS"], "-")
    progress_raw = _match_row_value(row, ["% PROGRES", "PROGRES (%)", "PROGRESS %", "PROGRES"], "-")
    progress = _parse_percent_value(progress_raw if progress_raw != "-" else row.get("% PROGRES", None))
    unit = _safe_resume_value(row, ["UNIT PENGUSUL/LEMBAGA", "UNIT", "LEMBAGA"], "-")
    pic = _safe_resume_value(row, ["PIC"], "-")
    stakeholder = _safe_resume_value(row, ["STAKEHOLDER"], "-")
    rincian = _safe_resume_value(row, ["RINCIAN KEGIATAN", "URAIAN KEGIATAN"], "-")
    deskripsi = _safe_resume_value(row, ["DESKRIPSI KEGIATAN"], "-")
    klasifikasi = _safe_resume_value(row, ["KLASIFIKASI STRATEGI", "KLASIFIKASI"], "-")
    start = _safe_resume_value(row, ["START", "TANGGAL MULAI", "MULAI"], "-")
    end = _safe_resume_value(row, ["END", "TARGET SELESAI", "TANGGAL SELESAI", "SELESAI"], "-")
    last_update = _safe_resume_value(row, ["UPDATE TERKINI", "LAST UPDATE", "UPDATE", "TERAKHIR UPDATE", "TERAKHIR DI UPDATE", "TERAKHIR DIUPDATE", "LAST UPDATE TERKINI"], "-")
    dampak = _safe_resume_value(row, ["DAMPAK", "DAMPAK / KONSEKUENSI", "DAMPAK KONSEKUENSI", "KONSEKUENSI"], "-")
    hambatan = _safe_resume_value(row, ["HAMBATAN", "HAMBATAN / KENDALA", "KENDALA", "RISIKO", "HAMBATAN KENDALA"], "-")
    keterangan = _safe_resume_value(row, ["KETERANGAN", "CATATAN", "CATATAN KEGIATAN"], "-")
    hasil_eval = _safe_resume_value(row, ["HASIL EVALUASI & REKOMENDASI LANGKAH SELANJUTNYA", "HASIL EVALUASI DAN REKOMENDASI LANGKAH SELANJUTNYA", "HASIL EVALUASI & REKOMENDASI", "HASIL EVALUASI DAN REKOMENDASI", "HASIL EVALUASI", "EVALUASI & REKOMENDASI", "EVALUASI DAN REKOMENDASI"], "-")
    tindak_lanjut = _safe_resume_value(row, ["TINDAK LANJUT YANG DILAKUKAN", "TINDAK LANJUT", "TINDAK LANJUT YANG TELAH DILAKUKAN", "TINDAK LANJUT KEGIATAN"], "-")

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 28
    content_width = width - (margin * 2)
    navy = "#0F172A"
    slate = "#334155"
    border = "#D8E0EA"
    panel_bg = "#F8FAFC"
    status_key = re.sub(r"\s+", " ", status.strip().upper())
    completed_statuses = {"SELESAI", "DONE", "COMPLETED"}
    progress_statuses = {"ON PROGRES", "ON PROGRESS", "IN PROGRESS", "ONPROGRES", "BERJALAN"}
    is_done = status_key in completed_statuses
    is_in_progress = status_key in progress_statuses
    status_txt = "Selesai" if is_done else "Dalam Proses" if is_in_progress else status
    status_display = "DONE" if is_done else status_txt.upper()
    status_fill = "#DCFCE7" if is_done else "#FFEDD5" if is_in_progress else "#F1F5F9"
    status_stroke = "#22C55E" if is_done else "#F97316" if is_in_progress else border
    status_text_color = "#166534" if is_done else "#9A3412" if is_in_progress else navy

    def wrap_lines(value: str, font_name: str, font_size: float, max_width: float) -> list[str]:
        lines: list[str] = []
        for paragraph in str(value).splitlines() or [""]:
            words = paragraph.split()
            if not words:
                lines.append("")
                continue
            current = ""
            for word in words:
                candidate = f"{current} {word}".strip()
                if pdf.stringWidth(candidate, font_name, font_size) <= max_width:
                    current = candidate
                else:
                    if current:
                        lines.append(current)
                    current = word
            if current:
                lines.append(current)
        return lines or ["-"]

    def draw_icon(center_x: float, center_y: float, icon_kind: str, accent: str) -> None:
        """Draw small vector icons so PDF symbols match the popup without emoji font issues."""
        pdf.setFillColor(accent)
        pdf.circle(center_x, center_y, 7, fill=1, stroke=0)
        pdf.setStrokeColor("#FFFFFF")
        pdf.setFillColor("#FFFFFF")
        pdf.setLineWidth(0.9)
        if icon_kind == "unit":
            pdf.rect(center_x - 3, center_y - 3, 6, 6, fill=0, stroke=1)
            pdf.line(center_x - 1, center_y - 3, center_x - 1, center_y + 3)
            pdf.line(center_x + 1, center_y - 3, center_x + 1, center_y + 3)
        elif icon_kind in {"pic", "stakeholder"}:
            pdf.circle(center_x, center_y + 2, 2, fill=1, stroke=0)
            pdf.arc(center_x - 3.5, center_y - 5, center_x + 3.5, center_y + 2, 0, 180)
            if icon_kind == "stakeholder":
                pdf.circle(center_x - 3.5, center_y + 1, 1.3, fill=1, stroke=0)
                pdf.circle(center_x + 3.5, center_y + 1, 1.3, fill=1, stroke=0)
        elif icon_kind == "done":
            pdf.line(center_x - 3.5, center_y, center_x - 1, center_y - 2.5)
            pdf.line(center_x - 1, center_y - 2.5, center_x + 4, center_y + 3.5)
        elif icon_kind == "progress":
            pdf.setFont("Helvetica-Bold", 6.5)
            pdf.drawCentredString(center_x, center_y - 2.3, "%")
        elif icon_kind == "update":
            pdf.circle(center_x, center_y, 3, fill=0, stroke=1)
            pdf.line(center_x, center_y, center_x, center_y + 2)
            pdf.line(center_x, center_y, center_x + 1.7, center_y - 1)
        else:
            pdf.setFont("Helvetica-Bold", 6.5)
            pdf.drawCentredString(center_x, center_y - 2.3, "i")

    def draw_card(x_pos: float, y_top: float, card_width: float, card_height: float,
                  title_text: str, body: str, fill=panel_bg, stroke=border,
                  body_size: float = 8.2, title_color=navy, body_color=slate,
                  body_bold: bool = False, icon_text: str | None = None) -> None:
        pdf.setLineWidth(0.65)
        pdf.setFillColor(fill)
        pdf.setStrokeColor(stroke)
        pdf.roundRect(x_pos, y_top - card_height, card_width, card_height, 7, fill=1, stroke=1)
        pdf.setFillColor(title_color)
        pdf.setFont("Helvetica-Bold", 8.2)
        title_x = x_pos + 9
        if icon_text:
            accent = status_stroke if title_color == status_text_color else "#DDE7FF"
            draw_icon(x_pos + 17, y_top - 16, icon_text, accent)
            title_x = x_pos + 29
            pdf.setFillColor(title_color)
            pdf.setFont("Helvetica-Bold", 8.2)
        pdf.drawString(title_x, y_top - 15, title_text)
        font_name = "Helvetica-Bold" if body_bold else "Helvetica"
        pdf.setFillColor(body_color)
        pdf.setFont(font_name, body_size)
        line_y = y_top - 30
        line_height = body_size + 3
        max_lines = max(1, int((card_height - 34) / line_height))
        lines = wrap_lines(body, font_name, body_size, card_width - 18)
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            lines[-1] = (lines[-1][: max(8, int(len(lines[-1]) * 0.82))].rstrip(" .,;:") + "...")
        for line in lines:
            pdf.drawString(x_pos + 9, line_y, line)
            line_y -= line_height

    def draw_section(x_pos: float, y_top: float, card_width: float, card_height: float,
                     title_text: str, body: str, fill="#FFFFFF", stroke=border,
                     body_size: float = 8.2, icon_text: str | None = None) -> None:
        draw_card(x_pos, y_top, card_width, card_height, title_text, body, fill, stroke, body_size, icon_text=icon_text)

    def draw_info_section(x_pos: float, y_top: float, card_width: float, card_height: float) -> None:
        """Render the information panel as separated icon rows like the popup."""
        pdf.setLineWidth(0.65)
        pdf.setFillColor("#FFFFFF")
        pdf.setStrokeColor(border)
        pdf.roundRect(x_pos, y_top - card_height, card_width, card_height, 7, fill=1, stroke=1)
        draw_icon(x_pos + 17, y_top - 16, "info", "#DBE7FF")
        pdf.setFillColor(navy)
        pdf.setFont("Helvetica-Bold", 8.2)
        pdf.drawString(x_pos + 29, y_top - 15, "Informasi Kegiatan")

        rows = [
            ("unit", "Unit Pengusul / Lembaga", unit),
            ("info", "Klasifikasi Strategi", klasifikasi),
            ("stakeholder", "Stakeholder", stakeholder),
            ("pic", "PIC", pic),
            ("done" if is_done else "progress", "Status", status_txt),
            ("progress", "Progres", progress_txt),
        ]
        row_y = y_top - 31
        label_width = min(76, card_width * 0.42)
        value_x = x_pos + 13 + label_width
        value_width = card_width - label_width - 22
        for index, (icon_kind, label, value) in enumerate(rows):
            label_lines = wrap_lines(label, "Helvetica-Bold", 6.6, label_width - 19)[:2]
            value_lines = wrap_lines(value, "Helvetica", 6.8, value_width)[:2]
            row_height = max(14, max(len(label_lines), len(value_lines)) * 7.5 + 5)
            if row_y - row_height < y_top - card_height + 7:
                break
            draw_icon(x_pos + 17, row_y - (row_height / 2), icon_kind, "#DBE7FF")
            pdf.setFillColor(navy)
            pdf.setFont("Helvetica-Bold", 6.6)
            for line_index, line in enumerate(label_lines):
                pdf.drawString(x_pos + 26, row_y - 8 - (line_index * 7.5), line)
            pdf.setFillColor(slate)
            pdf.setFont("Helvetica", 6.8)
            for line_index, line in enumerate(value_lines):
                pdf.drawString(value_x, row_y - 8 - (line_index * 7.5), line)
            if index < len(rows) - 1:
                pdf.setStrokeColor("#E8EEF6")
                pdf.line(x_pos + 10, row_y - row_height, x_pos + card_width - 10, row_y - row_height)
            row_y -= row_height

    pdf.setTitle(f"Resume {title}")
    y = height - margin
    gap = 7
    card_width = (content_width - (gap * 2)) / 3
    progress_txt = "-" if progress is None else f"{progress:.0f}%"
    progress_value = 0 if progress is None else max(0, min(100, progress))

    hero_height = 88
    pdf.setFillColor("#2D2A70")
    pdf.roundRect(margin, y - hero_height, content_width, hero_height, 9, fill=1, stroke=0)
    pdf.setFillColor("#E46A00")
    pdf.roundRect(width - margin - 7, y - hero_height, 7, hero_height, 3, fill=1, stroke=0)
    logo_x = margin + 12
    logo_y = y - 61
    logo_size = 38
    pdf.setFillColor("#FFFFFF")
    pdf.roundRect(logo_x, logo_y, logo_size, logo_size, 6, fill=1, stroke=0)
    try:
        logo_request = Request(
            KAI_LOGO_URL,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://seeklogo.com/",
            },
        )
        logo_data = urlopen(logo_request, timeout=10).read()
        pdf.drawImage(
            ImageReader(BytesIO(logo_data)),
            logo_x + 4,
            logo_y + 4,
            width=logo_size - 8,
            height=logo_size - 8,
            preserveAspectRatio=True,
            mask="auto",
        )
    except Exception:
        pdf.setFillColor("#2D2A70")
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawCentredString(logo_x + (logo_size / 2), logo_y + 14, "KAI")
    text_x = margin + 60
    pdf.setFillColor("#FBBF24")
    pdf.setFont("Helvetica-Bold", 7)
    pdf.drawString(text_x, y - 17, "RINGKASAN KEGIATAN")
    pdf.setFillColor("#FFFFFF")
    pdf.setFont("Helvetica-Bold", 11)
    title_y = y - 34
    for line in wrap_lines(title if title != "-" else "Kegiatan", "Helvetica-Bold", 11, content_width - 128)[:3]:
        pdf.drawString(text_x, title_y, line)
        title_y -= 14
    pdf.setFillColor("#E9D5FF")
    pdf.setFont("Helvetica-Bold", 7.2)
    pdf.drawString(text_x, y - hero_height + 14, klasifikasi[:65])

    ring_x = width - margin - 44
    ring_y = y - 44
    pdf.setLineWidth(8)
    pdf.setStrokeColor("#FFFFFF")
    pdf.circle(ring_x, ring_y, 25, fill=0, stroke=1)
    pdf.setStrokeColor("#FBBF24")
    if progress_value > 0:
        pdf.arc(ring_x - 25, ring_y - 25, ring_x + 25, ring_y + 25, startAng=90, extent=-360 * progress_value / 100)
    pdf.setFillColor("#FFFFFF")
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawCentredString(ring_x, ring_y - 3, progress_txt)
    y -= hero_height + 10

    pdf.setLineWidth(0.65)
    meta_width = (content_width - (gap * 2)) / 3
    draw_card(margin, y, meta_width, 42, "UNIT", unit, fill="#FFFFFF", body_size=8, body_bold=True, icon_text="unit")
    draw_card(margin + meta_width + gap, y, meta_width, 42, "PIC", pic, fill="#FFFFFF", body_size=8, body_bold=True, icon_text="pic")
    draw_card(margin + ((meta_width + gap) * 2), y, meta_width, 42, "STAKEHOLDER", stakeholder, fill="#FFFFFF", body_size=7.3, body_bold=True, icon_text="stakeholder")
    y -= 52

    draw_card(
        margin, y, card_width, 70, "STATUS KEGIATAN", f"{status_display}\n{status_txt}",
        fill=status_fill, stroke=status_stroke, body_size=10, body_bold=True,
        title_color=status_text_color, body_color=status_text_color, icon_text="done" if is_done else "progress",
    )
    progress_x = margin + card_width + gap
    draw_card(progress_x, y, card_width, 70, "PROGRESS KEGIATAN", "", fill="#FFFFFF", body_size=10, body_bold=True, icon_text="progress")
    donut_x = progress_x + 29
    donut_y = y - 35
    pdf.setLineWidth(6)
    pdf.setStrokeColor("#E2E8F0")
    pdf.circle(donut_x, donut_y, 16, fill=0, stroke=1)
    pdf.setStrokeColor("#16A34A" if progress_value >= 100 else "#E46A00")
    if progress_value > 0:
        pdf.arc(donut_x - 16, donut_y - 16, donut_x + 16, donut_y + 16, startAng=90, extent=-360 * progress_value / 100)
    pdf.setFillColor(navy)
    pdf.setFont("Helvetica-Bold", 7.5)
    pdf.drawCentredString(donut_x, donut_y - 2.5, progress_txt)
    pdf.setFillColor(navy)
    pdf.setFont("Helvetica-Bold", 9.5)
    pdf.drawString(progress_x + 55, y - 31, progress_txt)
    pdf.setFillColor(slate)
    pdf.setFont("Helvetica", 6.8)
    for line_index, line in enumerate(wrap_lines("Seluruh tahapan kegiatan telah terselesaikan." if progress_value >= 100 else f"Status: {status_txt}", "Helvetica", 6.8, card_width - 64)[:2]):
        pdf.drawString(progress_x + 55, y - 43 - (line_index * 8), line)
    draw_card(margin + ((card_width + gap) * 2), y, card_width, 70, "TERAKHIR UPDATE", f"{last_update}\n{end}", body_size=8.5, body_bold=True, icon_text="update")
    y -= 80

    left_width = content_width * 0.61
    right_width = content_width - left_width - gap
    details = "\n".join(
        f"{index}. {_remove_resume_number(item)}"
        for index, item in enumerate(_split_resume_items(rincian), start=1)
    ) or "-"
    draw_section(margin, y, left_width, 132, "Rincian Kegiatan", details, body_size=8.2, icon_text="info")
    draw_info_section(margin + left_width + gap, y, right_width, 132)
    y -= 142

    draw_section(margin, y, content_width, 82, "Deskripsi Kegiatan", deskripsi, body_size=8.2, icon_text="info")
    y -= 92

    alert_gap = 8
    alert_width = (content_width - alert_gap) / 2
    draw_section(margin, y, alert_width, 76, "Hambatan / Kendala", hambatan, fill="#FEF2F2", stroke="#FCA5A5", body_size=8.2, icon_text="progress")
    draw_section(margin + alert_width + alert_gap, y, alert_width, 76, "Dampak / Konsekuensi", dampak, fill="#FFF7ED", stroke="#F59E0B", body_size=8.2, icon_text="update")
    y -= 86

    draw_section(margin, y, left_width, 90, "Hasil Evaluasi & Rekomendasi", hasil_eval if hasil_eval != "-" else keterangan, body_size=8.2, icon_text="done")
    draw_section(margin + left_width + gap, y, right_width, 90, "Tindak Lanjut yang Dilakukan", tindak_lanjut, body_size=8.2, icon_text="info")

    pdf.save()
    return buffer.getvalue()


def build_resume_html(row: pd.Series, activity_label_col: str | None = None) -> str:
    """Build the resume markup that will be shown in a dialog."""
    if activity_label_col is None:
        activity_label_col = _pick_existing_column(row.to_frame().T, ["KEGIATAN", "PEKERJAAN", "RINCIAN KEGIATAN"]) or "KEGIATAN"

    title = _safe_resume_value(row, [activity_label_col, "KEGIATAN", "PEKERJAAN", "RINCIAN KEGIATAN"], "-")
    status = _safe_resume_value(row, ["STATUS"], "-")
    progress_raw = _match_row_value(row, ["% PROGRES", "PROGRES (%)", "PROGRESS %", "PROGRES"], "-")
    progress = _parse_percent_value(progress_raw if progress_raw != "-" else row.get("% PROGRES", None))
    unit = _safe_resume_value(row, ["UNIT PENGUSUL/LEMBAGA", "UNIT", "LEMBAGA"], "-")
    pic = _safe_resume_value(row, ["PIC"], "-")
    stakeholder = _safe_resume_value(row, ["STAKEHOLDER"], "-")
    rincian = _safe_resume_value(row, ["RINCIAN KEGIATAN", "URAIAN KEGIATAN"], "-")
    deskripsi = _safe_resume_value(row, ["DESKRIPSI KEGIATAN"], "-")
    klasifikasi = _safe_resume_value(row, ["KLASIFIKASI STRATEGI", "KLASIFIKASI"], "-")
    start = _safe_resume_value(row, ["START", "TANGGAL MULAI", "MULAI"], "-")
    end = _safe_resume_value(row, ["END", "TARGET SELESAI", "TANGGAL SELESAI", "SELESAI"], "-")
    last_update = _safe_resume_value(row, ["UPDATE TERKINI", "LAST UPDATE", "UPDATE", "TERAKHIR UPDATE", "TERAKHIR DI UPDATE", "TERAKHIR DIUPDATE", "LAST UPDATE TERKINI"], "-")
    keterangan = _safe_resume_value(row, ["KETERANGAN", "CATATAN", "CATATAN KEGIATAN"], "-")
    dampak = _safe_resume_value(row, ["DAMPAK", "DAMPAK / KONSEKUENSI", "DAMPAK KONSEKUENSI", "KONSEKUENSI"], "-")
    hambatan = _safe_resume_value(row, ["HAMBATAN", "HAMBATAN / KENDALA", "KENDALA", "RISIKO", "HAMBATAN KENDALA"], "-")
    hasil_eval = _safe_resume_value(row, ["HASIL EVALUASI & REKOMENDASI LANGKAH SELANJUTNYA", "HASIL EVALUASI DAN REKOMENDASI LANGKAH SELANJUTNYA", "HASIL EVALUASI & REKOMENDASI", "HASIL EVALUASI DAN REKOMENDASI", "HASIL EVALUASI", "EVALUASI & REKOMENDASI", "EVALUASI DAN REKOMENDASI"], "-")
    tindak_lanjut = _safe_resume_value(row, ["TINDAK LANJUT YANG DILAKUKAN", "TINDAK LANJUT", "TINDAK LANJUT YANG TELAH DILAKUKAN", "TINDAK LANJUT KEGIATAN"], "-")

    if progress is None:
        progress_txt = "-"
        progress_value = 0
    else:
        progress_txt = f"{progress:.0f}%"
        progress_value = max(0, min(100, progress))

    status_key = re.sub(r"\s+", " ", status.strip().upper())
    completed_statuses = {"SELESAI", "DONE", "COMPLETED"}
    progress_statuses = {"ON PROGRES", "ON PROGRESS", "IN PROGRESS", "ONPROGRES", "BERJALAN"}
    status_txt = "Selesai" if status_key in completed_statuses else "Dalam Proses" if status_key in progress_statuses else status
    status_panel_class = "status-done" if status_key in completed_statuses else "status-progress" if status_key in progress_statuses else ""
    status_display = "DONE" if status_key in completed_statuses else status_txt.upper()

    def _render_bullets(value: str) -> str:
        if value == "-":
            return "<li>-</li>"
        parts = []
        for piece in re.split(r"\n|;\s*|\.\s+", value):
            text = piece.strip()
            if text:
                parts.append(f"<li>{text}</li>")
        if not parts:
            return "<li>-</li>"
        return "".join(parts)

    def _render_numbered_items(value: str) -> str:
        items = _split_resume_items(value)
        if not items:
            return "<li>-</li>"
        return "".join(
            f"<li>{html_lib.escape(_remove_resume_number(item))}</li>"
            for item in items
        )

    eval_bullets = _render_bullets(hasil_eval if hasil_eval != '-' else keterangan)
    tindak_bullets = _render_bullets(tindak_lanjut)
    rincian_bullets = _render_numbered_items(rincian)

    return textwrap.dedent(f"""
    <style>
    body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f8fafc; }}
    .resume-wrap {{ padding: 16px 22px 24px; color: #334155; }}
    .resume-hero {{ display: grid; grid-template-columns: minmax(0, 1fr) 176px; gap: 18px; align-items: center; padding: 20px; border-radius: 16px; background: linear-gradient(120deg, #24205b 0%, #34308a 66%, #e46a00 150%); box-shadow: 0 10px 24px rgba(45,42,112,.18); color: #fff; }}
    .resume-brand {{ display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }}
    .resume-logo {{ width: 38px; height: 38px; object-fit: contain; flex: 0 0 38px; border-radius: 8px; background: rgba(255,255,255,.96); padding: 3px; box-sizing: border-box; }}
    .resume-kicker {{ margin-bottom: 8px; color: #fbbf24; font-size: .68rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }}
    .resume-main-title {{ font-weight: 800; font-size: 1.16rem; line-height: 1.42; color: #fff; margin-bottom: 12px; }}
    .resume-tag {{ display: inline-block; background: rgba(255,255,255,.14); color: #fff; border: 1px solid rgba(255,255,255,.34); border-radius: 999px; padding: 5px 10px; font-size: 0.72rem; font-weight: 700; }}
    .resume-meta {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin: 14px 0 16px; }}
            .resume-meta-item {{ display: flex; align-items: center; gap: 9px; font-size: 0.96rem; color: #374151; }}
      .resume-meta-label {{ font-weight: 700; color: #111827; }}
    .resume-meta-item {{ padding: 10px 12px; border: 1px solid #e2e8f0; border-radius: 10px; background: #fff; }}
    .resume-meta-item span:last-child {{ overflow-wrap: anywhere; }}
        .resume-meta-icon {{ display: grid; place-items: center; width: 28px; height: 28px; flex: 0 0 28px; border-radius: 50%; background: #eff6ff; font-size: 1rem; }}
    .resume-chart {{ display: flex; align-items: center; gap: 12px; padding: 12px; border: 1px solid rgba(255,255,255,.24); border-radius: 12px; background: rgba(15,23,42,.2); }}
    .progress-ring {{ width: 78px; height: 78px; flex: 0 0 78px; display: grid; place-items: center; border-radius: 50%; background: conic-gradient(#fbbf24 {progress_value:.0f}%, rgba(255,255,255,.18) 0); position: relative; }}
    .progress-ring::after {{ content: ''; width: 58px; height: 58px; position: absolute; border-radius: 50%; background: #302b79; }}
    .progress-ring strong {{ position: relative; z-index: 1; color: #fff; font-size: 1rem; }}
    .chart-copy {{ color: #fff; }}
    .chart-label {{ display: block; color: rgba(255,255,255,.68); font-size: .68rem; text-transform: uppercase; letter-spacing: .08em; font-weight: 800; }}
    .chart-status {{ display: block; margin-top: 5px; font-size: .9rem; font-weight: 800; }}
    .progress-track {{ height: 7px; margin-top: 8px; overflow: hidden; border-radius: 99px; background: #e2e8f0; }}
    .progress-fill {{ height: 100%; width: {progress_value:.0f}%; border-radius: inherit; background: linear-gradient(90deg, #2d2a70, #e46a00); }}
    .milestone {{ display: flex; justify-content: space-between; margin-top: 6px; color: #64748b; font-size: .68rem; }}
      .resume-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; margin-bottom: 18px; }}
    .resume-panel {{ position: relative; display: flex; flex-direction: column; justify-content: center; background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px 16px 16px 72px; min-height: 112px; box-shadow: 0 4px 12px rgba(15,23,42,.04); }}
    .resume-panel-icon {{ position: absolute; left: 19px; top: 50%; transform: translateY(-50%); display: grid; place-items: center; width: 40px; height: 40px; border-radius: 50%; background: #eff6ff; font-size: 1.3rem; }}
    .resume-panel.status-done .resume-panel-icon {{ background: #dcfce7; color: #16a34a; }}
    .resume-panel.status-progress .resume-panel-icon {{ background: #ffedd5; color: #ea580c; }}
    .resume-panel.progress-summary {{ padding-left: 96px; }}
    .progress-summary .resume-panel-icon {{ left: 18px; width: 62px; height: 62px; background: conic-gradient(#16a34a {progress_value:.0f}%, #e2e8f0 0); font-size: 0; }}
    .progress-summary .resume-panel-icon::after {{ content: '{progress_txt}'; display: grid; place-items: center; width: 48px; height: 48px; border-radius: 50%; background: #fff; color: #0f172a; font-size: .9rem; font-weight: 800; }}
      .panel-title {{ display: block; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 800; color: #475569; margin-bottom: 8px; }}
                .panel-value {{ font-size: 1.1rem; font-weight: 800; color: #0f172a; }}
            .panel-sub {{ margin-top: 4px; color: #64748b; font-size: 0.9rem; }}
            .resume-panel.status-done .panel-value {{ color: #16a34a; font-size: 1.12rem; }}
            .resume-panel.progress-summary .panel-value {{ color: #0f172a; }}
            .resume-panel.progress-summary .panel-sub {{ color: #35607c; font-size: .75rem; line-height: 1.35; max-width: 190px; }}
            .resume-panel.update-summary .resume-panel-icon {{ background: #fff7ed; color: #ea580c; }}
            .resume-panel.update-summary .panel-title {{ color: #ea580c; }}
        .resume-panel.status-done {{ border: 2px solid #22c55e; background: #dcfce7; box-shadow: 0 5px 14px rgba(34, 197, 94, .18); }}
        .resume-panel.status-done .panel-title, .resume-panel.status-done .panel-value {{ color: #166534; }}
        .resume-panel.status-done .panel-sub {{ color: #15803d; }}
        .resume-panel.status-progress {{ border: 2px solid #f97316; background: #ffedd5; box-shadow: 0 5px 14px rgba(249, 115, 22, .18); }}
        .resume-panel.status-progress .panel-title, .resume-panel.status-progress .panel-value {{ color: #9a3412; }}
        .resume-panel.status-progress .panel-sub {{ color: #c2410c; }}
    .resume-section {{ display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 16px; margin-top: 14px; }}
    .resume-left, .resume-right {{ background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; box-shadow: 0 4px 12px rgba(15,23,42,.035); }}
    .resume-section-title {{ display: flex; align-items: center; gap: 7px; font-size: 0.96rem; font-weight: 800; color: #0f172a; margin-bottom: 10px; }}
      .resume-info-table {{ width: 100%; border-collapse: collapse; font-size: 0.94rem; color: #334155; }}
      .resume-info-table td {{ padding: 4px 0; vertical-align: top; }}
      .resume-info-table td:first-child {{ font-weight: 700; color: #0f172a; width: 38%; }}
    .resume-info-list {{ margin: 0; }}
    .resume-info-row {{ display: grid; grid-template-columns: 30px minmax(130px, 0.85fr) minmax(0, 1.4fr); align-items: center; gap: 8px; padding: 10px 0; border-bottom: 1px solid #eef2f7; color: #334155; }}
    .resume-info-row:last-child {{ border-bottom: 0; padding-bottom: 0; }}
    .resume-info-icon {{ display: grid; place-items: center; width: 26px; height: 26px; border-radius: 50%; background: #eff6ff; font-size: 0.95rem; }}
    .resume-info-label {{ font-weight: 700; color: #0f172a; }}
    .resume-info-value {{ overflow-wrap: anywhere; }}
    .resume-status-badge {{ display: inline-block; width: fit-content; padding: 4px 12px; border-radius: 999px; background: #dcfce7; color: #15803d; font-weight: 800; font-size: 0.82rem; }}
      .resume-bullets {{ margin: 0; padding-left: 18px; color: #334155; line-height: 1.6; }}
      .resume-bullets li {{ margin-bottom: 8px; }}
    .resume-numbered {{ margin: 0; padding-left: 22px; color: #334155; line-height: 1.6; }}
    .resume-numbered li {{ margin-bottom: 8px; padding-left: 2px; }}
    .resume-description {{ margin: 0; color: #334155; line-height: 1.6; white-space: pre-wrap; }}
      .resume-eval {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 16px; }}
      .resume-alert, .resume-warning {{ border-radius: 12px; padding: 14px 16px; border: 1px solid #fcd34d; background: #fff7ed; color: #7c2d12; }}
      .resume-alert {{ border-color: #fca5a5; background: #fef2f2; color: #991b1b; }}
    @media (max-width: 900px) {{ .resume-hero, .resume-grid, .resume-section, .resume-eval {{ grid-template-columns: 1fr; }} .resume-meta {{ grid-template-columns: 1fr; }} .resume-chart {{ justify-content: flex-start; }} }}
    </style>
    <div class="resume-wrap">
            <div class="resume-hero">
                <div><div class="resume-brand"><img class="resume-logo" src="https://images.seeklogo.com/logo-png/40/2/pt-kai-kereta-api-indonesia-2020-logo-png_seeklogo-407558.png" alt="Logo PT KAI"><div class="resume-kicker">PT KAI · Activity intelligence</div></div><div class="resume-main-title">{title}</div><div class="resume-tag">{klasifikasi}</div></div>
                <div class="resume-chart"><div class="progress-ring"><strong>{progress_txt}</strong></div><div class="chart-copy"><span class="chart-label">Progress</span><span class="chart-status">{status_txt}</span><div class="progress-track"><div class="progress-fill"></div></div></div></div>
            </div>
      <div class="resume-meta">
                <div class="resume-meta-item"><span class="resume-meta-icon">🏢</span><span class="resume-meta-label">Unit</span><span>{unit}</span></div>
                <div class="resume-meta-item"><span class="resume-meta-icon">👤</span><span class="resume-meta-label">PIC</span><span>{pic}</span></div>
                <div class="resume-meta-item"><span class="resume-meta-icon">👥</span><span class="resume-meta-label">Stakeholder</span><span>{stakeholder}</span></div>
      </div>
      <div class="resume-grid">
                <div class="resume-panel {status_panel_class}"><span class="resume-panel-icon">✓</span><span class="panel-title">Status Kegiatan</span><div class="panel-value">{status_display}</div><div class="panel-sub">{status_txt}</div></div>
                <div class="resume-panel progress-summary"><span class="resume-panel-icon">📈</span><span class="panel-title">Progress Kegiatan</span><div class="panel-value">{progress_txt}</div><div class="progress-track"><div class="progress-fill"></div></div><div class="panel-sub">{('Belum ada update progres' if progress is None else f'{status_txt}. Seluruh tahapan kegiatan telah terselesaikan.')}</div></div>
                <div class="resume-panel update-summary"><span class="resume-panel-icon">◷</span><span class="panel-title">Terakhir Update</span><div class="panel-value">{last_update}</div><div class="panel-sub">{end}</div></div>
      </div>
      <div class="resume-section">
                <div class="resume-left"><div class="resume-section-title">📌 Rincian Kegiatan</div><ol class="resume-numbered">{rincian_bullets}</ol></div>
                <div class="resume-right"><div class="resume-section-title">ℹ️ Informasi Kegiatan</div><div class="resume-info-list"><div class="resume-info-row"><span class="resume-info-icon">🏢</span><span class="resume-info-label">Unit Pengusul / Lembaga</span><span class="resume-info-value">{unit}</span></div><div class="resume-info-row"><span class="resume-info-icon">🎯</span><span class="resume-info-label">Klasifikasi Strategi</span><span class="resume-info-value">{klasifikasi}</span></div><div class="resume-info-row"><span class="resume-info-icon">👥</span><span class="resume-info-label">Stakeholder</span><span class="resume-info-value">{stakeholder}</span></div><div class="resume-info-row"><span class="resume-info-icon">👤</span><span class="resume-info-label">PIC</span><span class="resume-info-value">{pic}</span></div><div class="resume-info-row"><span class="resume-info-icon">✅</span><span class="resume-info-label">Status</span><span class="resume-info-value"><span class="resume-status-badge">{status_txt}</span></span></div><div class="resume-info-row"><span class="resume-info-icon">📈</span><span class="resume-info-label">Progres</span><span class="resume-info-value"><strong>{progress_txt}</strong></span></div></div></div>
      </div>
            <div class="resume-section">
                <div class="resume-left" style="grid-column: 1 / -1;"><div class="resume-section-title">📝 Deskripsi Kegiatan</div><p class="resume-description">{html_lib.escape(deskripsi)}</p></div>
            </div>
      <div class="resume-eval">
        <div class="resume-alert"><div class="resume-section-title">⚠️ Hambatan / Kendala</div><div>{hambatan}</div></div>
        <div class="resume-warning"><div class="resume-section-title">⚡ Dampak / Konsekuensi</div><div>{dampak}</div></div>
      </div>
      <div class="resume-section">
        <div class="resume-left"><div class="resume-section-title">✅ Hasil Evaluasi &amp; Rekomendasi</div><ul class="resume-bullets">{eval_bullets}</ul></div>
        <div class="resume-right"><div class="resume-section-title">📝 Tindak Lanjut yang Dilakukan</div><ul class="resume-bullets">{tindak_bullets}</ul></div>
      </div>
    </div>
    """)
    """Render a resume layout resembling the provided mockup, using fields from the activity row."""
    html = build_resume_html(row, activity_label_col)
    components.html(html, height=850, scrolling=True)


def render_resume_dialog(row: pd.Series, activity_label_col: str | None = None) -> None:
    """Open the dialog immediately for the activity selected by the user."""
    st.session_state.resume_row = row
    _show_resume_dialog()


@st.dialog("Resume Kegiatan", width="large")
def _show_resume_dialog() -> None:
    """Render the resume in Streamlit's real centered modal dialog."""
    row_data = st.session_state.get("resume_row")
    if row_data is None:
        return

    st.html(build_resume_html(row_data))

    title = _safe_resume_value(row_data, ["KEGIATAN", "PEKERJAAN", "RINCIAN KEGIATAN"], "resume")
    safe_title = re.sub(r"[^a-zA-Z0-9]+", "_", str(title)).strip("_") or "resume"
    if HAS_REPORTLAB:
        st.download_button(
            label="Unduh sebagai PDF",
            data=build_resume_pdf_bytes(row_data),
            file_name=f"{safe_title}.pdf",
            mime="application/pdf",
            key="download_resume_pdf_button",
            use_container_width=True,
        )
    else:
        st.error(
            "Module 'reportlab' belum terpasang. Untuk mengaktifkan unduh PDF, jalankan: `pip install reportlab`"
        )

    if st.button("Tutup Popup Resume", key="close_resume_modal", use_container_width=True):
        st.session_state.show_resume_modal = False
        st.rerun()


def render_resume_modal() -> None:
    """Kept for compatibility; dialogs are now opened by the clicked activity button."""
    return


def _parse_progress_series(df: pd.DataFrame) -> pd.Series:
    if "% PROGRES" not in df.columns:
        return pd.Series(dtype=float)

    progress = (
        df["% PROGRES"]
        .astype(str)
        .str.replace("%", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.extract(r"(\d+(?:\.\d+)?)")[0]
    )
    return pd.to_numeric(progress, errors="coerce").dropna()


def _get_status_summary(df: pd.DataFrame) -> pd.DataFrame:
    if "STATUS" not in df.columns:
        return pd.DataFrame(columns=["STATUS_CLEAN", "JUMLAH"])

    status = df["STATUS"].astype(str).str.strip()
    valid = status[(status != "") & (status.str.lower() != "nan")]
    if valid.empty:
        return pd.DataFrame(columns=["STATUS_CLEAN", "JUMLAH"])

    status_clean = valid.str.upper().replace(
        {
            "ON PROGRESS": "ON PROGRES",
            "IN PROGRESS": "ON PROGRES",
        }
    )

    summary = (
        status_clean.value_counts()
        .rename_axis("STATUS_CLEAN")
        .reset_index(name="JUMLAH")
        .sort_values("JUMLAH", ascending=False)
    )
    return summary


def _clean_status_series(df: pd.DataFrame) -> pd.Series:
    if "STATUS" not in df.columns:
        return pd.Series(dtype=str)

    status = df["STATUS"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip().str.upper()
    status = status.replace(
        {
            "ON PROGRESS": "ON PROGRES",
            "IN PROGRESS": "ON PROGRES",
            "INPROGRESS": "ON PROGRES",
            "DONE": "SELESAI",
            "COMPLETED": "SELESAI",
            "FINISHED": "SELESAI",
        }
    )
    return status[(status != "") & (status.str.lower() != "nan")]


def _count_status(df: pd.DataFrame, target: str) -> int:
    return int((_clean_status_series(df) == target).sum())


def _count_unique_values(df: pd.DataFrame, candidates: list[str]) -> int:
    col = _pick_existing_column(df, candidates)
    if not col:
        return 0
    values = (
        df[col].astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
    )
    # Split combined values (e.g. "DZ/ZL" -> "DZ", "ZL") like in _get_group_counts
    exploded = values.apply(_split_group_values).explode().dropna().astype(str).str.strip()
    return int(exploded.nunique())


def _count_unique_stakeholders(df: pd.DataFrame) -> int:
    if "STAKEHOLDER" not in df.columns:
        return 0
    stakeholder_series = (
        df["STAKEHOLDER"]
        .astype(str)
        .str.split(",")
        .explode()
        .astype(str)
        .str.strip()
    )
    stakeholder_series = stakeholder_series[
        (stakeholder_series != "") & (stakeholder_series.str.lower() != "nan")
    ]
    return int(stakeholder_series.nunique())


df_krt = get_activity_rows(df_krt)
df_strategis = get_activity_rows(df_strategis)
df_kerjasama = get_activity_rows(df_kerjasama)

# ==========================================================
# 🔄 GABUNGKAN DATA KRT + STRATEGIS + KERJASAMA
# ==========================================================

df_all = pd.concat(
    [
        df_krt,
        df_strategis,
        df_kerjasama
    ],
    ignore_index=True,
    sort=False
)


# ==========================================================
# ⚙️ PANEL CONTROL
# ==========================================================
# ==========================================================
# ⚙️ PANEL CONTROL
# ==========================================================

with st.sidebar:

    if st.button("← Kembali ke Beranda", use_container_width=True):
        st.session_state.app_section = "home"
        st.rerun()

    st.markdown(
        f'<div class="sidebar-logo-panel"><img src="{KAI_LOGO_URL}" alt="Logo KAI"></div>',
        unsafe_allow_html=True,
    )

    st.header("⚙️ Panel Control")

    kategori = st.selectbox(
        "Kategori Monitoring",
        [
            "Semua",
            "KRT",
            "STRATEGIS",
            "KERJASAMA"
        ]
    )

    pic_strategis = "Semua PIC"
    if kategori == "STRATEGIS" and "PIC" in df_strategis.columns:
        pic_options = (
            df_strategis["PIC"]
            .astype(str)
            .str.strip()
            .replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
            .dropna()
            .drop_duplicates()
            .sort_values()
            .tolist()
        )
        pic_strategis = st.selectbox(
            "Filter PIC Strategis",
            ["Semua PIC"] + pic_options,
            help="Pilih PIC untuk menampilkan hanya kegiatan dan visualisasi milik PIC tersebut.",
        )

    # --- Search input untuk Unit / Lembaga pengusul ---
    unit_query = st.text_input(
        "Cari Unit / Lembaga pengusul",
        value="",
        help="Masukkan nama unit atau lembaga. Bisa menggunakan sebagian kata (case-insensitive)."
    )
    stakeholder_query = st.text_input(
        "Cari Stakeholder",
        value="",
        help="Masukkan nama stakeholder. Bisa menggunakan sebagian kata (case-insensitive)."
    )
    activity_query = st.text_input(
        "Cari Kegiatan (keyword)",
        value="",
        help="Ketik keyword kegiatan, misalnya MoU, untuk menampilkan kegiatan yang memuat keyword tersebut."
    )
    status_filter = st.selectbox(
        "Filter Status Kegiatan",
        ["Semua Status", "Done / Selesai", "On Progress", "Pending"],
        help="Pilih status untuk menampilkan kegiatan dengan status tertentu."
    )
# ==========================================================
# 🔍 FILTER DATA
# ==========================================================

if kategori == "Semua":

    df_filtered = df_all.copy()

elif kategori == "KRT":

    df_filtered = df_krt.copy()

elif kategori == "STRATEGIS":

    df_filtered = df_strategis.copy()

    if pic_strategis != "Semua PIC" and "PIC" in df_filtered.columns:
        df_filtered = df_filtered[
            df_filtered["PIC"].astype(str).str.strip().eq(pic_strategis)
        ].copy()

elif kategori == "KERJASAMA":

    df_filtered = df_kerjasama.copy()

if df_filtered.empty and "KATEGORI_MONEV" not in df_filtered.columns:
    df_filtered["KATEGORI_MONEV"] = pd.Series(dtype=str)
# ==========================================================
# 📊 JUDUL DASHBOARD
# ==========================================================

st.markdown(
    f"""
    <div class=\"kai-hero\">
        <div class=\"kai-hero-brand\">
            <img class=\"kai-logo\" src=\"https://images.seeklogo.com/logo-png/40/2/pt-kai-kereta-api-indonesia-2020-logo-png_seeklogo-407558.png\" alt=\"Logo PT KAI\">
            <div>
                <h2>Dashboard Monitoring HHI - PT KAI</h2>
                <p>Ringkasan kinerja kegiatan untuk kebutuhan monitoring manajemen.</p>
                <span class=\"kai-pill\">Kategori: {kategori}</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ==========================================================
# 📌 KPI
# ==========================================================

total_krt = get_activity_count(df_krt)

total_strategis = get_activity_count(df_strategis)

total_kerjasama = get_activity_count(df_kerjasama)

if kategori == "Semua":
    total_kegiatan = total_krt + total_strategis + total_kerjasama
else:
    total_kegiatan = get_activity_count(df_filtered)
# ==========================================================
# 🎯 TAMPILKAN KPI
# ==========================================================

if kategori == "KRT":
    cards = [
        {
            "label": "📌 Total KRT",
            "value": total_kegiatan,
            "note": "Total kegiatan KRT yang sedang dipantau.",
        },
        {
            "label": "✅ Selesai",
            "value": _count_status(df_filtered, "SELESAI"),
            "note": "Jumlah kegiatan KRT yang telah selesai.",
        },
        {
            "label": "⏳ On Progres",
            "value": _count_status(df_filtered, "ON PROGRES"),
            "note": "Jumlah kegiatan KRT yang sedang berjalan.",
        },
        {
            "label": "🕒 Pending",
            "value": _count_status(df_filtered, "PENDING"),
            "note": "Jumlah kegiatan KRT yang tertunda.",
        },
    ]
elif kategori == "STRATEGIS":
    cards = [
        {
            "label": "📌 Total Isu Strategis",
            "value": total_kegiatan,
            "note": "Jumlah kegiatan isu strategis yang sedang dipantau.",
        },
        {
            "label": "✅ Selesai",
            "value": _count_status(df_filtered, "SELESAI"),
            "note": "Jumlah kegiatan strategis yang telah selesai.",
        },
        {
            "label": "⏳ On Progress",
            "value": _count_status(df_filtered, "ON PROGRES"),
            "note": "Jumlah kegiatan strategis yang sedang berjalan.",
        },
        {
            "label": "🏛 Unit Pengusul / Lembaga",
            "value": _count_unique_values(
                df_filtered,
                ["UNIT PENGUSUL/LEMBAGA", "UNIT", "LEMBAGA"],
            ),
            "note": "Jumlah unit pengusul/lembaga unik.",
        },
        {
            "label": "🤝 Stakeholder Unik",
            "value": _count_unique_stakeholders(df_filtered),
            "note": "Jumlah stakeholder unik terlibat.",
        },
    ]
else:
    cards = [
        {
            "label": "📌 Total Kegiatan",
            "value": total_kegiatan,
            "note": "Total kegiatan valid dalam dashboard.",
        },
        {
            "label": "📋 KRT",
            "value": total_krt,
            "note": "Kegiatan KRT yang sedang dipantau.",
        },
        {
            "label": "🎯 Strategis",
            "value": total_strategis,
            "note": "Kegiatan strategis prioritas.",
        },
        {
            "label": "🤝 Kerjasama",
            "value": total_kerjasama,
            "note": "Kegiatan kolaborasi dan kemitraan.",
        },
    ]

card_html = "".join(
    f"<div class='kai-card-metric'><div class='metric-label'>{card['label']}</div><div class='metric-value'>{card['value']}</div><div class='metric-note'>{card['note']}</div></div>"
    for card in cards
)

st.markdown(f"<div class='kai-card-grid'>{card_html}</div>", unsafe_allow_html=True)

st.caption("Data dimuat langsung dari Google Sheets dan akan ikut berubah saat sheet diperbarui.")

# ==========================================================
# 📈 GRAFIK DASHBOARD
# ==========================================================

st.markdown("### 📈 Ringkasan Visual")

status_color_map = {
    "DONE": KAI_NAVY,
    "SELESAI": KAI_NAVY,
    "ON PROGRES": KAI_ORANGE,
    "PENDING": "#9AA5B5",
}

if kategori == "Semua":
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        df_kategori = pd.DataFrame(
            {
                "Kategori": ["KRT", "STRATEGIS", "KERJASAMA"],
                "Jumlah": [total_krt, total_strategis, total_kerjasama],
            }
        )
        fig_kategori = px.bar(
            df_kategori,
            x="Kategori",
            y="Jumlah",
            color="Kategori",
            color_discrete_map={
                "KRT": KAI_NAVY,
                "STRATEGIS": KAI_ORANGE,
                "KERJASAMA": KAI_SLATE,
            },
            text="Jumlah",
            title="Jumlah Kegiatan per Kategori",
        )
        fig_kategori.update_traces(textposition="outside")
        fig_kategori.update_layout(
            showlegend=False,
            yaxis_title="Jumlah Kegiatan",
            xaxis_title="",
            template=PLOT_TEMPLATE,
            margin=dict(l=20, r=20, t=60, b=20),
        )
        st.plotly_chart(fig_kategori, use_container_width=True)

    with chart_col2:
        status_all = _get_status_summary(df_all)
        if not status_all.empty:
            # Gabungkan SELESAI + DONE menjadi DONE untuk ringkasan semua data saja.
            status_all = status_all.copy()
            status_all["STATUS_CLEAN"] = status_all["STATUS_CLEAN"].replace({"SELESAI": "DONE"})
            status_all = (
                status_all.groupby("STATUS_CLEAN", as_index=False)["JUMLAH"]
                .sum()
                .sort_values("JUMLAH", ascending=False)
            )
            fig_status_all = px.pie(
                status_all,
                names="STATUS_CLEAN",
                values="JUMLAH",
                hole=0.55,
                title="Komposisi Status Seluruh Kegiatan",
                color="STATUS_CLEAN",
                color_discrete_map={
                    "DONE": KAI_NAVY,
                    "ON PROGRES": KAI_ORANGE,
                    "PENDING": "#9AA5B5",
                },
            )
            fig_status_all.update_traces(textposition="inside", textinfo="percent+label")
            fig_status_all.update_layout(
                template=PLOT_TEMPLATE,
                margin=dict(l=20, r=20, t=60, b=20),
            )
            st.plotly_chart(fig_status_all, use_container_width=True)
            st.markdown(
                "<div style='font-size:0.95rem; color:#4B5563; margin-top:-0.75rem;'>"
                "<strong>Catatan:</strong> nilai <em>DONE</em> merupakan gabungan dari "
                "<em>SELESAI</em> pada data KRT dan <em>DONE</em> pada data STRATEGIS.</div>",
                unsafe_allow_html=True,
            )
        else:
            st.info("Data status belum tersedia untuk ditampilkan pada mode Semua.")

    status_data = []
    for label, data in [
        ("KRT", df_krt),
        ("STRATEGIS", df_strategis),
        ("KERJASAMA", df_kerjasama),
    ]:
        status = _clean_status_series(data)
        if not status.empty:
            status = status.replace({"SELESAI": "DONE"})
            counts = status.value_counts().reindex(["DONE", "ON PROGRES", "PENDING"], fill_value=0)
            for status_label, count in counts.items():
                status_data.append(
                    {
                        "Kategori": label,
                        "Status": status_label,
                        "Jumlah": int(count),
                    }
                )

    if status_data:
        df_status_chart = pd.DataFrame(status_data)
        fig_progress = px.bar(
            df_status_chart,
            x="Kategori",
            y="Jumlah",
            color="Status",
            text="Jumlah",
            title="Jumlah Status per Kategori Monitoring",
            color_discrete_map={
                "DONE": KAI_NAVY,
                "ON PROGRES": KAI_ORANGE,
                "PENDING": "#9AA5B5",
            },
        )
        fig_progress.update_layout(
            barmode="group",
            xaxis_title="Kategori",
            yaxis_title="Jumlah Kegiatan",
            template=PLOT_TEMPLATE,
            margin=dict(l=20, r=20, t=60, b=20),
        )
        fig_progress.update_traces(textposition="outside")
        st.plotly_chart(fig_progress, use_container_width=True)

        if "STAKEHOLDER" in df_strategis.columns:
            df_stakeholder = _get_stakeholder_counts(df_strategis)

            if not df_stakeholder.empty:

                fig_stakeholder_all = px.bar(
                    df_stakeholder.iloc[::-1],
                    x="Jumlah",
                    y="Stakeholder",
                    orientation="h",
                    text="Jumlah",
                    title="Top Stakeholder dari STRATEGIS",
                    color="Jumlah",
                    color_continuous_scale=["#BBDEFB", "#1E88E5"],
                )
                fig_stakeholder_all.update_layout(
                    coloraxis_showscale=False,
                    template=PLOT_TEMPLATE,
                    xaxis_title="Jumlah Keterlibatan",
                    yaxis_title="",
                    margin=dict(l=20, r=20, t=60, b=20),
                )
                st.plotly_chart(fig_stakeholder_all, use_container_width=True)
            else:
                st.info("Data stakeholder STRATEGIS belum tersedia untuk ditampilkan pada mode Semua.")
        else:
            st.info("Kolom STAKEHOLDER tidak ditemukan pada data STRATEGIS.")

else:
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        status_filtered = _get_status_summary(df_filtered)
        if not status_filtered.empty:
            fig_status = px.pie(
                status_filtered,
                names="STATUS_CLEAN",
                values="JUMLAH",
                hole=0.55,
                title=f"Komposisi Status - {kategori}",
                color="STATUS_CLEAN",
                color_discrete_map=status_color_map,
            )
            fig_status.update_traces(textposition="inside", textinfo="percent+label")
            fig_status.update_layout(
                template=PLOT_TEMPLATE,
                margin=dict(l=20, r=20, t=60, b=20),
            )
            st.plotly_chart(fig_status, use_container_width=True)
        else:
            st.info(f"Data status untuk kategori {kategori} belum tersedia.")

    with chart_col2:
        # Strategis harus selalu memakai kolom unit pengusul/lembaga agar data 25 unit tetap terlihat.
        if kategori == "STRATEGIS" and "UNIT PENGUSUL/LEMBAGA" in df_filtered.columns:
            group_col = "UNIT PENGUSUL/LEMBAGA"
        elif kategori == "KRT":
            group_col = _pick_existing_column(df_filtered, ["PIC", "UNIT PENGUSUL/LEMBAGA", "UNIT", "LEMBAGA", "STAKEHOLDER"])
        else:
            group_col = _pick_existing_column(
                df_filtered,
                ["UNIT PENGUSUL/LEMBAGA", "UNIT", "LEMBAGA", "PIC", "STAKEHOLDER"],
            )
        if group_col:
            grouped = _get_group_counts(df_filtered, group_col, top_n=None)

            if not grouped.empty:
                fig_top = px.bar(
                    grouped,
                    x="Jumlah",
                    y=group_col,
                    orientation="h",
                    text="Jumlah",
                    title=f"Jumlah {group_col} dengan Kegiatan Terbanyak",
                    color="Jumlah",
                    color_continuous_scale=["#BBDEFB", "#1E88E5"],
                )
                # Keep the two-column row compact so the next analysis section stays visible.
                chart_height = max(400, min(len(grouped) * 28, 560))
                fig_top.update_layout(
                    coloraxis_showscale=False,
                    template=PLOT_TEMPLATE,
                    xaxis_title="Jumlah Kegiatan",
                    yaxis_title="",
                    margin=dict(l=120, r=20, t=60, b=20),
                    height=chart_height,
                )
                st.plotly_chart(fig_top, use_container_width=True)
            else:
                st.info("Data entitas belum cukup untuk membuat grafik Top 10.")
        else:
            st.info("Kolom PIC/UNIT/Stakeholder tidak ditemukan untuk kategori ini.")

    if kategori == "KRT":
        st.markdown("#### 🏢 Analisis Unit KRT")
        unit_col = _pick_existing_column(
            df_filtered,
            ["UNIT", "UNIT PENGUSUL/LEMBAGA", "LEMBAGA"],
        )
        if unit_col:
            df_unit = _get_group_counts(df_filtered, unit_col, top_n=None)

            if not df_unit.empty:
                fig_unit = px.bar(
                    df_unit,
                    x="Jumlah",
                    y=unit_col,
                    orientation="h",
                    text="Jumlah",
                    title="Top Unit KRT",
                    color="Jumlah",
                    color_continuous_scale=["#BBDEFB", "#1E88E5"],
                )
                # Calculate height based on number of units (min 400px, ~35px per bar)
                chart_height = max(400, len(df_unit) * 35)
                fig_unit.update_layout(
                    coloraxis_showscale=False,
                    template=PLOT_TEMPLATE,
                    xaxis_title="Jumlah Kegiatan",
                    yaxis_title="",
                    margin=dict(l=120, r=20, t=60, b=20),
                    height=chart_height,
                )
                st.plotly_chart(fig_unit, use_container_width=True)
            else:
                st.info("Tidak ada data unit yang valid untuk KRT.")
        else:
            st.info("Kolom unit tidak ditemukan di data KRT.")

    if kategori == "STRATEGIS":
        st.markdown("#### 🎯 Analisis Strategis")
        s_col1, s_col2 = st.columns(2)

        with s_col1:
            if "KLASIFIKASI STRATEGI" in df_filtered.columns:
                klasifikasi = (
                    df_filtered["KLASIFIKASI STRATEGI"]
                    .astype(str)
                    .str.strip()
                )
                klasifikasi = klasifikasi[
                    (klasifikasi != "") & (klasifikasi.str.lower() != "nan")
                ]

                if not klasifikasi.empty:
                    df_klasifikasi = (
                        klasifikasi.value_counts()
                        .rename_axis("Klasifikasi Strategi")
                        .reset_index(name="Jumlah")
                        .sort_values("Jumlah", ascending=False)
                    )

                    # Ubah dari donut/pie menjadi horizontal bar chart
                    df_klasifikasi_sorted = df_klasifikasi.copy()
                    # Untuk menampilkan bar terbesar di atas, balik urutan DataFrame
                    df_klasifikasi_sorted = df_klasifikasi_sorted.iloc[::-1]

                    fig_klasifikasi = px.bar(
                        df_klasifikasi_sorted,
                        x="Jumlah",
                        y="Klasifikasi Strategi",
                        orientation="h",
                        color="Klasifikasi Strategi",
                        color_discrete_sequence=["#2D2A70", "#43408B", "#5F5BB1", "#E46A00", "#F09A56"],
                        text="Jumlah",
                        title="Distribusi Klasifikasi Strategi",
                    )
                    fig_klasifikasi.update_traces(textposition="inside", texttemplate="%{text}")
                    total = int(df_klasifikasi['Jumlah'].sum())
                    # Calculate height based on number of classifications (min 350px, ~45px per bar)
                    chart_height = max(350, len(df_klasifikasi_sorted) * 45)
                    fig_klasifikasi.update_layout(
                        template=PLOT_TEMPLATE,
                        legend_title_text="",
                        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="left", x=0),
                        margin=dict(l=120, r=20, t=60, b=20),
                        xaxis_title="Jumlah",
                        yaxis_title="",
                        height=chart_height,
                    )
                    fig_klasifikasi.add_annotation(
                        x=0.99,
                        y=1.02,
                        xref='paper',
                        yref='paper',
                        text=f"Total <b>{total}</b>",
                        showarrow=False,
                        align='right',
                        font=dict(size=12, color=KAI_NAVY),
                    )
                    st.plotly_chart(fig_klasifikasi, use_container_width=True)
                else:
                    st.info("Data Klasifikasi Strategi belum tersedia.")
            else:
                st.info("Kolom KLASIFIKASI STRATEGI tidak ditemukan.")

        with s_col2:
            if "STAKEHOLDER" in df_filtered.columns:
                df_stakeholder = _get_stakeholder_counts(df_filtered)

                if not df_stakeholder.empty:

                    # Lollipop chart for a cleaner executive view.
                    ordered = df_stakeholder.iloc[::-1].copy()
                    max_count = int(ordered["Jumlah"].max())

                    fig_stakeholder = go.Figure()
                    for _, row in ordered.iterrows():
                        fig_stakeholder.add_shape(
                            type="line",
                            x0=0,
                            x1=row["Jumlah"],
                            y0=row["Stakeholder"],
                            y1=row["Stakeholder"],
                            line=dict(color="#D8DEF5", width=4),
                        )

                    marker_colors = [KAI_ORANGE if v == max_count else KAI_NAVY for v in ordered["Jumlah"]]
                    fig_stakeholder.add_trace(
                        go.Scatter(
                            x=ordered["Jumlah"],
                            y=ordered["Stakeholder"],
                            mode="markers+text",
                            marker=dict(size=16, color=marker_colors, line=dict(color="#FFFFFF", width=1.5)),
                            text=ordered["Jumlah"],
                            textposition="middle right",
                            hovertemplate="%{y}<br>Keterlibatan: %{x}<extra></extra>",
                            showlegend=False,
                        )
                    )

                    fig_stakeholder.update_layout(
                        title="Top 12 Stakeholder berdasarkan Keterlibatan",
                        template=PLOT_TEMPLATE,
                        xaxis_title="Jumlah Keterlibatan",
                        yaxis_title="",
                        xaxis=dict(showgrid=True, gridcolor="#F1F5F9", zeroline=False),
                        yaxis=dict(showgrid=False),
                        margin=dict(l=20, r=20, t=60, b=20),
                    )
                    st.plotly_chart(fig_stakeholder, use_container_width=True)
                else:
                    st.info("Data Stakeholder belum tersedia.")
            else:
                st.info("Kolom STAKEHOLDER tidak ditemukan.")

    progress_series = _parse_progress_series(df_filtered)
    if not progress_series.empty:
        avg_progress = float(progress_series.mean())
        completion_rate = float((progress_series >= 100).mean() * 100)

        p_col1, p_col2 = st.columns(2)
        with p_col1:
            fig_gauge = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=avg_progress,
                    number={"suffix": "%"},
                    title={"text": f"Rata-rata Progres {kategori}"},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": KAI_ORANGE},
                        "steps": [
                            {"range": [0, 50], "color": "#EEF2FF"},
                            {"range": [50, 80], "color": "#E0E7FF"},
                            {"range": [80, 100], "color": "#FFE7D1"},
                        ],
                    },
                )
            )
            fig_gauge.update_layout(
                template=PLOT_TEMPLATE,
                margin=dict(l=20, r=20, t=60, b=20),
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

        with p_col2:
            st.metric("Completion Rate (Progres >= 100%)", f"{completion_rate:.1f}%")
            st.caption("Persentase kegiatan yang progress-nya sudah mencapai 100%.")

# ==========================================================
# 📋 TABEL DATA KEGIATAN
# ==========================================================

if "show_resume_modal" not in st.session_state:
    st.session_state.show_resume_modal = False
if "resume_modal_html" not in st.session_state:
    st.session_state.resume_modal_html = ""

render_resume_modal()

if kategori != "Semua":
    st.subheader("📋 Data Kegiatan (Baris Valid)")

    if kategori == "STRATEGIS" and st.button("➕ Tambah Data Baru", type="primary"):
        _show_add_strategic_data_dialog(df_strategis)

    # Terapkan pencarian unit dan stakeholder jika ada input dari sidebar
    df_display = df_filtered.copy()
    status_filter_target = {
        "Done / Selesai": "SELESAI",
        "On Progress": "ON PROGRES",
        "Pending": "PENDING",
    }.get(status_filter)
    if status_filter_target:
        df_display = df_display[
            _clean_status_series(df_display).eq(status_filter_target)
        ].copy()
    try:
        unit_query
    except NameError:
        unit_query = ""
    try:
        stakeholder_query
    except NameError:
        stakeholder_query = ""
    try:
        activity_query
    except NameError:
        activity_query = ""

    if unit_query and str(unit_query).strip() != "":
        df_display = filter_by_unit(df_display, unit_query)

    if stakeholder_query and str(stakeholder_query).strip() != "":
        df_display = filter_by_stakeholder(df_display, stakeholder_query)

    if activity_query and str(activity_query).strip() != "":
        df_display = filter_by_activity_keyword(df_display, activity_query)

    active_filters = []
    if unit_query and str(unit_query).strip() != "":
        active_filters.append(f"Unit: {unit_query}")
    if stakeholder_query and str(stakeholder_query).strip() != "":
        active_filters.append(f"Stakeholder: {stakeholder_query}")
    if activity_query and str(activity_query).strip() != "":
        active_filters.append(f"Kegiatan: {activity_query}")
    if status_filter != "Semua Status":
        active_filters.append(f"Status: {status_filter}")
    if active_filters:
        st.markdown(f"**Hasil pencarian:** {' · '.join(active_filters)}")
        st.caption(f"Menampilkan {len(df_display)} baris.")

    if df_display.empty:
        st.info("Tidak ada data kegiatan yang cocok untuk ditampilkan.")
    else:
        st.dataframe(df_display, use_container_width=True)

        # Pemilihan kegiatan selalu tersedia; filter unit hanya bersifat opsional.
        try:
            activity_label_col = _pick_existing_column(df_display, ["KEGIATAN", "PEKERJAAN", "RINCIAN KEGIATAN"]) or "KEGIATAN"
            opts = []
            for _, r in df_display.reset_index().iterrows():
                row_index = r["index"]
                no = r.get("NO", "")
                title = str(r.get(activity_label_col, "")).strip()
                if not title:
                    title = str(r.get("PEKERJAAN", "")).strip()
                label = f"{no} — {title[:120]}"
                opts.append((label, row_index))

            st.markdown(
                '<div class="resume-action-panel">'
                '<div class="resume-action-eyebrow">Resume kegiatan</div>'
                '<div class="resume-action-title">Pilih aktivitas untuk melihat ringkasan</div>'
                '<div class="resume-action-copy">Buka detail kegiatan dalam format resume eksekutif dan siap diunduh sebagai PDF.</div>'
                '</div>',
                unsafe_allow_html=True,
            )
            selected = st.selectbox(
                "Pilih kegiatan",
                [o[0] for o in opts],
                label_visibility="collapsed",
                key="resume_activity_selector",
            )
            selected_idx = next((idx for label, idx in opts if label == selected), None)

            if selected_idx is not None:
                sel_row = df_display.loc[selected_idx]
                preview_title = str(sel_row.get(activity_label_col, "-")).strip() or "Kegiatan"
                preview_status = str(sel_row.get("STATUS", "-")).strip() or "-"
                preview_progress = str(sel_row.get("% PROGRES", "-")).strip() or "-"
                preview_unit = str(sel_row.get("UNIT PENGUSUL/LEMBAGA", sel_row.get("UNIT", "-"))).strip() or "-"
                st.markdown(
                    f'<div class="resume-preview"><strong>{preview_title[:180]}</strong><br>'
                    f'Status: <strong>{preview_status}</strong> &nbsp; · &nbsp; Progress: <strong>{preview_progress}</strong> &nbsp; · &nbsp; Unit: <strong>{preview_unit}</strong></div>',
                    unsafe_allow_html=True,
                )

                if st.button("Buka Resume Kegiatan", type="primary", use_container_width=True, key="open_resume_button"):
                    render_resume_dialog(sel_row, activity_label_col)
        except Exception:
            # Jika daftar pilihan gagal dibangun, dashboard tetap menampilkan tabel.
            pass