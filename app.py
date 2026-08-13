import streamlit as st
import pandas as pd
import yfinance as yf
import datetime

st.set_page_config(page_title="BIST Portföy Takibi", layout="wide")

st.title("📈 BIST Mobil Portföy Takibi")

# İşlem geçmişini hafızada tutma
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

# YENİ İŞLEM EKLEME
with st.expander("➕ Yeni İşlem Ekle", expanded=False):
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        tx_date = st.date_input(
            "İşlem Tarihi", 
            value=datetime.date.today(), 
            format="DD/MM/YYYY"
        )
    with col2:
        ticker = st.text_input("Hisse Kodu (Örn: THYAO)").upper().strip()
    with col3:
        action = st.selectbox("İşlem Tipi", ["AL", "SAT"])
    with col4:
        quantity = st.number_input("Adet", min_value=1, value=100)
    with col5:
        price = st.number_input("Birim Fiyat (TL)", min_value=0.01, value=10.0, step=0.1)

    if st.button("İşlemi Kaydet"):
        if ticker:
            formatted_date = tx_date.strftime("%d/%m/%Y")
            st.session_state.transactions.append({
                "Tarih": formatted_date,
                "Hisse": ticker,
                "İşlem": action,
                "Adet": quantity,
                "Fiyat": price,
                "Tutar": quantity * price
            })
            st.success(f"{ticker} işlemi başarıyla eklendi!")
            st.rerun()
        else:
            st.warning("Lütfen hisse kodunu girin.")

# İŞLEM GEÇMİŞİ VE SİLME
st.subheader("📋 İşlem Geçmişi")
if not st.session_state.transactions:
    st.info("Henüz kayıtlı bir işlem yok. Yukarıdaki 'Yeni İşlem Ekle' butonundan ilk işlemini girebilirsin.")
else:
    df_trans = pd.DataFrame(st.session_state.transactions)
    
    col_list, col_del = st.columns([3, 1])
    with col_list:
        st.dataframe(df_trans, use_container_width=True)
    with col_del:
        st.write("**🗑️ Yanlış İşlemi Sil**")
        options = [f"{i+1}. {t.get('Tarih', '')} - {t['Hisse']} ({t['İşlem']} - {t['Adet']} Adet)" for i, t in enumerate(st.session_state.transactions)]
        to_delete_idx = st.selectbox("Silinecek İşlemi Seç", range(len(options)), format_func=lambda x: options[x])
        if st.button("Seçilen İşlemi Sil", type="primary"):
            st.session_state.transactions.pop(to_delete_idx)
            st.success("İşlem silindi!")
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
    
    # Özet Göstergeler (Metrics)
    total_pnl = total_portfolio_val - total_portfolio_cost
    total_pnl_pct = (total_pnl / total_portfolio_cost * 100) if total_portfolio_cost > 0 else 0.0

    m1, m2, m3 = st.columns(3)
    m1.metric("Toplam Portföy Değeri", f"{total_portfolio_val:,.2f} TL")
    m2.metric("Toplam Maliyet", f"{total_portfolio_cost:,.2f} TL")
    m3.metric("Net Kâr / Zarar", f"{total_pnl:,.2f} TL", delta=f"%{total_pnl_pct:.2f}")
