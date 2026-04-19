from forexconnect import ForexConnect
import time


class FXCMDriver:

    def __init__(self, config):
        self.username = config.get("username")
        self.password = config.get("password")
        self.url = config.get("url")
        self.connection = config.get("connection", "Demo")

        self.fx = ForexConnect()
        self.connected = False
        self.account_id = None

        self._connect()

    # --------------------------------------------------
    # CONNECT
    # --------------------------------------------------
    def _connect(self):
        print("[FXCM] Connecting...")

        try:
            self.fx.login(
                self.username,
                self.password,
                self.url,
                self.connection
            )

            for _ in range(15):
                try:
                    accounts = self.fx.get_table(ForexConnect.ACCOUNTS)

                    if accounts and len(accounts) > 0:
                        self.connected = True

                        for acc in accounts:
                            self.account_id = acc.account_id
                            break

                        print(f"[FXCM] Connected | Account: {self.account_id}")
                        return

                except Exception:
                    pass

                time.sleep(1)

            print("[FXCM] Timeout waiting for tables")

        except Exception as e:
            print(f"[FXCM] Connection failed: {e}")

    # --------------------------------------------------
    # BALANCE
    # --------------------------------------------------
    def get_balance(self):
        try:
            accounts = self.fx.get_table(ForexConnect.ACCOUNTS)

            for acc in accounts:
                return float(acc.balance)

        except Exception as e:
            print(f"[FXCM] Balance error: {e}")

        return 0

    # --------------------------------------------------
    # PRICE
    # --------------------------------------------------
    def get_price(self, symbol):
        try:
            offers = self.fx.get_table(ForexConnect.OFFERS)

            formatted = symbol[:3] + "/" + symbol[3:]

            for offer in offers:
                if (
                    offer.instrument == formatted or
                    offer.instrument.replace("/", "") == symbol
                ):
                    bid = offer.bid
                    ask = offer.ask

                    return {
                        "bid": bid,
                        "ask": ask,
                        "mid": (bid + ask) / 2,
                        "offer_id": offer.offer_id
                    }

        except Exception as e:
            print(f"[FXCM] Price error: {e}")

        return {"bid": 0, "ask": 0, "mid": 0, "offer_id": None}

    # --------------------------------------------------
    # EXECUTE TRADE (FINAL STABLE)
    # --------------------------------------------------
    def execute_trade(self, signal):

        symbol = signal["symbol"]
        side = signal["side"]
        sl = signal.get("sl")

        price_data = self.get_price(symbol)

        if price_data["offer_id"] is None:
            print("[FXCM] Offer not found")
            return None

        entry = price_data["ask"] if side == "BUY" else price_data["bid"]

        balance = self.get_balance()

        risk_pct = self.full_config["risk"]["max_risk_per_trade_percent"]
        risk_amount = balance * (risk_pct / 100)

        pip = 0.0001
        sl_pips = abs(entry - sl) / pip

        if sl_pips == 0:
            print("[FXCM] Invalid SL distance")
            return None

        pip_value = 0.0001

        units = risk_amount / (sl_pips * pip_value)
        units = int(units)

        # enforce 1000 step
        units = (units // 1000) * 1000

        if units < 1000:
            units = 1000

        print(f"[FXCM] Balance: {balance}")
        print(f"[FXCM] Risk: {risk_amount}")
        print(f"[FXCM] SL pips: {sl_pips}")
        print(f"[FXCM] Units: {units}")

        try:
            request = self.fx.create_order_request(
                order_type="OM",
                ACCOUNT_ID=self.account_id,
                BUY_SELL="B" if side == "BUY" else "S",
                AMOUNT=str(units),
                OFFER_ID=price_data["offer_id"],

                RATE_STOP=sl  # 🔥 KEY FIX
            )

            self.fx.send_request(request)

            print(f"[FXCM] Order sent {symbol} {side}")

            # get trade_id
            trade_id = None

            for _ in range(10):
                trades = self.fx.get_table(ForexConnect.TRADES)

                for t in trades:
                    if t.offer_id == price_data["offer_id"]:
                        trade_id = t.trade_id
                        break

                if trade_id:
                    break

                time.sleep(0.5)

            if not trade_id:
                print("[FXCM] Trade not found")
                return None

            print(f"[FXCM] Trade ID: {trade_id}")

            return {
                "symbol": symbol,
                "side": side,
                "entry": entry,
                "units": units,
                "sl": sl,
                "trade_id": trade_id
            }

        except Exception as e:
            print(f"[FXCM] Order failed: {e}")
            return None

    # --------------------------------------------------
    # GET PROFIT
    # --------------------------------------------------
    def get_profit(self, trade):
        try:
            trades = self.fx.get_table(ForexConnect.TRADES)

            for t in trades:
                if t.trade_id == trade.get("trade_id"):
                    return float(t.pl)

        except Exception as e:
            print(f"[FXCM] Profit error: {e}")

        return 0

