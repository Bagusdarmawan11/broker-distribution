import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import io

# ==========================================
# 1. KONFIGURASI HALAMAN & SISTEM PIN
# ==========================================
st.set_page_config(
    page_title="Broker Distribution Analyzer v2.1 (Protected)",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LOGIKA OTENTIKASI (PIN) ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

def check_pin():
    # PIN HARDCODED SESUAI PERMINTAAN
    if st.session_state['pin_input'] == '241130':
        st.session_state['authenticated'] = True
        st.session_state['error_msg'] = None # Clear error
    else:
        st.session_state['authenticated'] = False
        st.session_state['error_msg'] = "❌ PIN Salah! Akses Ditolak."

# TAMPILAN LOGIN JIKA BELUM AUTHENTICATED
if not st.session_state['authenticated']:
    st.markdown("## 🔒 Restricted Access")
    st.markdown("Tools ini dilindungi. Silakan masukkan PIN untuk melanjutkan.")
    
    st.text_input(
        "Masukkan PIN:", 
        type="password", 
        key="pin_input", 
        on_change=check_pin
    )
    
    # Tombol Enter Manual (Opsional, karena on_change sudah handle enter)
    if st.button("Login"):
        check_pin()

    if 'error_msg' in st.session_state and st.session_state['error_msg']:
        st.error(st.session_state['error_msg'])
        
    st.stop() # Hentikan eksekusi kode di bawah jika belum login

# ==========================================
# 2. FUNGSI UTILITIES (CLEANING & PROCESSING)
# ==========================================

def clean_running_trade(df_input):
    """
    Membersihkan data raw Running Trade.
    Support kolom 'Stock'/'Code' opsional untuk filter.
    """
    df = df_input.copy()
    
    # 1. Normalisasi Header Kolom
    df.columns = df.columns.str.strip().str.capitalize()
    
    # Mapping nama kolom agar standar
    rename_map = {
        'Time': 'Time', 'Waktu': 'Time',
        'Price': 'Price', 'Harga': 'Price',
        'Lot': 'Lot', 'Vol': 'Lot', 'Volume': 'Lot',
        'Buyer': 'Buyer', 'B': 'Buyer', 'Broker Beli': 'Buyer',
        'Seller': 'Seller', 'S': 'Seller', 'Broker Jual': 'Seller',
        'Code': 'Stock', 'Kode': 'Stock', 'Stock': 'Stock', 'Saham': 'Stock' # Support kolom saham
    }
    
    # Rename kolom
    new_columns = {}
    for col in df.columns:
        if col in rename_map:
            new_columns[col] = rename_map[col]
    df.rename(columns=new_columns, inplace=True)

    # Validasi Kolom Wajib
    required_cols = ['Price', 'Lot', 'Buyer', 'Seller']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Kolom hilang: {', '.join(missing_cols)}")

    # 2. Fungsi Regex Parsing
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

    # 3. Terapkan Cleaning
    try:
        df['Price_Clean'] = df['Price'].apply(parse_price)
        df['Lot_Clean'] = df['Lot'].apply(parse_lot)
        df['Buyer_Code'] = df['Buyer'].apply(parse_broker)
        df['Seller_Code'] = df['Seller'].apply(parse_broker)
        
        # Bersihkan kolom Stock jika ada
        if 'Stock' in df.columns:
            df['Stock'] = df['Stock'].astype(str).str.upper().str.strip()
        
        # Hitung Value (Asumsi 1 Lot = 100 Lembar)
        df['Shares'] = df['Lot_Clean'] * 100
        df['Value'] = df['Shares'] * df['Price_Clean']
        
        df = df[df['Value'] > 0]
        
    except Exception as e:
        raise ValueError(f"Error saat parsing data: {str(e)}")

    return df

def aggregate_broker_stats(df):
    """Menghitung ringkasan Net Buy/Sell + Average Price per Broker"""
    # Agregasi Buyer
    buy_stats = df.groupby('Buyer_Code').agg({
        'Shares': 'sum', 'Value': 'sum'
    }).rename(columns={'Shares': 'Buy Vol', 'Value': 'Buy Val'})

    # Agregasi Seller
    sell_stats = df.groupby('Seller_Code').agg({
        'Shares': 'sum', 'Value': 'sum'
    }).rename(columns={'Shares': 'Sell Vol', 'Value': 'Sell Val'})

    # Gabung
    summary = pd.merge(buy_stats, sell_stats, left_index=True, right_index=True, how='outer').fillna(0)

    # Hitung Net
    summary['Net Vol'] = summary['Buy Vol'] - summary['Sell Vol']
    summary['Net Val'] = summary['Buy Val'] - summary['Sell Val']
    
    # --- FITUR BARU: Hitung Average Price ---
    # Hindari pembagian dengan nol
    summary['Avg Buy'] = summary.apply(lambda x: x['Buy Val'] / x['Buy Vol'] if x['Buy Vol'] > 0 else 0, axis=1)
    summary['Avg Sell'] = summary.apply(lambda x: x['Sell Val'] / x['Sell Vol'] if x['Sell Vol'] > 0 else 0, axis=1)
    
    summary.index.name = 'Broker'
    summary.reset_index(inplace=True)
    
    return summary.sort_values(by='Net Vol', ascending=False)

# ==========================================
# 3. FUNGSI SANKEY DIAGRAM
# ==========================================

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
        node=dict(
            pad=15, thickness=20,
            line=dict(color="white", width=0.5),
            label=labels, color=colors
        ),
        link=dict(
            source=src, target=tgt, value=val, color=l_colors
        )
    )])
    fig.update_layout(
        title_text="<b>Aliran Dana: Buyer (Kiri) → Seller (Kanan)</b>",
        font=dict(size=12, family="Arial"),
        height=600,
        margin=dict(l=10, r=10, t=40, b=20)
    )
    return fig

