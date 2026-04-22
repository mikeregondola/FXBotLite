import time


class TradeManager:

    def __init__(self, driver, telegram=None):
        self.driver = driver
        self.telegram = telegram
        self.trades = []

        # --- CONFIG ---
        self.BE_RATIO = 0.5            # 50% of SL distance
        self.BE_BUFFER_PIPS = 2        # lock small profit
        self.TRAIL_TRIGGER_PIPS = 15
        self.TRAIL_DISTANCE_PIPS = 10

    # --------------------------------------------------
    # TRACK NEW TRADE
    # --------------------------------------------------
    def track_trade(self, trade):

        trade["be_done"] = False

        # 🔥 Store initial SL distance (for adaptive BE)
        trade["initial_sl_pips"] = abs(
            (trade["entry"] - trade["sl"]) * 10000
        )

        self.trades.append(trade)

        print("[TM] New trade tracked")

    # --------------------------------------------------
    # CALCULATE PIPS
    # --------------------------------------------------
    def calculate_pips(self, entry, price, side):

        if side == "BUY":
            return (price - entry) * 10000
        else:
            return (entry - price) * 10000

    # --------------------------------------------------
    # MODIFY SL
    # --------------------------------------------------
    def update_sl(self, trade, new_sl):

        if trade["side"] == "BUY" and new_sl <= trade["sl"]:
            return

        if trade["side"] == "SELL" and new_sl >= trade["sl"]:
            return

        try:
            self.driver.modify_sl(trade, new_sl)
            trade["sl"] = new_sl

            print(f"[TM] SL updated → {new_sl}")

            if self.telegram:
                self.telegram.send_message(
                    f"🔄 SL Updated\n{trade['symbol']}\nNew SL: {new_sl}"
                )

        except Exception as e:
            print(f"[TM ERROR] SL update failed: {e}")

    # --------------------------------------------------
    # MONITOR LOOP
    # --------------------------------------------------
    def monitor(self):

        while True:

            for trade in list(self.trades):

                try:
                    # 🔥 FIX: get mid price
                    price_data = self.driver.get_price(trade["symbol"])

                    if not price_data:
                        continue

                    price = price_data["mid"]

                    profit = self.driver.get_profit(trade)

                    pips = self.calculate_pips(
                        trade["entry"],
                        price,
                        trade["side"]
                    )

                    print(
                        f"[TM DEBUG] {trade['symbol']} | "
                        f"Pips: {pips:.1f} | Profit: {profit:.2f}"
                    )

                    # ================= BE =================
                    if not trade["be_done"]:

                        be_trigger = trade["initial_sl_pips"] * self.BE_RATIO

                        if pips >= 0.3:

                            buffer = self.BE_BUFFER_PIPS / 10000

                            if trade["side"] == "BUY":
                                new_sl = trade["entry"] + buffer
                            else:
                                new_sl = trade["entry"] - buffer

                            self.update_sl(trade, new_sl)

                            trade["be_done"] = True

                            print("[TM] Adaptive BE triggered")

                            if self.telegram:
                                self.telegram.send_message(
                                    f"🟢 Adaptive BE\n{trade['symbol']}\nSL moved to BE+"
                                )

                    # ================= TRAILING =================
                    elif trade["be_done"]:

                        if pips >= self.TRAIL_TRIGGER_PIPS:

                            if trade["side"] == "BUY":
                                new_sl = price - (self.TRAIL_DISTANCE_PIPS / 10000)
                            else:
                                new_sl = price + (self.TRAIL_DISTANCE_PIPS / 10000)

                            self.update_sl(trade, new_sl)

                            print("[TM] Trailing SL updated")

                except Exception as e:
                    print(f"[TM ERROR] {e}")

            time.sleep(2)

