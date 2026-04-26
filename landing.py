import streamlit as st
import pandas as pd
import json

st.markdown("""<meta http-equiv="refresh" content="10">""", unsafe_allow_html=True)

def load_signals():
    try:
        with open("signals_live.json", "r") as f:
            return json.load(f)
    except:
        return []

st.set_page_config(page_title="FXBot Dashboard", layout="centered")

st.title("📈 FXBot SmartWave")

# ---------------- PERFORMANCE
st.header("📊 Performance Summary")

signals = load_signals()

if signals:
    total = len(signals)
    wins = sum(1 for s in signals if "TP" in s["status"])
    losses = sum(1 for s in signals if "SL" in s["status"])
    pnl = sum(s.get("pnl", 0) for s in signals)
    win_rate = (wins / total * 100) if total else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Trades", total)
    col2.metric("Win Rate", f"{win_rate:.1f}%")
    col3.metric("Total PnL", f"{pnl:.2f}")

# ---------------- TABLE
st.header("📡 Signals")
if signals:
    st.dataframe(pd.DataFrame(signals), use_container_width=True)

# ---------------- FEED
st.header("⚡ Activity")
for s in signals[:10]:
    txt = f"{s['time']} | {s['symbol']} {s['side']} → {s['status']}"
    if "TP" in s["status"]:
        st.success(txt)
    elif "SL" in s["status"]:
        st.error(txt)
    elif "BE" in s["status"]:
        st.warning(txt)
    else:
        st.write(txt)