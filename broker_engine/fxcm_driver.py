from forexconnect import ForexConnect
import time


class FXCMDriver:

    def __init__(self, config):
        self.config = config
        self.fx = ForexConnect()
        self.connected = False
        self.connect()

    # ----------------------------
    # CONNECT
    # ----------------------------
    def connect(self):
        try:
            print("🔥 CONFIG USED:", self.config)

            self.fx.login(
                self.config["username"],
                self.config["password"],
                self.config["url"],
                self.config["connection"]
            )

            self.connected = True
            print("[FXCM] Connected")

        except Exception as e:
            print("[FXCM ERROR] Connection failed:", e)

    # ----------------------------
    # GET PRICE
    # ----------------------------
    def get_price(self, symbol):
        try:
            offers = self.fx.get_table(self.fx.OFFERS)
            target = symbol.replace("/", "").upper()

            for i in range(offers.size):
                row = offers.get_row(i)

                inst = str(row.get_cell(1)).replace("/", "").upper()
                if inst == target:
                    bid = float(row.get_cell(3))
                    ask = float(row.get_cell(4))
                    return {"mid": (bid + ask) / 2}

        except Exception as e:
            print("[FXCM ERROR] get_price:", e)

        return None

    # ----------------------------
    # FIND OFFER ID
    # ----------------------------
    def _find_offer_id(self, symbol):
        try:
            offers = self.fx.get_table(self.fx.OFFERS)
            target = symbol.replace("/", "").upper()

            for i in range(offers.size):
                row = offers.get_row(i)

                inst = str(row.get_cell(1)).replace("/", "").upper()

                if inst == target:
                    offer_id = row.get_cell(0)
                    print(f"[FXCM DEBUG] OfferID detected: {offer_id}")
                    return offer_id

            return None

        except Exception as e:
            print("[FXCM ERROR] _find_offer_id:", e)
            return None

    # ----------------------------
    # EXECUTE TRADE (FINAL VERSION)
    # ----------------------------
    def execute_trade(self, data):
        try:
            symbol = data["symbol"]
            side = data["side"]
            amount = 1000
            sl = data.get("sl")

            target = symbol.replace("/", "").upper()

            # --- ACCOUNT ---
            accounts = self.fx.get_table(self.fx.ACCOUNTS)
            account_id = accounts.get_row(0).get_cell(0)

            # --- OFFER ---
            offer_id = self._find_offer_id(symbol)

            if not offer_id:
                print("[FXCM ERROR] OfferID not found")
                return False

            # --- VALIDATE SL BEFORE SENDING ---
            if sl:
                price_data = self.get_price(symbol)

                if price_data:
                    price = price_data["mid"]
                    MIN_DISTANCE = 0.0010  # ~10 pips safe

                    if side == "BUY":
                        if sl >= price:
                            sl = price - MIN_DISTANCE
                        elif price - sl < MIN_DISTANCE:
                            sl = price - MIN_DISTANCE

                    else:  # SELL
                        if sl <= price:
                            sl = price + MIN_DISTANCE
                        elif sl - price < MIN_DISTANCE:
                            sl = price + MIN_DISTANCE

                    print(f"[FXCM DEBUG] Final SL → {sl}")

            # --- EXECUTE WITH SL ATTACHED ---
            request = self.fx.create_order_request(
                order_type="OM",
                ACCOUNT_ID=account_id,
                OFFER_ID=offer_id,
                BUY_SELL="B" if side == "BUY" else "S",
                AMOUNT=amount,
                RATE_STOP=sl  # 🔥 FINAL FIX
            )

            self.fx.send_request_async(request)

            print(f"[FXCM] Trade executed: {symbol} {side}")
            print(f"[FXCM] SL attached → {sl}")

            return True

        except Exception as e:
            print("[FXCM ERROR] execute_trade:", e)
            return False

    # ----------------------------
    # GET PROFIT
    # ----------------------------
    def get_profit(self, trade):
        try:
            trades = self.fx.get_table(self.fx.TRADES)
            target = trade["symbol"].replace("/", "").upper()

            for i in range(trades.size):
                t = trades.get_row(i)

                inst = str(t.get_cell(27)).replace("/", "").upper()

                if inst == target:
                    return float(t.get_cell(21))

            return 0.0

        except Exception as e:
            print("[FXCM ERROR] get_profit:", e)
            return 0.0