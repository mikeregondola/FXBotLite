import csv
import os
from datetime import datetime


class TradeLogger:

    def __init__(self, filename="trade_log.csv"):
        self.filename = filename

        if not os.path.exists(self.filename):
            with open(self.filename, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp",
                    "symbol",
                    "side",
                    "entry",
                    "exit",
                    "pips",
                    "profit",       # REAL MONEY
                    "duration_sec",
                    "status"
                ])

    def log_trade(self, trade, exit_price, pips, profit):

        duration = 0
        if "open_time" in trade:
            duration = (datetime.now() - trade["open_time"]).total_seconds()

        with open(self.filename, "a", newline="") as f:
            writer = csv.writer(f)

            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                trade["symbol"],
                trade["side"],
                f"{trade['entry']:.5f}",
                f"{exit_price:.5f}",
                f"{pips:.1f}",
                f"{profit:.2f},",   # real $
                int(duration),
                "CLOSED"
            ])

