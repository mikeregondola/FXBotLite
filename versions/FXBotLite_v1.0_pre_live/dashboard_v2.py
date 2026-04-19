import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ----------------------------
# LOAD DATA
# ----------------------------
try:
    df = pd.read_csv("trade_log.csv")
except:
    st.error("No trade_log.csv found")
    st.stop()

# Normalize column names
df.columns = df.columns.str.lower()

# ----------------------------
# COLUMN FIXES
# ----------------------------

# Rename to expected names
if "time" in df.columns:
    df.rename(columns={"time": "timestamp"}, inplace=True)

if "profit_pips" in df.columns:
    df.rename(columns={"profit_pips": "pips"}, inplace=True)

# If profit not available → approximate using pips
if "profit" not in df.columns:
    df["profit"] = df["pips"]  # temporary fallback

# ----------------------------
# TYPE CONVERSION
# ----------------------------
df["pips"] = pd.to_numeric(df["pips"], errors="coerce").fillna(0)
df["profit"] = pd.to_numeric(df["profit"], errors="coerce").fillna(0)

# ----------------------------
# HEADER
# ----------------------------
st.title("📊 FXBot Performance Dashboard")

# ----------------------------
# BASIC STATS
# ----------------------------
total_trades = len(df)
wins = len(df[df["profit"] > 0])
losses = len(df[df["profit"] <= 0])
win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
total_profit = df["profit"].sum()

st.subheader("📌 Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Trades", total_trades)
col2.metric("Win Rate (%)", f"{win_rate:.2f}")
col3.metric("Net Profit", f"{total_profit:.2f}")
col4.metric("Wins / Losses", f"{wins} / {losses}")

# ----------------------------
# EQUITY CURVE
# ----------------------------
st.subheader("📈 Equity Curve")

df["cumulative_profit"] = df["profit"].cumsum()

fig, ax = plt.subplots()
ax.plot(df["cumulative_profit"])
ax.set_title("Equity Curve")

st.pyplot(fig)

# ----------------------------
# PIPS DISTRIBUTION
# ----------------------------
st.subheader("📊 Pips Distribution")

fig2, ax2 = plt.subplots()
ax2.hist(df["pips"], bins=20)

st.pyplot(fig2)

# ----------------------------
# PROFIT BY PAIR
# ----------------------------
st.subheader("💱 Profit by Pair")

pair_profit = df.groupby("symbol")["profit"].sum()
st.bar_chart(pair_profit)

# ----------------------------
# TABLE
# ----------------------------
st.subheader("📋 Trade Log")
st.dataframe(df.sort_values(by="timestamp", ascending=False))
You sent
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ----------------------------
# LOAD DATA
# ----------------------------
try:
    df = pd.read_csv("trade_log.csv")
except:
    st.error("No trade_log.csv found")
    st.stop()

# Normalize column names
df.columns = df.columns.str.lower()

# ----------------------------
# COLUMN FIXES (ADAPT TO YOUR CSV)
# ----------------------------
if "time" in df.columns:
    df.rename(columns={"time": "timestamp"}, inplace=True)

if "profit_pips" in df.columns:
    df.rename(columns={"profit_pips": "pips"}, inplace=True)

# If profit column missing → fallback to pips
if "profit" not in df.columns:
    df["profit"] = df["pips"]

# ----------------------------
# TYPE CONVERSION
# ----------------------------
df["pips"] = pd.to_numeric(df["pips"], errors="coerce").fillna(0)
df["profit"] = pd.to_numeric(df["profit"], errors="coerce").fillna(0)

# ----------------------------
# HEADER
# ----------------------------
st.title("📊 FXBot Performance Dashboard")

# ----------------------------
# BASIC STATS
# ----------------------------
total_trades = len(df)
wins = len(df[df["profit"] > 0])
losses = len(df[df["profit"] <= 0])
win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
total_profit = df["profit"].sum()

st.subheader("📌 Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Trades", total_trades)
col2.metric("Win Rate (%)", f"{win_rate:.2f}")
col3.metric("Net Profit", f"{total_profit:.2f}")
col4.metric("Wins / Losses", f"{wins} / {losses}")

# ----------------------------
# EQUITY CURVE
# ----------------------------
st.subheader("📈 Equity Curve")

df["equity"] = df["profit"].cumsum()

fig, ax = plt.subplots()
ax.plot(df["equity"])
ax.set_title("Equity Curve")
ax.set_xlabel("Trades")
ax.set_ylabel("Profit")

st.pyplot(fig)

# ----------------------------
# PIPS DISTRIBUTION
# ----------------------------
st.subheader("📊 Pips Distribution")

fig2, ax2 = plt.subplots()
ax2.hist(df["pips"], bins=20)
ax2.set_title("Pips Distribution")

st.pyplot(fig2)

# ----------------------------
# PROFIT BY PAIR
# ----------------------------
st.subheader("💱 Profit by Pair")

pair_profit = df.groupby("symbol")["profit"].sum()
st.bar_chart(pair_profit)

# ----------------------------
# ADVANCED METRICS
# ----------------------------
st.subheader("🧠 Advanced Metrics")

avg_win = df[df["profit"] > 0]["profit"].mean() if wins > 0 else 0
avg_loss = df[df["profit"] <= 0]["profit"].mean() if losses > 0 else 0

profit_sum = df[df["profit"] > 0]["profit"].sum()
loss_sum = df[df["profit"] <= 0]["profit"].sum()

profit_factor = abs(profit_sum / loss_sum) if loss_sum != 0 else 0

expectancy = (win_rate / 100 * avg_win) + ((1 - win_rate / 100) * avg_loss)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Avg Win", f"{avg_win:.2f}")
col2.metric("Avg Loss", f"{avg_loss:.2f}")
col3.metric("Profit Factor", f"{profit_factor:.2f}")
col4.metric("Expectancy", f"{expectancy:.2f}")

# ----------------------------
# DRAWDOWN
# ----------------------------
st.subheader("⚠️ Drawdown")

df["peak"] = df["equity"].cummax()
df["drawdown"] = df["equity"] - df["peak"]

max_dd = df["drawdown"].min()

st.metric("Max Drawdown", f"{max_dd:.2f}")

fig3, ax3 = plt.subplots()
ax3.plot(df["drawdown"])
ax3.set_title("Drawdown Curve")

st.pyplot(fig3)

# ----------------------------
# TRADE TABLE
# ----------------------------
st.subheader("📋 Trade Log")

st.dataframe(df.sort_values(by="timestamp", ascending=False))





