import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import io
import yfinance as yf
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
if 'pin_input' not in st.session_state:
    st.session_state['pin_input'] = ""
if 'dark_mode' not in st.session_state:
    st.session_state['dark_mode'] = True

# ==========================================
# 2. FITUR UI & CSS CUSTOM
# ==========================================

# CSS untuk Styling (Dark/Light, Footer, PIN Pad)
def inject_custom_css():
    mode = "dark" if st.session_state['dark_mode'] else "light"
    
    # Warna dasar berdasarkan mode
    bg_color = "#0e1117" if mode == "dark" else "#ffffff"
    text_color = "#ffffff" if mode == "dark" else "#000000"
    card_bg = "#262730" if mode == "dark" else "#f0f2f6"
    
    st.markdown(f"""
    <style>
        /* Main Background */
        .stApp {{
            background-color: {bg_color};
            color: {text_color};
        }}
        
        /* PIN Pad Styling */
        .pin-display {{
            font-size: 40px;
            font-weight: bold;
            text-align: center;
            letter-spacing: 10px;
            margin-bottom: 20px;
            color: {text_color};
            background-color: {card_bg};
            padding: 15px;
            border-radius: 10px;
        }}
        .stButton button {{
            width: 100%;
            height: 60px;
            font-size: 24px;
            border-radius: 15px;
        }}
        
        /* Footer Styling */
        .footer {{
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: {card_bg};
            color: {text_color};
            text-align: center;
            padding: 10px;
            font-size: 14px;
            border-top: 1px solid #444;
            z-index: 999;
        }}
        
        /* Marquee/Ticker Styling */
        .ticker-wrap {{
            width: 100%;
            background-color: {card_bg}; 
            color: {text_color};
            padding: 10px;
            margin-bottom: 10px;
            border-bottom: 1px solid #444;
            white-space: nowrap;
            overflow: hidden;
            box-sizing: border-box;
        }}
        .ticker-item {{
            display: inline-block;
            padding: 0 20px;
            font-size: 16px;
            font-weight: bold;
        }}
        .up {{ color: #00ff00; }}
        .down {{ color: #ff4b4b; }}
    </style>
    """, unsafe_allow_html=True)

# Fungsi Ticker Saham (Ambil Data LQ45 Sampel)
@st.cache_data(ttl=300) # Cache 5 menit agar tidak lambat
def get_stock_ticker():
    # Sampel saham LQ45 agar loading cepat (tidak semua 800 emiten)
    tickers = ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "TLKM.JK", "ASII.JK", 
               "UNTR.JK", "ICBP.JK", "GOTO.JK", "BUMI.JK", "ADRO.JK", "PGAS.JK"]
    
    ticker_html = ""
    try:
        data = yf.download(tickers, period="1d", progress=False)['Close']
        # Ambil data hari sebelumnya (untuk hitung %)
        prev_data = yf.download(tickers, period="2d", progress=False)['Close']
        
        for symbol in tickers:
            clean_symbol = symbol.replace(".JK", "")
            try:
                price = data[symbol].iloc[-1]
                prev_price = prev_data[symbol].iloc[-2] if len(prev_data) > 1 else price
                
                change = price - prev_price
                pct_change = (change / prev_price) * 100
                
                color_class = "up" if change >= 0 else "down"
                sign = "+" if change >= 0 else ""
                
                ticker_html += f"<span class='ticker-item'>{clean_symbol} {int(price):,} <span class='{color_class}'>({sign}{pct_change:.2f}%)</span></span>"
            except:
                continue
    except:
        ticker_html = "<span class='ticker-item'>Gagal memuat data pasar realtime.</span>"
        
    return f"<marquee scrollamount='8'>{ticker_html}</marquee>"

# ==========================================
# 3. SISTEM PIN (KEYPAD UI)
# ==========================================
def update_pin(digit):
    if len(st.session_state['pin_input']) < 6:
        st.session_state['pin_input'] += digit

