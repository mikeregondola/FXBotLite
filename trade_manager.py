import time
from datetime import datetime, timezone

from trade_logger import TradeLogger
from strategy_engine import StrategyEngine


class TradeManager:

    def __init__(self, driver, telegram=None, config=None):
        self.driver = driver
        self.telegram = telegram
        self.config = config

        self.trades = []
        self.logger = TradeLogger()
        self.engine = StrategyEngine(config)

        self.BE_BUFFER_PIPS = config["strategy"]["be_buffer_pips"]
        self.PARTIAL_CLOSE_RATIO = config["strategy"]["partial_close_ratio"]

    # ----------------------------
    # SESSION CHECK
    # ----------------------------
    def is_session_open(self):

        if not self.config.get("session", {}).get("enabled", False):
            return True

        now = datetime.now(timezone.utc)
        hour = now.hour

        start = self.config["session"]["start_hour_utc"]
        end = self.config["session"]["end_hour_utc"]

        return start <= hour < end

    # ----------------------------
    # CLOSE ALL TRADES
    # ----------------------------
    def close_all_trades(self):

        print("[SESSION] Closing all trades...")

        for trade in list(self.trades):
            try:
                self.driver.close_trade(trade)

                if self.telegram:
                    self.telegram.send_message(
                        f"🔚 Session Close\n{trade['symbol']} {trade['side']} closed",
                        chat_id=trade.get("chat_id")
                    )

                self.trades.remove(trade)

            except Exception as e:
                print("[SESSION CLOSE ERROR]", e)

    # ----------------------------
    # TRACK NEW TRADE
    # ----------------------------
    def track_trade(self, trade):

        trade = self.engine.init_trade(trade)
        trade["open_time"] = datetime.now()

        self.trades.append(trade)

        print(f"[TM] Trade tracked: {trade['symbol']}")

    # ----------------------------
    # CHECK IF TRADE STILL OPEN
    # ----------------------------
    def is_trade_open(self, trade):

        try:
            trades = self.driver.fx.get_table(self.driver.fx.TRADES)
            return any(t.trade_id == trade.get("trade_id") for t in trades)
        except:
            return False

    # ----------------------------
    # MONITOR LOOP
    # ----------------------------
    def monitor(self):

        while True:

            # -------- SESSION CLOSE --------
            if not self.is_session_open():

                if len(self.trades) > 0:
                    self.close_all_trades()

                time.sleep(60)
                continue

            for trade in list(self.trades):

                try:
                    # -------- CLOSED --------
                    if not self.is_trade_open(trade):

                        price = self.driver.get_price(trade["symbol"])["mid"]

                        pips = self.engine.calculate_pips(
                            trade["entry"],
                            price,
                            trade["side"]
                        )

                        profit = self.driver.get_profit(trade)

                        self.logger.log_trade(trade, price, pips, profit)

                        if self.telegram:
                            self.telegram.send_message(
                                f"❌ Trade Closed\n"
                                f"{trade['symbol']} {trade['side']}\n"
                                f"Pips: {pips:.1f} | Profit: {profit:.2f}",
                                chat_id=trade.get("chat_id")
                            )

                        self.trades.remove(trade)
                        continue

                    # -------- LIVE --------
                    price = self.driver.get_price(trade["symbol"])["mid"]

                    result = self.engine.process_tick(trade, price)

                    if result["action"] == "BE":
                        self.driver.modify_sl(trade, result["new_sl"])
                        trade["sl"] = result["new_sl"]
                        print("[TM] BE triggered")

                    if result["action"] == "PARTIAL":
                        self.driver.partial_close(trade, self.PARTIAL_CLOSE_RATIO)
                        print("[TM] Partial executed")

                except Exception as e:
                    print("[TM ERROR]", e)

            time.sleep(2)