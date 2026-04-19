import random
import time


class SimDriver:

    def __init__(self, config):

        self.config = config
        self.connected = True

        self.price = 1.0800
        self.spread = 0.0002

        self.trade = None
        self.balance = 1000

    # --------------------------------------------------
    def get_balance(self):
        return self.balance

    # --------------------------------------------------
    def get_price(self, symbol):

        # simulate movement
        move = random.uniform(-0.0003, 0.0003)
        self.price += move

        return {
            "bid": round(self.price, 5),
            "ask": round(self.price + self.spread, 5)
        }

    # --------------------------------------------------
    def execute_trade(self, signal):

        side = signal["side"]
        price = self.get_price(signal["symbol"])

        entry = price["ask"] if side == "BUY" else price["bid"]

        sl = signal.get("sl", entry - 0.002 if side == "BUY" else entry + 0.002)

        self.trade = {
            "symbol": signal["symbol"],
            "side": side,
            "entry": entry,
            "sl": sl
        }

        print(f"[SIM] Trade opened → {side} @ {entry} SL {sl}")

        return {
            "symbol": signal["symbol"],
            "side": side,
            "entry": entry
        }

    # --------------------------------------------------
    def modify_sl(self, new_sl):

        if self.trade:
            self.trade["sl"] = new_sl
            print(f"[SIM] SL updated → {new_sl}")
            return True

        return False

    # --------------------------------------------------
    def close_partial(self, ratio):

        print(f"[SIM] Partial close {ratio * 100}%")
        return True