def clear_pin():
    st.session_state['pin_input'] = ""

def check_pin():
    if st.session_state['pin_input'] == '241130':
        st.session_state['authenticated'] = True
    else:
        st.error("PIN Salah! Coba lagi.")
        st.session_state['pin_input'] = ""

# HALAMAN LOGIN
if not st.session_state['authenticated']:
    inject_custom_css() # Inject CSS untuk dark/light mode login
    
    col_center = st.columns([1, 2, 1])
    with col_center[1]:
        st.markdown("<h2 style='text-align: center;'>🔐 Restricted Access</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Silakan masukkan PIN keamanan.</p>", unsafe_allow_html=True)
        
        # Display PIN (Masked)
        display_pin = "•" * len(st.session_state['pin_input']) if st.session_state['pin_input'] else "ENTER PIN"
        st.markdown(f"<div class='pin-display'>{display_pin}</div>", unsafe_allow_html=True)
        
        # Keypad Grid
        c1, c2, c3 = st.columns(3)
        with c1: 
            if st.button("1"): update_pin("1")
            if st.button("4"): update_pin("4")
            if st.button("7"): update_pin("7")
        with c2: 
            if st.button("2"): update_pin("2")
            if st.button("5"): update_pin("5")
            if st.button("8"): update_pin("8")
            if st.button("0"): update_pin("0")
        with c3: 
            if st.button("3"): update_pin("3")
            if st.button("6"): update_pin("6")
            if st.button("9"): update_pin("9")
        
        # Action Buttons
        ac1, ac2 = st.columns(2)
        with ac1:
            if st.button("CLEAR", type="secondary"): clear_pin()
        with ac2:
            if st.button("LOGIN ➔", type="primary"): check_pin()
            
    st.stop() # Stop render jika belum login

# ==========================================
# 4. FUNGSI LOGIKA (DATA PROCESSING)
# ==========================================

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

def format_currency_label(value):
    if value >= 1_000_000_000: return f"{value / 1_000_000_000:.2f} B"
    elif value >= 1_000_000: return f"{value / 1_000_000:.2f} M"
    elif value >= 1_000: return f"{value / 1_000:.0f} K"
    return str(int(value))

def build_sankey_data(df, top_n=15):
    flow = df.groupby(['Buyer_Code', 'Seller_Code'])['Value'].sum().reset_index()
    flow = flow.sort_values('Value', ascending=False).head(top_n)

    flow['Source_Label'] = flow['Buyer_Code'] + " (B)"
    flow['Target_Label'] = flow['Seller_Code'] + " (S)"

    all_nodes = list(set(flow['Source_Label']).union(set(flow['Target_Label'])))
    node_map = {name: i for i, name in enumerate(all_nodes)}

    source_totals = flow.groupby('Source_Label')['Value'].sum().to_dict()
    target_totals = flow.groupby('Target_Label')['Value'].sum().to_dict()

    final_labels = []
    node_colors = []
    link_colors = []
    colors_palette = ['#9b78c4', '#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854', '#ffd92f', '#e5c494']
    source_color_map = {}

    for i, node in enumerate(all_nodes):
        broker_name = node.split(' ')[0]
        if node in source_totals:
            val_fmt = format_currency_label(source_totals[node])
            final_labels.append(f"{broker_name} {val_fmt}")
            c = colors_palette[i % len(colors_palette)]
            node_colors.append(c)
            source_color_map[node_map[node]] = c
        elif node in target_totals:
            val_fmt = format_currency_label(target_totals[node])
            final_labels.append(f"{val_fmt} {broker_name}")
            node_colors.append("#d9d9d9")
        else:
            final_labels.append(broker_name)
            node_colors.append("grey")

    l_source = [node_map[src] for src in flow['Source_Label']]
    l_target = [node_map[tgt] for tgt in flow['Target_Label']]
    l_value = flow['Value'].tolist()

    for src_idx in l_source:
        base_c = source_color_map.get(src_idx, '#888888')
        if base_c.startswith('#'):
            h = base_c.lstrip('#')
            rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
            link_colors.append(f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.6)")
        else:
            link_colors.append(base_c)

    return final_labels, node_colors, l_source, l_target, l_value, link_colors

