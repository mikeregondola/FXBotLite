import time


class TradeManager:

    def __init__(self, driver, telegram=None):
        self.driver = driver
        self.telegram = telegram
        self.trades = []

        # --- CONFIG ---
        self.BE_RATIO = 0.5
        self.BE_BUFFER_PIPS = 2

        # Structure config
        self.FRACTAL_WINDOW = 3      # true swing detection
        self.HTF_WINDOW = 10         # higher timeframe approximation

    # --------------------------------------------------
    def track_trade(self, trade):

        trade["be_done"] = False

        trade["initial_sl_pips"] = abs(
            (trade["entry"] - trade["sl"]) * 10000
        )

        trade["price_history"] = []
        trade["last_structure_sl"] = trade["sl"]

        self.trades.append(trade)

        print("[TM] New trade tracked")

    # --------------------------------------------------
    def calculate_pips(self, entry, price, side):

        if side == "BUY":
            return (price - entry) * 10000
        else:
            return (entry - price) * 10000

    # --------------------------------------------------
    def is_trade_open(self, trade):

        try:
            trades = self.driver.fx.get_table(self.driver.fx.TRADES)

            for t in trades:
                if t.trade_id == trade.get("trade_id"):
                    return True

        except Exception as e:
            print(f"[TM ERROR] Trade check failed: {e}")

        return False

    # --------------------------------------------------
    def update_sl(self, trade, new_sl):

        try:
            price_data = self.driver.get_price(trade["symbol"])
            if not price_data:
                return

            price = price_data["mid"]
            MIN_DISTANCE = 5 / 10000

            if trade["side"] == "BUY":
                if new_sl >= price - MIN_DISTANCE:
                    return
                if new_sl <= trade["sl"]:
                    return
            else:
                if new_sl <= price + MIN_DISTANCE:
                    return
                if new_sl >= trade["sl"]:
                    return

            self.driver.modify_sl(trade, new_sl)
            trade["sl"] = new_sl

            print(f"[TM] SL updated → {new_sl}")

            if self.telegram:
                self.telegram.send_message(
                    f"🔄 SL Updated\n{trade['symbol']}\nNew SL: {new_sl:.5f}",
                    chat_id=trade.get("chat_id")
                )

        except Exception as e:
            print(f"[TM ERROR] SL update failed: {e}")

    # --------------------------------------------------
    # FRACTAL DETECTION
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
    # HIGHER STRUCTURE (HTF)
    # --------------------------------------------------
    def get_htf_low(self, history):
        if len(history) < self.HTF_WINDOW:
            return None
        return min(history[-self.HTF_WINDOW:])

    def get_htf_high(self, history):
        if len(history) < self.HTF_WINDOW:
            return None
        return max(history[-self.HTF_WINDOW:])

    # --------------------------------------------------
    def monitor(self):

        while True:

            for trade in list(self.trades):

                try:
                    # CLOSE DETECTION
                    if not self.is_trade_open(trade):

                        price_data = self.driver.get_price(trade["symbol"])
                        exit_price = price_data["mid"] if price_data else trade["entry"]

                        pips = self.calculate_pips(
                            trade["entry"],
                            exit_price,
                            trade["side"]
                        )

                        profit = self.driver.get_profit(trade)

                        if self.telegram:
                            self.telegram.send_message(
                                f"❌ Trade Closed\n"
                                f"{trade['symbol']} {trade['side']}\n"
                                f"Entry: {trade['entry']:.5f}\n"
                                f"Exit: {exit_price:.5f}\n"
                                f"Pips: {pips:.1f}\n"
                                f"Profit: {profit:.2f}",
                                chat_id=trade.get("chat_id")
                            )

                        self.trades.remove(trade)
                        continue

                    # PRICE
                    price_data = self.driver.get_price(trade["symbol"])
                    if not price_data:
                        continue

                    price = price_data["mid"]
                    trade["price_history"].append(price)

                    if len(trade["price_history"]) > 100:
                        trade["price_history"].pop(0)

                    pips = self.calculate_pips(
                        trade["entry"],
                        price,
                        trade["side"]
                    )

                    # ================= BE =================
                    if not trade["be_done"]:

                        be_trigger = trade["initial_sl_pips"] * self.BE_RATIO

                        if pips >= be_trigger:

                            buffer = self.BE_BUFFER_PIPS / 10000

                            if trade["side"] == "BUY":
                                new_sl = trade["entry"] + buffer
                            else:
                                new_sl = trade["entry"] - buffer

                            self.update_sl(trade, new_sl)
                            trade["be_done"] = True

                    # ================= STRUCTURE TRAILING =================
                    else:

                        if trade["side"] == "BUY":

                            fractal_low = self.get_fractal_low(trade["price_history"])
                            htf_low = self.get_htf_low(trade["price_history"])

                            new_sl = fractal_low or htf_low

                            if new_sl and new_sl > trade["last_structure_sl"]:
                                self.update_sl(trade, new_sl)
                                trade["last_structure_sl"] = new_sl

                        else:

                            fractal_high = self.get_fractal_high(trade["price_history"])
                            htf_high = self.get_htf_high(trade["price_history"])

                            new_sl = fractal_high or htf_high

                            if new_sl and new_sl < trade["last_structure_sl"]:
                                self.update_sl(trade, new_sl)
                                trade["last_structure_sl"] = new_sl

                except Exception as e:
                    print(f"[TM ERROR] {e}")

            time.sleep(2)

