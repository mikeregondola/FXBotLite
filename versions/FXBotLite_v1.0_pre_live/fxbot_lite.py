import json
import threading
import time

from datetime import datetime, timezone
from flask import Flask, request, jsonify

from broker_engine.fxcm_driver import FXCMDriver
from trade_manager import TradeManager
from telegram_bot import TelegramBot
from node_manager import NodeManager


# ---------------- TREND FILTER ----------------
def is_trending(driver, symbol, config):

    prices = []

    for _ in range(20):
        p = driver.get_price(symbol)["mid"]
        prices.append(p)
        time.sleep(0.2)

    if len(prices) < 20:
        return True

    higher = 0
    lower = 0

    for i in range(1, len(prices)):
        if prices[i] > prices[i - 1]:
            higher += 1
        elif prices[i] < prices[i - 1]:
            lower += 1

    total = higher + lower

    if total == 0:
        return False

    strength = abs(higher - lower) / total
    threshold = config["strategy"]["trend_threshold"]

    print(f"[FILTER DEBUG] Strength: {strength:.2f} | Threshold: {threshold}")

    return strength > threshold


# ---------------- SESSION FILTER ----------------
def is_session_open(config):

    if not config.get("session", {}).get("enabled", False):
        return True

    now = datetime.now(timezone.utc)
    hour = now.hour

    start = config["session"]["start_hour_utc"]
    end = config["session"]["end_hour_utc"]

    return start <= hour < end


# ---------------- LOAD CONFIG ----------------
with open("config_lite.json", "r") as f:
    config = json.load(f)


# ---------------- NODE ----------------
node_manager = NodeManager()

node_id = config["node"]["node_id"]
api_key = config["node"]["api_key"]

valid, info = node_manager.validate(node_id, api_key)

if not valid:
    print("[AUTH] Failed:", info)
    exit()

print(f"[AUTH] Node validated → Tier: {info['tier']}")


# ---------------- BROKER ----------------
driver = FXCMDriver(config["broker"])
driver.full_config = config


# ---------------- TELEGRAM ----------------
tg = TelegramBot(
    config["telegram"]["chat_id"],
    config["telegram"]["bot_token"]
)


# ---------------- TRADE MANAGER ----------------
tm = TradeManager(driver, tg, config)


def start_tm():
    while not driver.connected:
        time.sleep(1)

    print("[LITE] FXCM ready → starting TradeManager")
    tm.monitor()


threading.Thread(target=start_tm, daemon=True).start()


# ---------------- TELEGRAM LISTENER ----------------
def start_telegram_listener():
    print("[LITE] Telegram listener started")

    while True:
        tg.handle_commands(node_manager)
        time.sleep(3)


threading.Thread(target=start_telegram_listener, daemon=True).start()


# ---------------- FLASK ----------------
app = Flask(__name__)


@app.route("/signal", methods=["POST"])
def signal():

    data = request.json
    print("[LITE] Signal:", data)

    tier = info["tier"]
    chat_id = node_manager.get_chat_id(node_id)

    # ---------- FREE ----------
    if tier == "FREE":
        return jsonify({"status": "delayed"})

    print("[AUTH] EXECUTION ALLOWED")

    # -------- SESSION FILTER --------
    if not is_session_open(config):

        print("[SESSION] Outside trading hours")

        tg.send_message(
            f"⛔ Trade Blocked (Session Closed)\n{data['symbol']} {data['side']}",
            chat_id=chat_id
        )

        return jsonify({"status": "blocked_session"})

    # -------- TREND FILTER --------
    if not is_trending(driver, data["symbol"], config):

        print("[FILTER] Ranging → blocked")

        tg.send_message(
            f"⛔ Trade Blocked (Range)\n{data['symbol']} {data['side']}",
            chat_id=chat_id
        )

        return jsonify({"status": "blocked"})

    # -------- EXECUTION --------
    trade = driver.execute_trade(data)

    if trade:
        trade["chat_id"] = chat_id
        tm.track_trade(trade)

        tg.send_message(
            f"📈 {trade['symbol']} {trade['side']}\n"
            f"Entry: {trade['entry']:.5f}\n"
            f"SL: {trade['sl']:.5f}",
            chat_id=chat_id
        )

        return jsonify({"status": "executed"})

    return jsonify({"status": "failed"})


# ---------------- MAIN ----------------
if __name__ == "__main__":
    print("[LITE] Starting...")
    app.run(host="0.0.0.0", port=9000)