import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import re
import os
import datetime
import requests
import streamlit.components.v1 as components

# =========================================================
# 1. KONFIGURASI HALAMAN (dark mode only)
# =========================================================
st.set_page_config(
    page_title="Bandarmology Pro",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# 2. KONFIGURASI BROKER (NAMA + KELOMPOK)
# =========================================================
# --- NAMA BROKER (LENGKAP) ---
BROKER_NAMES = {
    "CC": "Mandiri Sekuritas",
    "AK": "UBS Sekuritas Indonesia",
    "ZP": "Maybank Sekuritas Indonesia",
    "XL": "Stockbit Sekuritas Digital",
    "YP": "Mirae Asset Sekuritas Indonesia",
    "YU": "CGS International Sekuritas Indonesia",
    "BK": "J.P. Morgan Sekuritas Indonesia",
    "PD": "Indo Premier Sekuritas",
    "MG": "Semesta Indovest Sekuritas",
    "CP": "KB Valbury Sekuritas",
    "XC": "Ajaib Sekuritas Asia",
    "LG": "Trimegah Sekuritas Indonesia Tbk.",
    "SQ": "BCA Sekuritas",
    "KZ": "CLSA Sekuritas Indonesia",
    "NI": "BNI Sekuritas",
    "RX": "Macquarie Sekuritas Indonesia",
    "DH": "Sinarmas Sekuritas",
    "AZ": "Sucor Sekuritas",
    "OD": "BRI Danareksa Sekuritas",
    "BB": "Verdhana Sekuritas Indonesia",
    "KK": "Phillip Sekuritas Indonesia",
    "IF": "Samuel Sekuritas Indonesia",
    "GR": "Panin Sekuritas Tbk.",
    "EP": "MNC Sekuritas",
    "KI": "Ciptadana Sekuritas Asia",
    "DR": "RHB Sekuritas Indonesia",
    "TP": "OCBC Sekuritas Indonesia",
    "BQ": "Korea Investment and Sekuritas Indonesia",
    "YB": "Yakin Bertumbuh Sekuritas",
    "XA": "NH Korindo Sekuritas Indonesia",
    "AP": "Pacific Sekuritas Indonesia",
    "HP": "Henan Putihrai Sekuritas",
    "AI": "UOB Kay Hian Sekuritas",
    "HD": "KGI Sekuritas Indonesia",
    "DX": "Bahana Sekuritas",
    "YJ": "Lotus Andalan Sekuritas",
    "AG": "Kiwoom Sekuritas Indonesia",
    "SS": "Supra Sekuritas Indonesia",
    "DP": "DBS Vickers Sekuritas Indonesia",
    "AO": "Erdikha Elit Sekuritas",
    "RF": "Buana Capital Sekuritas",
    "RB": "Ina Sekuritas Indonesia",
    "BR": "Trust Sekuritas",
    "AT": "Phintraco Sekuritas",
    "CD": "Mega Capital Sekuritas",
    "IN": "Investindo Nusantara Sekuritas",
    "PO": "Pilarmas Investindo Sekuritas",
    "FS": "Yuanta Sekuritas Indonesia",
    "SH": "Artha Sekuritas Indonesia",
    "IH": "Indo Harvest Sekuritas",
    "TS": "Dwidana Sakti Sekuritas",
    "LS": "Reliance Sekuritas Indonesia Tbk.",
    "MI": "Victoria Sekuritas Indonesia",
    "FZ": "Waterfront Sekuritas Indonesia",
    "IU": "Indo Capital Sekuritas",
    "PC": "FAC Sekuritas Indonesia",
    "PP": "Aldiracita Sekuritas Indonesia",
    "MU": "Minna Padi Investama Sekuritas",
    "II": "Danatama Makmur Sekuritas",
    "RO": "Pluang Maju Sekuritas",
    "SA": "Elit Sukses Sekuritas",
    "ID": "Anugerah Sekuritas Indonesia",
    "EL": "Evergreen Sekuritas Indonesia",
    "GA": "BNC Sekuritas Indonesia",
    "ES": "Ekokapital Sekuritas",
    "AR": "Binaartha Sekuritas",
    "PG": "Panca Global Sekuritas",
    "AN": "Wanteg Sekuritas",
    "DU": "KAF Sekuritas Indonesia",
    "AH": "Shinhan Sekuritas Indonesia",
    "RG": "Profindo Sekuritas Indonesia",
    "ZR": "Bumiputera Sekuritas",
    "YO": "Amantara Sekuritas Indonesia",
    "SF": "Surya Fajar Sekuritas",
    "RS": "Yulie Sekuritas Indonesia Tbk.",
    "AF": "Harita Kencana Sekuritas",
    "PF": "Danasakti Sekuritas Indonesia",
    "PI": "Magenta Kapital Sekuritas Indonesia",
    "BS": "Equity Sekuritas Indonesia",
    "PS": "Paramitra Alfa Sekuritas",
    "JB": "Bjb Sekuritas",
    "OK": "Net Sekuritas",
    "GW": "HSBC Sekuritas Indonesia",
    "BF": "Inti Fikasa Sekuritas",
    "TF": "Universal Broker Indonesia Sekuritas",
    "QA": "Tuntun Sekuritas Indonesia",
    "GI": "Webull Sekuritas Indonesia",
    "IT": "Inti Teladan Sekuritas",
    "AD": "OSO Sekuritas Indonesia",
    "DD": "Makindo Sekuritas",
    "IC": "Integrity Capital Sekuritas",
    "FO": "Forte Global Sekuritas",
    "IP": "Yugen Bertumbuh Sekuritas",
    "SC": "IMG Sekuritas",
    "DM": "Masindo Artha Sekuritas",
    "CG": "Citigroup Sekuritas Indonesia",
    "CS": "Credit Suisse Sekuritas Indonesia",
    "DK": "KAF Sekuritas Indonesia",
}

# --- KELOMPOK BROKER: Asing / BUMN / Lokal ---
FOREIGN_BROKERS = {
    "AG", "AH", "AI", "AK", "BK", "BQ", "CG", "CP", "CS",
    "DR", "FS", "GI", "GW", "HD", "KI", "KK", "KZ", "RX",
    "TP", "XA", "YP", "YU", "ZP",
}

BUMN_BROKERS = {"CC", "DX", "NI", "OD"}


def get_broker_group(code: str) -> str:
    """Kembalikan kelompok broker: Asing / BUMN / Lokal."""
    c = str(code).upper().strip()
    if c in BUMN_BROKERS:
        return "BUMN"
    if c in FOREIGN_BROKERS:
        return "Asing"
    return "Lokal"


def get_broker_info(code: str):
    """Return (code, name, group)."""
    c = str(code).upper().strip()
    name = BROKER_NAMES.get(c, "Sekuritas Lain")
    group = get_broker_group(c)
    return c, name, group


# Warna untuk group broker (dipakai di tabel + sankey + label)
COLOR_MAP = {
    "Asing": "#ff4b4b",   # merah
    "BUMN": "#22c55e",    # hijau
    "Lokal": "#3b82f6",   # biru
    "Unknown": "#6b7280",  # abu
}


def style_broker_code(val):
    """Dipakai untuk mewarnai kolom 'Code' di tabel."""
    group = get_broker_group(val)
    color = COLOR_MAP.get(group, COLOR_MAP["Unknown"])
    return f"color:{color}; font-weight:700;"


# =========================================================
# 3. STATE AWAL
# =========================================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "df_raw" not in st.session_state:
    st.session_state["df_raw"] = None
if "current_stock" not in st.session_state:
    st.session_state["current_stock"] = "UNKNOWN"

# =========================================================
# 4. STYLING GLOBAL (DARK MODE ONLY)
# =========================================================
def inject_custom_css():
    bg_color = "#050816"
    sidebar_bg = "#0b1020"
    text_color = "#f9fafb"
    card_bg = "#111827"
    border_color = "#1f2937"
    input_bg = "#020617"
    input_border = "#4b5563"
    shadow = "rgba(0,0,0,0.6)"
    btn_hover = "#f97316"

    st.markdown(
        f"""
        <style>
        /* ============ BASE APP ============ */
        .stApp {{
            background-color: {bg_color};
            color: {text_color};
        }}
        h1, h2, h3, h4, h5, h6, p, span, label, div, li {{
            color: {text_color};
        }}

        /* ============ SIDEBAR ============ */
        [data-testid="stSidebar"] {{
            background-color: {sidebar_bg} !important;
            border-right: 1px solid {border_color};
        }}
        [data-testid="stSidebar"] * {{
            color: {text_color} !important;
        }}

        /* ============ TEXT INPUT (PIN) ============ */
        .stTextInput input {{
            text-align: center;
            font-size: 32px !important;
            letter-spacing: 12px;
            font-weight: 700;
            padding: 16px;
            border-radius: 14px;
            background-color: {input_bg} !important;
            color: {text_color} !important;
            border: 2px solid {input_border} !important;
            box-shadow: 0 14px 35px {shadow};
            transition: all 0.25s ease;
        }}
        .stTextInput input:focus {{
            border-color: #22c55e !important;
            box-shadow: 0 0 0 1px #22c55e;
        }}

        /* ============ BUTTONS ============ */
        .stButton button {{
            width: 100%;
            height: 46px;
            font-size: 15px;
            font-weight: 600;
            border-radius: 12px;
            border: 1px solid {border_color};
            background: linear-gradient(135deg, #111827, #020617);
            color: {text_color} !important;
            transition: all 0.2s ease;
        }}
        .stButton button:hover {{
            transform: translateY(-1px);
            border-color: {btn_hover};
            box-shadow: 0 10px 25px {shadow};
        }}

        /* ============ DATAFRAME SCROLL ============ */
        .stDataFrame {{
            border-radius: 12px;
            overflow: hidden;
        }}

        /* ============ DATE INPUT ============ */
        div[data-baseweb="input"] {{
            background-color: {input_bg} !important;
            border-color: {input_border} !important;
            color: {text_color} !important;
            border-radius: 8px;
        }}
        div[data-baseweb="calendar"] {{
            background-color: {card_bg} !important;
        }}

        /* ============ TICKER & TAG ============ */
        .tag {{
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 700;
            display: inline-block;
            margin-right: 6px;
        }}
        .tag-Asing {{ background-color: {COLOR_MAP["Asing"]}; color: #111827; }}
        .tag-BUMN {{ background-color: {COLOR_MAP["BUMN"]}; color: #052e16; }}
        .tag-Lokal {{ background-color: {COLOR_MAP["Lokal"]}; color: #e5e7eb; }}

        .insight-box {{
            background-color: {card_bg};
            padding: 18px 20px;
            border-radius: 14px;
            border-left: 4px solid {COLOR_MAP["Asing"]};
            margin-top: 16px;
            margin-bottom: 40px;
            box-shadow: 0 10px 30px {shadow};
            border: 1px solid {border_color};
        }}

        /* ============ BROKER METER (NEW) ============ */
        .meter-container {{
            width: 100%;
            height: 24px;
            background: #374151;
            border-radius: 12px;
            position: relative;
            margin: 10px 0;
            overflow: hidden;
        }}
        .meter-bar {{
            height: 100%;
            background: linear-gradient(90deg, #ef4444 0%, #9ca3af 50%, #22c55e 100%);
        }}
        .meter-marker {{
            position: absolute;
            top: -2px;
            width: 4px;
            height: 28px;
            background-color: #fff;
            box-shadow: 0 0 10px #fff;
            transform: translateX(-50%);
            transition: left 0.5s ease-out;
        }}
        .meter-labels {{
            display: flex;
            justify-content: space-between;
            font-size: 10px;
            color: #9ca3af;
            margin-top: 4px;
        }}

        /* ============ FOOTER ============ */
        .footer {{
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background: #020617;
            text-align: center;
            padding: 8px 0;
            font-size: 11px;
            border-top: 1px solid {border_color};
            z-index: 999;
        }}
        .footer span {{ color: #9ca3af !important; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def hide_sidebar():
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {display: none !important;}
        [data-testid="collapsedControl"] {display: none !important;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def show_sidebar():
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {display: block !important;}
        [data-testid="collapsedControl"] {display: block !important;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_footer():
    st.markdown(
        "<div class='footer'><span>© 2025 PT Catindo Bagus Perkasa | Bandarmology Pro (Dark)</span></div>",
        unsafe_allow_html=True,
    )

# =========================================================
# 5. TOOLS LAIN (YAHOO TICKER, FORMAT, DLL)
# =========================================================
def format_number_label(value):
    """Format angka biar mirip tampilan sekuritas (IDR): K/M/B/T."""
    try:
        value = float(value)
    except Exception:
        return str(value)


def format_lot_label(value):
    try:
        value = float(value)
    except Exception:
        return str(value)
    abs_val = abs(value)
    if abs_val >= 1e6:
        return f"{value/1e6:.2f}M"
    if abs_val >= 1e3:
        return f"{value/1e3:.2f}K"
    return f"{value:,.0f}"

def format_freq_label(value):
    try:
        value = float(value)
    except Exception:
        return str(value)
    abs_val = abs(value)
    if abs_val >= 1e6:
        return f"{value/1e6:.2f}M"
    if abs_val >= 1e3:
        return f"{value/1e3:.2f}K"
    return f"{value:,.0f}"
    abs_val = abs(value)
    if abs_val >= 1e12:
        return f"{value/1e12:.2f}T"
    if abs_val >= 1e9:
        return f"{value/1e9:.2f}B"
    if abs_val >= 1e6:
        return f"{value/1e6:.2f}M"
    if abs_val >= 1e3:
        return f"{value/1e3:.2f}K"
    return f"{value:,.0f}"


def get_yahoo_session():
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
    )
    return session


@st.cache_data(ttl=120)
def get_stock_ticker():
    try:
        import yfinance as yf

        tickers = ["BBCA", "BBRI", "BMRI", "BBNI", "TLKM", "ASII", "GOTO", "BUMI", "ADRO", "PGAS"]
        yf_tickers = [f"{t}.JK" for t in tickers]

        data = yf.download(
            yf_tickers,
            period="2d",
            progress=False,
            session=get_yahoo_session(),
        )["Close"]
        if data.empty:
            return "<div class='ticker-wrap'>Market Data Offline</div>"

        last = data.iloc[-1]
        prev = data.iloc[-2] if len(data) > 1 else last
        html = ""
        for t in tickers:
            tk = f"{t}.JK"
            try:
                p_now = last[tk]
                p_prev = prev[tk]
                if pd.isna(p_now):
                    continue
                chg = p_now - p_prev
                pct = (chg / p_prev) * 100 if p_prev != 0 else 0
                cls = "#22c55e" if chg >= 0 else "#f97316"
                sgn = "+" if chg >= 0 else ""
                html += (
                    f"<span class='ticker-item'>{t} {int(p_now):,} "
                    f"<span style='color:{cls}'>({sgn}{pct:.2f}%)</span></span>"
                )
            except Exception:
                continue
        return f"<div class='ticker-wrap'><marquee scrollamount='8'>{html}</marquee></div>"
    except ImportError:
        return "<div class='ticker-wrap'>yfinance not installed</div>"
    except Exception:
        return "<div class='ticker-wrap'>Connection Limited</div>"

# =========================================================
# 5B. DATABASE DATE RESOLVER (Tanggal -> Path File)
# =========================================================
MONTH_ID = {
    1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April', 5: 'Mei', 6: 'Juni',
    7: 'Juli', 8: 'Agustus', 9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember',
}

def _norm_token(s: str) -> str:
    return re.sub(r'[^a-z0-9]+', '', str(s).lower())

def _resolve_year_folder(p_stock: str, year: int) -> str | None:
    if not os.path.exists(p_stock):
        return None
    target = str(year)
    p = os.path.join(p_stock, target)
    if os.path.isdir(p):
        return target
    # fallback: cari folder yg cocok (case-insensitive / ada tambahan)
    for d in os.listdir(p_stock):
        if os.path.isdir(os.path.join(p_stock, d)) and _norm_token(d) == _norm_token(target):
            return d
    return None

def _resolve_month_folder(p_year: str, month: int) -> str | None:
    if not os.path.exists(p_year):
        return None
    id_name = MONTH_ID.get(month, str(month))
    # kandidat umum
    candidates = [
        id_name, id_name.lower(), id_name.upper(),
        id_name[:3], id_name[:3].lower(),
        str(month), f'{month:02d}',
        f'{month}-{id_name}', f'{month:02d}-{id_name}',
        f'{id_name}-{month}', f'{id_name}-{month:02d}',
    ]
    dirs = [d for d in os.listdir(p_year) if os.path.isdir(os.path.join(p_year, d))]
    norm_map = { _norm_token(d): d for d in dirs }
    for c in candidates:
        nc = _norm_token(c)
        if nc in norm_map:
            return norm_map[nc]
    # fallback: coba match mengandung nama bulan / angka bulan
    for d in dirs:
        nd = _norm_token(d)
        if _norm_token(id_name) in nd or _norm_token(f'{month:02d}') in nd:
            return d
    return None


def _resolve_daily_files(p_month: str, dt_date) -> list[str]:
    """Cari *semua* file harian yang match (bukan hanya 1 file).

    Perbaikan penting:
    - Hindari fallback 'dd in filename' yang terlalu longgar (bisa kebaca SEMUA file dalam 1 bulan, terutama kalau dd==mm seperti 12/12).
    - Match hanya jika:
        (1) nama file (tanpa ekstensi) diawali day (09.csv / 9_part1.csv / 09-xxx.csv), atau
        (2) nama file mengandung tanggal lengkap (YYYY-MM-DD / DD-MM-YYYY / YYYYMMDD / DDMMYYYY) dengan separator apa pun.

    Ini mencegah nilai transaksi membengkak (mis. jadi triliunan) karena salah load banyak hari sekaligus.
    """
    if not os.path.exists(p_month):
        return []

    day = int(dt_date.day)
    month = int(dt_date.month)
    year = int(dt_date.year)

    files = [f for f in os.listdir(p_month) if f.lower().endswith(('.csv', '.xlsx'))]
    if not files:
        return []

    dd, mm, yyyy = f"{day:02d}", f"{month:02d}", str(year)

    def stem_lower(fn: str) -> str:
        return os.path.splitext(fn)[0].strip().lower()

    # (1) kandidat utama: diawali hari
    start_day = re.compile(rf"^0?{day}([^0-9]|$)")
    cand = [f for f in files if start_day.search(stem_lower(f))]

    # (2) kandidat tanggal lengkap (lebih aman)
    if not cand:
        s_ddmm = f"{dd}{mm}"
        s_mmdd = f"{mm}{dd}"
        s_yyyymmdd = f"{yyyy}{mm}{dd}"
        s_ddmmyyyy = f"{dd}{mm}{yyyy}"

        # allow separators: -, _, ., space
        sep = r"[-_\.\s]"
        full_patterns = [
            re.compile(rf"{yyyy}{sep}{mm}{sep}{dd}"),
            re.compile(rf"{dd}{sep}{mm}{sep}{yyyy}"),
            re.compile(rf"{yyyy}{sep}{dd}{sep}{mm}"),  # jarang, tapi biarin
            re.compile(rf"{dd}{sep}{yyyy}{sep}{mm}"),  # jarang, tapi biarin
            re.compile(rf"{s_yyyymmdd}"),
            re.compile(rf"{s_ddmmyyyy}"),
        ]

        for f in files:
            s = f.lower()
            if any(p.search(s) for p in full_patterns):
                cand.append(f)

    # de-dup (tetap jaga urutan)
    seen = set()
    cand = [x for x in cand if not (x.lower() in seen or seen.add(x.lower()))]

    # urutan: prefer .csv dulu, lalu alfabet (stabil)
    cand_sorted = sorted(cand, key=lambda x: (0 if x.lower().endswith('.csv') else 1, x.lower()))
    return [os.path.join(p_month, fn) for fn in cand_sorted]

def _resolve_daily_file(p_month: str, dt_date) -> str | None:
    """Backward-compat: ambil file pertama yang match."""
    files = _resolve_daily_files(p_month, dt_date)
    return files[0] if files else None

def resolve_database_file(db_root: str, stock: str, dt_date) -> str | None:
    """Resolve path file database berdasarkan (stock, tanggal)."""
    p_stock = os.path.join(db_root, stock)
    year_folder = _resolve_year_folder(p_stock, int(dt_date.year))
    if not year_folder:
        return None
    p_year = os.path.join(p_stock, year_folder)
    month_folder = _resolve_month_folder(p_year, int(dt_date.month))
    if not month_folder:
        return None
    p_month = os.path.join(p_year, month_folder)
    return _resolve_daily_file(p_month, dt_date)


def resolve_database_files(db_root: str, stock: str, dt_date) -> list[str]:
    """Resolve *semua* file database berdasarkan (stock, tanggal)."""
    p_stock = os.path.join(db_root, stock)
    year_folder = _resolve_year_folder(p_stock, int(dt_date.year))
    if not year_folder:
        return []
    p_year = os.path.join(p_stock, year_folder)
    month_folder = _resolve_month_folder(p_year, int(dt_date.month))
    if not month_folder:
        return []
    p_month = os.path.join(p_year, month_folder)
    return _resolve_daily_files(p_month, dt_date)

def load_database_files(filepaths: list[str]) -> pd.DataFrame:
    """Load dan gabung banyak file (.csv/.xlsx) jadi 1 DataFrame."""
    frames = []
    for fp in filepaths:
        try:
            if fp.lower().endswith(".csv"):
                dfp = pd.read_csv(fp)
            else:
                dfp = pd.read_excel(fp)
            dfp["__source_file"] = os.path.basename(fp)
            frames.append(dfp)
        except Exception:
            continue
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)

# =========================================================
# 6. DATA PROCESSING (DIPERBAIKI UNTUK MENGHINDARI ERROR FORMAT)
# =========================================================

def clean_running_trade(df_input: pd.DataFrame, trade_date: datetime.date | None = None, volume_mode: str = "AUTO"):
    """
    Bersihin & standarisasi data running trade agar:
    - tidak ada baris hilang gara-gara parsing time/lot/price
    - bisa di-sort & di-filter berdasarkan waktu dengan rapi
    - Value dihitung konsisten: Shares * Price (Shares diturunkan dari Lot atau sebaliknya)

    trade_date dipakai untuk membentuk kolom DateTime intraday (default: hari ini).
    """
    if df_input is None or df_input.empty:
        return pd.DataFrame()

    df = df_input.copy()

    # --- 1) Normalisasi nama kolom ---
    df.columns = [str(c).strip() for c in df.columns]
    col_lut = {str(c).strip().lower(): str(c).strip() for c in df.columns}

    # mapping fleksibel (lowercase)
    rename_map = {
        "time": "Time", "waktu": "Time", "jam": "Time", "timestamp": "Time", "datetime": "Time",
        "price": "Price", "harga": "Price", "last": "Price",
        "lot": "Lot", "vol": "Lot", "volume": "Lot", "qty": "Lot", "quantity": "Lot", "shares": "Lot",
        "buyer": "Buyer", "b": "Buyer", "buyer broker": "Buyer", "broker beli": "Buyer", "bcode": "Buyer",
        "seller": "Seller", "s": "Seller", "seller broker": "Seller", "broker jual": "Seller", "scode": "Seller",
        "action": "Action", "type": "Action", "side": "Action", "bs": "Action",
        "buyer_code": "Buyer_Code", "seller_code": "Seller_Code",
    }

    for low, old in col_lut.items():
        if low in rename_map:
            df.rename(columns={old: rename_map[low]}, inplace=True)

    # --- 2) Pastikan kolom minimal ada ---
    required = {"Price", "Lot", "Buyer", "Seller"}
    if not required.issubset(set(df.columns)):
        raise ValueError(
            "Kolom wajib tidak lengkap. Minimal harus ada: Price, Lot, Buyer, Seller. "
            f"Kolom ditemukan: {list(df.columns)}"
        )

    # --- 3) Helper parsing ---
    def _clean_code(x) -> str:
        s = str(x).upper().strip()
        # ambil kode broker 2 huruf pertama yang valid
        m = re.search(r"\b([A-Z]{2})\b", s)
        if m:
            return m.group(1)
        # fallback: ambil token pertama
        return s.split()[0] if s else ""

    def _to_int_series(s: pd.Series) -> pd.Series:
        # generic int cleaner (dipakai untuk kolom yang memang murni angka)
        out = pd.to_numeric(s.astype(str).str.replace(r"[^\d-]", "", regex=True), errors="coerce")
        return out.fillna(0).astype(int)

    def _parse_first_number_series(s: pd.Series) -> pd.Series:
        """Ambil angka pertama dari string (penting untuk Price seperti '1,190 (+2.15%)')."""
        def _one(x):
            if pd.isna(x):
                return float('nan')
            t = str(x)
            m = re.search(r"([0-9][0-9,\.]+)", t)
            if not m:
                return float('nan')
            num = m.group(1).replace(",", "")
            if num.endswith("."):
                num = num[:-1]
            try:
                return float(num)
            except Exception:
                return float('nan')
        out = s.apply(_one)
        return pd.to_numeric(out, errors="coerce")

    def _parse_lot_series(s: pd.Series) -> pd.Series:
        """Lot bisa integer, bisa juga desimal kecil (mis. 0.06)."""
        def _one(x):
            if pd.isna(x):
                return float('nan')
            t = str(x).strip().replace(",", "")
            try:
                return float(t)
            except Exception:
                m = re.search(r"([0-9][0-9,\.]+)", t)
                if not m:
                    return float('nan')
                num = m.group(1).replace(",", "")
                if num.endswith("."):
                    num = num[:-1]
                try:
                    return float(num)
                except Exception:
                    return float('nan')
        out = s.apply(_one)
        return pd.to_numeric(out, errors="coerce")

    def _parse_time_to_dt(val, base_date: datetime.date) -> pd.Timestamp:
        if pd.isna(val):
            return pd.NaT
        if isinstance(val, datetime.datetime):
            return pd.Timestamp(val)
        if isinstance(val, datetime.time):
            return pd.Timestamp(datetime.datetime.combine(base_date, val))

        s = str(val).strip()
        if not s:
            return pd.NaT

        # Variasi yang sering muncul:
        # - "8:58.00"  -> "8:58:00"
        # - "08:58"    -> "08:58:00"
        # - "08:58:00.123" -> "08:58:00"
        s = s.replace(",", ":")
        if re.match(r"^\d{1,2}:\d{2}\.\d{1,2}$", s):
            s = s.replace(".", ":", 1)
        s = re.sub(r"\.\d+$", "", s)  # buang fractional seconds
        if re.match(r"^\d{1,2}:\d{2}$", s):
            s = s + ":00"

        t = pd.to_datetime(s, errors="coerce")
        if pd.isna(t):
            return pd.NaT
        return pd.Timestamp(datetime.datetime.combine(base_date, t.time()))

    # --- 4) Clean numerik ---
    df["Price"] = _parse_first_number_series(df["Price"]).round(0).astype("int64")
    df["Lot"] = _parse_lot_series(df["Lot"])
    # --- 7b) Satuan Volume (Lot vs Shares) ---
    # Banyak data sekuritas menampilkan volume dalam "Shares (lembar)", sementara file lain sudah dalam "Lot".
    # Kalau salah asumsi, nilai transaksi bisa melonjak (mis. jadi triliunan) atau mengecil.
    mode = (volume_mode or "AUTO").strip().upper()
    if mode.startswith("LOT"):
        mode = "LOT"
    elif mode.startswith("SHARE"):
        mode = "SHARES"
    elif mode.startswith("AUTO"):
        mode = "AUTO"
    if mode == "AUTO":
        s = df["Lot"].dropna()
        if len(s) == 0:
            mode = "LOT"
        else:
            # Heuristik: kalau mayoritas kelipatan 100 dan median cukup besar, kemungkinan ini Shares.
            div100 = ((s.astype("int64") % 100) == 0).mean()
            med = float(s.median())
            mode = "SHARES" if (div100 > 0.90 and med >= 100) else "LOT"

    if mode == "SHARES":
        df["Shares"] = df["Lot"].round(0).astype("int64")
        df["Lot"] = (df["Shares"] // 100).astype("int64")
    else:
        df["Lot"] = df["Lot"].astype("int64")
        df["Lot"] = df["Lot"].round(0).astype("int64")
        df["Shares"] = (df["Lot"] * 100).astype("int64")


    # --- 5) Clean broker ---
    df["Buyer_Code"] = df["Buyer"].apply(_clean_code)
    df["Seller_Code"] = df["Seller"].apply(_clean_code)

    # --- 6) Action (opsional) ---
    if "Action" in df.columns:
        def _norm_action(x):
            s = str(x).strip().lower()
            if "buy" in s or s.startswith("b"):
                return "Buy"
            if "sell" in s or s.startswith("s"):
                return "Sell"
            return "Unknown"
        df["Action"] = df["Action"].apply(_norm_action)
    else:
        df["Action"] = "Unknown"

    # --- 7) Time parsing ---
    base_date = trade_date or datetime.date.today()
    df["Time_Str"] = df["Time"].astype(str).str.strip()
    df["DateTime"] = df["Time"].apply(lambda x: _parse_time_to_dt(x, base_date))
    df["Time_Obj"] = pd.to_datetime(df["DateTime"], errors="coerce").dt.time

    # --- 8) Value ---
    df["Value"] = df["Shares"] * df["Price"]

    # --- 9) Filter baris tidak valid (jangan terlalu agresif) ---
    df = df[(df["Price"] > 0) & (df["Lot"] > 0)]
    # kalau time gagal diparse, tetap tampilkan, tapi DateTime = NaT (di-sort belakangan)
    return df


def get_detailed_broker_summary(df):
    """
    Menghitung Broker Summary lengkap dengan Net Val & Avg Price
    """
    buy = df.groupby("Buyer_Code").agg(
        Buy_Val=("Value", "sum"),
        Buy_Lot=("Lot", "sum")
    )
    sell = df.groupby("Seller_Code").agg(
        Sell_Val=("Value", "sum"),
        Sell_Lot=("Lot", "sum")
    )

    summ = pd.merge(buy, sell, left_index=True, right_index=True, how="outer").fillna(0)
    summ["Net_Val"] = summ["Buy_Val"] - summ["Sell_Val"]
    summ["Net_Lot"] = summ["Buy_Lot"] - summ["Sell_Lot"]
    summ["Total_Val"] = summ["Buy_Val"] + summ["Sell_Val"]
    
    # Hitung Avg Price (Hindari pembagian dengan nol)
    summ["Buy_Avg"] = 0
    mask_b = summ["Buy_Lot"] > 0
    summ.loc[mask_b, "Buy_Avg"] = summ.loc[mask_b, "Buy_Val"] / (summ.loc[mask_b, "Buy_Lot"] * 100)
    
    summ["Sell_Avg"] = 0
    mask_s = summ["Sell_Lot"] > 0
    summ.loc[mask_s, "Sell_Avg"] = summ.loc[mask_s, "Sell_Val"] / (summ.loc[mask_s, "Sell_Lot"] * 100)
    
    # Convert ke Int
    summ["Buy_Avg"] = summ["Buy_Avg"].astype(int)
    summ["Sell_Avg"] = summ["Sell_Avg"].astype(int)

    summ.index.name = "Code"
    summ = summ.reset_index()
    summ["Name"] = summ["Code"].apply(lambda x: get_broker_info(x)[1])
    summ["Group"] = summ["Code"].apply(lambda x: get_broker_info(x)[2])

    return summ.sort_values("Net_Val", ascending=False)


def calculate_broker_action_meter(summ):
    """
    Menghitung skala akumulasi (0-100)
    """
    top_buyers = summ.nlargest(5, "Net_Val")["Net_Val"].sum()
    top_sellers = summ.nsmallest(5, "Net_Val")["Net_Val"].sum() # Value is negative
    
    abs_sell = abs(top_sellers)
    total_power = top_buyers + abs_sell
    
    if total_power == 0:
        return 50 # Neutral
        
    # Rasio kekuatan buyer
    ratio = top_buyers / total_power
    return int(ratio * 100)



def prepare_trade_book_data(df: pd.DataFrame):
    """
    Menyiapkan data untuk Trade Book Chart & Price Table.
    - Price table: agregasi Buy/Sell per price
    - Chart: cumulative Buy/Sell per menit (intraday)

    Catatan:
    Action "Unknown" tidak dimasukkan ke chart kumulatif (biar chart tidak misleading).
    """
    # 1) Price table
    price_grp = df.groupby(["Price", "Action"]).agg(
        Lot=("Lot", "sum"),
        Freq=("Lot", "count")
    ).reset_index()

    pivot = price_grp.pivot(index="Price", columns="Action", values=["Lot", "Freq"]).fillna(0)
    pivot.columns = [f"{c[1]}_{c[0]}" for c in pivot.columns]  # e.g. Buy_Lot, Sell_Lot
    pivot = pivot.reset_index()

    for c in ["Buy_Lot", "Sell_Lot", "Buy_Freq", "Sell_Freq"]:
        if c not in pivot.columns:
            pivot[c] = 0

    pivot["Total_Lot"] = pivot["Buy_Lot"] + pivot["Sell_Lot"]
    pivot = pivot.sort_values("Price", ascending=False)

    # 2) Chart data
    chart_data = pd.DataFrame()
    if "DateTime" in df.columns:
        ts = df.dropna(subset=["DateTime"]).copy()
        ts = ts[ts["Action"].isin(["Buy", "Sell"])]
        if not ts.empty:
            ts = ts.set_index("DateTime").sort_index()
            res = ts.groupby([pd.Grouper(freq="1min"), "Action"])["Lot"].sum().unstack(fill_value=0)
            res["Buy_Cum"] = res.get("Buy", 0).cumsum()
            res["Sell_Cum"] = res.get("Sell", 0).cumsum()
            chart_data = res.reset_index()

    return pivot, chart_data


def build_sankey(df, top_n=15, metric="Value"):
    flow = df.groupby(["Buyer_Code", "Seller_Code"])[metric].sum().reset_index()
    flow = flow.sort_values(metric, ascending=False).head(top_n)

    flow["Source"] = flow["Buyer_Code"] + " (Buyer)"
    flow["Target"] = flow["Seller_Code"] + " (Seller)"
    
    all_nodes = list(set(flow["Source"]).union(set(flow["Target"])))
    node_map = {k: v for v, k in enumerate(all_nodes)}

    labels = all_nodes
    colors = []
    for node in all_nodes:
        code = node.split()[0]
        group = get_broker_group(code)
        colors.append(COLOR_MAP.get(group, "#888"))

    src = [node_map[x] for x in flow["Source"]]
    tgt = [node_map[x] for x in flow["Target"]]
    vals = flow[metric].tolist()

    link_colors = []
    for s_idx in src:
        c_hex = colors[s_idx].lstrip("#")
        try:
            rgb = tuple(int(c_hex[i: i + 2], 16) for i in (0, 2, 4))
            link_colors.append(f"rgba({rgb[0]},{rgb[1]},{rgb[2]},0.4)")
        except:
            link_colors.append("rgba(100,100,100,0.4)")

    return labels, colors, src, tgt, vals, link_colors

# =========================================================
# 7. UI COMPONENTS (VISUAL)
# =========================================================
def render_broker_action_meter(summ):
    val = calculate_broker_action_meter(summ)
    
    if val >= 60: label = "Big Accumulation"
    elif val <= 40: label = "Big Distribution"
    else: label = "Neutral"
    
    st.markdown("### Broker Action")
    st.markdown(f"""
    <div style="text-align:center; font-weight:bold; margin-bottom:5px; color:#fff;">{label}</div>
    <div class="meter-container">
        <div class="meter-bar"></div>
        <div class="meter-marker" style="left: {val}%;"></div>
    </div>
    <div class="meter-labels">
        <span>Big Dist</span>
        <span>Neutral</span>
        <span>Big Acc</span>
    </div>
    """, unsafe_allow_html=True)

def render_broker_summary_split(summ, net_mode=False):
    st.subheader("Broker Summary")
    
    # Logic: 
    # Jika Net Mode ON: Tampilkan Top Net Buy (Accum) di kiri, Top Net Sell (Dist) di kanan
    # Jika Net Mode OFF: Tampilkan Top Gross Buy Value di kiri, Top Gross Sell Value di kanan
    
    if net_mode:
        top_buyers = summ[summ["Net_Val"] > 0].sort_values("Net_Val", ascending=False).head(20)
        top_sellers = summ[summ["Net_Val"] < 0].sort_values("Net_Val", ascending=True).head(20)
        
        cols_buy = ["Code", "Net_Val", "Net_Lot", "Buy_Avg"]
        cols_sell = ["Code", "Net_Val", "Net_Lot", "Sell_Avg"]
    else:
        top_buyers = summ.sort_values("Buy_Val", ascending=False).head(20)
        top_sellers = summ.sort_values("Sell_Val", ascending=False).head(20)
        
        cols_buy = ["Code", "Buy_Val", "Buy_Lot", "Buy_Avg"]
        cols_sell = ["Code", "Sell_Val", "Sell_Lot", "Sell_Avg"]
        
    c1, c2 = st.columns(2)
    with c1:
        st.caption("Top Buyers (Accumulation)")
        st.dataframe(
            top_buyers[cols_buy].style.format({
                "Net_Val": format_number_label, "Buy_Val": format_number_label,
                "Net_Lot": "{:,.0f}", "Buy_Lot": "{:,.0f}", "Buy_Avg": "{:,.0f}"
            }).applymap(style_broker_code, subset=["Code"]),
            use_container_width=True, hide_index=True, height=450
        )
        
    with c2:
        st.caption("Top Sellers (Distribution)")
        st.dataframe(
            top_sellers[cols_sell].style.format({
                "Net_Val": format_number_label, "Sell_Val": format_number_label,
                "Net_Lot": "{:,.0f}", "Sell_Lot": "{:,.0f}", "Sell_Avg": "{:,.0f}"
            }).applymap(style_broker_code, subset=["Code"]),
            use_container_width=True, hide_index=True, height=450
        )

def render_trade_book(df):
    st.subheader("Trade Book")
    price_df, chart_df = prepare_trade_book_data(df)
    
    tab1, tab2 = st.tabs(["Chart", "Price Table"])
    
    with tab1:
        if not chart_df.empty:
            long_df = pd.melt(chart_df, id_vars=["DateTime"], value_vars=["Buy_Cum", "Sell_Cum"], var_name="Type", value_name="Volume")
            
            fig = px.line(long_df, x="DateTime", y="Volume", color="Type",
                          color_discrete_map={"Buy_Cum": "#22c55e", "Sell_Cum": "#ef4444"},
                          title="Intraday Cumulative Volume")
            
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#f9fafb'),
                              hovermode="x unified", legend=dict(orientation="h", y=1.1))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Data chart tidak tersedia.")
            
    with tab2:
        # Menampilkan tabel harga mirip Stockbit
        disp = price_df[["Price", "Buy_Lot", "Sell_Lot", "Buy_Freq", "Sell_Freq"]]
        st.dataframe(
            disp.style.format("{:,.0f}")
                .bar(subset=["Buy_Lot"], color='#064e3b')
                .bar(subset=["Sell_Lot"], color='#7f1d1d'),
            use_container_width=True, hide_index=True, height=400
        )



def compute_foreign_domestic_activity(df: pd.DataFrame):
    """
    Hitung aktivitas Foreign vs Domestic.
    Definisi:
      - F Buy  : trade dimana Buyer broker group = Asing
      - F Sell : trade dimana Seller broker group = Asing
      - D Buy/Sell: selain Asing (BUMN + Lokal)
    """
    dfx = df.copy()
    dfx["Buyer_Group"] = dfx["Buyer_Code"].apply(get_broker_group)
    dfx["Seller_Group"] = dfx["Seller_Code"].apply(get_broker_group)

    def _sum_where(mask, col):
        return float(dfx.loc[mask, col].sum()) if col in dfx.columns else 0.0

    def _cnt_where(mask):
        return int(mask.sum())

    is_f_buy = dfx["Buyer_Group"] == "Asing"
    is_f_sell = dfx["Seller_Group"] == "Asing"
    is_d_buy = ~is_f_buy
    is_d_sell = ~is_f_sell

    out = {
        "value": {
            "F_Buy": _sum_where(is_f_buy, "Value"),
            "F_Sell": _sum_where(is_f_sell, "Value"),
            "D_Buy": _sum_where(is_d_buy, "Value"),
            "D_Sell": _sum_where(is_d_sell, "Value"),
        },
        "volume": {
            "F_Buy": _sum_where(is_f_buy, "Lot"),
            "F_Sell": _sum_where(is_f_sell, "Lot"),
            "D_Buy": _sum_where(is_d_buy, "Lot"),
            "D_Sell": _sum_where(is_d_sell, "Lot"),
        },
        "freq": {
            "F_Buy": _cnt_where(is_f_buy),
            "F_Sell": _cnt_where(is_f_sell),
            "D_Buy": _cnt_where(is_d_buy),
            "D_Sell": _cnt_where(is_d_sell),
        }
    }

    # persentase Foreign vs Domestic (berdasarkan total dua sisi)
    for k in ["value", "volume", "freq"]:
        total_f = out[k]["F_Buy"] + out[k]["F_Sell"]
        total_d = out[k]["D_Buy"] + out[k]["D_Sell"]
        grand = total_f + total_d
        out[k]["Foreign_Pct"] = (total_f / grand * 100) if grand else 0.0
        out[k]["Domestic_Pct"] = (total_d / grand * 100) if grand else 0.0
        out[k]["Net_Foreign"] = out[k]["F_Buy"] - out[k]["F_Sell"]
    return out


def render_foreign_domestic_activity(df: pd.DataFrame):
    st.subheader("Foreign–Domestic Activity")

    stats = compute_foreign_domestic_activity(df)

    tab_val, tab_vol, tab_freq = st.tabs(["Value (IDR)", "Volume (Lot)", "Frequency (x)"])

    def _stacked_bar(metric_key: str, title: str):
        m = stats[metric_key]
        bar_df = pd.DataFrame([
            {"Group": "Foreign", "Side": "Buy", "Value": m["F_Buy"]},
            {"Group": "Foreign", "Side": "Sell", "Value": m["F_Sell"]},
            {"Group": "Domestic", "Side": "Buy", "Value": m["D_Buy"]},
            {"Group": "Domestic", "Side": "Sell", "Value": m["D_Sell"]},
        ])

        fig = go.Figure()
        for side, color in [("Buy", "#22c55e"), ("Sell", "#ef4444")]:
            sub = bar_df[bar_df["Side"] == side]
            fig.add_trace(go.Bar(
                x=sub["Group"],
                y=sub["Value"],
                name=side,
                marker_color=color,
            ))
        fig.update_layout(
            barmode="stack",
            title=title,
            height=420,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f9fafb"),
            legend=dict(orientation="h", y=1.1),
            margin=dict(l=10, r=10, t=60, b=10),
        )
        return fig

    with tab_val:
        m = stats["value"]
        c1, c2, c3 = st.columns(3)
        c1.metric("F Buy", f"Rp {format_number_label(m['F_Buy'])}")
        c2.metric("F Sell", f"Rp {format_number_label(m['F_Sell'])}")
        c3.metric("Net Foreign", f"Rp {format_number_label(m['Net_Foreign'])}",
                  delta="Net Buy" if m["Net_Foreign"] > 0 else ("Net Sell" if m["Net_Foreign"] < 0 else "Flat"))
        st.plotly_chart(_stacked_bar("value", "Value (IDR)"), use_container_width=True)
        st.markdown(
            f"<div style='text-align:center;color:#9ca3af;font-size:12px;'>"
            f"Foreign <b>{m['Foreign_Pct']:.2f}%</b> | Domestic <b>{m['Domestic_Pct']:.2f}%</b>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with tab_vol:
        m = stats["volume"]
        c1, c2, c3 = st.columns(3)
        c1.metric("F Buy", f"{m['F_Buy']:,.0f} Lot")
        c2.metric("F Sell", f"{m['F_Sell']:,.0f} Lot")
        c3.metric("Net Foreign", f"{m['Net_Foreign']:,.0f} Lot",
                  delta="Net Buy" if m["Net_Foreign"] > 0 else ("Net Sell" if m["Net_Foreign"] < 0 else "Flat"))
        st.plotly_chart(_stacked_bar("volume", "Volume (Lot)"), use_container_width=True)
        st.markdown(
            f"<div style='text-align:center;color:#9ca3af;font-size:12px;'>"
            f"Foreign <b>{m['Foreign_Pct']:.2f}%</b> | Domestic <b>{m['Domestic_Pct']:.2f}%</b>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with tab_freq:
        m = stats["freq"]
        c1, c2, c3 = st.columns(3)
        c1.metric("F Buy", f"{m['F_Buy']:,.0f} x")
        c2.metric("F Sell", f"{m['F_Sell']:,.0f} x")
        c3.metric("Net Foreign", f"{m['Net_Foreign']:,.0f} x",
                  delta="Net Buy" if m["Net_Foreign"] > 0 else ("Net Sell" if m["Net_Foreign"] < 0 else "Flat"))
        st.plotly_chart(_stacked_bar("freq", "Frequency (x)"), use_container_width=True)
        st.markdown(
            f"<div style='text-align:center;color:#9ca3af;font-size:12px;'>"
            f"Foreign <b>{m['Foreign_Pct']:.2f}%</b> | Domestic <b>{m['Domestic_Pct']:.2f}%</b>"
            f"</div>",
            unsafe_allow_html=True,
        )

    return stats


def render_insight_box(df: pd.DataFrame, summ: pd.DataFrame, fd_stats: dict):
    """
    Kesimpulan / insight / saran ringan (bukan rekomendasi investasi).
    """
    if df.empty or summ.empty:
        return

    # VWAP (aproksimasi) & last price (berdasarkan waktu terbaru)
    total_val = float(df["Value"].sum())
    total_lot = float(df["Lot"].sum())
    vwap = (total_val / (total_lot * 100)) if total_lot else 0

    last_price = None
    if "DateTime" in df.columns and df["DateTime"].notna().any():
        last_row = df.sort_values("DateTime").dropna(subset=["DateTime"]).iloc[-1]
        last_price = int(last_row["Price"])
        last_time = str(last_row.get("Time_Str", ""))
    else:
        last_time = ""

    top_acc = summ.sort_values("Net_Val", ascending=False).head(1).iloc[0]
    top_dist = summ.sort_values("Net_Val", ascending=True).head(1).iloc[0]

    net_foreign_val = fd_stats["value"]["Net_Foreign"]
    foreign_pct_val = fd_stats["value"]["Foreign_Pct"]

    label = "Net Buy" if net_foreign_val > 0 else ("Net Sell" if net_foreign_val < 0 else "Netral")

    bullets = []
    bullets.append(f"Broker akumulasi terbesar: <b>{top_acc['Code']}</b> ({get_broker_info(top_acc['Code'])[1]}) "
                   f"dengan Net <b>Rp {format_number_label(top_acc['Net_Val'])}</b>.")
    bullets.append(f"Broker distribusi terbesar: <b>{top_dist['Code']}</b> ({get_broker_info(top_dist['Code'])[1]}) "
                   f"dengan Net <b>Rp {format_number_label(top_dist['Net_Val'])}</b>.")
    bullets.append(f"Asing (Foreign) dominasi <b>{foreign_pct_val:.2f}%</b> (berdasarkan value 2 sisi) "
                   f"dengan <b>{label}</b> sebesar <b>Rp {format_number_label(net_foreign_val)}</b>.")
    bullets.append(f"VWAP intraday (aproksimasi): <b>{vwap:,.0f}</b>.")
    if last_price is not None:
        bullets.append(f"Harga transaksi terakhir terbaca: <b>{last_price:,.0f}</b> (time: {last_time}).")

    # Saran ringan berbasis pola (non-advice)
    tips = []
    if net_foreign_val > 0:
        tips.append("Jika tujuan kamu tracking bandar: pantau apakah akumulasi asing berlanjut saat harga mendekati VWAP/area resistance.")
    elif net_foreign_val < 0:
        tips.append("Jika asing net sell, hati-hati false break; pantau apakah distribusi terjadi di area high dan volume melemah.")
    else:
        tips.append("Net foreign netral; fokus ke broker lokal/BUMN yang dominan dan pola di price table / trade book.")

    tips.append("Cocokkan total lot & total value dengan data sekuritas. Kalau beda jauh, biasanya karena file harian ter-split dan belum tergabung / kolom time gagal diparse.")

    html = "<ul style='margin-top:6px;'>" + "".join([f"<li style='margin-bottom:8px;'>{b}</li>" for b in bullets]) + "</ul>"
    html2 = "<ul style='margin-top:6px;'>" + "".join([f"<li style='margin-bottom:8px;'>{t}</li>" for t in tips]) + "</ul>"

    st.markdown(
        f"""
        <div class="insight-box">
            <h4 style="margin:0 0 8px 0;">Kesimpulan & Insight</h4>
            {html}
            <h4 style="margin:14px 0 8px 0;">Saran (non-financial advice)</h4>
            {html2}
            <div style="color:#9ca3af;font-size:11px;margin-top:10px;">
                *Catatan: insight ini berbasis data running trade yang kamu load, bukan rekomendasi investasi.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_running_trade_raw(df: pd.DataFrame):
    st.subheader("Running Trade")

    # ===== Filters =====
    c1, c2, c3, c4 = st.columns([1.2, 1.4, 2.2, 1.2])

    with c1:
        act_filter = st.selectbox("Action", ["All", "Buy", "Sell", "Unknown"], index=0)

    with c2:
        sort_order = st.selectbox("Urutan", ["Terbaru dulu", "Terlama dulu"], index=0)

    # Range waktu (pakai Time_Obj)
    min_t = None
    max_t = None
    if "Time_Obj" in df.columns and df["Time_Obj"].notna().any():
        min_t = df["Time_Obj"].dropna().min()
        max_t = df["Time_Obj"].dropna().max()

    with c3:
        if min_t and max_t:
            t_from, t_to = st.slider(
                "Filter waktu",
                min_value=min_t,
                max_value=max_t,
                value=(min_t, max_t),
                format="HH:mm:ss",
            )
        else:
            t_from, t_to = None, None
            st.caption("Filter waktu tidak aktif (kolom Time tidak terbaca)")

    with c4:
        max_rows = st.number_input("Max rows", min_value=50, max_value=5000, value=500, step=50)

    df_show = df.copy()

    if act_filter != "All":
        df_show = df_show[df_show["Action"] == act_filter]

    if t_from and t_to and "Time_Obj" in df_show.columns:
        df_show = df_show[df_show["Time_Obj"].between(t_from, t_to)]

    asc = True if sort_order == "Terlama dulu" else False
    # sort utama pakai DateTime, fallback Time_Str
    if "DateTime" in df_show.columns and df_show["DateTime"].notna().any():
        df_show = df_show.sort_values("DateTime", ascending=asc, na_position="last")
    else:
        df_show = df_show.sort_values("Time_Str", ascending=asc)

    st.caption(f"Menampilkan {min(len(df_show), int(max_rows)):,} dari {len(df_show):,} transaksi")

    cols = ["Time_Str", "Price", "Action", "Lot", "Buyer_Code", "Seller_Code"]
    cols = [c for c in cols if c in df_show.columns]

    st.dataframe(
        df_show[cols].head(int(max_rows)).style.format({
            "Price": "{:,.0f}",
            "Lot": "{:,.0f}",
        })
        .applymap(lambda x: "color:#22c55e" if x == "Buy" else ("color:#ef4444" if x == "Sell" else ""), subset=["Action"] if "Action" in cols else None)
        .applymap(style_broker_code, subset=[c for c in ["Buyer_Code", "Seller_Code"] if c in cols]),
        use_container_width=True,
        hide_index=True,
        height=520,
    )


def login_page():
    inject_custom_css()
    hide_sidebar()

    # agar input PIN numeric only
    components.html(
        """
        <script>
        const frame = window.parent.document;
        const inputs = frame.querySelectorAll('input[type="password"]');
        inputs.forEach(e => {
            e.setAttribute('inputmode','numeric');
            e.setAttribute('pattern','[0-9]*');
        });
        </script>
        """,
        height=0,
    )

    st.markdown("<br><br>", unsafe_allow_html=True)
    _, c2, _ = st.columns([1, 2.2, 1])

    with c2:
        st.markdown(
            """
            <div style="
                background: radial-gradient(circle at top left, #1f2937, #020617);
                padding: 32px 32px 26px 32px;
                border-radius: 18px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.75);
                text-align: center;">
                <div style="font-size:44px;margin-bottom:8px;">🦅</div>
                <h2 style="margin-bottom:4px;">SECURE ACCESS</h2>
                <p style="font-size:14px;color:#9ca3af;margin-bottom:12px;">
                    Masukkan PIN rahasia untuk membuka fitur Bandarmology Pro.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("")
        with st.form("login_form"):
            pin = st.text_input(
                "PIN",
                type="password",
                max_chars=6,
                placeholder="0 0 0 0 0 0",
            )
            submitted = st.form_submit_button("UNLOCK")

        if submitted:
            if pin == "241130":
                st.session_state["authenticated"] = True
                st.session_state["df_raw"] = None
                st.session_state["current_stock"] = "UNKNOWN"
                show_sidebar()
                st.rerun()
            else:
                st.error("PIN salah, coba lagi.")

    render_footer()

# =========================================================
# 9. HALAMAN UTAMA (BANDARMOLOGY)
# =========================================================
def bandarmology_page():
    DB_ROOT = "database"

    df_raw = st.session_state.get("df_raw")
    current_stock = st.session_state.get("current_stock", "UNKNOWN")

    # --------- SIDEBAR: Sumber Data ---------
    with st.sidebar:
        st.markdown(get_stock_ticker(), unsafe_allow_html=True) # Ticker restored
        st.markdown("### 📂 Sumber Data")
        source_type = st.radio(
            "Sumber Data",
            ["Database Folder", "Upload Manual"],
            index=0,
            key="source_type_main",
        )

        if source_type == "Database Folder":
            if os.path.exists(DB_ROOT):
                stocks = sorted([
                    d for d in os.listdir(DB_ROOT) if os.path.isdir(os.path.join(DB_ROOT, d))
                ])
                sel_stock = st.selectbox("Saham", stocks) if stocks else None

                if not sel_stock:
                    st.info("Tidak ada folder saham di database.")
                else:
                    default_date = st.session_state.get("selected_date")
                    if default_date is None:
                        default_date = datetime.date.today()

                    try:
                        sel_date = st.date_input(
                            "Tanggal",
                            value=default_date,
                            format="DD/MM/YYYY",
                            key="db_date",
                        )
                    except TypeError:
                        sel_date = st.date_input("Tanggal", value=default_date, key="db_date")

                    st.session_state["selected_date"] = sel_date

                    load_btn = st.button("Load Data", use_container_width=True)
                    if load_btn:
                        fps = resolve_database_files(DB_ROOT, sel_stock, sel_date)
                        if not fps:
                            st.warning("Data tidak tersedia untuk tanggal tersebut.")
                        else:
                            try:
                                df_raw = load_database_files(fps)
                                if df_raw.empty:
                                    st.error("File ditemukan, tapi gagal dibaca. Cek format CSV/XLSX.")
                                else:
                                    current_stock = sel_stock
                                    st.session_state["df_raw"] = df_raw
                                    st.session_state["current_stock"] = current_stock
                                    # Debug / transparansi: file apa saja yang kebaca
                                    with st.expander("Detail file yang ter-load", expanded=False):
                                        st.write("Jumlah file:", len(fps))
                                        st.write("Daftar file:")
                                        for p in fps:
                                            st.code(p)
                                        st.write("Jumlah baris (raw):", len(df_raw))
                                    st.toast(f"Data {sel_stock} dimuat ({len(fps)} file).", icon="✅")
                            except Exception:
                                st.error("Gagal load data, cek file-nya.")
            else:
                st.warning(f"Folder database '{DB_ROOT}' belum dibuat.")
        else:
            uploaded = st.file_uploader(
                "Upload File Running Trade",
                type=["csv", "xlsx"],
                key="upload_file",
            )
            if uploaded:
                try:
                    if uploaded.name.endswith("csv"):
                        df_raw = pd.read_csv(uploaded)
                    else:
                        df_raw = pd.read_excel(uploaded)
                    current_stock = "UPLOADED"
                    st.session_state["df_raw"] = df_raw
                    st.session_state["current_stock"] = current_stock
                except Exception:
                    st.error("File tidak dapat dibaca, cek formatnya.")


        st.markdown("### ⚙️ Pengaturan Nilai")
        volume_mode_ui = st.selectbox(
            "Satuan Volume di file",
            ["Auto", "Lot (1 lot = 100 saham)", "Shares (lembar saham)"],
            index=0,
            key="volume_mode",
        )
        st.caption("Kalau nilai transaksi jadi terlalu besar/kecil, ubah opsi ini lalu refresh analisis.")

    # --------- MAIN CONTENT ---------
    if df_raw is None:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            """
            <div style="
                background-color:#020617;
                padding:40px 30px;
                border-radius:18px;
                margin:0 4%;
                border:1px dashed #283548;
                text-align:center;
                box-shadow:0 18px 45px rgba(0,0,0,0.65);">
                <h2 style="margin-bottom:6px;">Belum ada data yang dipilih 📁</h2>
                <p style="color:#9ca3af;font-size:14px;">
                    Pilih sumber data dan file running trade di sidebar untuk mulai analisis bandarmology saham kamu.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    try:
        # Data Cleaning & Processing
        df = clean_running_trade(df_raw, trade_date=st.session_state.get('selected_date'), volume_mode=st.session_state.get("volume_mode","Auto"))
        summ = get_detailed_broker_summary(df)

        st.title(f"📊 Bandarmology {current_stock}")

        # Metrics Top
        col1, col2, col3, col4 = st.columns(4)
        tot_val = df["Value"].sum()
        col1.metric("Total Transaksi", f"Rp {format_number_label(tot_val)}")
        col2.metric("Total Volume", f"{format_lot_label(df['Lot'].sum())} Lot")
        col3.metric("Frequency", f"{format_freq_label(len(df))} x")

        foreign_net = summ[summ["Group"] == "Asing"]["Net_Val"].sum()
        col4.metric("Net Foreign", f"Rp {format_number_label(foreign_net)}", delta_color="normal" if foreign_net==0 else ("inverse" if foreign_net < 0 else "normal"))

        st.markdown("---")

        # Foreign–Domestic Activity (mirip sekuritas)
        fd_stats = render_foreign_domestic_activity(df)

        # Kesimpulan / Insight
        render_insight_box(df, summ, fd_stats)

        # Broker Action Meter
        render_broker_action_meter(summ)
        st.write("")

        # Broker Summary Split (Modified)
        net_mode = st.toggle("Net Mode (Show Net Buy/Sell)", value=True)
        render_broker_summary_split(summ, net_mode)

        st.markdown("---")
        
        # Trade Book (Chart & Price)
        render_trade_book(df)
        
        st.markdown("---")
        
        # Running Trade Filtered
        render_running_trade_raw(df)
        
        st.markdown("---")

        st.subheader("🕸️ Broker Flow (Sankey)")
        left, right = st.columns([2, 1])
        with left:
            metric_choice = st.radio(
                "Metrik",
                ["Value (Dana)", "Lot (Volume)"],
                horizontal=True,
            )
        with right:
            top_n = st.slider("Jumlah interaksi", 5, 50, 15)

        metric_col = "Value" if "Value" in metric_choice else "Lot"

        try:
            labels, node_colors, src, tgt, vals, link_colors = build_sankey(
                df, top_n=top_n, metric=metric_col
            )
            fig = go.Figure(
                data=[
                    go.Sankey(
                        node=dict(
                            pad=20,
                            thickness=18,
                            line=dict(color="black", width=0.3),
                            label=labels,
                            color=node_colors,
                        ),
                        link=dict(
                            source=src,
                            target=tgt,
                            value=vals,
                            color=link_colors,
                        ),
                    )
                ]
            )
            fig.update_layout(
                height=600,
                margin=dict(l=10, r=10, t=10, b=10),
                font=dict(size=12, color="#e5e7eb"),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown(
                """
                <div style="text-align:center;margin-top:-10px;">
                    <span class="tag tag-Asing">Asing</span>
                    <span class="tag tag-BUMN">BUMN</span>
                    <span class="tag tag-Lokal">Lokal</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        except Exception as e:
            st.warning(f"Error pada visual Sankey: {e}")

    except Exception as e:
        st.error(f"Error saat memproses data: {e}")

# =========================================================
# 10. PAGE BARU: DAFTAR BROKER (ALFABET, FILTER & SEARCH)
# =========================================================
def daftar_broker_page():
    st.title("📚 Daftar Broker / Sekuritas")

    rows = []
    for code, name in BROKER_NAMES.items():
        group = get_broker_group(code)
        rows.append({"Code": code, "Sekuritas": name, "Kategori": group})
    df = pd.DataFrame(rows)

    col1, col2 = st.columns([2, 1])
    with col1:
        search = st.text_input(
            "Cari broker (kode / nama sekuritas)",
            key="search_broker",
            placeholder="Contoh: CC, Mandiri, Mirae ..."
        )
    with col2:
        kategori = st.radio(
            "Filter kategori",
            ["Semua", "Asing", "BUMN", "Lokal"],
            horizontal=True,
            key="kategori_broker",
        )

    df_filtered = df.copy()

    if kategori != "Semua":
        df_filtered = df_filtered[df_filtered["Kategori"] == kategori]

    if search:
        q = search.strip().lower()
        df_filtered = df_filtered[
            df_filtered["Code"].str.contains(q, case=False)
            | df_filtered["Sekuritas"].str.lower().str.contains(q)
        ]

    sort_by = st.selectbox(
        "Urutkan berdasarkan",
        ["Kode Broker", "Nama Sekuritas"],
        index=0,
        key="sort_broker",
    )

    if sort_by == "Kode Broker":
        df_filtered = df_filtered.sort_values("Code")
    else:
        df_filtered = df_filtered.sort_values("Sekuritas")

    if df_filtered.empty:
        st.info("Tidak ada broker yang cocok dengan filter.")
    else:
        st.dataframe(
            df_filtered.reset_index(drop=True).style.applymap(
                style_broker_code, subset=["Code"]
            ),
            use_container_width=True,
            height=600,
        )

# =========================================================
# 11. PAGE BARU: DAFTAR SAHAM INDONESIA (BERDASARKAN EXCEL)
# =========================================================
@st.cache_data
def load_daftar_saham():
    fname = "Daftar Saham.xlsx"
    if os.path.exists(fname):
        return pd.read_excel(fname)
    raise FileNotFoundError(
        "File 'Daftar Saham.xlsx' tidak ditemukan di folder aplikasi."
    )


def daftar_saham_page():
    st.title("📄 Daftar Saham Indonesia")

    try:
        df = load_daftar_saham()
    except Exception as e:
        st.error(f"Gagal memuat file daftar saham: {e}")
        st.info(
            "Letakkan file **'Daftar Saham.xlsx'** di folder yang sama dengan script Streamlit ini."
        )
        return

    # Rapikan kolom
    if "No" in df.columns:
        df = df.drop(columns=["No"])

    rename_map = {
        "Kode": "Kode",
        "Nama Perusahaan": "Nama Perusahaan",
        "Tanggal Pencatatan": "Tanggal Pencatatan",
        "Saham": "Saham",
        "Papan Pencatatan": "Papan Pencatatan",
    }
    df = df.rename(columns=rename_map)

    if "Tanggal Pencatatan" in df.columns:
        df["Tanggal Pencatatan"] = pd.to_datetime(
            df["Tanggal Pencatatan"], errors="ignore"
        )

    col1, col2 = st.columns([2, 1])
    with col1:
        search = st.text_input(
            "Cari saham (kode / nama perusahaan)",
            key="search_saham",
            placeholder="Contoh: BBRI, BANK RAKYAT ..."
        )
    with col2:
        if "Papan Pencatatan" in df.columns:
            papan_list = (
                ["Semua"]
                + sorted(
                    df["Papan Pencatatan"]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()
                )
            )
            papan = st.selectbox(
                "Papan Pencatatan",
                papan_list,
                key="papan_saham",
            )
        else:
            papan = "Semua"

    df_filtered = df.copy()

    if papan != "Semua" and "Papan Pencatatan" in df_filtered.columns:
        df_filtered = df_filtered[
            df_filtered["Papan Pencatatan"].astype(str) == papan
        ]

    if search:
        q = search.strip().lower()
        df_filtered = df_filtered[
            df_filtered["Kode"].astype(str).str.contains(q, case=False)
            | df_filtered["Nama Perusahaan"]
            .astype(str)
            .str.lower()
            .str.contains(q)
        ]

    if "Kode" in df_filtered.columns:
        df_filtered = df_filtered.sort_values("Kode")

    st.dataframe(
        df_filtered.reset_index(drop=True),
        use_container_width=True,
        height=600,
    )

# =========================================================
# 12. MAIN ROUTER
# =========================================================
def main():
    if not st.session_state["authenticated"]:
        login_page()
        return

    inject_custom_css()
    show_sidebar()

    with st.sidebar:
        st.title("🦅 Bandarmology")
        st.caption("Bandarmology Pro Dashboard")
        st.markdown("---")
        page = st.radio(
            "Menu",
            ["Bandarmology", "Daftar Broker", "Daftar Saham"],
            index=0,
            key="main_menu",
        )
        st.markdown("---")
        if st.button("Logout", use_container_width=True, key="logout_btn"):
            st.session_state["authenticated"] = False
            st.session_state["df_raw"] = None
            st.session_state["current_stock"] = "UNKNOWN"
            st.rerun()

    if page == "Bandarmology":
        bandarmology_page()
    elif page == "Daftar Broker":
        daftar_broker_page()
    else:
        daftar_saham_page()

    render_footer()


if __name__ == "__main__":
    main()
