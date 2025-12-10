import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import re
import io
import os
import yfinance as yf
import streamlit.components.v1 as components 
from datetime import datetime
from tvdatafeed import TvDatafeed, Interval

# ==========================================
# 1. KONFIGURASI & DATABASE BROKER
# ==========================================
st.set_page_config(
    page_title="Bandarmology Pro",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inisialisasi TradingView (Tanpa Login - Mode Anonymous)
try:
    tv = TvDatafeed()
except:
    tv = None

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
}

# --- PALET WARNA ---
COLOR_MAP = {
    'Foreign': '#00E396', # Hijau
    'BUMN': '#FEB019',    # Orange
    'Local': '#775DD0',   # Ungu
    'Unknown': '#546E7A'  # Abu Gelap
}

# Inisialisasi Session State
if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
if 'dark_mode' not in st.session_state: st.session_state['dark_mode'] = True

# ==========================================
# 2. HELPER FUNCTIONS & UTILITIES
# ==========================================

def get_broker_info(code):
    code = str(code).upper().strip()
    data = BROKER_DB.get(code, {'name': 'Sekuritas Lain', 'type': 'Unknown'})
    return code, data['name'], data['type']

def format_number_label(value):
    abs_val = abs(value)
    if abs_val >= 1e12: return f"{value/1e12:.2f}T"
    if abs_val >= 1e9: return f"{value/1e9:.2f}M"
    if abs_val >= 1e6: return f"{value/1e6:.2f}Jt"
    return f"{value:,.0f}"

