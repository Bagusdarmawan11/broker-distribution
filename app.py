import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import io

# ==========================================
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(
    page_title="Broker Distribution Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. FUNGSI UTILITIES (CLEANING & PROCESSING)
# ==========================================

def clean_running_trade(df_input):
    """
    Membersihkan data raw Running Trade:
    - Parsing Price (hapus persentase)
    - Parsing Lot (hapus koma)
    - Parsing Broker (ambil kode saja, misal 'YP [D]' -> 'YP')
    - Menghitung Value (Rupiah)
    """
    df = df_input.copy()
    
    # 1. Normalisasi Header Kolom (Capitalize)
    df.columns = df.columns.str.strip().str.capitalize()
    
    # Mapping nama kolom agar standar
    rename_map = {
        'Time': 'Time', 'Waktu': 'Time',
        'Price': 'Price', 'Harga': 'Price',
        'Lot': 'Lot', 'Vol': 'Lot', 'Volume': 'Lot',
        'Buyer': 'Buyer', 'B': 'Buyer', 'Broker Beli': 'Buyer',
        'Seller': 'Seller', 'S': 'Seller', 'Broker Jual': 'Seller'
    }
    
    # Rename kolom yang ditemukan
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
        # Ambil angka pertama sebelum spasi/kurung. "250 (+2%)" -> 250
        if pd.isna(x): return 0
        s = str(x)
        match = re.search(r"(\d+)", s.replace(',', '').replace('.', ''))
        return int(match.group(1)) if match else 0

    def parse_lot(x):
        # Hapus koma. "1,500" -> 1500
        if pd.isna(x): return 0
        s = str(x).replace(',', '').replace('.', '')
        return int(s) if s.isdigit() else 0

    def parse_broker(x):
        # Ambil kode broker. "YP [D]" -> "YP"
        if pd.isna(x): return "UNKNOWN"
        s = str(x).upper()
        return re.split(r'[\s\[]', s)[0].strip()

    # 3. Terapkan Cleaning
    try:
        df['Price_Clean'] = df['Price'].apply(parse_price)
        df['Lot_Clean'] = df['Lot'].apply(parse_lot)
        df['Buyer_Code'] = df['Buyer'].apply(parse_broker)
        df['Seller_Code'] = df['Seller'].apply(parse_broker)
        
        # Hitung Value (Asumsi 1 Lot = 100 Lembar)
        df['Shares'] = df['Lot_Clean'] * 100
        df['Value'] = df['Shares'] * df['Price_Clean']
        
        # Hapus transaksi 0 atau error
        df = df[df['Value'] > 0]
        
    except Exception as e:
        raise ValueError(f"Error saat parsing data: {str(e)}")

    return df

def aggregate_broker_stats(df):
    """Menghitung ringkasan Net Buy/Sell per Broker"""
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
    
    # Format agar rapi (Index jadi kolom Broker)
    summary.index.name = 'Broker'
    summary.reset_index(inplace=True)
    
    # Sort default berdasarkan Net Volume Accumulation
    return summary.sort_values(by='Net Vol', ascending=False)

# ==========================================
# 3. FUNGSI SANKEY DIAGRAM (STYLING KHUSUS)
# ==========================================

def format_currency_label(value):
    """Format angka jadi 10 M, 2.5 B, dll"""
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f} B"
    elif value >= 1_000_000:
        return f"{value / 1_000_000:.2f} M"
    elif value >= 1_000:
        return f"{value / 1_000:.0f} K"
    return str(int(value))

