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

# YENİ İŞLEM EKLEME FORM (Üst Alanda Sabit)
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

                raw_app = app_platform.strip()
                formatted_app = " ".join([word.capitalize() for word in raw_app.split()]) if raw_app else "-"

                st.session_state.transactions.append({
                    "Tarih_Obj": tx_date,
                    "Saat_Obj": tx_time,
                    "Tarih": formatted_date,
                    "Saat": formatted_time,
                    "Uygulama": formatted_app,
                    "Hisse": clean_ticker,
                    "İşlem": action,
                    "Adet": quantity,
                    "Fiyat": price,
                    "Komisyon": commission,
                    "Tutar": quantity * price
                })

                # Tarih ve Saat önceliğine göre sırala
                st.session_state.transactions.sort(
                    key=lambda x: (
                        x.get("Tarih_Obj", datetime.date.min),
                        x.get("Saat_Obj", datetime.time.min)
                    )
                )

                for i, item in enumerate(st.session_state.transactions):
                    item["Sıra"] = i + 1

                st.success(f"{clean_ticker} işlemi ({formatted_date} {formatted_time}) başarıyla eklendi!")
                st.rerun()
            else:
                st.warning("Lütfen hisse kodunu girin.")

# PORTFÖY HESAPLAMA MOTORU (Gerçekleşmiş Kâr/Zarar Dâhil)
def calculate_portfolio_data(transactions_list):
    portfolio = {}
    for t in transactions_list:
        symbol = t["Hisse"]
        if symbol not in portfolio:
            portfolio[symbol] = {
                "adet": 0,
                "toplam_maliyet_brut": 0.0,
                "toplam_maliyet_net": 0.0,
                "komisyon_toplam": 0.0,
                "gerceklesen_kar_brut": 0.0,
                "gerceklesen_kar_net": 0.0
            }

        qty = t["Adet"]
        price = t["Fiyat"]
        comm = t.get("Komisyon", 0.0)
        portfolio[symbol]["komisyon_toplam"] += comm

        if t["İşlem"] == "AL":
            portfolio[symbol]["toplam_maliyet_brut"] += (qty * price)
            portfolio[symbol]["toplam_maliyet_net"] += (qty * price) + comm
            portfolio[symbol]["adet"] += qty
        elif t["İşlem"] == "SAT":
            if portfolio[symbol]["adet"] > 0:
                avg_brut = portfolio[symbol]["toplam_maliyet_brut"] / portfolio[symbol]["adet"]
                avg_net = portfolio[symbol]["toplam_maliyet_net"] / portfolio[symbol]["adet"]

                sell_val_brut = qty * price
                sell_val_net = (qty * price) - comm
                cogs_brut = qty * avg_brut
                cogs_net = qty * avg_net

                portfolio[symbol]["gerceklesen_kar_brut"] += (sell_val_brut - cogs_brut)
                portfolio[symbol]["gerceklesen_kar_net"] += (sell_val_net - cogs_net)

                portfolio[symbol]["toplam_maliyet_brut"] -= cogs_brut
                portfolio[symbol]["toplam_maliyet_net"] -= cogs_net
                portfolio[symbol]["adet"] -= qty

    return portfolio

# SEKMELERİ OLUŞTURMA
unique_stocks = list(dict.fromkeys([t["Hisse"] for t in st.session_state.transactions]))
tab_list = ["🌐 Genel Portföy"] + [f"📌 {symbol}" for symbol in unique_stocks]
tabs = st.tabs(tab_list)

