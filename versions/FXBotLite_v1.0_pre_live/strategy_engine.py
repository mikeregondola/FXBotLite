class StrategyEngine:

    def __init__(self, config):
        self.config = config

    # ----------------------------
    # CALCULATE PIPS
    # ----------------------------
    def calculate_pips(self, entry, price, side):
        if side == "BUY":
            return (price - entry) * 10000
        else:
            return (entry - price) * 10000

    # ----------------------------
    # INITIALIZE TRADE STATE
    # ----------------------------
    def init_trade(self, trade):

        symbol = trade["symbol"]

        pair_cfg = self.config["pair_config"].get(
            symbol,
            {"be_ratio": 0.5, "partial": 15}
        )

        trade["be_ratio"] = pair_cfg["be_ratio"]
        trade["partial_trigger"] = pair_cfg["partial"]

        trade["be_done"] = False
        trade["partial_done"] = False

        trade["initial_sl_pips"] = abs(
            (trade["entry"] - trade["sl"]) * 10000
        )

        return trade

    # ----------------------------
    # PROCESS TRADE STEP
    # ----------------------------
    def process_tick(self, trade, price):

        result = {
            "action": None,
            "new_sl": None,
            "partial": False
        }

        pips = self.calculate_pips(
            trade["entry"],
            price,
            trade["side"]
        )

        # ---------------- BE ----------------
        if not trade["be_done"]:

            if pips >= trade["initial_sl_pips"] * trade["be_ratio"]:

                buffer = self.config["strategy"]["be_buffer_pips"] / 10000

                if trade["side"] == "BUY":
                    new_sl = trade["entry"] + buffer
                else:
                    new_sl = trade["entry"] - buffer

                trade["be_done"] = True

                result["action"] = "BE"
                result["new_sl"] = new_sl

                return result

        # ---------------- PARTIAL ----------------
        if not trade["partial_done"]:

            if pips >= trade["partial_trigger"]:

                trade["partial_done"] = True

                result["action"] = "PARTIAL"
                result["partial"] = True

                return result

        return result