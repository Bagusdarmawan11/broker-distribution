import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import os
import requests
import streamlit.components.v1 as components

# ==========================================
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(
    page_title="Bandarmology Pro",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DATABASE BROKER (MAPPING) ---
BROKER_DB = {
    # ASING (FOREIGN) - HIJAU
    'AK': {'name': 'UBS Sekuritas', 'type': 'Foreign'},
    'BK': {'name': 'J.P. Morgan', 'type': 'Foreign'},
    'ZP': {'name': 'Maybank Sekuritas', 'type': 'Foreign'},
    'YU': {'name': 'CGS International', 'type': 'Foreign'},
    'KZ': {'name': 'CLSA Sekuritas', 'type': 'Foreign'},
    'RX': {'name': 'Macquarie', 'type': 'Foreign'},
    'AI': {'name': 'UOB Kay Hian', 'type': 'Foreign'},
    'CG': {'name': 'Citigroup', 'type': 'Foreign'},
    'CS': {'name': 'Credit Suisse', 'type': 'Foreign'},
    'MS': {'name': 'Morgan Stanley', 'type': 'Foreign'},
    'GW': {'name': 'HSBC Sekuritas', 'type': 'Foreign'},
    'AG': {'name': 'Kiwoom Sekuritas', 'type': 'Foreign'},
    'BQ': {'name': 'Korea Investment', 'type': 'Foreign'},

    # BUMN (STATE OWNED) - KUNING/ORANGE
    'CC': {'name': 'Mandiri Sekuritas', 'type': 'BUMN'},
    'NI': {'name': 'BNI Sekuritas', 'type': 'BUMN'},
    'OD': {'name': 'BRI Danareksa', 'type': 'BUMN'},
    'DX': {'name': 'Bahana Sekuritas', 'type': 'BUMN'},

    # LOKAL (DOMESTIC) - UNGU/ABU
    'YP': {'name': 'Mirae Asset', 'type': 'Local'},
    'PD': {'name': 'Indo Premier', 'type': 'Local'},
    'XL': {'name': 'Stockbit', 'type': 'Local'},
    'XC': {'name': 'Ajaib', 'type': 'Local'},
    'MG': {'name': 'Semesta Indovest', 'type': 'Local'},
    'SQ': {'name': 'BCA Sekuritas', 'type': 'Local'},
    'LG': {'name': 'Trimegah', 'type': 'Local'},
    'EP': {'name': 'MNC Sekuritas', 'type': 'Local'},
    'KK': {'name': 'Phillip Sekuritas', 'type': 'Local'},
    'DR': {'name': 'RHB Sekuritas', 'type': 'Local'},
    'GR': {'name': 'Panin Sekuritas', 'type': 'Local'},
    'AZ': {'name': 'Sucor Sekuritas', 'type': 'Local'},
    'BB': {'name': 'Verdhana', 'type': 'Local'},
    'IF': {'name': 'Samuel Sekuritas', 'type': 'Local'},
    'YJ': {'name': 'Lotus Andalan', 'type': 'Local'},
    'LS': {'name': 'Reliance', 'type': 'Local'},
    'CP': {'name': 'KB Valbury', 'type': 'Local'},
    'RF': {'name': 'Buana Capital', 'type': 'Local'},
    'HP': {'name': 'Henan Putihrai', 'type': 'Local'},
    'DH': {'name': 'Sinarmas Sekuritas', 'type': 'Local'},
    'IT': {'name': 'Inti Teladan', 'type': 'Local'},
    'ID': {'name': 'Anugerah Sekuritas', 'type': 'Local'},
}

COLOR_MAP = {
    'Foreign': '#00E396',
    'BUMN': '#FEB019',
    'Local': '#775DD0',
    'Unknown': '#546E7A'
}

if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'dark_mode' not in st.session_state:
    st.session_state['dark_mode'] = True


# ==========================================
# 2. HELPER & STYLING (FIX UI/UX TOTAL)
# ==========================================

def get_broker_info(code):
    code = str(code).upper().strip()
    data = BROKER_DB.get(code, {'name': 'Sekuritas Lain', 'type': 'Unknown'})
    return code, data['name'], data['type']


def format_number_label(value):
    abs_val = abs(value)
    if abs_val >= 1e12:
        return f"{value/1e12:.2f}T"
    if abs_val >= 1e9:
        return f"{value/1e9:.2f}M"
    if abs_val >= 1e6:
        return f"{value/1e6:.2f}Jt"
    return f"{value:,.0f}"


def inject_custom_css(is_dark_mode: bool) -> None:
    """
    Styling custom:
    - Light mode benar-benar terang (header hitam default dihilangkan)
    - Login & konten utama pakai card yang rapi
    """
    if is_dark_mode:
        bg_color = "#0e1117"
        sidebar_bg = "#262730"
        text_color = "#FFFFFF"
        card_bg = "#1E1E1E"
        border_color = "#444444"

        input_bg = "#262730"
        input_border = "#555555"

        shadow = "rgba(0,0,0,0.5)"
        btn_hover = "#ff4b4b"
    else:
        bg_color = "#FFFFFF"
        sidebar_bg = "#F8F9FA"
        text_color = "#000000"
        card_bg = "#FFFFFF"
        border_color = "#D1D1D1"

        input_bg = "#FFFFFF"
        input_border = "#000000"

        shadow = "rgba(0,0,0,0.12)"
        btn_hover = "#ff4b4b"

    st.markdown(
        f"""
        <style>
        /* ========== GLOBAL LAYOUT ========== */
        .stApp {{
            background-color: {bg_color};
            color: {text_color};
        }}

        [data-testid="stAppViewContainer"] {{
            background-color: {bg_color};
        }}
        [data-testid="stHeader"] {{
            background-color: {bg_color};
            color: {text_color};
        }}

        [data-testid="stAppViewContainer"] .block-container {{
            padding-top: 2.5rem;
            padding-bottom: 4.5rem;
        }}

        /* SIDEBAR */
        [data-testid="stSidebar"] {{
            background-color: {sidebar_bg} !important;
            border-right: 1px solid {border_color};
        }}
        [data-testid="stSidebar"] * {{
            color: {text_color} !important;
        }}

        /* TIPOGRAFI */
        h1, h2, h3, h4, h5, h6,
        p, li, span, label, div, .stMarkdown, .stText {{
            color: {text_color} !important;
        }}

        a {{
            color: #4c8df5 !important;
        }}
        a:hover {{
            text-decoration: underline;
        }}

        /* CARD GENERIC */
        .app-card {{
            background-color: {card_bg};
            border-radius: 18px;
            padding: 24px 28px;
            border: 1px solid {border_color};
            box-shadow: 0 10px 30px {shadow};
        }}
        .app-card--center {{
            max-width: 520px;
            margin: 0 auto;
        }}

        .page-header {{
            margin-bottom: 1.25rem;
        }}
        .page-header h1 {{
            font-size: 1.7rem;
            margin-bottom: 0.2rem;
        }}
        .page-header p {{
            opacity: 0.75;
            font-size: 0.9rem;
        }}

        /* INPUT PIN */
        .stTextInput input {{
            text-align: center;
            font-size: 32px !important;
            letter-spacing: 10px;
            font-weight: bold;
            padding: 14px 18px;
            border-radius: 12px;

            background-color: {input_bg} !important;
            color: {text_color} !important;
            border: 2px solid {input_border} !important;

            box-shadow: 0 4px 10px {shadow};
            transition: all 0.25s ease;
        }}
        .stTextInput input::placeholder {{
            color: rgba(128,128,128,0.8) !important;
        }}
        .stTextInput input:focus {{
            border-color: #ff4b4b !important;
            outline: none;
            box-shadow: 0 0 8px rgba(255, 75, 75, 0.45);
        }}

        /* SELECTBOX */
        div[data-baseweb="select"] > div {{
            background-color: {input_bg} !important;
            color: {text_color} !important;
            border-color: {input_border} !important;
            border-radius: 12px;
            min-height: 42px;
        }}
        div[data-baseweb="select"] span {{
            color: {text_color} !important;
        }}
        ul[data-baseweb="menu"] {{
            background-color: {card_bg} !important;
            border-radius: 10px;
        }}
        li[data-baseweb="option"] {{
            color: {text_color} !important;
        }}

        /* BUTTON */
        .stButton button {{
            width: 100%;
            height: 46px;
            font-size: 15px;
            font-weight: 600;
            border-radius: 10px;
            border: 1px solid {border_color};
            background-color: {input_bg} !important;
            color: {text_color} !important;
            transition: all 0.2s;
        }}
        .stButton button:hover {{
            border-color: {btn_hover};
            color: {btn_hover} !important;
            background-color: rgba(255, 75, 75, 0.12) !important;
        }}

        /* METRIC CARD */
        [data-testid="stMetric"] {{
            background-color: {card_bg};
            padding: 12px 16px;
            border-radius: 14px;
            border: 1px solid {border_color};
            box-shadow: 0 3px 10px {shadow};
        }}

        /* TABEL */
        .stDataFrame, .stTable {{
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid {border_color};
        }}

        /* NOTIFICATION (st.info/dll) */
        [data-testid="stNotification"] > div{{
            background-color: {card_bg} !important;
            border-radius: 12px;
            border: 1px solid {border_color};
            box-shadow: 0 3px 10px {shadow};
        }}

        /* EMPTY STATE */
        .empty-state {{
            background-color: {card_bg};
            border-radius: 18px;
            border: 1px dashed {border_color};
            padding: 32px 30px;
            text-align: center;
            margin-top: 2rem;
            box-shadow: 0 6px 18px {shadow};
        }}
        .empty-state h2 {{
            margin-bottom: 0.4rem;
        }}
        .empty-state p {{
            font-size: 0.92rem;
            opacity: 0.8;
        }}

        /* TICKER */
        .ticker-wrap {{
            width: 100%;
            background-color: {card_bg};
            padding: 8px 0;
            border-bottom: 1px solid {border_color};
            position: sticky;
            top: 0;
            z-index: 20;
            box-shadow: 0 2px 5px {shadow};
        }}
        .ticker-item {{
            margin: 0 20px;
            font-weight: bold;
            font-family: monospace;
            font-size: 14px;
            color: {text_color};
        }}

        /* TAG & INSIGHT */
        .tag {{
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            color: white !important;
            display: inline-block;
            margin-right: 6px;
        }}
        .tag-Foreign {{ background-color: {COLOR_MAP['Foreign']}; }}
        .tag-BUMN {{ background-color: {COLOR_MAP['BUMN']}; color: black !important; }}
        .tag-Local {{ background-color: {COLOR_MAP['Local']}; }}

        .insight-box {{
            background-color: {card_bg};
            padding: 18px 20px;
            border-radius: 12px;
            border-left: 6px solid {COLOR_MAP['Foreign']};
            margin-top: 18px;
            margin-bottom: 50px;
            box-shadow: 0 2px 8px {shadow};
            border: 1px solid {border_color};
            font-size: 0.95rem;
        }}

        /* FOOTER */
        .footer {{
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background: {card_bg};
            text-align: center;
            padding: 8px 12px;
            font-size: 11px;
            border-top: 1px solid {border_color};
            z-index: 1000;
            color: {text_color} !important;
        }}

        [data-testid="stBottomBlockContainer"] {{
            padding-bottom: 3.5rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ==========================================
# 3. KONEKSI DATA (ANTI-BLOKIR)
# ==========================================

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
    # Optional: hanya aktif kalau yfinance terinstall
    try:
        import yfinance as yf

        tickers = ["BBCA", "BBRI", "BMRI", "BBNI", "TLKM", "ASII", "GOTO", "BUMI", "ADRO", "PGAS"]
        yf_tickers = [f"{t}.JK" for t in tickers]

        data = yf.download(yf_tickers, period="2d", progress=False, session=get_yahoo_session())["Close"]
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
                cls = "#00E396" if chg >= 0 else "#FF4560"
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


# ==========================================
# 4. DATA PROCESSING
# ==========================================

def clean_running_trade(df_input: pd.DataFrame) -> pd.DataFrame:
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
        raise ValueError(f"Parsing Error: {e}") from e


def get_broker_summary(df: pd.DataFrame) -> pd.DataFrame:
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
    summ["Type"] = summ["Code"].apply(lambda x: get_broker_info(x)[2])

    return summ.sort_values("Net_Val", ascending=False)


def build_sankey(df: pd.DataFrame, top_n: int = 15, metric: str = "Value"):
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
        b_type = get_broker_info(code)[2]
        color = COLOR_MAP.get(b_type, "#888")
        val = b_totals[node] if node in b_totals else s_totals.get(node, 0)
        labels.append(f"{code} {format_number_label(val)}")
        colors.append(color)

    src = [node_map[x] for x in flow["B_Label"]]
    tgt = [node_map[x] for x in flow["S_Label"]]
    vals = flow[metric].tolist()

    l_colors = []
    for s_idx in src:
        c_hex = colors[s_idx].lstrip("#")
        rgb = tuple(int(c_hex[i : i + 2], 16) for i in (0, 2, 4))
        l_colors.append(f"rgba({rgb[0]},{rgb[1]},{rgb[2]},0.6)")

    return labels, colors, src, tgt, vals, l_colors


def generate_smart_insight(summary_df: pd.DataFrame) -> str:
    top_buyer = summary_df.iloc[0]
    top_seller = summary_df.iloc[-1]

    if top_buyer["Net_Val"] > (abs(top_seller["Net_Val"]) * 1.1):
        action = "AKUMULASI"
    elif abs(top_seller["Net_Val"]) > (top_buyer["Net_Val"] * 1.1):
        action = "DISTRIBUSI"
    else:
        action = "NETRAL"

    return f"""
    ### 🧠 AI Insight: {action}
    **Top Buyer:** {top_buyer['Code']} ({top_buyer['Type']}) - Net Buy: Rp {format_number_label(top_buyer['Net_Val'])}  
    **Top Seller:** {top_seller['Code']} ({top_seller['Type']}) - Net Sell: Rp {format_number_label(abs(top_seller['Net_Val']))}
    """


# ==========================================
# 5. UI PAGES
# ==========================================

def login_page(is_dark_mode: bool) -> None:
    inject_custom_css(is_dark_mode)

    # paksa keyboard numeric di mobile
    components.html(
        """
        <script>
        const i = window.parent.document.querySelectorAll('input[type="password"]');
        i.forEach(e => {{
            e.setAttribute('inputmode','numeric');
            e.setAttribute('pattern','[0-9]*');
        }});
        </script>
        """,
        height=0,
    )

    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown(
            """
            <div class="app-card app-card--center" style="margin-top:3rem;">
                <div style="text-align:center; margin-bottom:1.5rem;">
                    <div style="font-size:40px; margin-bottom:0.5rem;">🦅</div>
                    <h2 style="margin-bottom:0.2rem;">SECURE ACCESS</h2>
                    <p style="font-size:0.9rem; opacity:0.75;">
                        Masukkan PIN rahasia untuk membuka fitur Bandarmology Pro.
                    </p>
                </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login"):
            pin = st.text_input(
                "PIN",
                type="password",
                placeholder="0 0 0 0 0 0",
                label_visibility="collapsed",
            )
            submit = st.form_submit_button("UNLOCK")

        if submit:
            if pin == "241130":
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("PIN yang kamu masukkan salah. Coba lagi ya 🔐")

        st.markdown("</div>", unsafe_allow_html=True)


def bandarmology_page(is_dark_mode: bool) -> None:
    inject_custom_css(is_dark_mode)
    DB_ROOT = "database"

    # ---------- SIDEBAR (INPUT DATA) ----------
    with st.sidebar:
        st.subheader("📂 Sumber Data")
        source_type = st.radio(
            "Tipe:",
            ["Database Folder", "Upload Manual"],
            label_visibility="collapsed",
        )
        df_raw = None
        current_stock = "UNKNOWN"

        if source_type == "Database Folder":
            if os.path.exists(DB_ROOT):
                stocks = sorted(
                    [
                        d
                        for d in os.listdir(DB_ROOT)
                        if os.path.isdir(os.path.join(DB_ROOT, d))
                    ]
                )
                sel_stock = st.selectbox("Saham", stocks) if stocks else None
                if sel_stock:
                    p_stock = os.path.join(DB_ROOT, sel_stock)
                    years = sorted(os.listdir(p_stock))
                    sel_year = st.selectbox("Tahun", years) if years else None
                    if sel_year:
                        p_year = os.path.join(p_stock, sel_year)
                        months = sorted(os.listdir(p_year))
                        sel_month = (
                            st.selectbox("Bulan", months) if months else None
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
                            sel_file = st.selectbox("Tanggal", files) if files else None
                            if (
                                sel_file
                                and st.button("Load Data", use_container_width=True)
                            ):
                                fp = os.path.join(p_month, sel_file)
                                try:
                                    if fp.endswith("csv"):
                                        df_raw = pd.read_csv(fp)
                                    else:
                                        df_raw = pd.read_excel(fp)
                                    current_stock = sel_stock
                                except Exception:
                                    st.error("Gagal membaca file. Cek format datanya.")
            else:
                st.warning(f"Buat dulu folder '{DB_ROOT}' di samping script aplikasi.")
        else:
            uploaded = st.file_uploader(
                "Upload File Running Trade", type=["csv", "xlsx"]
            )
            if uploaded:
                try:
                    if uploaded.name.endswith("csv"):
                        df_raw = pd.read_csv(uploaded)
                    else:
                        df_raw = pd.read_excel(uploaded)
                    current_stock = uploaded.name.split(".")[0].upper()
                except Exception:
                    st.error("File tidak bisa dibaca. Pastikan formatnya benar ya 😊")

    # ---------- MAIN CONTENT ----------
    if df_raw is not None:
        try:
            df = clean_running_trade(df_raw)
            summ = get_broker_summary(df)

            # Header halaman
            st.markdown(
                f"""
                <div class="page-header">
                    <h1>📊 Bandarmology {current_stock}</h1>
                    <p>Distribusi dan akumulasi broker berdasarkan transaksi running trade.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            c1, c2, c3 = st.columns(3)
            tot_val = df["Value"].sum()
            c1.metric("Total Nilai Transaksi", f"Rp {format_number_label(tot_val)}")
            c2.metric("Total Volume", f"{df['Lot_Clean'].sum():,.0f} Lot")
            f_share = (
                summ[summ["Type"] == "Foreign"]["Total_Val"].sum() / (tot_val * 2) * 100
                if tot_val > 0
                else 0
            )
            c3.metric("Porsi Asing", f"{f_share:.1f}%")

            st.markdown("---")

            # ---------- TOP BROKER ----------
            st.subheader("🏆 Top Broker")
            tabs = st.tabs(["Semua", "Asing", "BUMN", "Lokal"])
            cats = ["All", "Foreign", "BUMN", "Local"]

            def color_net(val):
                if val > 0:
                    return "color:#00E396; font-weight:bold;"
                elif val < 0:
                    return "color:#FF4560; font-weight:bold;"
                return "color:inherit;"

            for tab, cat in zip(tabs, cats):
                with tab:
                    if cat == "All":
                        d = summ
                    else:
                        d = summ[summ["Type"] == cat]
                    if not d.empty:
                        st.dataframe(
                            d[["Code", "Name", "Total_Val", "Net_Val"]]
                            .style.format(
                                {
                                    "Total_Val": format_number_label,
                                    "Net_Val": format_number_label,
                                }
                            )
                            .map(color_net, subset=["Net_Val"]),
                            use_container_width=True,
                            height=350,
                        )
                    else:
                        st.info("Belum ada data broker di kategori ini.")

            # ---------- SANKEY / FLOW MAP ----------
            st.subheader("🕸️ Broker Flow Map")
            sc1, sc2 = st.columns([2, 1])
            with sc1:
                met = st.radio(
                    "Metrik visualisasi",
                    ["Value (Dana)", "Lot (Barang)"],
                    horizontal=True,
                )
            with sc2:
                top_n = st.slider("Jumlah interaksi", 5, 50, 15)

            met_col = "Value" if "Value" in met else "Lot_Clean"

            try:
                lbl, col, src, tgt, val, l_col = build_sankey(df, top_n, met_col)
                fig = go.Figure(
                    data=[
                        go.Sankey(
                            node=dict(
                                pad=20,
                                thickness=20,
                                line=dict(color="black", width=0.5),
                                label=lbl,
                                color=col,
                            ),
                            link=dict(
                                source=src,
                                target=tgt,
                                value=val,
                                color=l_col,
                            ),
                        )
                    ]
                )

                font_col = "white" if is_dark_mode else "black"
                fig.update_layout(
                    height=600,
                    margin=dict(l=10, r=10, t=10, b=10),
                    font=dict(size=12, color=font_col),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                )

                st.plotly_chart(fig, use_container_width=True)
                st.markdown(
                    "<div style='text-align:center;margin-top:0.4rem;'>"
                    "<span class='tag tag-Foreign'>ASING</span>"
                    "<span class='tag tag-BUMN'>BUMN</span>"
                    "<span class='tag tag-Local'>LOKAL</span>"
                    "</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<div class='insight-box'>{generate_smart_insight(summ)}</div>",
                    unsafe_allow_html=True,
                )
            except Exception as e:
                st.warning(f"Gagal membuat visualisasi flow: {e}")

        except Exception as e:
            st.error(f"Terjadi error saat memproses data: {e}")
    else:
        # Empty state yang lebih manis daripada st.info biasa
        st.markdown(
            """
            <div class="empty-state">
                <h2>Belum ada data yang dipilih 📂</h2>
                <p>Pilih sumber data dan file running trade di sidebar untuk mulai analisis
                bandarmology saham kamu.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ==========================================
# 6. MAIN APP
# ==========================================

def main():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "dark_mode" not in st.session_state:
        st.session_state["dark_mode"] = True

    inject_custom_css(st.session_state["dark_mode"])

    # ---------- SIDEBAR ATAS (BRAND + THEME) ----------
    with st.sidebar:
        if st.session_state["authenticated"]:
            st.markdown(
                "<h2 style='margin-bottom:0.2rem;'>🦅 Bandarmology</h2>",
                unsafe_allow_html=True,
            )
            st.caption("Bandarmology Pro Dashboard")
        else:
            st.markdown(
                "<h2 style='margin-bottom:0.2rem;'>Pengaturan</h2>",
                unsafe_allow_html=True,
            )
            st.caption("Atur tampilan & akses aplikasi")

        st.divider()

        mode_icon = "🌙" if st.session_state["dark_mode"] else "☀️"
        mode_text = "Dark Mode" if st.session_state["dark_mode"] else "Light Mode"

        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{mode_icon} {mode_text}**")
        with col2:
            is_dark = st.toggle(
                "Theme_Toggle",
                value=st.session_state["dark_mode"],
                label_visibility="collapsed",
            )

        if is_dark != st.session_state["dark_mode"]:
            st.session_state["dark_mode"] = is_dark
            st.rerun()

        if st.session_state["authenticated"]:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Logout", use_container_width=True):
                st.session_state["authenticated"] = False
                st.rerun()

    # ---------- ROUTING ----------
    if st.session_state["authenticated"]:
        # Optional: ticker kalau mau dinyalakan
        # st.markdown(get_stock_ticker(), unsafe_allow_html=True)
        bandarmology_page(st.session_state["dark_mode"])

        footer_mode = "Dark" if st.session_state["dark_mode"] else "Light"
        st.markdown(
            f"<div class='footer'>© 2025 PT Catindo Bagus Perkasa | Mode: {footer_mode}</div>",
            unsafe_allow_html=True,
        )
    else:
        login_page(st.session_state["dark_mode"])
        footer_mode = "Dark" if st.session_state["dark_mode"] else "Light"
        st.markdown(
            f"<div class='footer'>© 2025 PT Catindo Bagus Perkasa | Mode: {footer_mode}</div>",
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
