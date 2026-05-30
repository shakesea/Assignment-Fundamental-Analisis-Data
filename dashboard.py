import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.lines import Line2D
import matplotlib.patches as mpatches

# --- KONFIGURASI HALAMAN STREAMLIT ---
st.set_page_config(
    page_title="Bike-Sharing Analytics Dashboard",
    page_icon="🚲",
    layout="wide"
)

# --- FUNGSI LOAD DATA (DENGAN CACHING AGAR CEPAT) ---
@st.cache_data
def load_data():
    day_df = pd.read_csv("day.csv")
    hour_df = pd.read_csv("hour.csv")
    
    # Konversi tipe data tanggal
    day_df['dteday'] = pd.to_datetime(day_df['dteday'])
    hour_df['dteday'] = pd.to_datetime(hour_df['dteday'])
    
    # Pemetaan label deskriptif cuaca
    weather_mapping = {1: 'Clear', 2: 'Mist/Cloudy', 3: 'Light Snow/Rain', 4: 'Heavy Rain/Ice'}
    day_df['weather_label'] = day_df['weathersit'].map(weather_mapping)
    
    return day_df, hour_df

# Memuat data
try:
    day_df, hour_df = load_data()
except FileNotFoundError:
    st.error("Gagal memuat data! Pastikan file 'day.csv' dan 'hour.csv' berada di folder yang sama dengan file dashboard.py ini.")
    st.stop()

# --- SIDEBAR COMPONENT (FILTER LOGIK) ---
st.sidebar.image("https://images.unsplash.com/photo-1485965120184-e220f721d03e?auto=format&fit=crop&w=300&q=80", use_container_width=True)
st.sidebar.title("Filter Panel")

# Filter Rentang Tanggal
min_date = day_df['dteday'].min()
max_date = day_df['dteday'].max()

start_date, end_date = st.sidebar.date_input(
    label="Pilih Rentang Waktu",
    min_value=min_date,
    max_value=max_date,
    value=[min_date, max_date]
)

# Menerapkan filter rentang tanggal pada data harian dan jam
filtered_day_df = day_df[(day_df['dteday'] >= pd.to_datetime(start_date)) & (day_df['dteday'] <= pd.to_datetime(end_date))]
filtered_hour_df = hour_df[(hour_df['dteday'] >= pd.to_datetime(start_date)) & (hour_df['dteday'] <= pd.to_datetime(end_date))]

# --- MAIN PANEL ---
st.title("🚲 Bike-Sharing Interactive Analytics Dashboard")
st.markdown("Dashboard interaktif untuk menganalisis tren operasional rental sepeda berdasarkan pola waktu dan fluktuasi kondisi lingkungan.")

st.markdown("---")

# --- RENDER KPI METRICS ---
total_rentals = filtered_day_df['cnt'].sum()
avg_casual = filtered_day_df['casual'].mean()
avg_registered = filtered_day_df['registered'].mean()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Total Volume Penyewaan", value=f"{total_rentals:,} unit")
with col2:
    st.metric(label="Rata-rata Sewa Harian (Casual)", value=f"{avg_casual:.2f} unit")
with col3:
    st.metric(label="Rata-rata Sewa Harian (Registered)", value=f"{avg_registered:.2f} unit")

st.markdown("---")

# --- VISUALISASI 1: TREN PER JAM (Pola Waktu) ---
st.subheader("1. Karakteristik Tren Beban Operasional Per Jam")

# Filter tambahan tahun 2012 khusus untuk menjawab Pertanyaan SMART 1 secara konsisten
hour_2012_df = filtered_hour_df[filtered_hour_df['yr'] == 1]

if not hour_2012_df.empty:
    hourly_trend = hour_2012_df.groupby(['workingday', 'hr'], observed=False)['cnt'].mean().reset_index()

    fig1, ax1 = plt.subplots(figsize=(12, 5))
    sns.lineplot(
        data=hourly_trend, 
        x='hr', 
        y='cnt', 
        hue='workingday', 
        marker='o', 
        linewidth=2.5,
        ax=ax1,
        legend=False
    )
    ax1.set_title('Tren Penyewaan Sepeda Per Jam: Hari Kerja vs Hari Libur (Filter Tahun 2012)', fontsize=12, pad=10)
    ax1.set_xlabel('Jam Operasional (00.00 - 23.00)', fontsize=10)
    ax1.set_ylabel('Rata-rata Volume Penyewaan', fontsize=10)
    ax1.set_xticks(range(0, 24))
    ax1.grid(True, linestyle='--', alpha=0.5)

    custom_legend_q1 = [
        Line2D([0], [0], color='#4c72b0', marker='o', linewidth=2.5, label='Hari Libur / Akhir Pekan'),
        Line2D([0], [0], color='#dd8452', marker='o', linewidth=2.5, label='Hari Kerja')
    ]
    ax1.legend(handles=custom_legend_q1, title='Keterangan Hari', fontsize=9)
    
    st.pyplot(fig1)
else:
    st.warning("Data untuk visualisasi tren jam tahun 2012 tidak tersedia pada rentang filter tanggal yang Anda pilih.")

st.markdown("---")

# --- VISUALISASI 2: DAMPAK CUACA (Pola Lingkungan) ---
st.subheader("2. Dampak Kondisi Cuaca terhadap Segmentasi Pengguna")

if not filtered_day_df.empty:
    weather_impact = filtered_day_df.groupby('weather_label', observed=False)[['casual', 'registered']].mean().reset_index()
    weather_melted = pd.melt(
        weather_impact, 
        id_vars=['weather_label'], 
        value_vars=['casual', 'registered'],
        var_name='user_type', 
        value_name='avg_rentals'
    )

    fig2, ax2 = plt.subplots(figsize=(10, 5))
    sns.barplot(
        data=weather_melted, 
        x='weather_label', 
        y='avg_rentals', 
        hue='user_type', 
        palette='muted',
        ax=ax2
    )
    ax2.set_title('Dampak Kondisi Cuaca terhadap Rata-rata Volume Penyewaan Harian', fontsize=12, pad=10)
    ax2.set_xlabel('Kondisi Cuaca', fontsize=10)
    ax2.set_ylabel('Rata-rata Penyewaan per Hari', fontsize=10)
    ax2.grid(axis='y', linestyle='--', alpha=0.5)

    colors = [patch.get_facecolor() for patch in ax2.patches[:2]]
    custom_legend_q2 = [
        mpatches.Patch(color=colors[0], label='Casual (Biasa)'),
        mpatches.Patch(color=colors[1], label='Registered (Terdaftar)')
    ]
    ax2.legend(handles=custom_legend_q2, title='Tipe Pengguna', fontsize=9)
    
    st.pyplot(fig2)
else:
    st.warning("Data harian tidak tersedia pada rentang filter tanggal yang Anda pilih.")

# --- FOOTER ---
st.markdown("---")
st.caption("© 2026 Proyek Analisis Data - Coding Camp powered by DBS Foundation. All Rights Reserved.")