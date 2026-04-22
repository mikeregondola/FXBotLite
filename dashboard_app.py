import streamlit as st
import json
import pandas as pd
import os
import time

st.set_page_config(page_title="StructuraFX Dashboard", layout="wide")

DASHBOARD_PATH = "dashboard/data.json"
JOURNAL_PATH = "journal/trades.json"

# ---------------- LOAD DATA ----------------
def load_dashboard():
    try:
        if not os.path.exists(DASHBOARD_PATH):
            return {}
        with open(DASHBOARD_PATH, "r") as f:
            return json.load(f)
    except:
        return {}

def load_trades():
    try:
        if not os.path.exists(JOURNAL_PATH):
            return pd.DataFrame()

        with open(JOURNAL_PATH, "r") as f:
            data = json.load(f)

        if not isinstance(data, list):
            return pd.DataFrame()

        df = pd.DataFrame(data)

        if "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"])

        return df.sort_values("time")

    except:
        return pd.DataFrame()

data = load_dashboard()
trades = load_trades()

# ---------------- HEADER ----------------
st.title("📊 StructuraFX Control Dashboard")

# ---------------- STATUS ----------------
st.subheader("⚙️ System Status")

c1, c2, c3 = st.columns(3)
c1.metric("Mode", data.get("mode", "N/A"))
c2.metric("Paused", data.get("paused", "N/A"))
c3.metric("Last Signal", data.get("last_signal", "N/A"))

# ---------------- EQUITY ----------------
st.subheader("💰 Equity & Performance")

c1, c2 = st.columns(2)

equity = data.get("equity", 0)
pnl = data.get("daily_pnl", 0)

c1.metric("Equity", f"{equity:.2f}" if isinstance(equity, (int, float)) else "N/A")
c2.metric("Daily PnL", f"{pnl:.2f}" if isinstance(pnl, (int, float)) else "N/A")

# ---------------- EQUITY CURVE ----------------
st.subheader("📈 Equity Curve")

if not trades.empty and "result" in trades.columns:

    # Assign simple values:
    # executed = +1, blocked = 0 (placeholder)
    trades["value"] = trades["result"].apply(
        lambda x: 1 if x == "executed" else 0
    )

    trades["equity_curve"] = trades["value"].cumsum()

    st.line_chart(trades.set_index("time")["equity_curve"])

else:
    st.info("Not enough data for equity curve")

# ---------------- DRAWDOWN ----------------
st.subheader("📉 Drawdown")

if not trades.empty and "equity_curve" in trades.columns:

    trades["peak"] = trades["equity_curve"].cummax()
    trades["drawdown"] = trades["equity_curve"] - trades["peak"]

    st.line_chart(trades.set_index("time")["drawdown"])

else:
    st.info("Not enough data for drawdown")

# ---------------- TRADE JOURNAL ----------------
st.subheader("📜 Trade Journal")

if not trades.empty:
    st.dataframe(trades.tail(20), use_container_width=True)

    if "result" in trades.columns:
        st.subheader("📊 Trade Outcomes")
        st.bar_chart(trades["result"].value_counts())

else:
    st.info("No trade data yet")

# ---------------- AUTO REFRESH ----------------
st.caption("🔄 Auto-refresh every 5 seconds")
time.sleep(5)
st.experimental_rerun()