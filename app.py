import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import interp1d

st.set_page_config(page_title="FTIR Spektrum Analizörü", layout="wide")

REGIONS = {
    "C=O Bölgesi (1800-1600 cm⁻¹)": {"min_x": 1600, "max_x": 1800},
    "O-H / N-H Bölgesi (3600-3200 cm⁻¹)": {"min_x": 3200, "max_x": 3600},
    "C-H Bölgesi (3000-2800 cm⁻¹)": {"min_x": 2800, "max_x": 3000},
}

st.title("🧪 FTApp")

# Sol menüye (Sidebar) laboratuvar dosya formatı için ayarlar ekliyoruz
st.sidebar.header("⚙️ Dosya Format Ayarlari")
st.sidebar.write("Cihazinizin çikti formatina göre ayarlayin:")

# Excel görüntünüze göre Türkiye'de varsayılan: Seperator ";" ve Decimal "," olur
csv_sep = st.sidebar.selectbox("Sütun Ayirici (Delimiter):", [";", ","], index=0)
csv_decimal = st.sidebar.selectbox("Ondalik Ayirici (Decimal):", [",", "."], index=0)

# 1. Dosya Yükleme Alanı
uploaded_file = st.file_uploader("FTIR Veri Dosyasini Seçin (.csv)", type=["csv"])

if uploaded_file is not None:
    try:

        df = pd.read_csv(uploaded_file, skiprows=1, sep=csv_sep, decimal=csv_decimal)
        
        # Sütun isimlerini temizleme
        df.columns = [c.strip() for c in df.columns]
        
        x_col = df.columns[0] # cm-1
        y_col = df.columns[1] # A
        
        st.success(f"Veri başariyla yüklendi! Sütunlar: {x_col} ve {y_col}")
        
        
        # 2. Bölge Seçimi
        selected_region_name = st.selectbox("Analiz Edilecek Pik Bölgesini Seçin:", list(REGIONS.keys()))
        region = REGIONS[selected_region_name]
        
        # Veriyi seçilen bölgeye göre filtreleme
        region_df = df[(df[x_col] >= region["min_x"]) & (df[x_col] <= region["max_x"])].sort_values(by=x_col)
        
        if region_df.empty:
            st.error("Seçilen dalga sayisi araliğinda veri bulunamadi. Lütfen CSV dosyanizi kontrol edin.")
        else:
            x_data = region_df[x_col].values
            y_data = region_df[y_col].values
            
            # 3. %80 Yükseklik Hesaplama Algoritması
            y_max = np.max(y_data)
            y_min = np.min(y_data)
            
            # (Max - Min) * 0.8 + Min
            y_target = (y_max - y_min) * 0.8 + y_min
            
            # Pikin tepe noktasının indeksi
            max_idx = np.argmax(y_data)
            
    
            try:
                # Sol taraf interpolasyonu
                f_left = interp1d(y_data[:max_idx+1], x_data[:max_idx+1], kind='linear')
                x_left = float(f_left(y_target))
                
                # Sağ taraf interpolasyonu
                f_right = interp1d(y_data[max_idx:], x_data[max_idx:], kind='linear')
                x_right = float(f_right(y_target))
                
                # Sonuçlar
                center_wavenumber = (x_left + x_right) / 2
                bandwidth = abs(x_left - x_right)
                
                # 4.Metrik Kartları
                col1, col2, col3 = st.columns(3)
                col1.metric(label="Maksimum Pik Noktasi (Y)", value=f"{y_max:.4f}")
                col2.metric(label="Merkez Dalga Sayisi (cm⁻¹)", value=f"{center_wavenumber:.2f}")
                col3.metric(label="Bant Genişliği (Bandwidth)", value=f"{bandwidth:.2f}")
                
                # 5. İnteraktif Plotly Grafiği
                fig = go.Figure()
                
                # Orijinal Spektrum Eğrisi
                fig.add_trace(go.Scatter(x=x_data, y=y_data, mode='lines', name='Spektrum Eğrisi', line=dict(color='blue')))
                
                # %80 Eşik Çizgisi 
                fig.add_trace(go.Scatter(x=[region["min_x"], region["max_x"]], y=[y_target, y_target], 
                                         mode='lines', name='%80 Eşik Çizgisi', line=dict(color='red', dash='dash')))
                
                # Kesişim Noktaları
                fig.add_trace(go.Scatter(x=[x_left, x_right], y=[y_target, y_target], 
                                         mode='markers', name='Kesişim Noktalari', marker=dict(color='green', size=10, symbol='x')))
                
                fig.update_layout(
                    title=f"{selected_region_name} Detayli Analizi",
                    xaxis_title=f"{x_col} (cm⁻¹)",
                    yaxis_title=f"{y_col}",
                    xaxis=dict(autorange="reverse"), 
                    template="plotly_white"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.error(f"İnterpolasyon hesaplamasi yapilirken bir hata oluştu. Pik yapisi stabil olmayabilir. Hata: {e}")
                
    except Exception as e:
        st.error(f"Dosya okunurken bir hata oluştu. Dosyanin geçerli bir CSV olduğundan emin olun. Hata: {e}")