def inject_custom_css():
    mode = "dark" if st.session_state['dark_mode'] else "light"
    bg_color = "#0e1117" if mode == "dark" else "#ffffff"
    text_color = "#ffffff" if mode == "dark" else "#000000"
    card_bg = "#1E1E1E" if mode == "dark" else "#f0f2f6"
    
    st.markdown(f"""
    <style>
        .stApp {{ background-color: {bg_color}; color: {text_color}; }}
        
        /* PIN Styles */
        .stTextInput input {{
            text-align: center; font-size: 32px !important; letter-spacing: 15px;
            font-weight: bold; padding: 20px; border-radius: 15px;
            background-color: {card_bg}; color: {text_color}; border: 1px solid #444;
        }}
        .stButton button {{ width: 100%; height: 50px; font-size: 18px; border-radius: 12px; }}
        
        /* Custom Table */
        thead tr th:first-child {{display:none}} tbody th {{display:none}}
        
        /* Broker Tags */
        .tag {{ padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; color: white; display: inline-block; margin-right: 5px;}}
        .tag-Foreign {{ background-color: {COLOR_MAP['Foreign']}; }}
        .tag-BUMN {{ background-color: {COLOR_MAP['BUMN']}; color: black; }}
        .tag-Local {{ background-color: {COLOR_MAP['Local']}; }}
        
        /* Marquee */
        .ticker-wrap {{
            width: 100%; background-color: {card_bg}; padding: 12px 0;
            border-bottom: 1px solid #333; position: sticky; top: 0; z-index: 99;
        }}
        .ticker-item {{ margin: 0 25px; font-weight: bold; font-family: 'Courier New', monospace; font-size: 15px; }}
        .up {{color: #00E396;}} .down {{color: #FF4560;}}
        
        /* Footer */
        .footer {{
            position: fixed; left: 0; bottom: 0; width: 100%; background: {card_bg};
            text-align: center; padding: 8px; font-size: 12px; border-top: 1px solid #333; z-index: 1000;
        }}
        
        /* Insight Box */
        .insight-box {{
            background-color: {card_bg}; padding: 20px; border-radius: 10px; border-left: 5px solid {COLOR_MAP['Foreign']};
            margin-top: 20px; margin-bottom: 50px;
        }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. LIVE MARKET DATA (HYBRID ENGINE)
# ==========================================

@st.cache_data(ttl=60) # Update tiap 60 detik
def get_stock_ticker():
    tickers = ["BBCA", "BBRI", "BMRI", "BBNI", "TLKM", "ASII", "GOTO", "BUMI", "ADRO", "PGAS", "ANTM"]
    yf_tickers = [f"{t}.JK" for t in tickers]
    
    try:
        data = yf.download(yf_tickers, period="2d", progress=False)['Close']
        if data.empty: return ""
        
        last_prices = data.iloc[-1]
        prev_prices = data.iloc[-2] if len(data) > 1 else last_prices
        
        html_content = ""
        for symbol in tickers:
            ticker_jk = f"{symbol}.JK"
            try:
                price = last_prices[ticker_jk]
                prev = prev_prices[ticker_jk]
                if pd.isna(price) or pd.isna(prev): continue
                
                change = price - prev
                pct = (change / prev) * 100
                color_class = "up" if change >= 0 else "down"
                sign = "+" if change >= 0 else ""
                
                html_content += f"<span class='ticker-item'>{symbol} {int(price):,} <span class='{color_class}'>({sign}{pct:.2f}%)</span></span>"
            except: continue
            
        return f"<div class='ticker-wrap'><marquee scrollamount='8'>{html_content}</marquee></div>"
    except Exception as e:
        return f"<div class='ticker-wrap'>Market Data Offline</div>"

@st.cache_data(ttl=300)
def get_stock_details(symbol):
    """
    HYBRID SYSTEM: Coba Yahoo Finance, jika gagal fallback ke TradingView (TvDatafeed)
    """
    symbol = symbol.upper()
    
    # 1. COBA YAHOO FINANCE
    try:
        ticker = yf.Ticker(f"{symbol}.JK")
        hist = ticker.history(period="1d")
        
        if not hist.empty:
            info = ticker.info
            current = hist.iloc[-1]
            return {
                'Source': 'Yahoo Finance',
                'Open': current['Open'], 'High': current['High'],
                'Low': current['Low'], 'Close': current['Close'],
                'Volume': current['Volume'],
                'Value_Est': current['Close'] * current['Volume'],
                'MarketCap': info.get('marketCap', 0),
                'PE': info.get('trailingPE', 0),
                'EPS': info.get('trailingEps', 0),
                'Revenue': info.get('totalRevenue', 0),
                'Profit': info.get('grossProfits', 0)
            }
    except Exception as e:
        print(f"Yahoo Fail: {e}")

    # 2. FALLBACK: TRADINGVIEW (TVDATAFEED)
    if tv:
        try:
            # Exchange IDX
            df_tv = tv.get_hist(symbol=symbol, exchange='IDX', interval=Interval.in_daily, n_bars=1)
            if df_tv is not None and not df_tv.empty:
                curr_tv = df_tv.iloc[-1]
                return {
                    'Source': 'TradingView (Live)',
                    'Open': curr_tv['open'], 'High': curr_tv['high'],
                    'Low': curr_tv['low'], 'Close': curr_tv['close'],
                    'Volume': curr_tv['volume'],
                    'Value_Est': curr_tv['close'] * curr_tv['volume'],
                    # Fundamental Data tidak tersedia di free TVDatafeed
                    'MarketCap': 0, 'PE': 0, 'EPS': 0, 'Revenue': 0, 'Profit': 0
                }
        except Exception as e:
            print(f"TV Fail: {e}")
            
    return None

# ==========================================
# 4. BANDARMOLOGY LOGIC
# ==========================================

def clean_running_trade(df_input):
    df = df_input.copy()
    df.columns = df.columns.str.strip().str.capitalize()
    
    rename_map = {
        'Time': 'Time', 'Waktu': 'Time', 'Price': 'Price', 'Harga': 'Price',
        'Lot': 'Lot', 'Vol': 'Lot', 'Volume': 'Lot',
        'Buyer': 'Buyer', 'B': 'Buyer', 'Broker Beli': 'Buyer',
        'Seller': 'Seller', 'S': 'Seller', 'Broker Jual': 'Seller'
    }
    
    new_cols = {c: rename_map[c] for c in df.columns if c in rename_map}
    df.rename(columns=new_cols, inplace=True)
    
    if not {'Price', 'Lot', 'Buyer', 'Seller'}.issubset(df.columns):
        raise ValueError("Kolom Wajib (Price, Lot, Buyer, Seller) tidak lengkap.")

    def clean_num(x): 
        return int(re.sub(r'[^\d]', '', str(x).split('(')[0])) if pd.notnull(x) else 0
    
    def clean_code(x): 
        return str(x).upper().split()[0].strip()

    try:
        df['Price_Clean'] = df['Price'].apply(clean_num)
        df['Lot_Clean'] = df['Lot'].apply(clean_num)
        df['Buyer_Code'] = df['Buyer'].apply(clean_code)
        df['Seller_Code'] = df['Seller'].apply(clean_code)
        
        df['Value'] = df['Lot_Clean'] * 100 * df['Price_Clean']
        return df[df['Value'] > 0]
    except Exception as e:
        raise ValueError(f"Parsing Error: {e}")

def get_broker_summary(df):
    buy = df.groupby('Buyer_Code').agg({'Value': 'sum', 'Lot_Clean': 'sum'}).rename(columns={'Value': 'Buy_Val', 'Lot_Clean': 'Buy_Vol'})
    sell = df.groupby('Seller_Code').agg({'Value': 'sum', 'Lot_Clean': 'sum'}).rename(columns={'Value': 'Sell_Val', 'Lot_Clean': 'Sell_Vol'})
    
    summ = pd.merge(buy, sell, left_index=True, right_index=True, how='outer').fillna(0)
    summ['Net_Val'] = summ['Buy_Val'] - summ['Sell_Val']
    summ['Total_Val'] = summ['Buy_Val'] + summ['Sell_Val']
    
    # Enrich Data
    summ.index.name = 'Code'
    summ = summ.reset_index()
    summ['Name'] = summ['Code'].apply(lambda x: get_broker_info(x)[1])
    summ['Type'] = summ['Code'].apply(lambda x: get_broker_info(x)[2])
    
    return summ.sort_values('Net_Val', ascending=False)

def build_sankey(df, top_n=15, metric='Value'):
    flow = df.groupby(['Buyer_Code', 'Seller_Code'])[metric].sum().reset_index()
    flow = flow.sort_values(metric, ascending=False).head(top_n)
    
    flow['B_Label'] = flow['Buyer_Code'] + " (B)"
    flow['S_Label'] = flow['Seller_Code'] + " (S)"
    
    all_nodes = list(set(flow['B_Label']).union(set(flow['S_Label'])))
    node_map = {k: v for v, k in enumerate(all_nodes)}
    
    b_totals = flow.groupby('B_Label')[metric].sum()
    s_totals = flow.groupby('S_Label')[metric].sum()
    
    labels, colors = [], []
    
    for node in all_nodes:
        code = node.split()[0]
        b_type = get_broker_info(code)[2]
        color = COLOR_MAP.get(b_type, '#888')
        
        if node in b_totals:
            val_str = format_number_label(b_totals[node])
            labels.append(f"{code} {val_str}")
        else:
            val_str = format_number_label(s_totals.get(node, 0))
            labels.append(f"{val_str} {code}")
            
        colors.append(color)
        
    src = [node_map[x] for x in flow['B_Label']]
    tgt = [node_map[x] for x in flow['S_Label']]
    vals = flow[metric].tolist()
    
    l_colors = []
    for s_idx in src:
        c_hex = colors[s_idx].lstrip('#')
        rgb = tuple(int(c_hex[i:i+2], 16) for i in (0, 2, 4))
        l_colors.append(f"rgba({rgb[0]},{rgb[1]},{rgb[2]}, 0.6)")
        
    return labels, colors, src, tgt, vals, l_colors

def generate_smart_insight(summary_df):
    top_buyer = summary_df.iloc[0]
    top_seller = summary_df.iloc[-1]
    
    buyer_code = top_buyer['Code']
    buyer_val = top_buyer['Net_Val']
    buyer_type = top_buyer['Type']
    
    seller_code = top_seller['Code']
    seller_val = abs(top_seller['Net_Val'])
    
    action = "AKUMULASI" if buyer_val > (seller_val * 1.2) else "DISTRIBUSI" if seller_val > (buyer_val * 1.2) else "NETRAL / TRADING"
    
    insight = f"""
    ### 🧠 AI Smart Insight
    **Kesimpulan Pasar Saat Ini: {action}**
    
    Berdasarkan data aliran dana di atas, terlihat **{get_broker_info(buyer_code)[1]} ({buyer_code})** melakukan pembelian bersih (Net Buy) masif sebesar **Rp {format_number_label(buyer_val)}**. 
    Broker ini tergolong **{buyer_type}**.
    
    Di sisi lain, tekanan jual terbesar datang dari **{seller_code}** senilai **Rp {format_number_label(seller_val)}**.
    
    **Interpretasi:**
    {'Jika Broker ' + buyer_type + ' terus mengakumulasi, ini bisa menjadi indikasi Smart Money sedang masuk.' if action == 'AKUMULASI' else 'Waspada tekanan jual yang lebih dominan dari pembelian.'}
    """
    return insight

# ==========================================
# 5. UI PAGES
# ==========================================

def login_page():
    inject_custom_css()
    components.html("""<script>
    const i=window.parent.document.querySelectorAll('input[type="password"]');
    i.forEach(e=>{e.setAttribute('inputmode','numeric');e.setAttribute('pattern','[0-9]*');});
    </script>""", height=0)
    
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("<br><br><h1 style='text-align:center'>🔒 SYSTEM LOCKED</h1>", unsafe_allow_html=True)
        with st.form("login"):
            pin = st.text_input("PIN", type="password", placeholder="• • • • • •", label_visibility="collapsed")
            if st.form_submit_button("UNLOCK"):
                if pin == "241130":
                    st.session_state['authenticated'] = True
                    st.rerun()
                else: st.error("ACCESS DENIED")

def market_intelligence_page():
    st.header("🌍 Market Intelligence (Live)")
    
    col_search, col_btn = st.columns([3, 1])
    with col_search:
        symbol = st.text_input("Cari Kode Saham (Contoh: BBCA, BUMI)", value="BBCA").upper()
    with col_btn:
        st.write("")
        st.write("")
        btn_search = st.button("🔍 Analisis Live")
        
    if btn_search or symbol:
        with st.spinner(f"Mengambil Data {symbol}..."):
            data = get_stock_details(symbol)
            
        if data:
            # Source indicator
            st.caption(f"Data Source: {data.get('Source', 'Unknown')}")
            
            # Main Metrics
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Close", f"Rp {data['Close']:,.0f}")
            m2.metric("Open", f"Rp {data['Open']:,.0f}")
            m3.metric("Volume", format_number_label(data['Volume']))
            m4.metric("Value Est.", f"Rp {format_number_label(data['Value_Est'])}")
            
            st.divider()
            
            # Chart & Financials
            t1, t2 = st.tabs(["📈 Chart & Trend", "💰 Financial Insight"])
            
            with t1:
                # Charting fallback
                try:
                    ticker = yf.Ticker(f"{symbol}.JK")
                    hist = ticker.history(period="3mo")
                    if not hist.empty:
                        fig = go.Figure(data=[go.Candlestick(x=hist.index,
                                open=hist['Open'], high=hist['High'],
                                low=hist['Low'], close=hist['Close'])])
                        fig.update_layout(height=400, title=f"Pergerakan Harga {symbol} (3 Bulan)", template="plotly_dark")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Chart Data Unavailable from Yahoo Finance.")
                except: st.warning("Chart Error.")
                
            with t2:
                if data['MarketCap'] > 0: # Only show if data valid
                    f1, f2 = st.columns(2)
                    with f1:
                        st.subheader("Revenue vs Earnings")
                        rev = data['Revenue']
                        earn = data['Profit']
                        fig_fin = go.Figure(data=[
                            go.Bar(name='Revenue', x=['TTM'], y=[rev], marker_color='#00E396'),
                            go.Bar(name='Gross Profit', x=['TTM'], y=[earn], marker_color='#775DD0')
                        ])
                        fig_fin.update_layout(barmode='group', height=300, template="plotly_dark")
                        st.plotly_chart(fig_fin, use_container_width=True)
                    with f2:
                        st.subheader("Fundamental Key")
                        st.dataframe(pd.DataFrame({
                            'Metric': ['Market Cap', 'PE Ratio', 'EPS'],
                            'Value': [format_number_label(data['MarketCap']), f"{data['PE']:.2f}x", f"{data['EPS']:.2f}"]
                        }), hide_index=True, use_container_width=True)
                else:
                    st.info("Data Fundamental tidak tersedia untuk sumber data ini (TradingView Fallback).")
        else:
            st.error("Saham tidak ditemukan atau koneksi bermasalah di kedua server (Yahoo & TradingView).")

def bandarmology_page():
    # DIRECTORY HANDLING
    DB_ROOT = "database"
    
    with st.sidebar:
        st.subheader("📂 Data Source")
        source_type = st.radio("Pilih Sumber:", ["Database Folder", "Upload Manual"], label_visibility="collapsed")
        
        df_raw = None
        current_stock = "UNKNOWN"
        
        if source_type == "Database Folder":
            if os.path.exists(DB_ROOT):
                stocks = sorted([d for d in os.listdir(DB_ROOT) if os.path.isdir(os.path.join(DB_ROOT, d))])
                sel_stock = st.selectbox("Saham", stocks)
                if sel_stock:
                    path_stock = os.path.join(DB_ROOT, sel_stock)
                    years = sorted(os.listdir(path_stock))
                    sel_year = st.selectbox("Tahun", years) if years else None
                    if sel_year:
                        path_year = os.path.join(path_stock, sel_year)
                        months = sorted(os.listdir(path_year))
                        sel_month = st.selectbox("Bulan", months) if months else None
                        if sel_month:
                            path_month = os.path.join(path_year, sel_month)
                            files = sorted([f for f in os.listdir(path_month) if f.endswith('csv') or f.endswith('xlsx')])
                            sel_file = st.selectbox("Tanggal", files)
                            
                            if sel_file and st.button("Load Data"):
                                fp = os.path.join(path_month, sel_file)
                                try:
                                    df_raw = pd.read_csv(fp) if fp.endswith('csv') else pd.read_excel(fp)
                                    current_stock = sel_stock
                                except: st.error("Gagal baca file")
            else:
                st.warning(f"Buat folder '{DB_ROOT}' di root directory.")
        else:
            uploaded = st.file_uploader("Upload CSV/XLSX", type=['csv','xlsx'])
            if uploaded:
                try:
                    df_raw = pd.read_csv(uploaded) if uploaded.name.endswith('csv') else pd.read_excel(uploaded)
                    current_stock = "UPLOADED"
                except: st.error("Format File Salah")

    # MAIN ANALYSIS
    if df_raw is not None:
        try:
            df = clean_running_trade(df_raw)
            summ = get_broker_summary(df)
            
            st.title(f"📊 Analisis Broker: {current_stock}")
            
            # --- SUMMARY STATS ---
            tot_val = df['Value'].sum()
            f_share = summ[summ['Type']=='Foreign']['Total_Val'].sum() / (tot_val*2) * 100
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Transaksi", f"Rp {format_number_label(tot_val)}")
            c2.metric("Total Volume", f"{df['Lot_Clean'].sum():,.0f} Lot")
            c3.metric("Partisipasi Asing", f"{f_share:.1f}%")
            
            st.divider()
            
            # --- TOP BROKER TABLE ---
            st.subheader("🏆 Top Broker Summary")
            
            def color_row(row):
                color = '#00E396' if row['Net_Val'] > 0 else '#FF4560'
                return [f'color: {color}; font-weight: bold' if col == 'Net_Val' else '' for col in row.index]

            tabs = st.tabs(["ALL", "ASING", "BUMN", "LOKAL"])
            categories = ['All', 'Foreign', 'BUMN', 'Local']
            
            for tab, cat in zip(tabs, categories):
                with tab:
                    data = summ if cat == 'All' else summ[summ['Type'] == cat]
                    if not data.empty:
                        show = data[['Code', 'Name', 'Total_Val', 'Net_Val']].copy()
                        st.dataframe(
                            show.style.format({
                                'Total_Val': format_number_label, 
                                'Net_Val': format_number_label
                            }).applymap(lambda v: f'color: {"#00E396" if v>0 else "#FF4560"}', subset=['Net_Val']),
                            use_container_width=True, height=350,
                            column_config={"Code": "Kode", "Name": "Sekuritas", "Total_Val": "Total Value", "Net_Val": "Net Buy/Sell"}
                        )
                    else: st.info("Data Kosong")
            
            # --- SANKEY VISUALIZATION ---
            st.subheader("🕸️ Peta Aliran Dana (Broker Flow)")
            
            sc1, sc2 = st.columns([2,1])
            with sc1:
                metrik_viz = st.radio("Metrik:", ["Value (Dana)", "Lot (Barang)"], horizontal=True)
            with sc2:
                top_n = st.slider("Jml Interaksi", 5, 50, 15)
                
            col_target = 'Value' if "Value" in metrik_viz else 'Lot_Clean'
            
            try:
                lbl, col, src, tgt, val, l_col = build_sankey(df, top_n, col_target)
                fig = go.Figure(data=[go.Sankey(
                    node=dict(pad=20, thickness=20, line=dict(color="black", width=0.5), label=lbl, color=col),
                    link=dict(source=src, target=tgt, value=val, color=l_col)
                )])
                fig.update_layout(height=600, margin=dict(l=10,r=10,t=10,b=10), font=dict(size=12))
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown(f"""
                <div style='text-align: center; margin-bottom: 10px;'>
                    <span class='tag tag-Foreign'>ASING</span>
                    <span class='tag tag-BUMN'>BUMN</span>
                    <span class='tag tag-Local'>LOKAL</span>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"<div class='insight-box'>{generate_smart_insight(summ)}</div>", unsafe_allow_html=True)
                
            except Exception as e: st.warning(f"Gagal memuat visualisasi: {e}")

        except Exception as e: st.error(f"Error Processing Data: {e}")
    else:
        st.info("👈 Silakan pilih data dari Sidebar untuk memulai analisis.")

# ==========================================
# 6. MAIN APP CONTROLLER
# ==========================================

def main():
    inject_custom_css()
    
    if st.session_state['authenticated']:
        st.markdown(get_stock_ticker(), unsafe_allow_html=True)
        
        with st.sidebar:
            st.title("🦅 Bandarmology Pro")
            page = st.radio("Menu Navigasi", ["📊 Bandarmology", "🌍 Market Intelligence"])
            st.divider()
            is_dark = st.toggle("Dark Mode", value=True)
            st.session_state['dark_mode'] = is_dark
            if st.button("Logout"):
                st.session_state['authenticated'] = False
                st.rerun()
                
        if page == "📊 Bandarmology":
            bandarmology_page()
        else:
            market_intelligence_page()
            
        st.markdown("<div class='footer'>© 2025 PT Catindo Bagus Perkasa | Market Data Delay 15 Mins</div>", unsafe_allow_html=True)
    else:
        login_page()

if __name__ == "__main__":
    main()
