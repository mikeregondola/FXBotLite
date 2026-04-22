import time
import threading
from flask import Flask, request, jsonify

from broker_engine.fxcm_driver import FXCMDriver
from trade_manager import TradeManager

# ----------------------------
# INIT
# ----------------------------
app = Flask(__name__)

config = {
    "username": "...",
    "password": "...",
    "url": "http://www.fxcorporate.com/Hosts.jsp",
    "connection": "Demo"
}

driver = FXCMDriver(config)
trade_manager = TradeManager(driver)

# ----------------------------
# START TRADE MANAGER LOOP
# ----------------------------
def start_tm():
    trade_manager.monitor()

threading.Thread(target=start_tm, daemon=True).start()

print("[LITE] TradeManager started")

# ----------------------------
# SIGNAL ENDPOINT
# ----------------------------
@app.route("/signal", methods=["POST"])
def signal():

    data = request.json

    print("[DEBUG] Incoming signal:", data)

    result = driver.execute_trade(data)

    if result:
        try:
            price_data = driver.get_price(data["symbol"])

            if not price_data:
                return jsonify({"status": "no_price"})

            entry_price = price_data["mid"]

            trade = {
                "symbol": data["symbol"],
                "side": data["side"],
                "entry": entry_price,
                "sl": data.get("sl", entry_price)
            }

            # 🔥 CRITICAL FIX (this was missing)
            trade_manager.track_trade(trade)

            print("[DEBUG] Trade passed to TradeManager")

        except Exception as e:
            print("[ERROR] Trade tracking failed:", e)

    return jsonify({"status": "ok"})

# ----------------------------
# RUN SERVER
# ----------------------------
if __name__ == "__main__":
    print("[LITE] Starting...")
    app.run(host="0.0.0.0", port=9000)