# ==========================================
# 4. MAIN APPLICATION
# ==========================================

def main():
    # TOMBOL LOGOUT (Opsional, di Sidebar)
    if st.sidebar.button("Logout"):
        st.session_state['authenticated'] = False
        st.rerun()

    st.title("📊 Broker Distribution Analyzer v2.1")
    st.markdown("""
    Analisis data **Running Trade** dengan fitur **Average Price** dan **Stock Filter**.
    """)
    
    st.sidebar.header("📂 Input Data")
    uploaded_file = st.sidebar.file_uploader("Upload File Running Trade", type=['csv', 'xlsx', 'xls'])

    if not uploaded_file:
        st.info("👋 Silakan upload file CSV atau Excel.")
        st.markdown("---")
        st.markdown("### Tips Kolom:")
        st.markdown("""
        Agar fitur **Filter Saham** aktif, pastikan ada kolom **'Code'** atau **'Stock'** di file kamu.
        Jika hanya analisis satu saham, kolom tersebut tidak wajib.
        """)
        return

    try:
        if uploaded_file.name.endswith('.csv'):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file)
            
        df_clean = clean_running_trade(df_raw)
        
        # --- FITUR BARU: FILTER SAHAM ---
        if 'Stock' in df_clean.columns:
            st.sidebar.markdown("---")
            st.sidebar.subheader("🔍 Filter Saham")
            all_stocks = sorted(df_clean['Stock'].unique())
            selected_stocks = st.sidebar.multiselect("Pilih Saham", all_stocks, default=all_stocks)
            
            if selected_stocks:
                df_clean = df_clean[df_clean['Stock'].isin(selected_stocks)]
            else:
                st.warning("Silakan pilih minimal satu saham.")
                st.stop()
        
        # --- METRIK UTAMA ---
        st.divider()
        c1, c2, c3 = st.columns(3)
        total_val = df_clean['Value'].sum()
        total_vol = df_clean['Lot_Clean'].sum()
        unique_brokers = pd.concat([df_clean['Buyer_Code'], df_clean['Seller_Code']]).nunique()
        
        c1.metric("Total Transaksi", f"Rp {format_currency_label(total_val)}")
        c2.metric("Total Volume", f"{total_vol:,.0f} Lot")
        c3.metric("Broker Terlibat", f"{unique_brokers}")
        
        # --- TABEL RINGKASAN BROKER (UPDATED) ---
        st.header("📋 Ringkasan Broker + Average Price")
        
        min_vol = st.sidebar.number_input("Filter Min. Volume (Lot)", min_value=0, value=0, step=100)
        
        summary_df = aggregate_broker_stats(df_clean)
        filtered_summary = summary_df[
            (summary_df['Buy Vol'] + summary_df['Sell Vol']) >= min_vol
        ]
        
        # Display dengan format Average Price
        st.dataframe(
            filtered_summary.style.format({
                'Buy Val': "Rp {:,.0f}", 'Sell Val': "Rp {:,.0f}", 
                'Net Val': "Rp {:,.0f}", 'Buy Vol': "{:,.0f}", 
                'Sell Vol': "{:,.0f}", 'Net Vol': "{:,.0f}",
                'Avg Buy': "Rp {:,.0f}", 'Avg Sell': "Rp {:,.0f}" # Kolom Baru
            }).background_gradient(subset=['Net Val'], cmap='RdYlGn'),
            use_container_width=True,
            height=400
        )

        # --- SANKEY DIAGRAM ---
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

if __name__ == "__main__":
    main()
