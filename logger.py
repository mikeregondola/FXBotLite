import os
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "trades.log")

os.makedirs(LOG_DIR, exist_ok=True)

def log_trade(trade_id, action, symbol="", price=0, pnl=0):

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    line = f"{ts} | {trade_id} | {action} | {symbol} | {price} | {pnl}\n"

    with open(LOG_FILE, "a") as f:
        f.write(line)