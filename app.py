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

# YENİ İŞLEM EKLEME FORM
with st.expander("➕ Yeni İşlem Ekle", expanded=True):
    with st.form("new_transaction_form", clear_on_submit=True):
        col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([0.8, 1.2, 1.0, 1.2, 1.1, 0.8, 0.9, 1.0, 1.0])
        with col1:
            tx_order = st.number_input("Sıra No", min_value=1, value=len(st.session_state.transactions) + 1, step=1)
        with col2:
            tx_date = st.date_input("İşlem Tarihi", value=datetime.date.today(), format="DD/MM/YYYY")
        with col3:
            tx_time = st.time_input("Saat", value=datetime.datetime.now().time())
        with col4:
            app_platform = st.text_input("Uygulama / Banka", placeholder="Midas, İş Cep vb.")
        with col5:
            ticker = st.text_input("Hisse Kodu", placeholder="THYAO")
        with col6:
            action = st.selectbox("İşlem", ["AL", "SAT"])
        with col7:
            quantity = st.number_input("Adet", min_value=1, value=100)
        with col8:
            price = st.number_input("Fiyat (TL)", min_value=0.01, value=10.0, step=0.1)
        with col9:
            commission = st.number_input("Komisyon (TL)", min_value=0.0, value=0.0, step=0.1)

        submit_btn = st.form_submit_button("İşlemi Kaydet", type="primary")

        if submit_btn:
            clean_ticker = ticker.strip().upper()
            if clean_ticker:
                formatted_date = tx_date.strftime("%d/%m/%Y")
                formatted_time = tx_time.strftime("%H:%M")

                st.session_state.transactions.append({
                    "Tarih_Obj": tx_date,
                    "Saat_Obj": tx_time,
                    "Tarih": formatted_date,
                    "Saat": formatted_time,
                    "Sıra": tx_order,
                    "Uygulama": app_platform.strip() if app_platform else "-",
                    "Hisse": clean_ticker,
                    "İşlem": action,
                    "Adet": quantity,
                    "Fiyat": price,
                    "Komisyon": commission,
                    "Tutar": quantity * price
                })
                # Tarih ve Saat önceliğine göre otomatik sıralama (Tarih -> Saat -> Sıra No)
                st.session_state.transactions.sort(
                    key=lambda x: (
                        x.get("Tarih_Obj", datetime.date.min),
                        x.get("Saat_Obj", datetime.time.min),
                        x.get("Sıra", 0)
                    )
                )
                st.success(f"#{tx_order} - {clean_ticker} işlemi ({formatted_date} {formatted_time}) başarıyla eklendi!")
                st.rerun()
            else:
                st.warning("Lütfen hisse kodunu girin.")

# İŞLEM GEÇMİŞİ
st.subheader("📋 İşlem Geçmişi")

if not st.session_state.transactions:
    st.info("Henüz kayıtlı bir işlem yok. Yukarıdaki formdan ilk işlemini ekleyebilirsin.")
