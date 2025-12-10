import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import os
import requests
import yfinance as yf
import streamlit.components.v1 as components 
from datetime import datetime

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
}

COLOR_MAP = {
    'Foreign': '#00E396', 
    'BUMN': '#FEB019',    
    'Local': '#775DD0',   
    'Unknown': '#546E7A'  
}

if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
if 'dark_mode' not in st.session_state: st.session_state['dark_mode'] = True

# ==========================================
# 2. HELPER FUNCTIONS & STYLING
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
        .stTextInput input {{
            text-align: center; font-size: 32px !important; letter-spacing: 15px;
            font-weight: bold; padding: 20px; border-radius: 15px;
            background-color: {card_bg}; color: {text_color}; border: 1px solid #444;
        }}
        .stButton button {{ width: 100%; height: 50px; font-size: 18px; border-radius: 12px; }}
        thead tr th:first-child {{display:none}} tbody th {{display:none}}
        .tag {{ padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; color: white; display: inline-block; margin-right: 5px;}}
        .tag-Foreign {{ background-color: {COLOR_MAP['Foreign']}; }}
        .tag-BUMN {{ background-color: {COLOR_MAP['BUMN']}; color: black; }}
        .tag-Local {{ background-color: {COLOR_MAP['Local']}; }}
        .ticker-wrap {{
            width: 100%; background-color: {card_bg}; padding: 12px 0;
            border-bottom: 1px solid #333; position: sticky; top: 0; z-index: 99;
        }}
        .ticker-item {{ margin: 0 25px; font-weight: bold; font-family: 'Courier New', monospace; font-size: 15px; }}
        .up {{color: #00E396;}} .down {{color: #FF4560;}}
        .footer {{
            position: fixed; left: 0; bottom: 0; width: 100%; background: {card_bg};
            text-align: center; padding: 8px; font-size: 12px; border-top: 1px solid #333; z-index: 1000;
        }}
        .insight-box {{
            background-color: {card_bg}; padding: 20px; border-radius: 10px; border-left: 5px solid {COLOR_MAP['Foreign']};
            margin-top: 20px; margin-bottom: 50px;
        }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. KONEKSI DATA (ANTI-BLOKIR)
# ==========================================

# Membuat Session khusus agar dianggap browser (Bukan Bot)
def get_yahoo_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    return session

@st.cache_data(ttl=120) # Cache 2 menit
def get_stock_ticker():
    tickers = ["BBCA", "BBRI", "BMRI", "BBNI", "TLKM", "ASII", "GOTO", "BUMI", "ADRO", "PGAS"]
    yf_tickers = [f"{t}.JK" for t in tickers]
    
    try:
        # Gunakan session custom
        data = yf.download(yf_tickers, period="2d", progress=False, session=get_yahoo_session())['Close']
        
        if data.empty: return "<div class='ticker-wrap'>Market Data Offline</div>"
        
        last = data.iloc[-1]
        prev = data.iloc[-2] if len(data) > 1 else last
        
        html = ""
        for t in tickers:
            tk = f"{t}.JK"
            try:
                p_now = last[tk]; p_prev = prev[tk]
                if pd.isna(p_now): continue
                
                chg = p_now - p_prev
                pct = (chg/p_prev)*100 if p_prev != 0 else 0
                cls = "up" if chg >= 0 else "down"
                sgn = "+" if chg >= 0 else ""
                html += f"<span class='ticker-item'>{t} {int(p_now):,} <span class='{cls}'>({sgn}{pct:.2f}%)</span></span>"
            except: continue
            
        return f"<div class='ticker-wrap'><marquee scrollamount='8'>{html}</marquee></div>"
    except:
        return "<div class='ticker-wrap'>Connection Limited (Try Refresh)</div>"

@st.cache_data(ttl=600) # Cache 10 menit untuk detail
def get_stock_details(symbol):
    symbol = symbol.upper().replace(".JK", "")
    try:
        session = get_yahoo_session()
        ticker = yf.Ticker(f"{symbol}.JK", session=session)
        
        # Ambil history dulu (paling ringan)
        hist = ticker.history(period="1d")
        if hist.empty: return None
        
        curr = hist.iloc[-1]
        info = ticker.info # Ini yang sering berat
        
        return {
            'Open': curr['Open'], 'High': curr['High'], 
            'Low': curr['Low'], 'Close': curr['Close'],
            'Volume': curr['Volume'],
            'Value_Est': curr['Close'] * curr['Volume'],
            'MarketCap': info.get('marketCap', 0),
            'PE': info.get('trailingPE', 0),
            'EPS': info.get('trailingEps', 0),
            'Revenue': info.get('totalRevenue', 0),
            'Profit': info.get('grossProfits', 0)
        }
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

# ==========================================
# 4. LOGIKA ANALISIS
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
    except Exception as e: raise ValueError(f"Parsing Error: {e}")

def get_broker_summary(df):
    buy = df.groupby('Buyer_Code').agg({'Value': 'sum', 'Lot_Clean': 'sum'}).rename(columns={'Value': 'Buy_Val', 'Lot_Clean': 'Buy_Vol'})
    sell = df.groupby('Seller_Code').agg({'Value': 'sum', 'Lot_Clean': 'sum'}).rename(columns={'Value': 'Sell_Val', 'Lot_Clean': 'Sell_Vol'})
    
    summ = pd.merge(buy, sell, left_index=True, right_index=True, how='outer').fillna(0)
    summ['Net_Val'] = summ['Buy_Val'] - summ['Sell_Val']
    summ['Total_Val'] = summ['Buy_Val'] + summ['Sell_Val']
    
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
        
        val = b_totals[node] if node in b_totals else s_totals.get(node, 0)
        labels.append(f"{code} {format_number_label(val)}")
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
    
    action = "AKUMULASI" if top_buyer['Net_Val'] > (abs(top_seller['Net_Val']) * 1.1) else "DISTRIBUSI" if abs(top_seller['Net_Val']) > (top_buyer['Net_Val'] * 1.1) else "NETRAL"
    
    return f"""
    ### 🧠 AI Insight: {action}
    **Top Buyer:** {top_buyer['Code']} ({top_buyer['Type']}) - Net Buy: Rp {format_number_label(top_buyer['Net_Val'])}
    **Top Seller:** {top_seller['Code']} ({top_seller['Type']}) - Net Sell: Rp {format_number_label(abs(top_seller['Net_Val']))}
    """

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
        st.markdown("<br><h1 style='text-align:center'>🔒 SECURE ACCESS</h1>", unsafe_allow_html=True)
        with st.form("login"):
            pin = st.text_input("PIN", type="password", placeholder="• • • • • •", label_visibility="collapsed")
            if st.form_submit_button("UNLOCK"):
                if pin == "241130":
                    st.session_state['authenticated'] = True
                    st.rerun()
                else: st.error("Wrong PIN")

def market_intelligence_page():
    st.header("🌍 Market Intelligence (Live)")
    
    c_search, c_btn = st.columns([3,1])
    with c_search:
        symbol = st.text_input("Kode Saham", value="BBCA").upper()
    with c_btn:
        st.write("")
        st.write("")
        refresh = st.button("🔄 Refresh Data")
    
    if symbol:
        with st.spinner(f"Connecting to Exchange ({symbol})..."):
            data = get_stock_details(symbol)
            
        if data:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Close", f"Rp {data['Close']:,.0f}")
            m2.metric("Open", f"Rp {data['Open']:,.0f}")
            m3.metric("Vol", format_number_label(data['Volume']))
            m4.metric("Val", format_number_label(data['Value_Est']))
            
            st.divider()
            
            t1, t2 = st.tabs(["📈 Chart", "📊 Financials"])
            with t1:
                try:
                    tick = yf.Ticker(f"{symbol}.JK", session=get_yahoo_session())
                    hist = tick.history(period="3mo")
                    if not hist.empty:
                        fig = go.Figure(data=[go.Candlestick(x=hist.index,
                                open=hist['Open'], high=hist['High'],
                                low=hist['Low'], close=hist['Close'])])
                        fig.update_layout(height=400, title=f"Trend {symbol}", template="plotly_dark")
                        st.plotly_chart(fig, use_container_width=True)
                except: st.warning("Chart unavailable")
                
            with t2:
                if data.get('MarketCap', 0) > 0:
                    f1, f2 = st.columns(2)
                    with f1:
                        st.subheader("Revenue vs Profit")
                        fig = go.Figure(data=[
                            go.Bar(name='Rev', x=['TTM'], y=[data['Revenue']], marker_color='#00E396'),
                            go.Bar(name='Profit', x=['TTM'], y=[data['Profit']], marker_color='#775DD0')
                        ])
                        fig.update_layout(height=300, template="plotly_dark")
                        st.plotly_chart(fig, use_container_width=True)
                    with f2:
                        st.subheader("Ratios")
                        st.dataframe(pd.DataFrame({
                            'Metric': ['Market Cap', 'PE Ratio', 'EPS'],
                            'Value': [format_number_label(data['MarketCap']), f"{data['PE']:.2f}", f"{data['EPS']:.2f}"]
                        }), hide_index=True, use_container_width=True)
        else:
            st.error(f"Gagal mengambil data {symbol}. Coba refresh atau cek koneksi.")

def bandarmology_page():
    DB_ROOT = "database"
    with st.sidebar:
        st.subheader("📂 Source")
        src = st.radio("Type", ["Database", "Upload"], label_visibility="collapsed")
        df_raw = None
        current_stock = "UNKNOWN"
        
        if src == "Database":
            if os.path.exists(DB_ROOT):
                stocks = sorted(os.listdir(DB_ROOT))
                sel_s = st.selectbox("Stock", stocks)
                if sel_s:
                    p_s = os.path.join(DB_ROOT, sel_s)
                    years = sorted(os.listdir(p_s))
                    sel_y = st.selectbox("Year", years) if years else None
                    if sel_y:
                        p_y = os.path.join(p_s, sel_y)
                        months = sorted(os.listdir(p_y))
                        sel_m = st.selectbox("Month", months) if months else None
                        if sel_m:
                            p_m = os.path.join(p_y, sel_m)
                            files = sorted([f for f in os.listdir(p_m) if f.endswith(('csv','xlsx'))])
                            sel_f = st.selectbox("Date", files)
                            if sel_f and st.button("Load"):
                                fp = os.path.join(p_m, sel_f)
                                try:
                                    df_raw = pd.read_csv(fp) if fp.endswith('csv') else pd.read_excel(fp)
                                    current_stock = sel_s
                                except: st.error("Load failed")
            else: st.warning("No database folder")
        else:
            upl = st.file_uploader("Upload", type=['csv','xlsx'])
            if upl:
                try:
                    df_raw = pd.read_csv(upl) if upl.name.endswith('csv') else pd.read_excel(upl)
                    current_stock = "UPLOADED"
                except: st.error("File error")

    if df_raw is not None:
        try:
            df = clean_running_trade(df_raw)
            summ = get_broker_summary(df)
            
            st.title(f"📊 Analisis: {current_stock}")
            
            c1, c2, c3 = st.columns(3)
            tot_v = df['Value'].sum()
            c1.metric("Val", format_number_label(tot_v))
            c2.metric("Vol", f"{df['Lot_Clean'].sum():,.0f}")
            f_share = summ[summ['Type']=='Foreign']['Total_Val'].sum() / (tot_v*2) * 100
            c3.metric("Foreign Flow", f"{f_share:.1f}%")
            
            st.divider()
            
            # Table
            st.subheader("🏆 Top Broker")
            def color_net(val): return f'color: {"#00E396" if val>0 else "#FF4560"}; font-weight: bold'
            
            tabs = st.tabs(["ALL", "ASING", "BUMN", "LOKAL"])
            cats = ['All', 'Foreign', 'BUMN', 'Local']
            
            for tab, cat in zip(tabs, cats):
                with tab:
                    d = summ if cat == 'All' else summ[summ['Type']==cat]
                    if not d.empty:
                        show = d[['Code','Name','Total_Val','Net_Val']].copy()
                        st.dataframe(show.style.format({
                            'Total_Val': format_number_label, 'Net_Val': format_number_label
                        }).map(color_net, subset=['Net_Val']), use_container_width=True, height=350)
            
            # Sankey
            st.subheader("🕸️ Flow Map")
            c_opt1, c_opt2 = st.columns([2,1])
            with c_opt1: mode = st.radio("Metric", ["Value","Lot"], horizontal=True)
            with c_opt2: n = st.slider("Nodes", 5, 50, 15)
            
            met = 'Value' if mode == "Value" else 'Lot_Clean'
            try:
                lbl, col, src, tgt, val, l_col = build_sankey(df, n, met)
                fig = go.Figure(data=[go.Sankey(
                    node=dict(pad=15, thickness=20, line=dict(color="black", width=0.5), label=lbl, color=col),
                    link=dict(source=src, target=tgt, value=val, color=l_col)
                )])
                fig.update_layout(height=600, margin=dict(l=10,r=10,b=10,t=10), font=dict(size=12))
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown(f"""<div style='text-align:center'><span class='tag tag-Foreign'>ASING</span><span class='tag tag-BUMN'>BUMN</span><span class='tag tag-Local'>LOKAL</span></div>""", unsafe_allow_html=True)
                st.markdown(f"<div class='insight-box'>{generate_smart_insight(summ)}</div>", unsafe_allow_html=True)
            except: st.warning("Visualisasi butuh data lebih banyak")
            
        except Exception as e: st.error(f"Error: {e}")

def main():
    inject_custom_css()
    if st.session_state['authenticated']:
        st.markdown(get_stock_ticker(), unsafe_allow_html=True)
        with st.sidebar:
            st.title("🦅 Pro Tools")
            page = st.radio("Menu", ["Bandarmology", "Market Intel"])
            st.divider()
            if st.button("Logout"):
                st.session_state['authenticated'] = False
                st.rerun()
        
        if page == "Bandarmology": bandarmology_page()
        else: market_intelligence_page()
        
        st.markdown("<div class='footer'>© 2025 PT Catindo Bagus Perkasa</div>", unsafe_allow_html=True)
    else: login_page()

if __name__ == "__main__": main()
