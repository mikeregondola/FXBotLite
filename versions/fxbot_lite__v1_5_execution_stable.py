
import json
import threading
import time

from flask import Flask, request, jsonify

from broker_engine.fxcm_driver import FXCMDriver
from trade_manager import TradeManager
from telegram_bot import TelegramBot
from node_manager import NodeManager


# LOAD CONFIG
with open("config_lite.json", "r") as f:
    config = json.load(f)


# NODE
node_manager = NodeManager()

node_id = config["node"]["node_id"]
api_key = config["node"]["api_key"]

valid, info = node_manager.validate(node_id, api_key)

if not valid:
    print(f"[AUTH] Failed: {info}")
    exit()

print(f"[AUTH] Node validated → Tier: {info['tier']}")


# BROKER
driver = FXCMDriver(config["broker"])
driver.full_config = config


# TELEGRAM
tg = TelegramBot(
    config["telegram"]["chat_id"],
    config["telegram"]["bot_token"]
)


# TRADE MANAGER
tm = TradeManager(driver, tg)


def start_tm():
    while not driver.connected:
        time.sleep(1)

    print("[LITE] FXCM ready → starting TradeManager")
    tm.monitor()


threading.Thread(target=start_tm, daemon=True).start()


# TELEGRAM LISTENER
def start_telegram_listener():
    print("[LITE] Telegram listener started")

    while True:
        tg.handle_commands(node_manager)
        time.sleep(3)


threading.Thread(target=start_telegram_listener, daemon=True).start()


# FLASK
app = Flask(__name__)


@app.route("/signal", methods=["POST"])
def signal():

    data = request.json
    print(f"[LITE] Signal: {data}")

    tier = info["tier"]
    chat_id = node_manager.get_chat_id(node_id)

    # ---------- FREE ----------
    if tier == "FREE":

        print("[AUTH] FREE → delayed")

        def delayed():
            time.sleep(5)
            
            tg.send_message(
                f"📊 {data['symbol']} {data['side']} (DELAYED)\n\n"
                f"SL: {data.get('sl', 'N/A')}\n\n"
                f"⚠️ Execute manually.\n"
                f"🚀 Upgrade to PRO.",
                chat_id=chat_id
            )

        threading.Thread(target=delayed, daemon=True).start()

        return jsonify({"status": "delayed"})

    # ---------- PRO ----------
    print("[AUTH] EXECUTION ALLOWED")

    trade = driver.execute_trade(data)

    if trade:
        tm.track_trade(trade)

        tg.send_message(
            f"📈 {trade['symbol']} {trade['side']}\n"
            f"Entry: {trade['entry']:.5f}\n"
            f"SL: {trade['sl']:.5f}",
            chat_id=chat_id
        )

        return jsonify({"status": "executed"})

    return jsonify({"status": "failed"})


if __name__ == "__main__":
    print("[LITE] Starting...")
    app.run(host="0.0.0.0", port=9000)

