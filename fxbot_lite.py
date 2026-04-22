import threading
import json
import requests
from flask import Flask, request, jsonify

from broker_engine.fxcm_driver import FXCMDriver
from trade_manager import TradeManager

# ----------------------------
# INIT
# ----------------------------
app = Flask(__name__)

# ----------------------------
# LOAD CONFIG
# ----------------------------
try:
    with open("config_lite.json") as f:
        CONFIG = json.load(f)

    broker_config = CONFIG.get("broker", {})
    telegram_config = CONFIG.get("telegram", {})

    print("[DEBUG] Config loaded successfully")

except Exception as e:
    print("[ERROR] Failed to load config:", e)
    broker_config = None
    telegram_config = {}

# ----------------------------
# TELEGRAM FUNCTION
# ----------------------------
def send_telegram(message):
    try:
        token = telegram_config.get("token")
        chat_id = telegram_config.get("chat_id")

        if not token or not chat_id:
            print("[TG] Missing config")
            return

        url = f"https://api.telegram.org/bot{token}/sendMessage"

        response = requests.post(url, json={
            "chat_id": chat_id,
            "text": message
        })

        print("[TG SEND STATUS]", response.status_code)

    except Exception as e:
        print("[TG ERROR]", e)

# ----------------------------
# INIT DRIVER + TRADE MANAGER
# ----------------------------
driver = None
trade_manager = None

if broker_config:
    driver = FXCMDriver(broker_config)
    trade_manager = TradeManager(driver)

    # Start TradeManager loop
    def run_tm():
        trade_manager.monitor()

    threading.Thread(target=run_tm, daemon=True).start()

    print("[LITE] TradeManager started")

else:
    print("[FATAL] Broker config missing")

# ----------------------------
# SIGNAL ENDPOINT
# ----------------------------
@app.route("/signal", methods=["POST"])
def signal():

    if not driver:
        return jsonify({"status": "no_driver"})

    data = request.json
    print("[DEBUG] Incoming signal:", data)

    result = driver.execute_trade(data)

    if result:
        try:
            # Get entry price
            price_data = driver.get_price(data["symbol"])
            entry_price = price_data["mid"] if price_data else 0

            trade = {
                "symbol": data["symbol"],
                "side": data["side"],
                "entry": entry_price,
                "sl": data.get("sl", entry_price)
            }

            # Track trade
            if trade_manager:
                trade_manager.track_trade(trade)

            # Telegram message
            send_telegram(
                f"🚀 Trade Executed\n"
                f"{trade['symbol']} {trade['side']}\n"
                f"Entry: {entry_price}\n"
                f"SL: {trade['sl']}"
            )

        except Exception as e:
            print("[ERROR] Post-trade handling failed:", e)

    return jsonify({"status": "ok"})

# ----------------------------
# STATUS ENDPOINT
# ----------------------------
@app.route("/status", methods=["GET"])
def status():
    return jsonify({
        "driver": "connected" if driver else "not_initialized",
        "trade_manager": "running" if trade_manager else "not_initialized"
    })

# ----------------------------
# HEARTBEAT (OPTIONAL)
# ----------------------------
def heartbeat():
    import time
    while True:
        print("[LITE] Alive | running")
        time.sleep(10)

threading.Thread(target=heartbeat, daemon=True).start()

# ----------------------------
# RUN SERVER
# ----------------------------
if __name__ == "__main__":
    print("[LITE] Starting...")
    app.run(host="0.0.0.0", port=9000)