import time
from datetime import datetime


class TradeManager:

    def __init__(self, driver, telegram=None):
        self.driver = driver
        self.telegram = telegram
        self.trades = []

        # --- CONFIG ---
        self.BE_RATIO = 0.5
        self.BE_BUFFER_PIPS = 2

        self.FRACTAL_WINDOW = 3
        self.HTF_WINDOW = 10

        # --- PARTIAL CLOSE ---
        self.PARTIAL_TRIGGER_PIPS = 15
        self.PARTIAL_CLOSE_RATIO = 0.5

        # --- EQUITY PROTECTION ---
        self.daily_start_balance = None
        self.daily_loss_limit_pct = 5
        self.trading_enabled = True
        self.current_day = datetime.now().date()

    # --------------------------------------------------
    def track_trade(self, trade):

        trade["be_done"] = False
        trade["partial_done"] = False

        trade["initial_sl_pips"] = abs(
            (trade["entry"] - trade["sl"]) * 10000
        )

        trade["price_history"] = []
        trade["last_structure_sl"] = trade["sl"]

        self.trades.append(trade)

    # --------------------------------------------------
    def calculate_pips(self, entry, price, side):

        if side == "BUY":
            return (price - entry) * 10000
        else:
            return (entry - price) * 10000

    # --------------------------------------------------
    def is_trade_open(self, trade):

        trades = self.driver.fx.get_table(self.driver.fx.TRADES)

        for t in trades:
            if t.trade_id == trade.get("trade_id"):
                return True

        return False

    # --------------------------------------------------
    def check_equity_protection(self):

        balance = self.driver.get_balance()

        today = datetime.now().date()

        if self.current_day != today:
            self.current_day = today
            self.daily_start_balance = balance
            self.trading_enabled = True

        if self.daily_start_balance is None:
            self.daily_start_balance = balance

        loss_pct = ((self.daily_start_balance - balance) / self.daily_start_balance) * 100

        if loss_pct >= self.daily_loss_limit_pct:
            self.trading_enabled = False

            if self.telegram:
                self.telegram.send_message(
                    f"🛑 Daily Stop Hit\nLoss: {loss_pct:.2f}%",
                    chat_id=None
                )

    # --------------------------------------------------
    def get_fractal_low(self, history):
        if len(history) < 5:
            return None
        mid = history[-3]
        if mid < history[-4] and mid < history[-2]:
            return mid
        return None

    def get_fractal_high(self, history):
        if len(history) < 5:
            return None
        mid = history[-3]
        if mid > history[-4] and mid > history[-2]:
            return mid
        return None

    # --------------------------------------------------
    def monitor(self):

        while True:

            self.check_equity_protection()

            for trade in list(self.trades):

                try:
                    if not self.is_trade_open(trade):
                        self.trades.remove(trade)
                        continue

                    price = self.driver.get_price(trade["symbol"])["mid"]

                    trade["price_history"].append(price)

                    if len(trade["price_history"]) > 100:
                        trade["price_history"].pop(0)

                    pips = self.calculate_pips(
                        trade["entry"],
                        price,
                        trade["side"]
                    )

                    # ---------------- PARTIAL CLOSE ----------------
                    if not trade["partial_done"] and pips >= self.PARTIAL_TRIGGER_PIPS:

                        try:
                            self.driver.partial_close(
                                trade,
                                self.PARTIAL_CLOSE_RATIO
                            )

                            trade["partial_done"] = True

                            if self.telegram:
                                self.telegram.send_message(
                                    f"💰 Partial Close\n{trade['symbol']}\nLocked profit",
                                    chat_id=trade.get("chat_id")
                                )

                        except Exception as e:
                            print("[TM] Partial close failed:", e)

                    # ---------------- BE ----------------
                    if not trade["be_done"]:

                        if pips >= trade["initial_sl_pips"] * self.BE_RATIO:

                            buffer = self.BE_BUFFER_PIPS / 10000

                            if trade["side"] == "BUY":
                                new_sl = trade["entry"] + buffer
                            else:
                                new_sl = trade["entry"] - buffer

                            self.driver.modify_sl(trade, new_sl)
                            trade["be_done"] = True

                    # ---------------- STRUCTURE TRAILING ----------------
                    else:

                        if trade["side"] == "BUY":

                            fractal_low = self.get_fractal_low(trade["price_history"])

                            if fractal_low and fractal_low > trade["last_structure_sl"]:
                                self.driver.modify_sl(trade, fractal_low)
                                trade["last_structure_sl"] = fractal_low

                        else:

                            fractal_high = self.get_fractal_high(trade["price_history"])

                            if fractal_high and fractal_high < trade["last_structure_sl"]:
                                self.driver.modify_sl(trade, fractal_high)
                                trade["last_structure_sl"] = fractal_high

                except Exception as e:
                    print("[TM ERROR]", e)

            time.sleep(2)