else:
    # Başlık Satırı
    h1, h2, h3, h4, h5, h6, h7, h8, h9, h10, h11 = st.columns([0.6, 1.0, 0.8, 1.1, 0.9, 0.7, 0.8, 0.9, 0.9, 1.0, 0.5])
    h1.markdown("**Sıra**")
    h2.markdown("**Tarih**")
    h3.markdown("**Saat**")
    h4.markdown("**Uygulama**")
    h5.markdown("**Hisse**")
    h6.markdown("**İşlem**")
    h7.markdown("**Adet**")
    h8.markdown("**Fiyat**")
    h9.markdown("**Komisyon**")
    h10.markdown("**Tutar**")
    h11.markdown("**Sil**")
    st.divider()

    # İşlem Satırları ve Çöp Kutusu
    to_delete = None
    for idx, t in enumerate(st.session_state.transactions):
        c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11 = st.columns([0.6, 1.0, 0.8, 1.1, 0.9, 0.7, 0.8, 0.9, 0.9, 1.0, 0.5])
        c1.write(f"#{t.get('Sıra', idx+1)}")
        c2.write(t.get("Tarih", ""))
        c3.write(t.get("Saat", "--:--"))
        c4.write(t.get("Uygulama", "-"))
        c5.write(f"**{t['Hisse']}**")
        c6.write(f"🟢 AL" if t['İşlem'] == "AL" else f"🔴 SAT")
        c7.write(f"{t['Adet']:,}")
        c8.write(f"{t['Fiyat']:.2f} TL")
        c9.write(f"{t.get('Komisyon', 0.0):.2f} TL")
        c10.write(f"{t['Tutar']:.2f} TL")
        if c11.button("🗑️", key=f"del_{idx}"):
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
        portfolio[symbol] = {"adet": 0, "maliyet_brut": 0.0, "komisyon_toplam": 0.0}
    
    comm = t.get("Komisyon", 0.0)
    
    if t["İşlem"] == "AL":
        portfolio[symbol]["adet"] += t["Adet"]
        portfolio[symbol]["maliyet_brut"] += t["Adet"] * t["Fiyat"]
        portfolio[symbol]["komisyon_toplam"] += comm
    elif t["İşlem"] == "SAT":
        portfolio[symbol]["adet"] -= t["Adet"]
        portfolio[symbol]["maliyet_brut"] -= t["Adet"] * t["Fiyat"]
        portfolio[symbol]["komisyon_toplam"] += comm

summary_data = []
total_portfolio_val = 0.0
total_portfolio_brut_cost = 0.0
total_portfolio_commission = 0.0

with st.spinner("BIST güncel fiyatları çekiliyor..."):
    for symbol, data in portfolio.items():
        if data["adet"] > 0:
            avg_cost_brut = data["maliyet_brut"] / data["adet"]
            maliyet_net = data["maliyet_brut"] + data["komisyon_toplam"]
            avg_cost_net = maliyet_net / data["adet"]
            
            curr_price = get_stock_price(symbol)
            
            if curr_price is None:
                curr_price = avg_cost_brut
                price_str = f"{avg_cost_brut:.2f} TL (Canlı Veri Alınamadı)"
            else:
                price_str = f"{curr_price:.2f} TL"

            total_brut_cost = data["maliyet_brut"]
            total_net_cost = maliyet_net
            total_val = data["adet"] * curr_price
            
            pnl_brut = total_val - total_brut_cost
            pnl_net = total_val - total_net_cost
            pnl_net_pct = (pnl_net / total_net_cost * 100) if total_net_cost > 0 else 0.0

            total_portfolio_val += total_val
            total_portfolio_brut_cost += total_brut_cost
            total_portfolio_commission += data["komisyon_toplam"]

            summary_data.append({
                "Hisse": symbol,
                "Adet": data["adet"],
                "Ort. Maliyet (Brüt)": f"{avg_cost_brut:.2f} TL",
                "Ort. Maliyet (Net)": f"{avg_cost_net:.2f} TL",
                "Güncel Fiyat": price_str,
                "Toplam Komisyon": f"{data['komisyon_toplam']:.2f} TL",
                "Güncel Değer": f"{total_val:.2f} TL",
                "Brüt Kâr / Zarar": f"{pnl_brut:+.2f} TL",
                "Net Kâr / Zarar": f"{pnl_net:+.2f} TL",
                "Net Kâr (%)": f"%{pnl_net_pct:+.2f}"
            })

if summary_data:
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
    
    total_net_cost = total_portfolio_brut_cost + total_portfolio_commission
    total_pnl_brut = total_portfolio_val - total_portfolio_brut_cost
    total_pnl_net = total_portfolio_val - total_net_cost
    total_pnl_net_pct = (total_pnl_net / total_net_cost * 100) if total_net_cost > 0 else 0.0

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Toplam Portföy Değeri", f"{total_portfolio_val:,.2f} TL")
    m2.metric("Toplam Net Maliyet", f"{total_net_cost:,.2f} TL")
    m3.metric("Toplam Komisyon", f"{total_portfolio_commission:,.2f} TL")
    m4.metric("Brüt Kâr / Zarar", f"{total_pnl_brut:,.2f} TL")
    m5.metric("Net Kâr / Zarar (Komisyonlu)", f"{total_pnl_net:,.2f} TL", delta=f"%{total_pnl_net_pct:.2f}")