# --- SEKME 1: GENEL PORTFÖY ---
with tabs[0]:
    st.subheader("📋 Tüm İşlem Geçmişi")
    if not st.session_state.transactions:
        st.info("Henüz kayıtlı bir işlem yok.")
    else:
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

        to_delete = None
        for idx, t in enumerate(st.session_state.transactions):
            c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11 = st.columns([0.6, 1.0, 0.8, 1.1, 0.9, 0.7, 0.8, 0.9, 0.9, 1.0, 0.5])
            c1.write(f"#{idx+1}")
            c2.write(t.get("Tarih", ""))
            c3.write(t.get("Saat", "--:--"))
            c4.write(t.get("Uygulama", "-"))
            c5.write(f"**{t['Hisse']}**")
            c6.write(f"🟢 AL" if t['İşlem'] == "AL" else f"🔴 SAT")
            c7.write(f"{t['Adet']:,}")
            c8.write(f"{t['Fiyat']:.2f} TL")
            c9.write(f"{t.get('Komisyon', 0.0):.2f} TL")
            c10.write(f"{t['Tutar']:.2f} TL")
            if c11.button("🗑️", key=f"del_all_{idx}"):
                to_delete = idx

        if to_delete is not None:
            st.session_state.transactions.pop(to_delete)
            for i, item in enumerate(st.session_state.transactions):
                item["Sıra"] = i + 1
            st.rerun()

    st.subheader("📊 Portföy Özetiniz (15 Dakika Gecikmeli Canlı Fiyatlar)")
    portfolio = calculate_portfolio_data(st.session_state.transactions)
    
    summary_data = []
    total_portfolio_val = 0.0
    total_portfolio_net_cost = 0.0
    total_portfolio_commission = 0.0
    total_realized_pnl_net = 0.0
    total_unrealized_pnl_net = 0.0

    with st.spinner("BIST güncel fiyatları çekiliyor..."):
        for symbol, data in portfolio.items():
            total_portfolio_commission += data["komisyon_toplam"]
            total_realized_pnl_net += data["gerceklesen_kar_net"]

            if data["adet"] > 0:
                avg_cost_brut = data["toplam_maliyet_brut"] / data["adet"]
                avg_cost_net = data["toplam_maliyet_net"] / data["adet"]

                curr_price = get_stock_price(symbol)
                if curr_price is None:
                    curr_price = avg_cost_brut
                    price_str = f"{avg_cost_brut:.2f} TL (Canlı Veri Yok)"
                else:
                    price_str = f"{curr_price:.2f} TL"

                total_net_cost = data["toplam_maliyet_net"]
                total_val = data["adet"] * curr_price

                unrealized_net = total_val - total_net_cost
                total_unrealized_pnl_net += unrealized_net
                stock_total_net_pnl = unrealized_net + data["gerceklesen_kar_net"]
                net_pnl_pct = (stock_total_net_pnl / total_net_cost * 100) if total_net_cost > 0 else 0.0

                total_portfolio_val += total_val
                total_portfolio_net_cost += total_net_cost

                summary_data.append({
                    "Hisse": symbol,
                    "Adet": data["adet"],
                    "Ort. Maliyet (Net)": f"{avg_cost_net:.2f} TL",
                    "Güncel Fiyat": price_str,
                    "Güncel Değer": f"{total_val:.2f} TL",
                    "Satış Kârı (Net)": f"{data['gerceklesen_kar_net']:+.2f} TL",
                    "Açık Poz. Kârı": f"{unrealized_net:+.2f} TL",
                    "Toplam Net Kâr / Zarar": f"{stock_total_net_pnl:+.2f} TL",
                    "Net Kâr (%)": f"{net_pnl_pct:+.2f}%"
                })

    if summary_data:
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True)

        overall_net_pnl = total_unrealized_pnl_net + total_realized_pnl_net
        overall_net_pct = (overall_net_pnl / total_portfolio_net_cost * 100) if total_portfolio_net_cost > 0 else 0.0

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Toplam Portföy Değeri", f"{total_portfolio_val:,.2f} TL")
        m2.metric("Açık Poz. Net Maliyet", f"{total_portfolio_net_cost:,.2f} TL")
        m3.metric("Toplam Komisyon", f"{total_portfolio_commission:,.2f} TL")
        m4.metric("Satış Kârı (Realized)", f"{total_realized_pnl_net:,.2f} TL")
        m5.metric("Net Kâr / Zarar (Toplam)", f"{overall_net_pnl:,.2f} TL", delta=f"{overall_net_pct:+.2f}%")

# --- HİSSEYE ÖZEL SEKMELER ---
for i, symbol in enumerate(unique_stocks):
    with tabs[i + 1]:
        st.subheader(f"📌 {symbol} Hisse Detayı ve İşlemleri")
        
        # Sadece bu hissenin işlemlerini filtrele
        stock_txs = [t for t in st.session_state.transactions if t["Hisse"] == symbol]
        stock_portfolio = calculate_portfolio_data(stock_txs).get(symbol, {})

        if stock_portfolio:
            qty = stock_portfolio["adet"]
            net_cost = stock_portfolio["toplam_maliyet_net"]
            realized_net = stock_portfolio["gerceklesen_kar_net"]
            comm = stock_portfolio["komisyon_toplam"]

            curr_price = get_stock_price(symbol)
            if curr_price is None:
                curr_price = (net_cost / qty) if qty > 0 else 0.0

            curr_val = qty * curr_price
            unrealized_net = (curr_val - net_cost) if qty > 0 else 0.0
            total_stock_pnl = unrealized_net + realized_net

            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric("Mevcut Adet", f"{qty:,}")
            k2.metric("Güncel Fiyat", f"{curr_price:.2f} TL")
            k3.metric("Satış Kârı (Net)", f"{realized_net:+.2f} TL")
            k4.metric("Açık Pozisyon Kârı", f"{unrealized_net:+.2f} TL")
            k5.metric("Toplam Net Kâr / Zarar", f"{total_stock_pnl:+.2f} TL")

        st.divider()
        st.markdown(f"### 📋 {symbol} İşlem Geçmişi")
        
        h1, h2, h3, h4, h5, h6, h7, h8, h9 = st.columns([0.8, 1.1, 0.9, 1.2, 0.8, 0.9, 1.0, 1.0, 1.1])
        h1.markdown("**Sıra**")
        h2.markdown("**Tarih**")
        h3.markdown("**Saat**")
        h4.markdown("**Uygulama**")
        h5.markdown("**İşlem**")
        h6.markdown("**Adet**")
        h7.markdown("**Fiyat**")
        h8.markdown("**Komisyon**")
        h9.markdown("**Tutar**")
        st.divider()

        for s_idx, t in enumerate(stock_txs):
            c1, c2, c3, c4, c5, c6, c7, c8, c9 = st.columns([0.8, 1.1, 0.9, 1.2, 0.8, 0.9, 1.0, 1.0, 1.1])
            c1.write(f"#{t.get('Sıra', s_idx+1)}")
            c2.write(t.get("Tarih", ""))
            c3.write(t.get("Saat", "--:--"))
            c4.write(t.get("Uygulama", "-"))
            c5.write(f"🟢 AL" if t['İşlem'] == "AL" else f"🔴 SAT")
            c6.write(f"{t['Adet']:,}")
            c7.write(f"{t['Fiyat']:.2f} TL")
            c8.write(f"{t.get('Komisyon', 0.0):.2f} TL")
            c9.write(f"{t['Tutar']:.2f} TL")
