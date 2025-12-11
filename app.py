import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import os
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
# --- NAMA BROKER (lengkap 95 kode + beberapa tambahan) ---
BROKER_NAMES = {
    # Top broker list (95 dari tabel kamu)
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

    # Tambahan kode yang tidak muncul di tabel 95 tapi ada di sistem
    "CG": "Citigroup Sekuritas Indonesia",
    "CS": "Credit Suisse Sekuritas Indonesia",
    "DK": "KAF Sekuritas Indonesia",  # kode lama/alternatif
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
    abs_val = abs(value)
    if abs_val >= 1e12:
        return f"{value/1e12:.2f}T"
    if abs_val >= 1e9:
        return f"{value/1e9:.2f}M"
    if abs_val >= 1e6:
        return f"{value/1e6:.2f}Jt"
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
# 6. DATA PROCESSING
# =========================================================
def clean_running_trade(df_input):
    df = df_input.copy()
    df.columns = df.columns.str.strip().str.capitalize()

    rename_map = {
        "Time": "Time",
        "Waktu": "Time",
        "Price": "Price",
        "Harga": "Price",
        "Lot": "Lot",
        "Vol": "Lot",
        "Volume": "Lot",
        "Buyer": "Buyer",
        "B": "Buyer",
        "Broker Beli": "Buyer",
        "Seller": "Seller",
        "S": "Seller",
        "Broker Jual": "Seller",
    }
    new_cols = {c: rename_map[c] for c in df.columns if c in rename_map}
    df.rename(columns=new_cols, inplace=True)

    if not {"Price", "Lot", "Buyer", "Seller"}.issubset(df.columns):
        raise ValueError("Kolom Wajib (Price, Lot, Buyer, Seller) tidak lengkap.")

    def clean_num(x):
        return int(re.sub(r"[^\d]", "", str(x).split("(")[0])) if pd.notnull(x) else 0

    def clean_code(x):
        return str(x).upper().split()[0].strip()

    try:
        df["Price_Clean"] = df["Price"].apply(clean_num)
        df["Lot_Clean"] = df["Lot"].apply(clean_num)
        df["Buyer_Code"] = df["Buyer"].apply(clean_code)
        df["Seller_Code"] = df["Seller"].apply(clean_code)
        df["Value"] = df["Lot_Clean"] * 100 * df["Price_Clean"]
        return df[df["Value"] > 0]
    except Exception as e:
        raise ValueError(f"Parsing Error: {e}")


def get_broker_summary(df):
    buy = (
        df.groupby("Buyer_Code")
        .agg({"Value": "sum", "Lot_Clean": "sum"})
        .rename(columns={"Value": "Buy_Val", "Lot_Clean": "Buy_Vol"})
    )
    sell = (
        df.groupby("Seller_Code")
        .agg({"Value": "sum", "Lot_Clean": "sum"})
        .rename(columns={"Value": "Sell_Val", "Lot_Clean": "Sell_Vol"})
    )

    summ = pd.merge(buy, sell, left_index=True, right_index=True, how="outer").fillna(0)
    summ["Net_Val"] = summ["Buy_Val"] - summ["Sell_Val"]
    summ["Total_Val"] = summ["Buy_Val"] + summ["Sell_Val"]

    summ.index.name = "Code"
    summ = summ.reset_index()
    summ["Name"] = summ["Code"].apply(lambda x: get_broker_info(x)[1])
    summ["Group"] = summ["Code"].apply(lambda x: get_broker_info(x)[2])

    return summ.sort_values("Net_Val", ascending=False)


def build_sankey(df, top_n=15, metric="Value"):
    flow = df.groupby(["Buyer_Code", "Seller_Code"])[metric].sum().reset_index()
    flow = flow.sort_values(metric, ascending=False).head(top_n)

    flow["B_Label"] = flow["Buyer_Code"] + " (B)"
    flow["S_Label"] = flow["Seller_Code"] + " (S)"
    all_nodes = list(set(flow["B_Label"]).union(set(flow["S_Label"])))
    node_map = {k: v for v, k in enumerate(all_nodes)}

    b_totals = flow.groupby("B_Label")[metric].sum()
    s_totals = flow.groupby("S_Label")[metric].sum()

    labels, colors = [], []
    for node in all_nodes:
        code = node.split()[0]
        group = get_broker_group(code)
        color = COLOR_MAP.get(group, COLOR_MAP["Unknown"])
        val = b_totals[node] if node in b_totals else s_totals.get(node, 0)
        labels.append(f"{code} {format_number_label(val)}")
        colors.append(color)

    src = [node_map[x] for x in flow["B_Label"]]
    tgt = [node_map[x] for x in flow["S_Label"]]
    vals = flow[metric].tolist()

    link_colors = []
    for s_idx in src:
        c_hex = colors[s_idx].lstrip("#")
        rgb = tuple(int(c_hex[i: i + 2], 16) for i in (0, 2, 4))
        link_colors.append(f"rgba({rgb[0]},{rgb[1]},{rgb[2]},0.55)")

    return labels, colors, src, tgt, vals, link_colors


def generate_smart_insight(summary_df: pd.DataFrame, stock_code: str = "") -> str:
    """
    Menghasilkan teks 'Kesimpulan' dalam bentuk HTML (judul bold, tanpa ##).
    """
    if summary_df is None or summary_df.empty:
        return "<strong>🧾 Kesimpulan</strong><p>Data broker belum tersedia.</p>"

    sorted_df = summary_df.sort_values("Net_Val", ascending=False)
    top_buyer = sorted_df.iloc[0]
    top_seller = sorted_df.iloc[-1]

    total_val = summary_df["Total_Val"].sum()
    foreign_val = summary_df[summary_df["Group"] == "Asing"]["Total_Val"].sum()
    bumn_val = summary_df[summary_df["Group"] == "BUMN"]["Total_Val"].sum()
    lokal_val = summary_df[summary_df["Group"] == "Lokal"]["Total_Val"].sum()

    def pct(v):
        return (v / total_val * 100) if total_val > 0 else 0.0

    foreign_pct = pct(foreign_val)
    bumn_pct = pct(bumn_val)
    lokal_pct = pct(lokal_val)

    if top_buyer["Net_Val"] > (abs(top_seller["Net_Val"]) * 1.1):
        headline = "AKUMULASI — tekanan beli masih dominan."
    elif abs(top_seller["Net_Val"]) > (top_buyer["Net_Val"] * 1.1):
        headline = "DISTRIBUSI — tekanan jual lebih kuat."
    else:
        headline = "NETRAL — tarik-menarik beli dan jual relatif seimbang."

    stock_label = f" {stock_code}" if stock_code else ""

    return f"""
    <strong>🧾 Kesimpulan{stock_label}</strong>
    <p><strong>Sinyal utama:</strong> {headline}</p>
    <ul>
        <li>Porsi nilai transaksi asing sekitar <strong>{foreign_pct:.1f}%</strong>, 
            BUMN <strong>{bumn_pct:.1f}%</strong>, dan lokal <strong>{lokal_pct:.1f}%</strong> 
            dari total transaksi hari ini.</li>
        <li>Broker dengan akumulasi terbesar adalah 
            <strong>{top_buyer['Code']} ({top_buyer['Group']})</strong> dengan net buy sekitar 
            <strong>Rp {format_number_label(top_buyer['Net_Val'])}</strong>.</li>
        <li>Tekanan jual terbesar datang dari 
            <strong>{top_seller['Code']} ({top_seller['Group']})</strong> dengan net sell sekitar 
            <strong>Rp {format_number_label(abs(top_seller['Net_Val']))}</strong>.</li>
    </ul>
    <p>Untuk investor ritel, amati apakah pola akumulasi atau distribusi ini konsisten dalam beberapa sesi ke depan.
    Pergerakan besar dari broker asing maupun BUMN sering menjadi sinyal awal perubahan tren harga,
    sehingga bisa dijadikan pertimbangan untuk timing masuk/keluar posisi.</p>
    """

# =========================================================
# 7. HALAMAN LOGIN (PIN TANPA SIDEBAR)
# =========================================================
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
    c1, c2, c3 = st.columns([1, 2.2, 1])

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
# 8. HALAMAN UTAMA (BANDARMOLOGY)
# =========================================================
def bandarmology_page():
    DB_ROOT = "database"

    df_raw = st.session_state.get("df_raw")
    current_stock = st.session_state.get("current_stock", "UNKNOWN")

    # --------- SIDEBAR: Sumber Data ---------
    with st.sidebar:
        st.markdown("### 📂 Sumber Data")
        source_type = st.radio(
            "Sumber Data",
            ["Database Folder", "Upload Manual"],
            index=0,
            key="source_type_main",
        )

        if source_type == "Database Folder":
            if os.path.exists(DB_ROOT):
                stocks = sorted(
                    [
                        d
                        for d in os.listdir(DB_ROOT)
                        if os.path.isdir(os.path.join(DB_ROOT, d))
                    ]
                )
                sel_stock = st.selectbox("Saham", stocks, key="stock_sel") if stocks else None
                if sel_stock:
                    p_stock = os.path.join(DB_ROOT, sel_stock)
                    years = sorted(os.listdir(p_stock))
                    sel_year = st.selectbox("Tahun", years, key="year_sel") if years else None
                    if sel_year:
                        p_year = os.path.join(DB_ROOT, sel_year)
                        months = sorted(os.listdir(p_year))
                        sel_month = (
                            st.selectbox("Bulan", months, key="month_sel") if months else None
                        )
                        if sel_month:
                            p_month = os.path.join(p_year, sel_month)
                            files = sorted(
                                [
                                    f
                                    for f in os.listdir(p_month)
                                    if f.endswith(("csv", "xlsx"))
                                ]
                            )
                            sel_file = st.selectbox(
                                "Tanggal", files, key="file_sel"
                            ) if files else None
                            load_btn = st.button(
                                "Load Data", use_container_width=True, key="load_btn"
                            )
                            if sel_file and load_btn:
                                fp = os.path.join(p_month, sel_file)
                                try:
                                    if fp.endswith("csv"):
                                        df_raw = pd.read_csv(fp)
                                    else:
                                        df_raw = pd.read_excel(fp)
                                    current_stock = sel_stock
                                    st.session_state["df_raw"] = df_raw
                                    st.session_state["current_stock"] = current_stock
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
        df = clean_running_trade(df_raw)
        summ = get_broker_summary(df)

        st.title(f"📊 Bandarmology {current_stock}")

        col1, col2, col3 = st.columns(3)
        tot_val = df["Value"].sum()
        col1.metric("Total Transaksi", f"Rp {format_number_label(tot_val)}")
        col2.metric("Total Volume", f"{df['Lot_Clean'].sum():,} Lot")

        foreign_val = summ[summ["Group"] == "Asing"]["Total_Val"].sum()
        share_foreign = foreign_val / (tot_val * 2) * 100 if tot_val > 0 else 0
        col3.metric("Porsi Asing", f"{share_foreign:.1f}%")

        st.markdown("---")

        # --- TOP BROKER TABLE ---
        st.subheader("🏆 Top Broker")

        tabs = st.tabs(["Semua", "Asing", "BUMN", "Lokal"])
        group_labels = ["ALL", "Asing", "BUMN", "Lokal"]

        for tab, g in zip(tabs, group_labels):
            with tab:
                if g == "ALL":
                    df_show = summ.copy()
                else:
                    df_show = summ[summ["Group"] == g].copy()

                if df_show.empty:
                    st.info("Belum ada broker di kategori ini.")
                else:
                    st.dataframe(
                        df_show[
                            ["Code", "Name", "Group", "Total_Val", "Net_Val"]
                        ]
                        .sort_values("Total_Val", ascending=False)
                        .style.format(
                            {
                                "Total_Val": format_number_label,
                                "Net_Val": format_number_label,
                            }
                        )
                        .applymap(style_broker_code, subset=["Code"]),
                        use_container_width=True,
                        height=360,
                    )

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

        metric_col = "Value" if "Value" in metric_choice else "Lot_Clean"

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

            st.markdown(
                f"<div class='insight-box'>{generate_smart_insight(summ, current_stock)}</div>",
                unsafe_allow_html=True,
            )
        except Exception as e:
            st.warning(f"Error pada visual Sankey: {e}")

    except Exception as e:
        st.error(f"Error saat memproses data: {e}")

# =========================================================
# 9. PAGE BARU: DAFTAR BROKER (ALFABET, FILTER & SEARCH)
# =========================================================
def daftar_broker_page():
    st.title("📚 Daftar Broker / Sekuritas")

    # Siapkan DataFrame master broker
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
# 10. PAGE BARU: DAFTAR SAHAM INDONESIA (BERDASARKAN EXCEL)
# =========================================================
@st.cache_data
def load_daftar_saham():
    """
    Load file daftar saham.
    Pastikan file 'Daftar Saham.xlsx' ada di folder yang sama dengan app.
    Kalau namanya berbeda, silakan sesuaikan di sini.
    """
    candidates = [
        "Daftar Saham  - 20251211.xlsx",
        "Daftar Saham-20251211.xlsx",
        "Daftar Saham.xlsx",
    ]
    for fname in candidates:
        if os.path.exists(fname):
            return pd.read_excel(fname)
    raise FileNotFoundError(
        "File 'Daftar Saham  - 20251211.xlsx' tidak ditemukan di folder aplikasi."
    )


def daftar_saham_page():
    st.title("📄 Daftar Saham Indonesia")

    try:
        df = load_daftar_saham()
    except Exception as e:
        st.error(f"Gagal memuat file daftar saham: {e}")
        st.info(
            "Letakkan file **'Daftar Saham  - 20251211.xlsx'** di folder yang sama dengan script Streamlit ini."
        )
        return

    # Rapikan kolom
    if "No" in df.columns:
        df = df.drop(columns=["No"])

    # Pastikan nama kolom standar
    rename_map = {
        "Kode": "Kode",
        "Nama Perusahaan": "Nama Perusahaan",
        "Tanggal Pencatatan": "Tanggal Pencatatan",
        "Saham": "Saham",
        "Papan Pencatatan": "Papan Pencatatan",
    }
    df = df.rename(columns=rename_map)

    # Parsing tanggal kalau bisa
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

    # Urut abjad berdasarkan kode
    if "Kode" in df_filtered.columns:
        df_filtered = df_filtered.sort_values("Kode")

    st.dataframe(
        df_filtered.reset_index(drop=True),
        use_container_width=True,
        height=600,
    )

# =========================================================
# 11. MAIN ROUTER
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