def create_sankey_figure(labels, colors, src, tgt, val, l_colors):
    fig = go.Figure(data=[go.Sankey(
        node=dict(pad=15, thickness=20, line=dict(color="white", width=0.5), label=labels, color=colors),
        link=dict(source=src, target=tgt, value=val, color=l_colors)
    )])
    fig.update_layout(
        title_text="<b>Aliran Dana: Buyer (Kiri) → Seller (Kanan)</b>",
        font=dict(size=12, family="Arial"), height=600,
        margin=dict(l=10, r=10, t=40, b=20)
    )
    return fig

# ==========================================
# 5. MAIN APPLICATION
# ==========================================

def main():
    # --- Sidebar Settings ---
    st.sidebar.title("⚙️ Pengaturan")
    
    # Toggle Dark Mode
    is_dark = st.sidebar.toggle("Dark Mode", value=True)
    st.session_state['dark_mode'] = is_dark
    inject_custom_css() # Apply CSS based on toggle
    
    # Logout Button
    if st.sidebar.button("Logout 🔓"):
        st.session_state['authenticated'] = False
        st.session_state['pin_input'] = ""
        st.rerun()

    # --- Running Text (Ticker) ---
    st.markdown(get_stock_ticker(), unsafe_allow_html=True)
    
    # --- Main Content ---
    st.title("📊 Broker Distribution Analyzer")
    st.markdown("Tools analisis bandarmologi dengan data Running Trade BEI.")
    
    st.sidebar.header("📂 Input Data")
    uploaded_file = st.sidebar.file_uploader("Upload File Running Trade", type=['csv', 'xlsx', 'xls'])

    if not uploaded_file:
        st.info("👋 Silakan upload file CSV atau Excel untuk memulai.")
        return

    try:
        if uploaded_file.name.endswith('.csv'):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file)
            
        df_clean = clean_running_trade(df_raw)
        
        # --- Filter Saham (Jika Ada) ---
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
        
        # --- Metrik ---
        st.divider()
        c1, c2, c3 = st.columns(3)
        total_val = df_clean['Value'].sum()
        total_vol = df_clean['Lot_Clean'].sum()
        unique_brokers = pd.concat([df_clean['Buyer_Code'], df_clean['Seller_Code']]).nunique()
        
        c1.metric("Total Transaksi", f"Rp {format_currency_label(total_val)}")
        c2.metric("Total Volume", f"{total_vol:,.0f} Lot")
        c3.metric("Broker Terlibat", f"{unique_brokers}")
        
        # --- Tabel Ringkasan (Dengan Matplotlib Gradient) ---
        st.header("📋 Ringkasan Broker (Net Buy/Sell)")
        
        min_vol = st.sidebar.number_input("Filter Min. Volume (Lot)", min_value=0, value=0, step=100)
        
        summary_df = aggregate_broker_stats(df_clean)
        filtered_summary = summary_df[
            (summary_df['Buy Vol'] + summary_df['Sell Vol']) >= min_vol
        ]
        
        # Format Tabel
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

        # --- Sankey Diagram ---
        st.header("🕸️ Peta Aliran Dana")
        top_n = st.slider("Jumlah Interaksi Terbesar", 5, 50, 15)
        
        try:
            lbl, col, src, tgt, val, l_col = build_sankey_data(df_clean, top_n=top_n)
            fig = create_sankey_figure(lbl, col, src, tgt, val, l_col)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning("Data tidak cukup untuk grafik Sankey.")

    except ValueError as ve:
        st.error(f"❌ Format Data Salah: {str(ve)}")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        
    # --- Footer ---
    st.markdown("""
        <div class="footer">
            Copyright by PT Catindo Bagus Perkasa 2025 | Data Market Delay 15 Mins
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
