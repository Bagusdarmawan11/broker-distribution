import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px  # Tambahan untuk chart trade book
import re
import os
import datetime
import requests
import streamlit.components.v1 as components
import numpy as np

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

FOREIGN_BROKERS = {
    "AG", "AH", "AI", "AK", "BK", "BQ", "CG", "CP", "CS",
    "DR", "FS", "GI", "GW", "HD", "KI", "KK", "KZ", "RX",
    "TP", "XA", "YP", "YU", "ZP",
}

BUMN_BROKERS = {"CC", "DX", "NI", "OD"}

def get_broker_group(code: str) -> str:
    c = str(code).upper().strip()
    if c in BUMN_BROKERS:
        return "BUMN"
    if c in FOREIGN_BROKERS:
        return "Asing"
    return "Lokal"

def get_broker_info(code: str):
    c = str(code).upper().strip()
    name = BROKER_NAMES.get(c, "Sekuritas Lain")
    group = get_broker_group(c)
    return c, name, group

COLOR_MAP = {
    "Asing": "#ff4b4b",   # merah
    "BUMN": "#22c55e",    # hijau
    "Lokal": "#3b82f6",   # biru
    "Unknown": "#6b7280",  # abu
}

def style_broker_code(val):
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
        .stApp {{ background-color: {bg_color}; color: {text_color}; }}
        h1, h2, h3, h4, h5, h6, p, span, label, div, li {{ color: {text_color}; }}
        [data-testid="stSidebar"] {{ background-color: {sidebar_bg} !important; border-right: 1px solid {border_color}; }}
        
        /* PIN Input */
        .stTextInput input {{
            text-align: center; font-size: 32px !important; letter-spacing: 12px;
            font-weight: 700; padding: 16px; border-radius: 14px;
            background-color: {input_bg} !important; color: {text_color} !important;
            border: 2px solid {input_border} !important; box-shadow: 0 14px 35px {shadow};
        }}
        
        /* Buttons */
        .stButton button {{
            width: 100%; height: 46px; font-size: 15px; font-weight: 600;
            border-radius: 12px; border: 1px solid {border_color};
            background: linear-gradient(135deg, #111827, #020617); color: {text_color} !important;
            transition: all 0.2s ease;
        }}
        .stButton button:hover {{ transform: translateY(-1px); border-color: {btn_hover}; }}

        /* Date Input Fix */
        div[data-baseweb="input"] {{ background-color: {input_bg} !important; border-color: {input_border} !important; }}
        div[data-baseweb="calendar"] {{ background-color: {card_bg} !important; }}

        /* Tag & Metrics */
        .tag {{ padding: 4px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; margin-right: 6px; }}
        .tag-Asing {{ background-color: {COLOR_MAP["Asing"]}; color: #111827; }}
        .tag-BUMN {{ background-color: {COLOR_MAP["BUMN"]}; color: #052e16; }}
        .tag-Lokal {{ background-color: {COLOR_MAP["Lokal"]}; color: #e5e7eb; }}

        /* Broker Action Meter */
        .meter-container {{
            width: 100%; height: 24px; background: #374151; border-radius: 12px;
            position: relative; margin: 10px 0; overflow: hidden;
        }}
        .meter-bar {{
            height: 100%;
            background: linear-gradient(90deg, #ff4b4b 0%, #9ca3af 50%, #22c55e 100%);
        }}
        .meter-marker {{
            position: absolute; top: -2px; width: 4px; height: 28px;
            background-color: #fff; box-shadow: 0 0 10px #fff;
            transform: translateX(-50%);
        }}
        .meter-labels {{
            display: flex; justify-content: space-between; font-size: 10px; color: #9ca3af; margin-top: 4px;
        }}

        .footer {{ position: fixed; left: 0; bottom: 0; width: 100%; background: #020617; text-align: center; padding: 8px 0; font-size: 11px; border-top: 1px solid {border_color}; z-index: 999; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def hide_sidebar():
    st.markdown("""<style>[data-testid="stSidebar"] {display: none !important;} [data-testid="collapsedControl"] {display: none !important;}</style>""", unsafe_allow_html=True)

def show_sidebar():
    st.markdown("""<style>[data-testid="stSidebar"] {display: block !important;} [data-testid="collapsedControl"] {display: block !important;}</style>""", unsafe_allow_html=True)

def render_footer():
    st.markdown("<div class='footer'><span>© 2025 PT Catindo Bagus Perkasa | Bandarmology Pro (Dark)</span></div>", unsafe_allow_html=True)

# =========================================================
# 5. TOOLS & DATA HELPERS
# =========================================================
def format_number_label(value):
    abs_val = abs(value)
    if abs_val >= 1e12: return f"{value/1e12:.2f}T"
    if abs_val >= 1e9: return f"{value/1e9:.2f}M"
    if abs_val >= 1e6: return f"{value/1e6:.2f}Jt"
    return f"{value:,.0f}"

MONTH_ID = {1:'Januari', 2:'Februari', 3:'Maret', 4:'April', 5:'Mei', 6:'Juni', 7:'Juli', 8:'Agustus', 9:'September', 10:'Oktober', 11:'November', 12:'Desember'}

def _norm_token(s): return re.sub(r'[^a-z0-9]+', '', str(s).lower())

def resolve_database_file(db_root, stock, dt_date):
    """Simple resolver logic"""
    p_stock = os.path.join(db_root, stock)
    if not os.path.exists(p_stock): return None
    
    # Check Year
    year = str(dt_date.year)
    p_year = os.path.join(p_stock, year)
    if not os.path.exists(p_year):
        # Try finding loose match
        for d in os.listdir(p_stock):
            if _norm_token(d) == _norm_token(year):
                p_year = os.path.join(p_stock, d)
                break
        else: return None
        
    # Check Month
    month_name = MONTH_ID.get(dt_date.month, str(dt_date.month))
    p_month = None
    for d in os.listdir(p_year):
        if _norm_token(month_name) in _norm_token(d) or _norm_token(f"{dt_date.month:02d}") in _norm_token(d):
            p_month = os.path.join(p_year, d)
            break
    if not p_month: return None
    
    # Check Day File
    day_str = f"{dt_date.day:02d}"
    for f in os.listdir(p_month):
        if f.lower().endswith(('.csv', '.xlsx')):
            if day_str in f or f.startswith(str(dt_date.day)):
                return os.path.join(p_month, f)
    return None

# =========================================================
# 6. DATA PROCESSING
# =========================================================
def clean_running_trade(df_input):
    df = df_input.copy()
    df.columns = df.columns.str.strip().str.capitalize()

    rename_map = {
        "Time": "Time", "Waktu": "Time", "Price": "Price", "Harga": "Price",
        "Lot": "Lot", "Vol": "Lot", "Volume": "Lot",
        "Buyer": "Buyer", "B": "Buyer", "Broker Beli": "Buyer",
        "Seller": "Seller", "S": "Seller", "Broker Jual": "Seller",
        "Action": "Action", "Type": "Action" # Ensure Action column exists
    }
    new_cols = {c: rename_map[c] for c in df.columns if c in rename_map}
    df.rename(columns=new_cols, inplace=True)
    
    # Validate essential columns
    required = {"Price", "Lot", "Buyer", "Seller"}
    if not required.issubset(df.columns):
        raise ValueError("Kolom Wajib (Price, Lot, Buyer, Seller) tidak lengkap.")

    # Cleaning
    def clean_num(x): return int(re.sub(r"[^\d]", "", str(x).split("(")[0])) if pd.notnull(x) else 0
    def clean_code(x): return str(x).upper().split()[0].strip()

    df["Price_Clean"] = df["Price"].apply(clean_num)
    df["Lot_Clean"] = df["Lot"].apply(clean_num)
    df["Buyer_Code"] = df["Buyer"].apply(clean_code)
    df["Seller_Code"] = df["Seller"].apply(clean_code)
    df["Value"] = df["Lot_Clean"] * 100 * df["Price_Clean"]
    
    # If Action column is missing, infer it (Optional: usually RT has it)
    if "Action" not in df.columns:
        # Default logic if needed, or set to 'Unknown'
        df["Action"] = "Buy" # Placeholder if not present
    else:
        # Normalize Action to "Buy" or "Sell"
        df["Action"] = df["Action"].astype(str).str.capitalize()
    
    # Ensure time is parsed for charting
    try:
        df["Time_Obj"] = pd.to_datetime(df["Time"], format="%H:%M:%S", errors='coerce').dt.time
        # Create a dummy datetime for today to allow resampling
        today = datetime.date.today()
        df["DateTime"] = df["Time"].apply(lambda t: datetime.datetime.combine(today, pd.to_datetime(t, format="%H:%M:%S").time()) if isinstance(t, str) else pd.NaT)
    except:
        pass

    return df[df["Value"] > 0]

def get_detailed_broker_summary(df, net_mode=False):
    """Calculates Detailed Summary including Avg Price."""
    # Buyer Stats
    buy_stats = df.groupby("Buyer_Code").agg(
        Buy_Val=("Value", "sum"),
        Buy_Lot=("Lot_Clean", "sum")
    )
    buy_stats["Buy_Avg"] = (buy_stats["Buy_Val"] / (buy_stats["Buy_Lot"] * 100)).fillna(0).astype(int)
    
    # Seller Stats
    sell_stats = df.groupby("Seller_Code").agg(
        Sell_Val=("Value", "sum"),
        Sell_Lot=("Lot_Clean", "sum")
    )
    sell_stats["Sell_Avg"] = (sell_stats["Sell_Val"] / (sell_stats["Sell_Lot"] * 100)).fillna(0).astype(int)

    # Merge
    summ = pd.merge(buy_stats, sell_stats, left_index=True, right_index=True, how="outer").fillna(0)
    summ["Net_Val"] = summ["Buy_Val"] - summ["Sell_Val"]
    summ["Net_Lot"] = summ["Buy_Lot"] - summ["Sell_Lot"]
    
    summ.index.name = "Code"
    summ = summ.reset_index()
    summ["Group"] = summ["Code"].apply(lambda x: get_broker_group(x))
    
    return summ

def calculate_broker_action_meter(summ):
    """
    Menghitung posisi meter (0-100)
    0 = Big Dist, 50 = Neutral, 100 = Big Acc
    Logic: Bandingkan Top 5 Net Buy vs Top 5 Net Sell
    """
    top_buyers = summ.nlargest(5, "Net_Val")["Net_Val"].sum()
    top_sellers = summ.nsmallest(5, "Net_Val")["Net_Val"].sum() # Negative value
    
    abs_sell = abs(top_sellers)
    total_pressure = top_buyers + abs_sell
    
    if total_pressure == 0:
        return 50 # Neutral
        
    # Ratio akumulasi (0 to 1)
    acc_ratio = top_buyers / total_pressure 
    
    # Scale to 0-100
    meter_val = int(acc_ratio * 100)
    return meter_val

def prepare_trade_book_data(df):
    """
    Prepare data for Trade Book (Chart & Price Table)
    """
    # 1. Price Table
    # Aggregation based on Action type
    # If Action == Buy, it contributes to Buy Volume at that price (Hajar Kanan)
    # If Action == Sell, it contributes to Sell Volume at that price (Hajar Kiri)
    
    price_grp = df.groupby(["Price_Clean", "Action"]).agg(
        Lot=("Lot_Clean", "sum"),
        Freq=("Lot_Clean", "count")
    ).reset_index()
    
    # Pivot to get Buy Lot and Sell Lot columns
    price_pivot = price_grp.pivot(index="Price_Clean", columns="Action", values=["Lot", "Freq"]).fillna(0)
    price_pivot.columns = [f"{c[1]}_{c[0]}" for c in price_pivot.columns] # e.g., Buy_Lot, Sell_Lot
    
    # Flatten and cleanup
    price_df = price_pivot.reset_index()
    # Ensure columns exist
    for col in ["Buy_Lot", "Sell_Lot", "Buy_Freq", "Sell_Freq"]:
        if col not in price_df.columns: price_df[col] = 0
        
    price_df["Total_Lot"] = price_df["Buy_Lot"] + price_df["Sell_Lot"]
    price_df["Total_Freq"] = price_df["Buy_Freq"] + price_df["Sell_Freq"]
    price_df = price_df.sort_values("Price_Clean", ascending=False)
    
    # 2. Chart Data (Time Series)
    # Resample by Minute
    if "DateTime" in df.columns and pd.notnull(df["DateTime"]).all():
        ts_df = df.set_index("DateTime").sort_index()
        ts_resampled = ts_df.groupby([pd.Grouper(freq='1min'), "Action"])["Lot_Clean"].sum().unstack(fill_value=0)
        
        # Cumulative Sum
        ts_resampled["Buy_Cum"] = ts_resampled.get("Buy", 0).cumsum()
        ts_resampled["Sell_Cum"] = ts_resampled.get("Sell", 0).cumsum()
        ts_chart = ts_resampled.reset_index()
    else:
        ts_chart = pd.DataFrame()
        
    return price_df, ts_chart

def build_sankey(df, top_n=15, metric="Value"):
    # Label Kiri: Buyer, Kanan: Seller
    flow = df.groupby(["Buyer_Code", "Seller_Code"])[metric].sum().reset_index()
    flow = flow.sort_values(metric, ascending=False).head(top_n)

    # Buat label unik: "YP (B)" vs "YP (S)"
    flow["Source"] = flow["Buyer_Code"] + " (Buyer)"
    flow["Target"] = flow["Seller_Code"] + " (Seller)"
    
    all_nodes = list(set(flow["Source"]).union(set(flow["Target"])))
    node_map = {k: v for v, k in enumerate(all_nodes)}

    labels = all_nodes
    colors = []
    for node in all_nodes:
        # Extract broker code from "YP (Buyer)"
        code = node.split()[0]
        group = get_broker_group(code)
        colors.append(COLOR_MAP.get(group, "#888"))

    src = [node_map[x] for x in flow["Source"]]
    tgt = [node_map[x] for x in flow["Target"]]
    vals = flow[metric].tolist()

    link_colors = []
    for s_idx in src:
        c_hex = colors[s_idx].lstrip("#")
        rgb = tuple(int(c_hex[i: i + 2], 16) for i in (0, 2, 4))
        link_colors.append(f"rgba({rgb[0]},{rgb[1]},{rgb[2]},0.4)")

    return labels, colors, src, tgt, vals, link_colors

# =========================================================
# 7. MAIN UI COMPONENTS
# =========================================================

def render_broker_action_meter(summ):
    val = calculate_broker_action_meter(summ)
    
    # Determine Label
    if val > 60: status = "Big Accumulation"
    elif val < 40: status = "Big Distribution"
    else: status = "Neutral"
    
    st.markdown("### Broker Action")
    st.markdown(f"""
    <div style="text-align:center; font-weight:bold; margin-bottom:5px;">{status}</div>
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

def render_broker_summary_split(summ, net_mode):
    st.subheader("Broker Summary")
    
    # Sort for Top Buyers and Top Sellers
    if net_mode:
        # Net Mode: Sort by Net Value
        # Top Buyers: Highest Positive Net_Val
        top_buyers = summ[summ["Net_Val"] > 0].sort_values("Net_Val", ascending=False).head(20)
        # Top Sellers: Lowest Negative Net_Val (Most negative)
        top_sellers = summ[summ["Net_Val"] < 0].sort_values("Net_Val", ascending=True).head(20)
        
        # Adjust display columns for Net
        b_cols = ["Code", "Net_Val", "Net_Lot", "Buy_Avg"]
        s_cols = ["Code", "Net_Val", "Net_Lot", "Sell_Avg"]
    else:
        # Regular Mode: Sort by Gross Buy/Sell Val
        top_buyers = summ.sort_values("Buy_Val", ascending=False).head(20)
        top_sellers = summ.sort_values("Sell_Val", ascending=False).head(20)
        
        b_cols = ["Code", "Buy_Val", "Buy_Lot", "Buy_Avg"]
        s_cols = ["Code", "Sell_Val", "Sell_Lot", "Sell_Avg"]

    c1, c2 = st.columns(2)
    
    with c1:
        st.caption("Top Buyers (Accumulation)")
        st.dataframe(
            top_buyers[b_cols].style.format({
                "Buy_Val": format_number_label, "Net_Val": format_number_label, 
                "Buy_Lot": "{:,.0f}", "Net_Lot": "{:,.0f}", "Buy_Avg": "{:,.0f}"
            }).applymap(style_broker_code, subset=["Code"]),
            use_container_width=True, hide_index=True, height=400
        )
        
    with c2:
        st.caption("Top Sellers (Distribution)")
        # For Net Sellers, Net_Val is negative, but usually we display absolute or keep negative
        st.dataframe(
            top_sellers[s_cols].style.format({
                "Sell_Val": format_number_label, "Net_Val": format_number_label,
                "Sell_Lot": "{:,.0f}", "Net_Lot": "{:,.0f}", "Sell_Avg": "{:,.0f}"
            }).applymap(style_broker_code, subset=["Code"]),
            use_container_width=True, hide_index=True, height=400
        )

def render_trade_book(df):
    st.subheader("Trade Book")
    price_df, chart_df = prepare_trade_book_data(df)
    
    tab1, tab2 = st.tabs(["Chart", "Price"])
    
    with tab1:
        if not chart_df.empty:
            # Prepare long format for Plotly Express
            chart_long = pd.melt(chart_df, id_vars=["DateTime"], value_vars=["Buy_Cum", "Sell_Cum"], 
                                 var_name="Type", value_name="Volume")
            
            fig = px.line(chart_long, x="DateTime", y="Volume", color="Type", 
                          color_discrete_map={"Buy_Cum": "#00E396", "Sell_Cum": "#FF4560"},
                          title="Cumulative Buy vs Sell Volume (Intraday)")
            fig.update_layout(
                xaxis_title="Time", yaxis_title="Cumulative Lot",
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#f9fafb'), hovermode="x unified",
                legend=dict(orientation="h", y=1.1)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Data waktu tidak cukup untuk membuat chart.")

    with tab2:
        # Tampilan mirip Screenshot: Price, B.Lot, S.Lot, B.Freq, S.Freq
        disp_df = price_df[["Price_Clean", "Buy_Lot", "Sell_Lot", "Buy_Freq", "Sell_Freq"]]
        st.dataframe(
            disp_df.style.format("{:,.0f}").bar(subset=["Buy_Lot"], color='#004d26')
                                           .bar(subset=["Sell_Lot"], color='#4d0012'),
            use_container_width=True, hide_index=True, height=400
        )

def render_running_trade_raw(df):
    st.subheader("Running Trade")
    
    # Filter Controls
    col_f1, col_f2 = st.columns([1, 4])
    with col_f1:
        filter_action = st.radio("Filter Action:", ["All", "Buy", "Sell"], horizontal=True)
    
    # Apply Filter
    df_show = df.copy()
    if filter_action == "Buy":
        df_show = df_show[df_show["Action"] == "Buy"]
    elif filter_action == "Sell":
        df_show = df_show[df_show["Action"] == "Sell"]
        
    # Select columns to match screenshot: Time, Price, Action, Lot, Buyer, Seller
    cols = ["Time", "Price", "Action", "Lot_Clean", "Buyer_Code", "Seller_Code"]
    
    st.dataframe(
        df_show[cols].sort_values("Time", ascending=False).style.format({
            "Lot_Clean": "{:,.0f}", "Price": "{:,.0f}"
        }).applymap(lambda x: "color: #22c55e" if x == "Buy" else ("color: #ef4444" if x == "Sell" else ""), subset=["Action"])
          .applymap(style_broker_code, subset=["Buyer_Code", "Seller_Code"]),
        use_container_width=True, hide_index=True, height=400
    )


# =========================================================
# 8. HALAMAN LOGIN
# =========================================================
def login_page():
    inject_custom_css()
    hide_sidebar()
    components.html("""<script>const frame = window.parent.document; const inputs = frame.querySelectorAll('input[type="password"]'); inputs.forEach(e => { e.setAttribute('inputmode','numeric'); e.setAttribute('pattern','[0-9]*'); });</script>""", height=0)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, c2, _ = st.columns([1, 2.2, 1])
    with c2:
        st.markdown(
            """
            <div style="background: radial-gradient(circle at top left, #1f2937, #020617); padding: 32px; border-radius: 18px; text-align: center; border: 1px solid #374151;">
                <div style="font-size:44px;margin-bottom:8px;">🦅</div>
                <h2 style="margin-bottom:4px;">SECURE ACCESS</h2>
                <p style="font-size:14px;color:#9ca3af;margin-bottom:12px;">Masukkan PIN rahasia untuk membuka fitur Bandarmology Pro.</p>
            </div>
            """, unsafe_allow_html=True
        )
        with st.form("login_form"):
            pin = st.text_input("PIN", type="password", max_chars=6, placeholder="0 0 0 0 0 0")
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
# 9. HALAMAN BANDARMOLOGY
# =========================================================
def bandarmology_page():
    DB_ROOT = "database"
    df_raw = st.session_state.get("df_raw")
    current_stock = st.session_state.get("current_stock", "UNKNOWN")

    with st.sidebar:
        st.markdown("### 📂 Sumber Data")
        source_type = st.radio("Mode", ["Database", "Upload"], index=0)

        if source_type == "Database":
            if os.path.exists(DB_ROOT):
                stocks = sorted([d for d in os.listdir(DB_ROOT) if os.path.isdir(os.path.join(DB_ROOT, d))])
                sel_stock = st.selectbox("Saham", stocks)
                
                # Perbaikan Date Input: Format DD/MM/YYYY
                default_date = st.session_state.get("selected_date", datetime.date.today())
                sel_date = st.date_input("Tanggal", value=default_date, format="DD/MM/YYYY")
                st.session_state["selected_date"] = sel_date

                if st.button("Load Data", use_container_width=True):
                    fp = resolve_database_file(DB_ROOT, sel_stock, sel_date)
                    if fp:
                        try:
                            if fp.endswith(".csv"): df_raw = pd.read_csv(fp)
                            else: df_raw = pd.read_excel(fp)
                            st.session_state["df_raw"] = df_raw
                            st.session_state["current_stock"] = sel_stock
                            st.success(f"Loaded {sel_stock}")
                            st.rerun()
                        except: st.error("File error.")
                    else:
                        st.warning("Data tidak ditemukan.")
            else:
                st.warning(f"Folder '{DB_ROOT}' missing.")
        else:
            uploaded = st.file_uploader("Upload CSV/XLSX", type=["csv", "xlsx"])
            if uploaded:
                try:
                    if uploaded.name.endswith("csv"): df_raw = pd.read_csv(uploaded)
                    else: df_raw = pd.read_excel(uploaded)
                    st.session_state["df_raw"] = df_raw
                    st.session_state["current_stock"] = "UPLOADED"
                except: st.error("Format file salah.")

    # --- MAIN CONTENT ---
    if df_raw is None:
        st.info("Silakan pilih data saham di sidebar.")
        return

    try:
        # 1. Clean Data
        df = clean_running_trade(df_raw)
        
        # 2. Metrics Header
        st.title(f"🦅 {current_stock} - Bandarmology Pro")
        col1, col2, col3, col4 = st.columns(4)
        tot_val = df["Value"].sum()
        tot_vol = df["Lot_Clean"].sum()
        freq = len(df)
        
        col1.metric("Total Value", f"Rp {format_number_label(tot_val)}")
        col2.metric("Total Volume", f"{tot_vol:,.0f} Lot")
        col3.metric("Frequency", f"{freq:,.0f} x")
        
        # Calculate Foreign Flow
        summ = get_detailed_broker_summary(df)
        foreign_net = summ[summ["Group"]=="Asing"]["Net_Val"].sum()
        col4.metric("Net Foreign", f"Rp {format_number_label(foreign_net)}", 
                    delta_color="normal" if foreign_net==0 else ("inverse" if foreign_net < 0 else "normal"))

        st.divider()

        # 3. Broker Action Meter
        render_broker_action_meter(summ)
        
        st.markdown("<br>", unsafe_allow_html=True)

        # 4. Broker Summary (Split View)
        # Add Net Toggle
        net_mode = st.toggle("Net Mode (Filter Crossing)", value=False)
        render_broker_summary_split(summ, net_mode)

        st.divider()

        # 5. Trade Book (Chart & Price)
        render_trade_book(df)
        
        st.divider()
        
        # 6. Running Trade Table (New Feature)
        render_running_trade_raw(df)

        st.divider()

        # 7. Sankey Diagram (Broker Flow)
        st.subheader("Broker Flow (Sankey)")
        st.caption("Alur Dana: Buyer (Kiri) -> Seller (Kanan)")
        
        c_san1, c_san2 = st.columns([1, 3])
        with c_san1:
            top_n = st.slider("Jumlah Jalur", 5, 50, 15)
            metric_sankey = st.selectbox("Metrik", ["Value", "Lot_Clean"])
            
        labels, node_colors, src, tgt, vals, link_colors = build_sankey(df, top_n, metric_sankey)
        
        fig = go.Figure(data=[go.Sankey(
            node=dict(pad=20, thickness=18, line=dict(color="black", width=0.3), label=labels, color=node_colors),
            link=dict(source=src, target=tgt, value=vals, color=link_colors)
        )])
        fig.update_layout(height=600, font=dict(size=11, color="#e5e7eb"), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error Processing Data: {e}")
        st.write(e)

# =========================================================
# 10. DAFTAR BROKER & SAHAM (Placeholder)
# =========================================================
def daftar_broker_page():
    st.title("📚 Daftar Broker")
    rows = [{"Kode": k, "Nama": v, "Grup": get_broker_group(k)} for k, v in BROKER_NAMES.items()]
    df = pd.DataFrame(rows)
    st.dataframe(df.style.applymap(style_broker_code, subset=["Kode"]), use_container_width=True, height=600)

def daftar_saham_page():
    st.title("📄 Daftar Saham")
    st.info("Fitur ini membutuhkan file 'Daftar Saham.xlsx'.")

# =========================================================
# 11. MAIN
# =========================================================
def main():
    if not st.session_state["authenticated"]:
        login_page()
        return

    inject_custom_css()
    show_sidebar()

    with st.sidebar:
        st.title("🦅 Menu")
        page = st.radio("Navigasi", ["Bandarmology", "Daftar Broker", "Daftar Saham"])
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.rerun()

    if page == "Bandarmology": bandarmology_page()
    elif page == "Daftar Broker": daftar_broker_page()
    else: daftar_saham_page()
    
    render_footer()

if __name__ == "__main__":
    main()
