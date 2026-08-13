import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# Mobil ekran düzeni ayarı
st.set_page_config(page_title="Hisse Portföyüm", page_icon="📈", layout="wide")

DATA_FILE = "portfoy_verileri.json"

def verileri_yukle():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def verileri_kaydet(veriler):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(veriler, f, ensure_ascii=False, indent=4)

islemler = verileri_yukle()

st.title("📈 BIST Mobil Portföy Takibi")

# --- MOBİL UYUMLU İŞLEM EKLEME FORMU ---
with st.expander("➕ Yeni İşlem Ekle", expanded=False):
    with st.form("islem_formu"):
        col1, col2 = st.columns(2)
        with col1:
            uygulama = st.text_input("İşlem Yapılan Uygulama", placeholder="Örn: İş Bankası, Midas")
            hisse = st.text_input("Hisse Kodu (Adı)", placeholder="Örn: MOGAN").upper()
            islem_tipi = st.selectbox("İşlem Tipi", ["ALIŞ", "SATIŞ"])
            birim_fiyat = st.number_input("Gerçekleşen Birim Fiyat (TL)", min_value=0.01, step=0.01, format="%.2f")
            lot = st.number_input("İşlem Adedi (Lot)", min_value=1, step=1)
        
        with col2:
            tarih = st.date_input("İşlem Tarihi", datetime.now()).strftime("%Y-%m-%d")
            guncel_fiyat = st.number_input("Hisse Güncel Birim Fiyatı (TL)", min_value=0.0, step=0.01, format="%.2f")
            komisyon = st.number_input("Komisyon Ücreti (TL)", min_value=0.0, step=0.1, format="%.2f")
            islem_no = st.text_input("Bankadaki İşlem Numarası", placeholder="Opsiyonel")

        kaydet = st.form_submit_button("İşlemi Kaydet")

        if kaydet and hisse:
            yeni_islem = {
                "uygulama": uygulama,
                "tarih": tarih,
                "hisse": hisse,
                "islem_tipi": islem_tipi,
                "guncel_fiyat": guncel_fiyat,
                "alis_fiyati": birim_fiyat if islem_tipi == "ALIŞ" else 0.0,
                "satis_fiyati": birim_fiyat if islem_tipi == "SATIŞ" else 0.0,
                "lot": lot,
                "komisyon": komisyon,
                "islem_no": islem_no
            }
            islemler.append(yeni_islem)
            verileri_kaydet(islemler)
            st.success(f"{hisse} işlemi başarıyla kaydedildi!")
            st.rerun()

# --- HESAPLAMA MANTIĞI VE ÖZET SAYFALARI ---
if islemler:
    df = pd.DataFrame(islemler)
    
    # Tüm Hisse Listesi
    hisseler = sorted(list(set(df['hisse'])))
    
    # SEKMELER (Görselindeki sekme yapısının birebir aynısı)
    sekmeler = st.tabs(["📊 Tüm Hisse İşlemleri"] + [f"📌 {h}" for h in hisseler])
    
    # 1. TÜM HİSSE İŞLEMLERİ SEKMESİ
    with sekmeler[0]:
        st.subheader("Tüm İşlem Kayıtları")
        
        # Genel özet kartları
        toplam_islem_sayisi = len(df)
        st.metric("Toplam Kayıtlı İşlem", toplam_islem_sayisi)
        
        # Tablo gösterimi
        st.dataframe(df, use_container_width=True)

    # 2. HİSSE BAZLI ÖZEL SEKMELER
    for i, h_kod in enumerate(hisseler):
        with sekmeler[i+1]:
            h_df = df[df['hisse'] == h_kod].copy()
            
            # Stok / Maliyet / Kâr Hesaplama
            toplam_alis_lot = h_df[h_df['islem_tipi'] == 'ALIŞ']['lot'].sum()
            toplam_satis_lot = h_df[h_df['islem_tipi'] == 'SATIŞ']['lot'].sum()
            kalan_lot = toplam_alis_lot - toplam_satis_lot
            
            toplam_alis_tutar = (h_df[h_df['islem_tipi'] == 'ALIŞ']['alis_fiyati'] * h_df[h_df['islem_tipi'] == 'ALIŞ']['lot']).sum()
            ort_alis = (toplam_alis_tutar / toplam_alis_lot) if toplam_alis_lot > 0 else 0.0
            
            toplam_satis_tutar = (h_df[h_df['islem_tipi'] == 'SATIŞ']['satis_fiyati'] * h_df[h_df['islem_tipi'] == 'SATIŞ']['lot']).sum()
            ort_satis = (toplam_satis_tutar / toplam_satis_lot) if toplam_satis_lot > 0 else 0.0
            
            # Realize Kar/Zarar
            realize_kar = toplam_satis_tutar - (toplam_satis_lot * ort_alis) - h_df['komisyon'].sum()
            
            # Kart Görünümleri (Mobil Uyumlu)
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Eldeki Kalan Lot", f"{kalan_lot} Lot")
            col_b.metric("Ortalama Alış Fiyatı", f"{ort_alis:.2f} TL")
            col_c.metric("Realize Kâr/Zarar", f"{realize_kar:.2f} TL", delta_color="normal")
            
            st.divider()
            st.write(f"**{h_kod} İşlem Geçmişi:**")
            st.dataframe(h_df, use_container_width=True)
else:
    st.info("Henüz kayıtlı bir işlem yok. Yukarıdaki 'Yeni İşlem Ekle' butonundan ilk işlemini girebilirsin.")
