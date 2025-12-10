import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import io
import os
import yfinance as yf
import streamlit.components.v1 as components 
from datetime import datetime

# ==========================================
# 1. KONFIGURASI & DATABASE BROKER
# ==========================================
st.set_page_config(
    page_title="Bandarmology Pro",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DATABASE BROKER (MAPPING) ---
# Referensi broker berdasarkan screenshot & data umum BEI
BROKER_DB = {
    # ASING (FOREIGN) - Biasanya Hijau
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
    'AG': {'name': 'Kiwoom Sekuritas', 'type': 'Foreign'}, # Korea (Asing)
    'BQ': {'name': 'Korea Investment', 'type': 'Foreign'}, 

    # BUMN (STATE OWNED) - Biasanya Orange/Kuning/Merah BUMN
    'CC': {'name': 'Mandiri Sekuritas', 'type': 'BUMN'},
    'NI': {'name': 'BNI Sekuritas', 'type': 'BUMN'},
    'OD': {'name': 'BRI Danareksa', 'type': 'BUMN'},
    'DX': {'name': 'Bahana Sekuritas', 'type': 'BUMN'},

    # LOKAL (DOMESTIC/RETAIL) - Biasanya Ungu/Abu
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
}

# --- PALET WARNA (Sesuai Request) ---
COLOR_MAP = {
    'Foreign': '#00E396', # Hijau Terang (Asing)
    'BUMN': '#FEB019',    # Orange/Emas (BUMN)
    'Local': '#775DD0',   # Ungu (Lokal/Ritel/Bandar Lokal)
    'Unknown': '#546E7A'  # Abu-abu
}

# Inisialisasi Session State
if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
if 'dark_mode' not in st.session_state: st.session_state['dark_mode'] = True

# ==========================================
# 2. HELPER FUNCTIONS (UTILITIES)
# ==========================================

def get_broker_info(code):
    """Mendapatkan Nama Lengkap & Tipe Broker"""
    code = str(code).upper().strip()
    data = BROKER_DB.get(code, {'name': 'Sekuritas Lain', 'type': 'Unknown'})
    return code, data['name'], data['type']

def format_number_label(value):
    """Format angka besar (Milyar/Triliun)"""
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
        
        /* PIN Pad Styles */
        .stTextInput input {{
            text-align: center; font-size: 32px !important; letter-spacing: 15px;
            font-weight: bold; padding: 20px; border-radius: 15px;
            background-color: {card_bg}; color: {text_color}; border: 1px solid #444;
        }}
        .stButton button {{ width: 100%; height: 60px; font-size: 20px; border-radius: 12px; }}
        
        /* Custom Table Header */
        thead tr th:first-child {{display:none}}
        tbody th {{display:none}}
        
        /* Tags for Broker Type */
        .tag {{
            padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; color: white;
        }}
        .tag-Foreign {{ background-color: {COLOR_MAP['Foreign']}; }}
        .tag-BUMN {{ background-color: {COLOR_MAP['BUMN']}; color: black; }}
        .tag-Local {{ background-color: {COLOR_MAP['Local']}; }}
        .tag-Unknown {{ background-color: {COLOR_MAP['Unknown']}; }}

        /* Running Text */
        .ticker-wrap {{
            width: 100%; background-color: {card_bg}; padding: 10px 0;
            border-bottom: 1px solid #333; position: sticky; top: 0; z-index: 99;
        }}
        .ticker-item {{ margin: 0 20px; font-weight: bold; font-family: monospace; font-size: 14px; }}
        .up {{color: #00E396;}} .down {{color: #FF4560;}}
        
        /* Footer */
        .footer {{
            position: fixed; left: 0; bottom: 0; width: 100%; background: {card_bg};
            text-align: center; padding: 5px; font-size: 11px; border-top: 1px solid #333;
        }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. CORE LOGIC (DATA PROCESSING)
# ==========================================

@st.cache_data(ttl=300)
def get_stock_ticker():
    tickers = ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "TLKM.JK", "ASII.JK", "GOTO.JK", "BUMI.JK", "ADRO.JK"]
    try:
        data = yf.download(tickers, period="2d", progress=False)['Close']
        if data.empty or len(data) < 2: return ""
        
        last = data.iloc[-1]
        prev = data.iloc[-2]
        
        html = ""
        for t in tickers:
            sym = t.replace(".JK", "")
            try:
                p_now = last[t]; p_prev = prev[t]
                chg = p_now - p_prev
                pct = (chg/p_prev)*100
                cls = "up" if chg >= 0 else "down"
                sgn = "+" if chg >= 0 else ""
                html += f"<span class='ticker-item'>{sym} {int(p_now):,} <span class='{cls}'>({sgn}{pct:.2f}%)</span></span>"
            except: continue
        return f"<div class='ticker-wrap'><marquee>{html}</marquee></div>"
    except: return ""

def clean_running_trade(df_input):
    df = df_input.copy()
    df.columns = df.columns.str.strip().str.capitalize()
    
    # Mapping Header Fleksibel
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

    # Parsing Functions
    def clean_num(x): 
        return int(re.sub(r'[^\d]', '', str(x).split('(')[0])) if pd.notnull(x) else 0
    
    def clean_code(x): 
        return str(x).upper().split()[0].strip()

    try:
        df['Price_Clean'] = df['Price'].apply(clean_num)
        df['Lot_Clean'] = df['Lot'].apply(clean_num)
        df['Buyer_Code'] = df['Buyer'].apply(clean_code)
        df['Seller_Code'] = df['Seller'].apply(clean_code)
        
        # Enrich Broker Type
        df['Buyer_Type'] = df['Buyer_Code'].apply(lambda x: get_broker_info(x)[2])
        df['Seller_Type'] = df['Seller_Code'].apply(lambda x: get_broker_info(x)[2])
        
        df['Value'] = df['Lot_Clean'] * 100 * df['Price_Clean']
        return df[df['Value'] > 0]
    except Exception as e:
        raise ValueError(f"Parsing Error: {e}")

def get_broker_summary(df):
    # Buy Stats
    buy = df.groupby('Buyer_Code').agg({'Value': 'sum', 'Lot_Clean': 'sum'}).rename(columns={'Value': 'Buy_Val', 'Lot_Clean': 'Buy_Vol'})
    # Sell Stats
    sell = df.groupby('Seller_Code').agg({'Value': 'sum', 'Lot_Clean': 'sum'}).rename(columns={'Value': 'Sell_Val', 'Lot_Clean': 'Sell_Vol'})
    
    summ = pd.merge(buy, sell, left_index=True, right_index=True, how='outer').fillna(0)
    
    summ['Net_Val'] = summ['Buy_Val'] - summ['Sell_Val']
    summ['Net_Vol'] = summ['Buy_Vol'] - summ['Sell_Vol']
    summ['Total_Val'] = summ['Buy_Val'] + summ['Sell_Val']
    
    # Enrich Data
    summ.index.name = 'Code'
    summ = summ.reset_index()
    summ['Name'] = summ['Code'].apply(lambda x: get_broker_info(x)[1])
    summ['Type'] = summ['Code'].apply(lambda x: get_broker_info(x)[2])
    
    return summ.sort_values('Net_Val', ascending=False)

def build_sankey(df, top_n=15, metric='Value'):
    # Grouping
    flow = df.groupby(['Buyer_Code', 'Seller_Code'])[metric].sum().reset_index()
    flow = flow.sort_values(metric, ascending=False).head(top_n)
    
    # Labeling (Add Value to Label)
    flow['B_Label'] = flow['Buyer_Code'] + " (B)"
    flow['S_Label'] = flow['Seller_Code'] + " (S)"
    
    all_nodes = list(set(flow['B_Label']).union(set(flow['S_Label'])))
    node_map = {k: v for v, k in enumerate(all_nodes)}
    
    # Totals for Labels
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
        
    # Links
    src = [node_map[x] for x in flow['B_Label']] # Buyer source? No, usually Seller -> Buyer is flow of goods. Buyer -> Seller is flow of money.
    # Logic User: "Buyer (Kiri) -> Seller (Kanan)" (Flow of Money)
    # Source = Buyer, Target = Seller
    
    tgt = [node_map[x] for x in flow['S_Label']]
    vals = flow[metric].tolist()
    
    # Link Colors (Transparent version of Source/Buyer)
    l_colors = []
    for s_idx in src:
        c_hex = colors[s_idx].lstrip('#')
        rgb = tuple(int(c_hex[i:i+2], 16) for i in (0, 2, 4))
        l_colors.append(f"rgba({rgb[0]},{rgb[1]},{rgb[2]}, 0.6)")
        
    return labels, colors, src, tgt, vals, l_colors

# ==========================================
# 4. DIRECTORY & FILE HANDLING
# ==========================================
DB_ROOT = "database" # Ganti sesuai nama folder root

def get_available_stocks():
    if not os.path.exists(DB_ROOT): return []
    return sorted([d for d in os.listdir(DB_ROOT) if os.path.isdir(os.path.join(DB_ROOT, d))])

def get_years(stock):
    path = os.path.join(DB_ROOT, stock)
    return sorted(os.listdir(path)) if os.path.exists(path) else []

def get_months(stock, year):
    path = os.path.join(DB_ROOT, stock, year)
    return sorted(os.listdir(path)) if os.path.exists(path) else []

def get_dates(stock, year, month):
    path = os.path.join(DB_ROOT, stock, year, month)
    if not os.path.exists(path): return []
    files = [f for f in os.listdir(path) if f.endswith('.csv') or f.endswith('.xlsx')]
    return sorted(files)

# ==========================================
# 5. MAIN APP UI
# ==========================================

def login_page():
    inject_custom_css()
    # Numpad Hack
    components.html("""<script>
    const i=window.parent.document.querySelectorAll('input[type="password"]');
    i.forEach(e=>{e.setAttribute('inputmode','numeric');e.setAttribute('pattern','[0-9]*');});
    </script>""", height=0)
    
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("<br><br><h1 style='text-align:center'>🔒 ACCESS REQUIRED</h1>", unsafe_allow_html=True)
        with st.form("login"):
            pin = st.text_input("PIN", type="password", placeholder="• • • • • •", label_visibility="collapsed")
            if st.form_submit_button("UNLOCK SYSTEM"):
                if pin == "241130":
                    st.session_state['authenticated'] = True
                    st.rerun()
                else: st.error("ACCESS DENIED")

def main_dashboard():
    inject_custom_css()
    st.markdown(get_stock_ticker(), unsafe_allow_html=True)
    
    # SIDEBAR CONTROL
    with st.sidebar:
        st.title("🎛️ Control Panel")
        
        # --- DATA SOURCE SELECTOR ---
        source_type = st.radio("Sumber Data:", ["📂 Database Folder", "📤 Upload Manual"])
        
        df_raw = None
        current_stock = "UNKNOWN"
        
        if source_type == "📂 Database Folder":
            stocks = get_available_stocks()
            if not stocks:
                st.error(f"Folder '{DB_ROOT}' tidak ditemukan!")
            else:
                sel_stock = st.selectbox("Emiten", stocks)
                current_stock = sel_stock
                
                years = get_years(sel_stock)
                sel_year = st.selectbox("Tahun", years) if years else None
                
                months = get_months(sel_stock, sel_year) if sel_year else []
                sel_month = st.selectbox("Bulan", months) if months else None
                
                dates = get_dates(sel_stock, sel_year, sel_month) if sel_month else []
                sel_file = st.selectbox("Tanggal (File)", dates) if dates else None
                
                if sel_file:
                    file_path = os.path.join(DB_ROOT, sel_stock, sel_year, sel_month, sel_file)
                    if st.button("🚀 LOAD DATA"):
                        try:
                            if file_path.endswith('.csv'): df_raw = pd.read_csv(file_path)
                            else: df_raw = pd.read_excel(file_path)
                            st.success(f"Loaded: {sel_file}")
                        except Exception as e: st.error(f"Err: {e}")
                        
        else: # Upload Manual
            uploaded = st.file_uploader("Drop CSV/Excel", type=['csv','xlsx'])
            if uploaded:
                try:
                    if uploaded.name.endswith('.csv'): df_raw = pd.read_csv(uploaded)
                    else: df_raw = pd.read_excel(uploaded)
                    current_stock = "UPLOADED"
                except: st.error("File Error")

        st.divider()
        if st.button("Logout"): 
            st.session_state['authenticated'] = False
            st.rerun()

    # MAIN CONTENT
    if df_raw is not None:
        try:
            df = clean_running_trade(df_raw)
            summ = get_broker_summary(df)
            
            # --- HEADER ---
            st.title(f"📊 Analisis Bandarmology: {current_stock}")
            
            # --- SUMMARY CARDS ---
            tot_val = df['Value'].sum()
            tot_vol = df['Lot_Clean'].sum()
            
            # Hitung Dominasi Asing vs Lokal
            val_by_type = summ.groupby('Type')['Total_Val'].sum()
            f_val = val_by_type.get('Foreign', 0)
            l_val = val_by_type.get('Local', 0)
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Value", format_number_label(tot_val))
            c2.metric("Total Volume", f"{tot_vol:,.0f}")
            c3.metric("Asing (Foreign)", f"{(f_val/tot_val*100 if tot_val else 0):.1f}%", help="Partisipasi Broker Asing")
            c4.metric("Lokal (Local)", f"{(l_val/tot_val*100 if tot_val else 0):.1f}%")
            
            st.divider()
            
            # --- TABEL TOP BROKER (Styling Mirip Screenshot) ---
            st.subheader("🏆 Top Broker Summary")
            
            tab_all, tab_asing, tab_bumn, tab_lokal = st.tabs(["SEMUA", "ASING (Foreign)", "BUMN", "LOKAL"])
            
            def render_broker_table(data_df):
                if data_df.empty:
                    st.info("Tidak ada data untuk kategori ini.")
                    return
                
                # Custom Styling Function
                def color_net_val(val):
                    color = '#00E396' if val > 0 else '#FF4560'
                    return f'color: {color}; font-weight: bold;'
                
                def broker_tag(b_type):
                    return f'background-color: {COLOR_MAP.get(b_type, "#888")}; color: white; padding: 2px 5px; border-radius: 4px;'

                # Display Logic
                display_df = data_df[['Code', 'Name', 'Total_Val', 'Net_Val']].copy()
                
                # Kita pakai Styler bawaan Pandas untuk warna teks angka
                st.dataframe(
                    display_df.style
                    .format({'Total_Val': format_number_label, 'Net_Val': format_number_label})
                    .applymap(color_net_val, subset=['Net_Val']),
                    use_container_width=True,
                    height=400,
                    column_config={
                        "Code": "Kode",
                        "Name": "Sekuritas",
                        "Total_Val": "T. Val",
                        "Net_Val": "Net Val (Acc/Dist)"
                    }
                )

            with tab_all: render_broker_table(summ)
            with tab_asing: render_broker_table(summ[summ['Type'] == 'Foreign'])
            with tab_bumn: render_broker_table(summ[summ['Type'] == 'BUMN'])
            with tab_lokal: render_broker_table(summ[summ['Type'] == 'Local'])
            
            # --- LEGEND WARNA ---
            st.markdown(f"""
            <div style="display:flex; gap:15px; justify-content:center; margin-top:10px; margin-bottom:30px;">
                <span class="tag tag-Foreign">ASING (Foreign)</span>
                <span class="tag tag-BUMN">BUMN</span>
                <span class="tag tag-Local">LOKAL</span>
            </div>
            """, unsafe_allow_html=True)

            # --- SANKEY DIAGRAM ---
            st.subheader("🕸️ Peta Aliran Dana (Broker Flow)")
            
            s_col1, s_col2 = st.columns([3, 1])
            with s_col1:
                viz_type = st.radio("Metrik:", ["Value (Dana)", "Lot (Barang)"], horizontal=True)
            with s_col2:
                top_n = st.slider("Jml Interaksi", 5, 50, 15)
                
            met_col = 'Value' if "Value" in viz_type else 'Lot_Clean'
            
            try:
                lbl, col, src, tgt, val, l_col = build_sankey(df, top_n, met_col)
                fig = go.Figure(data=[go.Sankey(
                    node=dict(pad=20, thickness=20, line=dict(color="black", width=0.5), label=lbl, color=col),
                    link=dict(source=src, target=tgt, value=val, color=l_col)
                )])
                fig.update_layout(height=600, margin=dict(l=10, r=10, t=10, b=10), font=dict(size=12))
                st.plotly_chart(fig, use_container_width=True)
                
                # Label Bawah Visual
                st.caption(f"visualisasi: Aliran {viz_type} dari Buyer (Kiri) ke Seller (Kanan). Warna Node menunjukkan kategori broker.")
                
            except Exception as e: st.warning("Data tidak cukup untuk Sankey.")

        except Exception as e:
            st.error(f"Terjadi Kesalahan Pemrosesan: {str(e)}")
    
    else:
        st.info("👈 Silakan pilih Data dari Sidebar atau Upload File.")

    # Footer
    st.markdown("<div class='footer'>© 2025 PT Catindo Bagus Perkasa | Market Data Delay 15 Mins</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    if st.session_state['authenticated']:
        main_dashboard()
    else:
        login_page()