def build_sankey_data(df, top_n=15):
    """
    Menyiapkan data nodes & links.
    Logic: Buyer (Source/Kiri) -> Seller (Target/Kanan).
    Warna Link mengikuti warna Buyer.
    """
    # Grouping interaksi Buyer -> Seller
    flow = df.groupby(['Buyer_Code', 'Seller_Code'])['Value'].sum().reset_index()
    flow = flow.sort_values('Value', ascending=False).head(top_n)

    # Buat label unik dengan suffix agar node kiri & kanan terpisah
    flow['Source_Label'] = flow['Buyer_Code'] + " (B)"
    flow['Target_Label'] = flow['Seller_Code'] + " (S)"

    # List semua node unik
    all_nodes = list(set(flow['Source_Label']).union(set(flow['Target_Label'])))
    node_map = {name: i for i, name in enumerate(all_nodes)}

    # Hitung total value per node untuk label
    source_totals = flow.groupby('Source_Label')['Value'].sum().to_dict()
    target_totals = flow.groupby('Target_Label')['Value'].sum().to_dict()

    # --- KONFIGURASI WARNA & LABEL ---
    final_labels = []
    node_colors = []
    link_colors = []
    
    # Palette warna cerah
    colors_palette = ['#9b78c4', '#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854', '#ffd92f', '#e5c494']
    source_color_map = {} # Mapping index buyer -> warna

    for i, node in enumerate(all_nodes):
        broker_name = node.split(' ')[0]
        
        if node in source_totals: # BUYER NODE
            val_fmt = format_currency_label(source_totals[node])
            final_labels.append(f"{broker_name} {val_fmt}")
            
            # Assign warna
            c = colors_palette[i % len(colors_palette)]
            node_colors.append(c)
            source_color_map[node_map[node]] = c
            
        elif node in target_totals: # SELLER NODE
            val_fmt = format_currency_label(target_totals[node])
            final_labels.append(f"{val_fmt} {broker_name}")
            node_colors.append("#d9d9d9") # Abu-abu soft
        else:
            final_labels.append(broker_name)
            node_colors.append("grey")

    # --- BUILD LINKS ---
    l_source = [node_map[src] for src in flow['Source_Label']]
    l_target = [node_map[tgt] for tgt in flow['Target_Label']]
    l_value = flow['Value'].tolist()

    # Warna link mengikuti Buyer (Source) dengan transparansi
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
    st.title("📊 Broker Distribution Analyzer")
    st.markdown("""
    Aplikasi ini menganalisis data **Running Trade** dari Bursa Efek Indonesia untuk melihat peta kekuatan Broker (Bandarmology).
    
    **Cara Pakai:**
    1. Export data Running Trade dari sekuritas (Stockbit/OLT lain) ke Excel/CSV.
    2. Upload file di bawah ini.
    """)
    
    # --- SIDEBAR INPUT ---
    st.sidebar.header("📂 Input Data")
    uploaded_file = st.sidebar.file_uploader("Upload File Running Trade", type=['csv', 'xlsx', 'xls'])

    # --- JIKA BELUM UPLOAD FILE ---
    if not uploaded_file:
        st.info("👋 Silakan upload file CSV atau Excel untuk memulai.")
        st.markdown("### Format Kolom yang Dibutuhkan:")
        st.markdown("""
        Pastikan file kamu memiliki header kolom seperti berikut (urutan tidak masalah):
        - `Time` (Waktu transaksi)
        - `Price` (Harga, format "250" atau "250 (+1%)")
        - `Lot` / `Volume` (Jumlah Lot, boleh ada koma)
        - `Buyer` (Kode Broker Pembeli, misal "YP [D]")
        - `Seller` (Kode Broker Penjual, misal "PD [D]")
        """)
        
        st.markdown("**Contoh Data:**")
        sample_data = pd.DataFrame({
            'Time': ['09:00:01', '09:00:05'],
            'Price': ['250', '252 (+1%)'],
            'Lot': ['1,000', '500'],
            'Buyer': ['YP [D]', 'PD'],
            'Seller': ['KK', 'YP [D]']
        })
        st.table(sample_data)
        return # Stop eksekusi sampai file diupload

    # --- PROSES FILE ---
    try:
        # Load File
        if uploaded_file.name.endswith('.csv'):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file)
            
        # Cleaning
        df_clean = clean_running_trade(df_raw)
        
        # --- METRIK UTAMA ---
        st.divider()
        c1, c2, c3 = st.columns(3)
        total_val = df_clean['Value'].sum()
        total_vol = df_clean['Lot_Clean'].sum()
        unique_brokers = pd.concat([df_clean['Buyer_Code'], df_clean['Seller_Code']]).nunique()
        
        c1.metric("Total Transaksi (Value)", f"Rp {format_currency_label(total_val)}")
        c2.metric("Total Volume (Lot)", f"{total_vol:,.0f}")
        c3.metric("Broker Terlibat", f"{unique_brokers} Broker")
        
        # --- PREVIEW DATA ---
        with st.expander("🔍 Lihat Preview Data Bersih"):
            st.dataframe(df_clean.head(50), use_container_width=True)

        # --- TABEL RINGKASAN BROKER ---
        st.header("📋 Ringkasan Broker (Net Buy/Sell)")
        
        # Opsi Filter
        min_vol = st.sidebar.number_input("Filter Min. Volume (Lot)", min_value=0, value=0, step=100)
        
        summary_df = aggregate_broker_stats(df_clean)
        
        # Filter tampilan tabel
        filtered_summary = summary_df[
            (summary_df['Buy Vol'] + summary_df['Sell Vol']) >= min_vol
        ]
        
        # Highlight logic (opsional styling pandas)
        st.dataframe(
            filtered_summary.style.format({
                'Buy Val': "Rp {:,.0f}", 'Sell Val': "Rp {:,.0f}", 
                'Net Val': "Rp {:,.0f}", 'Buy Vol': "{:,.0f}", 
                'Sell Vol': "{:,.0f}", 'Net Vol': "{:,.0f}"
            }).background_gradient(subset=['Net Val'], cmap='RdYlGn'),
            use_container_width=True,
            height=400
        )

        # --- SANKEY DIAGRAM ---
        st.header("🕸️ Peta Aliran Dana (Sankey)")
        st.caption("Visualisasi ini menunjukkan Broker Pembeli (Kiri) mengirim uang ke Broker Penjual (Kanan).")
        
        # Kontrol Jumlah Node
        top_n = st.slider("Jumlah Interaksi Terbesar yang Ditampilkan", 5, 50, 15)
        
        # Build & Plot
        try:
            lbl, col, src, tgt, val, l_col = build_sankey_data(df_clean, top_n=top_n)
            fig = create_sankey_figure(lbl, col, src, tgt, val, l_col)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Data tidak cukup untuk membuat grafik Sankey. ({str(e)})")

    except ValueError as ve:
        st.error(f"❌ Kesalahan Format Data: {str(ve)}")
        st.write("Pastikan nama kolom sesuai instruksi di atas.")
    except Exception as e:
        st.error(f"❌ Terjadi kesalahan tak terduga: {str(e)}")

if __name__ == "__main__":
    main()

# ==========================================
# CATATAN DEPLOYMENT (STREAMLIT CLOUD)
# ==========================================
# Agar bisa jalan di Streamlit Cloud, buat file 'requirements.txt'
# sejajar dengan app.py isinya:
#
# streamlit
# pandas
# plotly
# openpyxl
#
# ==========================================
