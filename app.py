import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import os
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
}

COLOR_MAP = {
    'Foreign': '#00E396', # Hijau
    'BUMN': '#FEB019',    # Kuning/Orange
    'Local': '#775DD0',   # Ungu
    'Unknown': '#546E7A'  
}

if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False

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

def inject_custom_css(is_dark_mode):
    # Tentukan warna berdasarkan mode
    if is_dark_mode:
        bg_color = "#0e1117"
        text_color = "#ffffff"
        card_bg = "#262730"
        border_color = "#444"
        sidebar_bg = "#262730"
    else:
        bg_color = "#ffffff"
        text_color = "#000000"
        card_bg = "#f0f2f6"
        border_color = "#ccc"
        sidebar_bg = "#f0f2f6"
    
    st.markdown(f"""
    <style>
        /* Main App Background & Text */
        .stApp {{
            background-color: {bg_color};
            color: {text_color};
        }}
        
        /* Typography overrides for Light Mode visibility */
        h1, h2, h3, h4, h5, h6, p, span, div, label {{
            color: {text_color} !important;
        }}
        
        /* PIN & Input Styles */
        .stTextInput input {{
            text-align: center; 
            font-size: 32px !important; 
            letter-spacing: 15px;
            font-weight: bold; 
            padding: 20px; 
            border-radius: 15px;
            background-color: {card_bg} !important; 
            color: {text_color} !important; 
            border: 1px solid {border_color};
        }}
        
        /* Buttons */
        .stButton button {{ 
            width: 100%; 
            height: 50px; 
            font-size: 18px; 
            border-radius: 12px;
            border: 1px solid {border_color};
            color: {text_color};
        }}
        
        /* Hide default tables index */
        thead tr th:first-child {{display:none}} 
        tbody th {{display:none}}
        
        /* Broker Tags */
        .tag {{ padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; color: white !important; display: inline-block; margin-right: 5px;}}
        .tag-Foreign {{ background-color: {COLOR_MAP['Foreign']}; }}
        .tag-BUMN {{ background-color: {COLOR_MAP['BUMN']}; color: black !important; }}
        .tag-Local {{ background-color: {COLOR_MAP['Local']}; }}
        
        /* Footer */
        .footer {{
            position: fixed; left: 0; bottom: 0; width: 100%; background: {card_bg};
            text-align: center; padding: 8px; font-size: 12px; border-top: 1px solid {border_color}; z-index: 1000;
            color: {text_color} !important;
        }}
        
        /* Insight Box */
        .insight-box {{
            background-color: {card_bg}; 
            padding: 20px; 
            border-radius: 10px; 
            border-left: 5px solid {COLOR_MAP['Foreign']};
            margin-top: 20px; 
            margin-bottom: 50px;
            color: {text_color} !important;
        }}
        
        /* Sidebar fix for Light Mode */
        [data-testid="stSidebar"] {{
            background-color: {sidebar_bg};
        }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. DATA PROCESSING LOGIC
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

def login_page(is_dark_mode):
    inject_custom_css(is_dark_mode)
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

def bandarmology_page(is_dark_mode):
    inject_custom_css(is_dark_mode)
    DB_ROOT = "database"
    
    with st.sidebar:
        st.subheader("📂 Sumber Data")
        source_type = st.radio("Tipe:", ["Database Folder", "Upload Manual"], label_visibility="collapsed")
        df_raw = None
        current_stock = "UNKNOWN"
        
        if source_type == "Database Folder":
            if os.path.exists(DB_ROOT):
                stocks = sorted([d for d in os.listdir(DB_ROOT) if os.path.isdir(os.path.join(DB_ROOT, d))])
                sel_stock = st.selectbox("Saham", stocks)
                if sel_stock:
                    p_stock = os.path.join(DB_ROOT, sel_stock)
                    years = sorted(os.listdir(p_stock))
                    sel_year = st.selectbox("Tahun", years) if years else None
                    if sel_year:
                        p_year = os.path.join(p_stock, sel_year)
                        months = sorted(os.listdir(p_year))
                        sel_month = st.selectbox("Bulan", months) if months else None
                        if sel_month:
                            p_month = os.path.join(p_year, sel_month)
                            files = sorted([f for f in os.listdir(p_month) if f.endswith(('csv','xlsx'))])
                            sel_file = st.selectbox("Tanggal", files)
                            if sel_file and st.button("Load Data"):
                                fp = os.path.join(p_month, sel_file)
                                try:
                                    df_raw = pd.read_csv(fp) if fp.endswith('csv') else pd.read_excel(fp)
                                    current_stock = sel_stock
                                except: st.error("Load failed")
            else: st.warning(f"Buat folder '{DB_ROOT}'")
        else:
            uploaded = st.file_uploader("Upload File", type=['csv','xlsx'])
            if uploaded:
                try:
                    df_raw = pd.read_csv(uploaded) if uploaded.name.endswith('csv') else pd.read_excel(uploaded)
                    current_stock = "UPLOADED"
                except: st.error("File Error")

    if df_raw is not None:
        try:
            df = clean_running_trade(df_raw)
            summ = get_broker_summary(df)
            st.title(f"📊 Analisis: {current_stock}")
            
            c1, c2, c3 = st.columns(3)
            tot_val = df['Value'].sum()
            c1.metric("Total Transaksi", f"Rp {format_number_label(tot_val)}")
            c2.metric("Total Volume", f"{df['Lot_Clean'].sum():,.0f} Lot")
            f_share = summ[summ['Type']=='Foreign']['Total_Val'].sum() / (tot_val*2) * 100
            c3.metric("Asing", f"{f_share:.1f}%")
            
            st.divider()
            
            st.subheader("🏆 Top Broker")
            # PEWARNAAN TABEL
            def color_net(val):
                return f'color: {"#00E396" if val>0 else "#FF4560"}; font-weight: bold;'

            tabs = st.tabs(["ALL", "ASING", "BUMN", "LOKAL"])
            cats = ['All', 'Foreign', 'BUMN', 'Local']
            for tab, cat in zip(tabs, cats):
                with tab:
                    d = summ if cat == 'All' else summ[summ['Type']==cat]
                    if not d.empty:
                        st.dataframe(d[['Code','Name','Total_Val','Net_Val']].style.format({
                            'Total_Val': format_number_label, 'Net_Val': format_number_label
                        }).map(color_net, subset=['Net_Val']), use_container_width=True, height=350)
                    else: st.info("Kosong")
            
            st.subheader("🕸️ Flow Map")
            sc1, sc2 = st.columns([2,1])
            with sc1:
                met = st.radio("Metrik Visual:", ["Value (Dana)", "Lot (Barang)"], horizontal=True)
            with sc2:
                top_n = st.slider("Jumlah Interaksi", 5, 50, 15)
                
            met_col = 'Value' if "Value" in met else 'Lot_Clean'
            try:
                lbl, col, src, tgt, val, l_col = build_sankey(df, top_n, met_col)
                fig = go.Figure(data=[go.Sankey(
                    node=dict(pad=20, thickness=20, line=dict(color="black", width=0.5), label=lbl, color=col),
                    link=dict(source=src, target=tgt, value=val, color=l_col)
                )])
                
                # Plotly layout juga perlu diadjust untuk Light Mode agar text terbaca
                font_color = "white" if is_dark_mode else "black"
                fig.update_layout(
                    height=600, 
                    margin=dict(l=10,r=10,t=10,b=10), 
                    font=dict(size=12, color=font_color),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown(f"""<div style='text-align:center'><span class='tag tag-Foreign'>ASING</span><span class='tag tag-BUMN'>BUMN</span><span class='tag tag-Local'>LOKAL</span></div>""", unsafe_allow_html=True)
                st.markdown(f"<div class='insight-box'>{generate_smart_insight(summ)}</div>", unsafe_allow_html=True)
            except Exception as e: st.warning(f"Error Visual: {e}")
            
        except Exception as e: st.error(f"Error: {e}")
    else: st.info("Silakan pilih data di sidebar.")

def main():
    # SIDEBAR CONTROLS (Ditaruh di sini agar CSS bisa di-inject langsung setelahnya)
    with st.sidebar:
        st.title("🦅 Bandarmology")
        st.divider()
        # Toggle ini mengembalikan True/False langsung
        is_dark = st.toggle("Dark Mode", value=True)
        if st.button("Logout"):
            st.session_state['authenticated'] = False
            st.rerun()
            
    # Inject CSS berdasarkan state toggle
    inject_custom_css(is_dark)
    
    if st.session_state['authenticated']:
        bandarmology_page(is_dark)
        st.markdown("<div class='footer'>© 2025 PT Catindo Bagus Perkasa | Market Data Delay 15 Mins</div>", unsafe_allow_html=True)
    else:
        login_page(is_dark)

if __name__ == "__main__":
    main()
