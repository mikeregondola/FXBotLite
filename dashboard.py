import streamlit as st
import requests
import csv
import os
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh

LITE_URL = "http://127.0.0.1:9000"
LOG_FILE = "trade_log.csv"

st.set_page_config(page_title="FXBot Dashboard", layout="wide")

st.title("📊 FXBot SmartWave Dashboard")

# --------------------------------------------------
# AUTO REFRESH
# --------------------------------------------------
st_autorefresh(interval=3000, key="refresh")

# --------------------------------------------------
# FETCH LIVE DATA
# --------------------------------------------------
def get_data():
    try:
        r = requests.get(f"{LITE_URL}/state")
        return r.json()
    except:
        return {"status": "offline", "trades": [], "last_signal": None}

data = get_data()

# --------------------------------------------------
# LOAD TRADE LOG
# --------------------------------------------------
def load_log():

    if not os.path.exists(LOG_FILE):
        return []

    rows = []

    with open(LOG_FILE, newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                row["profit_pips"] = float(row["profit_pips"])
                rows.append(row)
            except:
                pass

    return rows


log_data = load_log()

# --------------------------------------------------
# ANALYTICS
# --------------------------------------------------
profits = [r["profit_pips"] for r in log_data]

total = len(profits)
wins = len([p for p in profits if p > 0])
losses = len([p for p in profits if p <= 0])
pnl = sum(profits)

avg_win = sum([p for p in profits if p > 0]) / wins if wins else 0
avg_loss = sum([p for p in profits if p <= 0]) / losses if losses else 0

# --------------------------------------------------
# STATUS
# --------------------------------------------------
st.subheader("System Status")
st.write(data["status"])

# --------------------------------------------------
# METRICS
# --------------------------------------------------
st.subheader("📈 Performance")

col1, col2, col3 = st.columns(3)

col1.metric("Total Trades", total)
col2.metric("Win Rate", f"{(wins / total * 100) if total else 0:.1f}%")
col3.metric("Total PnL (pips)", round(pnl, 2))

col4, col5 = st.columns(2)

col4.metric("Avg Win", round(avg_win, 2))
col5.metric("Avg Loss", round(avg_loss, 2))

# --------------------------------------------------
# 📊 EQUITY CURVE
# --------------------------------------------------
st.subheader("📊 Equity Curve")

if profits:

    equity = []
    running = 0

    for p in profits:
        running += p
        equity.append(running)

    fig = plt.figure()
    plt.plot(equity)
    plt.xlabel("Trades")
    plt.ylabel("PnL (pips)")
    plt.title("Equity Curve")

    st.pyplot(fig)

else:
    st.write("No trade data yet")

# --------------------------------------------------
# LAST SIGNAL
# --------------------------------------------------
st.subheader("Last Signal")

if data.get("last_signal"):
    st.json(data["last_signal"])
else:
    st.write("No signals yet")

# --------------------------------------------------
# ACTIVE TRADES
# --------------------------------------------------
st.subheader("Active Trades")

if data["trades"]:

    for t in data["trades"]:

        color = "🟢" if t["profit_pips"] >= 0 else "🔴"

        st.markdown(f"""
        ### {t['symbol']} | {t['side']} {color}

        - Entry: {t['entry']}  
        - Current: {t['current']}  
        - Profit: {t['profit_pips']} pips  
        - BE: {t['be_done']}  
        - SL: {t['last_sl']}  
        - Partial Closed: {t['partial_done']}
        """)

else:
    st.write("No active trades")

# --------------------------------------------------
# CONTROLS
# --------------------------------------------------
st.subheader("Controls")

col1, col2 = st.columns(2)

with col1:
    if st.button("BUY EURUSD", key="buy_btn"):
        requests.post(f"{LITE_URL}/signal", json={
            "symbol": "EURUSD",
            "side": "BUY"
        })

with col2:
    if st.button("SELL EURUSD", key="sell_btn"):
        requests.post(f"{LITE_URL}/signal", json={
            "symbol": "EURUSD",
            "side": "SELL"
        })