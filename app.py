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
# --- NAMA BROKER (boleh kamu tambah kalau perlu) ---
BROKER_NAMES = {
    # BUMN
    "CC": "Mandiri Sekuritas",
    "DX": "Bahana Sekuritas",
    "NI": "BNI Sekuritas",
    "OD": "BRI Danareksa Sekuritas",

    # ASING (contoh dari screenshot dan umum di BEI)
    "AG": "Kiwoom Sekuritas Indonesia",
    "AH": "Shinhan Sekuritas Indonesia",
    "AI": "UOB Kay Hian Sekuritas",
    "AK": "UBS Sekuritas Indonesia",
    "BK": "J.P. Morgan Sekuritas Indonesia",
    "BQ": "Korea Investment and Sekuritas Indonesia",
    "CG": "Citigroup Sekuritas Indonesia",
    "CP": "KB Valbury Sekuritas",
    "CS": "Credit Suisse Sekuritas Indonesia",
    "DR": "RHB Sekuritas Indonesia",
    "FS": "Yuanta Sekuritas Indonesia",
    "GI": "Webull Sekuritas Indonesia",
    "GW": "HSBC Sekuritas Indonesia",
    "HD": "KGI Sekuritas Indonesia",
    "KI": "Ciptadana Sekuritas Asia",
    "KK": "Phillip Sekuritas Indonesia",
    "KZ": "CLSA Sekuritas Indonesia",
    "RX": "Macquarie Sekuritas Indonesia",
    "TP": "OCBC Sekuritas Indonesia",
    "XA": "NH Korindo Sekuritas Indonesia",
    "YP": "Mirae Asset Sekuritas Indonesia",
    "YU": "CGS International Sekuritas Indonesia",
    "ZP": "Maybank Sekuritas Indonesia",

    # LOKAL (contoh yang sering muncul)
    "XL": "Stockbit Sekuritas Digital",
    "PD": "Indo Premier Sekuritas",
    "LG": "Trimegah Sekuritas Indonesia",
    "MG": "Semesta Indovest Sekuritas",
    "EP": "MNC Sekuritas",
    "SQ": "BCA Sekuritas",
    "BB": "Verdhana Sekuritas Indonesia",
    "DH": "Sinarmas Sekuritas",
    "AZ": "Sucor Sekuritas",
    "DK": "KAF Sekuritas Indonesia",
    "GR": "Panin Sekuritas Tbk.",
    "ID": "Anugerah Sekuritas Indonesia",
    "HP": "Henan Putihrai Sekuritas",
    "IF": "Samuel Sekuritas Indonesia",
    "AP": "Pacific Sekuritas Indonesia",
    "EL": "Evergreen Sekuritas Indonesia",
    "SA": "Elit Sukses Sekuritas",
    "IP": "Yugen Bertumbuh Sekuritas",
    "SC": "IMG Sekuritas",
    "DM": "Masindo Artha Sekuritas",
    # dst... silakan tambah sendiri sesuai kebutuhan
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
    if c in FOREIGN_BROKOKERS:
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

# =========================================================
# 3. STATE AWAL
# =========================================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

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
        .ticker-wrap {{
            background: #020617;
            padding: 6px 12px;
            border-radius: 999px;
            border: 1px solid {border_color};
            font-size: 11px;
            color: #e5e7eb;
            white-space: nowrap;
        }}
        .ticker-item {{
            margin-right: 18px;
        }}

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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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
    """
    Build data untuk sankey.
    metric: "Value" (Rp) atau "Lot_Clean" (Lot).
    Dibuat lebih robust supaya tidak error saat ganti metrik / slider.
    """
    metric = "Lot_Clean" if metric == "Lot_Clean" else "Value"

    if metric not in df.columns:
        raise ValueError(f"Kolom '{metric}' tidak ditemukan di data running trade.")

    # Hanya ambil kolom yang perlu
    flow = (
        df[["Buyer_Code", "Seller_Code", metric]]
        .groupby(["Buyer_Code", "Seller_Code"], as_index=False)[metric]
        .sum()
    )

    # Buang transaksi nol
    flow = flow[flow[metric] > 0]

    # Sort & batasi top_n
    flow = flow.sort_values(metric, ascending=False).head(top_n)

    if flow.empty:
        raise ValueError(
            "Tidak ada interaksi broker yang cukup besar untuk dibuatkan Broker Flow."
        )

    # Build node
    flow["B_Label"] = flow["Buyer_Code"] + " (B)"
    flow["S_Label"] = flow["Seller_Code"] + " (S)"
    all_nodes = list(sorted(set(flow["B_Label"]).union(set(flow["S_Label"]))))
    node_map = {k: v for v, k in enumerate(all_nodes)}

    # Total per node, dipakai untuk label
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

    # Link
    src = [node_map[x] for x in flow["B_Label"]]
    tgt = [node_map[x] for x in flow["S_Label"]]
    vals = flow[metric].astype(float).tolist()

    # Warna link mengikuti warna node sumber
    link_colors = []
    for s_idx in src:
        c_hex = colors[s_idx].lstrip("#")
        rgb = tuple(int(c_hex[i : i + 2], 16) for i in (0, 2, 4))
        link_colors.append(f"rgba({rgb[0]},{rgb[1]},{rgb[2]},0.55)")

    return labels, colors, src, tgt, vals, link_colors


def generate_kesimpulan(summary_df: pd.DataFrame, stock_code: str) -> str:
    """
    Kesimpulan yang lebih komunikatif & kaya insight untuk investor ritel.
    """
    if summary_df.empty:
        return (
            "### 🧾 Kesimpulan\n"
            "Belum ada data broker yang cukup untuk dianalisis hari ini."
        )

    # Top buyer & seller berdasarkan Net_Val
    buyers = summary_df.sort_values("Net_Val", ascending=False)
    sellers = summary_df.sort_values("Net_Val", ascending=True)

    top_buyer = buyers.iloc[0]
    top_seller = sellers.iloc[0]

    # Arah utama bandar
    total_net = summary_df["Net_Val"].sum()
    if total_net > 0:
        trend = "didominasi **AKUMULASI** (net buy)"
    elif total_net < 0:
        trend = "didominasi **DISTRIBUSI** (net sell)"
    else:
        trend = "cenderung **NETRAL** (seimbang antara buy dan sell)"

    # Dominasinya asing / lokal / BUMN
    group_net = summary_df.groupby("Group")["Net_Val"].sum().sort_values(ascending=False)
    dom_group = group_net.index[0]
    dom_val = group_net.iloc[0]

    if dom_val > 0:
        dom_sentence = (
            f"Aliran dana terbesar berasal dari broker **{dom_group}** "
            f"dengan kecenderungan **net buy** sekitar Rp {format_number_label(dom_val)}."
        )
    elif dom_val < 0:
        dom_sentence = (
            f"Tekanan jual terbesar muncul dari broker **{dom_group}** "
            f"dengan **net sell** sekitar Rp {format_number_label(abs(dom_val))}."
        )
    else:
        dom_sentence = (
            "Kontribusi bersih antar kelompok broker (Asing, BUMN, Lokal) hari ini relatif berimbang."
        )

    # Rangkuman praktis untuk ritel
    buyer_line = (
        f"- **Top Buyer:** {top_buyer['Code']} ({top_buyer['Group']}) "
        f"dengan net buy sekitar **Rp {format_number_label(top_buyer['Net_Val'])}**."
    )
    seller_line = (
        f"- **Top Seller:** {top_seller['Code']} ({top_seller['Group']}) "
        f"dengan net sell sekitar **Rp {format_number_label(abs(top_seller['Net_Val']))}**."
    )

    if total_net > 0:
        ritel_hint = (
            "👉 Untuk investor ritel: perhatikan apakah akumulasi ini konsisten "
            "beberapa hari ke depan. Jika harga juga ikut naik dengan volume sehat, "
            "potensi **uptrend lanjutan** cukup menarik, tetapi hindari FOMO di pucuk."
        )
    elif total_net < 0:
        ritel_hint = (
            "👉 Untuk investor ritel: distribusi oleh broker besar perlu diwaspadai. "
            "Jika penurunan harga disertai net sell berulang, lebih bijak fokus ke "
            "manajemen risiko (cut loss / kurangi posisi) daripada menebak bottom."
        )
    else:
        ritel_hint = (
            "👉 Untuk investor ritel: pola hari ini masih netral. Cocok untuk **wait & see**, "
            "menunggu konfirmasi arah dari pergerakan bandar pada sesi berikutnya."
        )

    text = f"""
### 🧾 Kesimpulan {stock_code}

Secara keseluruhan, aktivitas bandar hari ini **{trend}**.

{dom_sentence}

**Broker kunci yang perlu kamu perhatikan:**

{buyer_line}  
{seller_line}

{ritel_hint}
"""
    return text


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
                place
