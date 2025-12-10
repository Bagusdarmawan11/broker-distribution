import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import io
import yfinance as yf
import streamlit.components.v1 as components # Wajib ada untuk hack Numpad
from datetime import datetime

# ==========================================
# 1. KONFIGURASI HALAMAN & STATE
# ==========================================
st.set_page_config(
    page_title="Broker Distribution Analyzer Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inisialisasi Session State
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'dark_mode' not in st.session_state:
    st.session_state['dark_mode'] = True

# ==========================================
# 2. CSS CUSTOM (RESPONSIF & UI)
# ==========================================
def inject_custom_css():
    mode = "dark" if st.session_state['dark_mode'] else "light"
    
    # Warna Theme
    bg_color = "#0e1117" if mode == "dark" else "#ffffff"
    text_color = "#ffffff" if mode == "dark" else "#000000"
    card_bg = "#262730" if mode == "dark" else "#f0f2f6"
    
    st.markdown(f"""
    <style>
        /* Global Background */
        .stApp {{
            background-color: {bg_color};
            color: {text_color};
        }}
        
        /* LOGIN CARD STYLING (CENTERED) */
        .login-container {{
            display: flex;
            justify_content: center;
            align-items: center;
            height: 70vh;
            flex-direction: column;
        }}
        
        /* Input Field Styling (PIN LOOK) */
        .stTextInput input {{
            text-align: center;
            font-size: 32px !important; /* Font Besar agar enak di HP */
            letter-spacing: 8px;
            font-weight: bold;
            padding: 15px;
            border-radius: 12px;
            background-color: {card_bg};
            color: {text_color};
            border: 2px solid #555;
            transition: all 0.3s ease;
        }}
        
        .stTextInput input:focus {{
            border-color: #ff4b4b;
            box-shadow: 0 0 10px rgba(255, 75, 75, 0.5);
        }}
        
        /* Button Styling */
        .stButton button {{
            width: 100%;
            border-radius: 10px;
            font-weight: bold;
            height: 55px;
            font-size: 18px;
            margin-top: 10px;
        }}
        
        /* Running Text / Ticker */
        .ticker-wrap {{
            width: 100%;
            background-color: {card_bg}; 
            color: {text_color};
            padding: 8px 0;
            border-bottom: 1px solid #444;
            white-space: nowrap;
            overflow: hidden;
            box-sizing: border-box;
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        .ticker-item {{
            display: inline-block;
            padding: 0 15px;
            font-size: 14px;
            font-weight: bold;
        }}
        .up {{ color: #00ff00; }}
        .down {{ color: #ff4b4b; }}
        
        /* Footer */
        .footer {{
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: {card_bg};
            color: {text_color};
            text-align: center;
            padding: 10px;
            font-size: 12px;
            border-top: 1px solid #444;
            z-index: 999;
        }}
        
        /* --- MEDIA QUERY UNTUK MOBILE --- */
        @media only screen and (max-width: 600px) {{
            .stTextInput input {{
                font-size: 28px !important;
            }}
            h1 {{ font-size: 24px !important; }}
            h2 {{ font-size: 20px !important; }}
            .ticker-item {{ font-size: 12px; }}
        }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. FUNGSI LOGIKA (BACKEND)
# ==========================================

# Fungsi Ticker Saham
@st.cache_data(ttl=300)
def get_stock_ticker():
    tickers = ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "TLKM.JK", "ASII.JK", "GOTO.JK", "BUMI.JK", "ADRO.JK"]
    ticker_html = ""
    try:
        data = yf.download(tickers, period="5d", progress=False)['Close']
        if data.empty: return "<span class='ticker-item'>Market Closed / No Data</span>"
        
        last_prices = data.iloc[-1]
        prev_prices = data.iloc[-2]
        
        for symbol in tickers:
            clean_symbol = symbol.replace(".JK", "")
            try:
                price = last_prices[symbol]
                prev = prev_prices[symbol]
                if pd.isna(price) or pd.isna(prev): continue
                
                change = price - prev
                pct_change = (change / prev) * 100
                color_class = "up" if change >= 0 else "down"
                sign = "+" if change >= 0 else ""
                
                ticker_html += f"<span class='ticker-item'>{clean_symbol} {int(price):,} <span class='{color_class}'>({sign}{pct_change:.2f}%)</span></span>"
            except: continue
    except:
        return "<span class='ticker-item'>Gagal memuat data pasar.</span>"
        
    return f"<marquee scrollamount='6'>{ticker_html}</marquee>"

# Fungsi Cleaning Data
def clean_running_trade(df_input):
    df = df_input.copy()
    df.columns = df.columns.str.strip().str.capitalize()
    
    rename_map = {
        'Time': 'Time', 'Waktu': 'Time',
        'Price': 'Price', 'Harga': 'Price',
        'Lot': 'Lot', 'Vol': 'Lot', 'Volume': 'Lot',
        'Buyer': 'Buyer', 'B': 'Buyer', 'Broker Beli': 'Buyer',
        'Seller': 'Seller', 'S': 'Seller', 'Broker Jual': 'Seller',
        'Code': 'Stock', 'Kode': 'Stock', 'Stock': 'Stock', 'Saham': 'Stock'
    }
    
    new_columns = {}
    for col in df.columns:
        if col in rename_map:
            new_columns[col] = rename_map[col]
    df.rename(columns=new_columns, inplace=True)

    required_cols = ['Price', 'Lot', 'Buyer', 'Seller']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Kolom hilang: {', '.join(missing_cols)}")

    def parse_price(x):
        if pd.isna(x): return 0
        s = str(x)
        match = re.search(r"(\d+)", s.replace(',', '').replace('.', ''))
        return int(match.group(1)) if match else 0

    def parse_lot(x):
        if pd.isna(x): return 0
        s = str(x).replace(',', '').replace('.', '')
        return int(s) if s.isdigit() else 0

    def parse_broker(x):
        if pd.isna(x): return "UNKNOWN"
        s = str(x).upper()
        return re.split(r'[\s\[]', s)[0].strip()

    try:
        df['Price_Clean'] = df['Price'].apply(parse_price)
        df['Lot_Clean'] = df['Lot'].apply(parse_lot)
        df['Buyer_Code'] = df['Buyer'].apply(parse_broker)
        df['Seller_Code'] = df['Seller'].apply(parse_broker)
        
        if 'Stock' in df.columns:
            df['Stock'] = df['Stock'].astype(str).str.upper().str.strip()
        
        df['Shares'] = df['Lot_Clean'] * 100
        df['Value'] = df['Shares'] * df['Price_Clean']
        df = df[df['Value'] > 0]
        
    except Exception as e:
        raise ValueError(f"Error saat parsing data: {str(e)}")

    return df

# Fungsi Agregasi
def aggregate_broker_stats(df):
    buy_stats = df.groupby('Buyer_Code').agg({'Shares': 'sum', 'Value': 'sum'}).rename(columns={'Shares': 'Buy Vol', 'Value': 'Buy Val'})
    sell_stats = df.groupby('Seller_Code').agg({'Shares': 'sum', 'Value': 'sum'}).rename(columns={'Shares': 'Sell Vol', 'Value': 'Sell Val'})
    
    summary = pd.merge(buy_stats, sell_stats, left_index=True, right_index=True, how='outer').fillna(0)
    summary['Net Vol'] = summary['Buy Vol'] - summary['Sell Vol']
    summary['Net Val'] = summary['Buy Val'] - summary['Sell Val']
    
    summary['Avg Buy'] = summary.apply(lambda x: x['Buy Val'] / x['Buy Vol'] if x['Buy Vol'] > 0 else 0, axis=1)
    summary['Avg Sell'] = summary.apply(lambda x: x['Sell Val'] / x['Sell Vol'] if x['Sell Vol'] > 0 else 0, axis=1)
    
    summary.index.name = 'Broker'
    summary.reset_index(inplace=True)
    return summary.sort_values(by='Net Vol', ascending=False)

def format_number_label(value):
    if value >= 1_000_000_000: return f"{value / 1_000_000_000:.2f} B"
    elif value >= 1_000_000: return f"{value / 1_000_000:.2f} M"
    elif value >= 1_000: return f"{value / 1_000:.0f} K"
    return str(int(value))

# UPDATED: Perbaikan Variable Name 'l_colors'
def build_sankey_data(df, top_n=15, metric_col='Value'):
    # Group berdasarkan kolom metrik yang dipilih (Value / Lot_Clean)
    flow = df.groupby(['Buyer_Code', 'Seller_Code'])[metric_col].sum().reset_index()
    flow = flow.sort_values(metric_col, ascending=False).head(top_n)
    
    # Rename kolom metric jadi 'Weight' agar standar
    flow.rename(columns={metric_col: 'Weight'}, inplace=True)

    flow['Source_Label'] = flow['Buyer_Code'] + " (B)"
    flow['Target_Label'] = flow['Seller_Code'] + " (S)"

    all_nodes = list(set(flow['Source_Label']).union(set(flow['Target_Label'])))
    node_map = {name: i for i, name in enumerate(all_nodes)}

    source_totals = flow.groupby('Source_Label')['Weight'].sum().to_dict()
    target_totals = flow.groupby('Target_Label')['Weight'].sum().to_dict()

    final_labels = []
    node_colors = []
    link_colors = [] # Definisikan list penampung warna
    
    colors_palette = ['#9b78c4', '#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854', '#ffd92f', '#e5c494']
    source_color_map = {}

    for i, node in enumerate(all_nodes):
        broker_name = node.split(' ')[0]
        if node in source_totals:
            val_fmt = format_number_label(source_totals[node])
            final_labels.append(f"{broker_name} {val_fmt}")
            c = colors_palette[i % len(colors_palette)]
            node_colors.append(c)
            source_color_map[node_map[node]] = c
        elif node in target_totals:
            val_fmt = format_number_label(target_totals[node])
            final_labels.append(f"{val_fmt} {broker_name}")
            node_colors.append("#d9d9d9")
        else:
            final_labels.append(broker_name)
            node_colors.append("grey")

    l_source = [node_map[src] for src in flow['Source_Label']]
    l_target = [node_map[tgt] for tgt in flow['Target_Label']]
    l_value = flow['Weight'].tolist()

    for src_idx in l_source:
        base_c = source_color_map.get(src_idx, '#888888')
        # Buat warna link transparan
        if 'rgb' in base_c:
             link_colors.append(base_c.replace('rgb', 'rgba').replace(')', ', 0.6)'))
        elif base_c.startswith('#'):
            h = base_c.lstrip('#')
            rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
            link_colors.append(f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.6)")
        else:
            link_colors.append(base_c)

    # Return variabel 'link_colors' yang benar
    return final_labels, node_colors, l_source, l_target, l_value, link_colors

def create_sankey_figure(labels, colors, src, tgt, val, l_colors, title):
    fig = go.Figure(data=[go.Sankey(
        node=dict(pad=15, thickness=20, line=dict(color="white", width=0.5), label=labels, color=colors),
        link=dict(source=src, target=tgt, value=val, color=l_colors)
    )])
    fig.update_layout(
        title_text=f"<b>{title}</b>",
        font=dict(size=12, family="Arial"), height=600,
        margin=dict(l=10, r=10, t=40, b=20)
    )
    return fig

# ==========================================
# 4. SISTEM LOGIN (KEYBOARD NUMPAD FIX)
# ==========================================

def login_system():
    inject_custom_css()
    
    # --- JAVASCRIPT HACK UNTUK NUMPAD ---
    components.html("""
        <script>
            const inputs = window.parent.document.querySelectorAll('input[type="password"]');
            inputs.forEach(input => {
                input.setAttribute('inputmode', 'numeric');
                input.setAttribute('pattern', '[0-9]*');
            });
        </script>
    """, height=0, width=0)
    # -------------------------------------

    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.markdown("<h2 style='text-align: center; margin-bottom: 5px;'>🔐 Restricted Access</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #888; margin-bottom: 30px;'>Input PIN Access</p>", unsafe_allow_html=True)
            
            # Input PIN
            pin_input = st.text_input("PIN", type="password", placeholder="••••••", label_visibility="collapsed")
            
            submit = st.form_submit_button("LOGIN ➔", type="primary")
            
            if submit:
                if pin_input == "241130":
                    st.session_state['authenticated'] = True
                    st.rerun()
                else:
                    st.error("❌ PIN Salah!")

# ==========================================
# 5. MAIN APPLICATION
# ==========================================

def main():
    # Cek Auth
    if not st.session_state['authenticated']:
        login_system()
        st.stop() # Stop render konten utama jika belum login

    # --- JIKA SUDAH LOGIN ---
    
    # Sidebar Settings
    st.sidebar.title("⚙️ Pengaturan")
    is_dark = st.sidebar.toggle("Dark Mode", value=True)
    st.session_state['dark_mode'] = is_dark
    inject_custom_css() # Re-inject CSS
    
    # Logout
    if st.sidebar.button("Logout 🔓"):
        st.session_state['authenticated'] = False
        st.rerun()

    # Ticker Running Text
    st.markdown(get_stock_ticker(), unsafe_allow_html=True)
    
    # Konten Utama
    st.title("📊 Broker Distribution Analyzer")
    st.markdown("Tools analisis bandarmologi Running Trade BEI.")
    
    st.sidebar.header("📂 Input Data")
    uploaded_file = st.sidebar.file_uploader("Upload File Running Trade", type=['csv', 'xlsx', 'xls'])

    if not uploaded_file:
        st.info("👋 Silakan upload file CSV atau Excel.")
        # Tampilkan footer
        st.markdown("""<div class="footer">Copyright by PT Catindo Bagus Perkasa 2025 | Data Market Delay 15 Mins</div>""", unsafe_allow_html=True)
        return

    try:
        if uploaded_file.name.endswith('.csv'):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file)
            
        df_clean = clean_running_trade(df_raw)
        
        # Filter Saham
        if 'Stock' in df_clean.columns:
            st.sidebar.markdown("---")
            st.sidebar.subheader("🔍 Filter Saham")
            all_stocks = sorted(df_clean['Stock'].unique())
            selected_stocks = st.sidebar.multiselect("Pilih Saham", all_stocks, default=all_stocks)
            
            if selected_stocks:
                df_clean = df_clean[df_clean['Stock'].isin(selected_stocks)]
            else:
                st.warning("Pilih minimal satu saham.")
                st.stop()
        
        # Metrik
        st.divider()
        c1, c2, c3 = st.columns(3)
        total_val = df_clean['Value'].sum()
        total_vol = df_clean['Lot_Clean'].sum()
        unique_brokers = pd.concat([df_clean['Buyer_Code'], df_clean['Seller_Code']]).nunique()
        
        c1.metric("Total Transaksi", f"Rp {format_number_label(total_val)}")
        c2.metric("Total Volume", f"{total_vol:,.0f} Lot")
        c3.metric("Broker Terlibat", f"{unique_brokers}")
        
        # Tabel
        st.header("📋 Ringkasan Broker")
        min_vol = st.sidebar.number_input("Filter Min. Volume (Lot)", min_value=0, value=0, step=100)
        summary_df = aggregate_broker_stats(df_clean)
        filtered_summary = summary_df[(summary_df['Buy Vol'] + summary_df['Sell Vol']) >= min_vol]
        
        st.dataframe(
            filtered_summary.style.format({
                'Buy Val': "Rp {:,.0f}", 'Sell Val': "Rp {:,.0f}", 
                'Net Val': "Rp {:,.0f}", 'Buy Vol': "{:,.0f}", 
                'Sell Vol': "{:,.0f}", 'Net Vol': "{:,.0f}",
                'Avg Buy': "Rp {:,.0f}", 'Avg Sell': "Rp {:,.0f}"
            }).background_gradient(subset=['Net Val'], cmap='RdYlGn'),
            use_container_width=True,
            height=400
        )

        # Sankey Diagram (Switch Mode)
        st.header("🕸️ Peta Aliran Dana & Volume")
        
        # --- OPSI SWITCH METRIC (VALUE / VOLUME) ---
        col_opt1, col_opt2 = st.columns([2, 1])
        with col_opt1:
            viz_mode = st.radio(
                "Pilih Metrik Visualisasi:", 
                ["💰 Value (Aliran Dana)", "📦 Volume (Aliran Barang/Lot)"], 
                horizontal=True
            )
        with col_opt2:
            top_n = st.slider("Jumlah Interaksi", 5, 50, 15)
        
        # Tentukan Logic Berdasarkan Pilihan
        if "Value" in viz_mode:
            metric_col = 'Value'
            title_sankey = "Peta Aliran Dana (Rupiah): Buyer (Kiri) → Seller (Kanan)"
        else:
            metric_col = 'Lot_Clean'
            title_sankey = "Peta Aliran Barang (Lot): Buyer (Kiri) → Seller (Kanan)"
        
        try:
            lbl, col, src, tgt, val, l_col = build_sankey_data(df_clean, top_n=top_n, metric_col=metric_col)
            fig = create_sankey_figure(lbl, col, src, tgt, val, l_col, title=title_sankey)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Data tidak cukup untuk visualisasi. ({str(e)})")

    except ValueError as ve:
        st.error(f"❌ Format Data Salah: {str(ve)}")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        
    # Footer
    st.markdown("""
        <div class="footer">
            Copyright by PT Catindo Bagus Perkasa 2025 | Data Market Delay 15 Mins
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
