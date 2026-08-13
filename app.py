import streamlit as st
import pandas as pd
import yfinance as yf
import datetime

st.set_page_config(page_title="BIST Portföy Takibi", layout="wide")

st.title("📈 BIST Mobil Portföy Takibi")

# Hafıza Tanımlamaları
if "transactions" not in st.session_state:
    st.session_state.transactions = []

# Yahoo Finance üzerinden BIST fiyatı çekme fonksiyonu
@st.cache_data(ttl=300)
def get_stock_price(ticker):
    try:
        full_ticker = f"{ticker.upper().strip()}.IS"
        stock = yf.Ticker(full_ticker)
        history = stock.history(period="1d")
        if not history.empty:
            return float(history["Close"].iloc[-1])
    except Exception:
        pass
    return None

# YENİ İŞLEM EKLEME FORM (Streamlit Form Yapısı)
with st.expander("➕ Yeni İşlem Ekle", expanded=True):
    with st.form("new_transaction_form", clear_on_submit=True):
        col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 1.5, 1.2, 1.5, 1, 1.2, 1.2])
        with col1:
            tx_order = st.number_input("Sıra No", min_value=1, value=len(st.session_state.transactions) + 1, step=1)
        with col2:
            tx_date = st.date_input("İşlem Tarihi", value=datetime.date.today(), format="DD/MM/YYYY")
        with col3:
            tx_time = st.time_input("Saat", value=datetime.datetime.now().time())
        with col4:
            ticker = st.text_input("Hisse Kodu", placeholder="THYAO")
        with col5:
            action = st.selectbox("İşlem", ["AL", "SAT"])
        with col6:
            quantity = st.number_input("Adet", min_value=1, value=100)
        with col7:
            price = st.number_input("Fiyat (TL)", min_value=0.01, value=10.0, step=0.1)

        submit_btn = st.form_submit_button("İşlemi Kaydet", type="primary")

        if submit_btn:
            clean_ticker = ticker.strip().upper()
            if clean_ticker:
                st.session_state.transactions.append({
                    "Tarih_Obj": tx_date,
                    "Saat_Obj": tx_time,
                    "Tarih": tx_date.strftime("%d/%m/%Y"),
                    "Saat": tx_time.strftime("%H:%M"),
                    "Sıra": tx_order,
                    "Hisse": clean_ticker,
                    "İşlem": action,
                    "Adet": quantity,
                    "Fiyat": price,
                    "Tutar": quantity * price
                })
                # Otomatik kronolojik sıralama (Tarih -> Saat -> Sıra No)
                st.session_state.transactions.sort(
                    key=lambda x: (
                        x.get("Tarih_Obj", datetime.date.min),
                        x.get("Saat_Obj", datetime.time.min),
                        x.get("Sıra", 0)
                    )
                )
                st.success(f"{clean_ticker} işlemi başarıyla eklendi ve sıralandı!")
                st.rerun()
            else:
                st.warning("Lütfen hisse kodunu girin.")

# İŞLEM GEÇMİŞİ
st.subheader("📋 İşlem Geçmişi")

if not st.session_state.transactions:
    st.info("Henüz kayıtlı bir işlem yok. Yukarıdaki formdan ilk işlemini ekleyebilirsin.")
else:
    # Başlık Satırı (1. Sıra No, 2. Tarih, 3. Saat...)
    h1, h2, h3, h4, h5, h6, h7, h8, h9 = st.columns([0.8, 1.2, 1, 1.2, 1, 1, 1.2, 1.2, 0.6])
    h1.markdown("**Sıra**")
    h2.markdown("**Tarih**")
    h3.markdown("**Saat**")
    h4.markdown("**Hisse**")
    h5.markdown("**İşlem**")
    h6.markdown("**Adet**")
    h7.markdown("**Fiyat**")
    h8.markdown("**Tutar**")
    h9.markdown("**Sil**")
    st.divider()

    # İşlem Satırları ve Çöp Kutusu Butonları
    to_delete = None
    for idx, t in enumerate(st.session_state.transactions):
        c1, c2, c3, c4, c5, c6, c7, c8, c9 = st.columns([0.8, 1.2, 1, 1.2, 1, 1, 1.2, 1.2, 0.6])
        c1.write(f"#{t.get('Sıra', idx+1)}")
        c2.write(t.get("Tarih", ""))
        c3.write(t.get("Saat", "--:--"))
        c4.write(f"**{t['Hisse']}**")
        c5.write(f"🟢 AL" if t['İşlem'] == "AL" else f"🔴 SAT")
        c6.write(f"{t['Adet']:,}")
        c7.write(f"{t['Fiyat']:.2f} TL")
        c8.write(f"{t['Tutar']:.2f} TL")
        if c9.button("🗑️", key=f"del_{idx}"):
            to_delete = idx

    if to_delete is not None:
        st.session_state.transactions.pop(to_delete)
        st.rerun()

# PORTFÖY ÖZETİ VE CANLI VERİ HESAPLAMA
st.subheader("📊 Portföy Özetiniz (15 Dakika Gecikmeli Canlı Fiyatlar)")
    
portfolio = {}
for t in st.session_state.transactions:
    symbol = t["Hisse"]
    if symbol not in portfolio:
        portfolio[symbol] = {"adet": 0, "maliyet_toplam": 0.0}
    
    if t["İşlem"] == "AL":
        portfolio[symbol]["adet"] += t["Adet"]
        portfolio[symbol]["maliyet_toplam"] += t["Adet"] * t["Fiyat"]
    elif t["İşlem"] == "SAT":
        portfolio[symbol]["adet"] -= t["Adet"]
        portfolio[symbol]["maliyet_toplam"] -= t["Adet"] * t["Fiyat"]

summary_data = []
total_portfolio_val = 0.0
total_portfolio_cost = 0.0

with st.spinner("BIST güncel fiyatları çekiliyor..."):
    for symbol, data in portfolio.items():
        if data["adet"] > 0:
            avg_cost = data["maliyet_toplam"] / data["adet"]
            curr_price = get_stock_price(symbol)
            
            if curr_price is None:
                curr_price = avg_cost
                price_str = f"{avg_cost:.2f} TL (Canlı Veri Alınamadı)"
            else:
                price_str = f"{curr_price:.2f} TL"

            total_cost = data["adet"] * avg_cost
            total_val = data["adet"] * curr_price
            pnl = total_val - total_cost
            pnl_pct = (pnl / total_cost * 100) if total_cost > 0 else 0.0

            total_portfolio_val += total_val
            total_portfolio_cost += total_cost

            summary_data.append({
                "Hisse": symbol,
                "Adet": data["adet"],
                "Ort. Maliyet": f"{avg_cost:.2f} TL",
                "Güncel Fiyat": price_str,
                "Toplam Maliyet": f"{total_cost:.2f} TL",
                "Güncel Değer": f"{total_val:.2f} TL",
                "Kâr / Zarar": f"{pnl:+.2f} TL",
                "Kâr / Zarar (%)": f"%{pnl_pct:+.2f}"
            })

if summary_data:
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
    
    total_pnl = total_portfolio_val - total_portfolio_cost
    total_pnl_pct = (total_pnl / total_portfolio_cost * 100) if total_portfolio_cost > 0 else 0.0

    m1, m2, m3 = st.columns(3)
    m1.metric("Toplam Portföy Değeri", f"{total_portfolio_val:,.2f} TL")
    m2.metric("Toplam Maliyet", f"{total_portfolio_cost:,.2f} TL")
    m3.metric("Net Kâr / Zarar", f"{total_pnl:,.2f} TL", delta=f"%{total_pnl_pct:.2f}")
