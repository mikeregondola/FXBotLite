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
            self.connected = False

    # ----------------------------
    # ACCOUNT INFO
    # ----------------------------
    def get_account_info(self):
        try:
            table = self.fx.get_table(self.fx.ACCOUNTS)

            if table.size == 0:
                return None

            acc = table.get_row(0)

            info = {
                "balance": float(acc.balance),
                "equity": float(acc.equity),
                "usable_margin": 0.0,
                "used_margin": 0.0
            }

            print("[FXCM DEBUG] Account info:", info)
            return info

        except Exception as e:
            print("[FXCM ERROR] get_account_info failed:", e)
            return None

    # ----------------------------
    # PRICE
    # ----------------------------
    def get_price(self, symbol):
        try:
            offers = self.fx.get_table(self.fx.OFFERS)
            target = symbol.replace("/", "").upper()

            for i in range(offers.size):
                row = offers.get_row(i)
                inst = row.instrument.replace("/", "").upper()

                if inst == target:
                    mid = (row.bid + row.ask) / 2
                    return {"mid": mid}

            return None

        except Exception as e:
            print("[FXCM ERROR] get_price failed:", e)
            return None

    # ----------------------------
    # EXECUTE TRADE (NO SL HERE)
    # ----------------------------
    def execute_trade(self, data):
        try:
            symbol = data["symbol"]
            side = data["side"]
            amount = 1000

            # ---------- ACCOUNT ----------
            accounts = self.fx.get_table(self.fx.ACCOUNTS)

            if accounts.size == 0:
                print("[FXCM ERROR] No account rows")
                return False

            acc = accounts.get_row(0)

            account_id = None
            for i in range(len(accounts.columns)):
                val = acc.get_cell(i)
                if isinstance(val, str) and len(val) > 5:
                    account_id = val
                    break

            if not account_id:
                print("[FXCM ERROR] Could not detect AccountID")
                return False

            print("[FXCM DEBUG] Using AccountID:", account_id)

            # ---------- OFFER ----------
            offers = self.fx.get_table(self.fx.OFFERS)
            target = symbol.replace("/", "").upper()

            offer = None
            for i in range(offers.size):
                row = offers.get_row(i)
                inst = row.instrument.replace("/", "").upper()

                if inst == target:
                    offer = row
                    break

            if offer is None:
                print(f"[FXCM ERROR] No offer for {symbol}")
                return False

            offer_id = None
            for i in range(len(offers.columns)):
                val = offer.get_cell(i)
                if isinstance(val, str) and val.isdigit():
                    offer_id = val
                    break

            if not offer_id:
                print("[FXCM ERROR] Could not detect OfferID")
                return False

            print("[FXCM DEBUG] Using OfferID:", offer_id)

            # ---------- EXECUTE ----------
            request = self.fx.create_order_request(
                order_type="OM",
                ACCOUNT_ID=account_id,
                OFFER_ID=offer_id,
                BUY_SELL="B" if side == "BUY" else "S",
                AMOUNT=amount
            )

            self.fx.send_request(request)
            print(f"[FXCM] Trade executed: {symbol} {side}")

            return True

        except Exception as e:
            print("[FXCM ERROR] execute_trade failed:", e)
            return False

    # ----------------------------
    # MODIFY SL (USED BY TradeManager)
    # ----------------------------
    def modify_sl(self, trade, new_sl):
        try:
            trades = self.fx.get_table(self.fx.TRADES)

            if trades.size == 0:
                print("[FXCM ERROR] No trades found")
                return False

            target_trade = None
            target_symbol = trade["symbol"].replace("/", "").upper()

            for i in range(trades.size):
                t = trades.get_row(i)
                inst = t.instrument.replace("/", "").upper()

                if inst == target_symbol:
                    target_trade = t
                    break

            if target_trade is None:
                print("[FXCM ERROR] Trade not found for SL update")
                return False

            # detect trade ID via index
            trade_id = None
            for i in range(len(trades.columns)):
                val = target_trade.get_cell(i)
                if isinstance(val, str) and val.isdigit():
                    trade_id = val
                    break

            if not trade_id:
                print("[FXCM ERROR] Could not detect TradeID")
                return False

            # 🔥 CORRECT METHOD (based on your working system)
            request = self.fx.create_order_request(
                order_type="EDIT",
                TRADE_ID=trade_id,
                RATE_STOP=new_sl
            )

            self.fx.send_request(request)

            print(f"[FXCM] SL modified → {new_sl}")
            return True

        except Exception as e:
            print("[FXCM ERROR] modify_sl failed:", e)
            return False

    # ----------------------------
    # OPEN POSITIONS
    # ----------------------------
    def get_open_positions(self):
        try:
            trades = self.fx.get_table(self.fx.TRADES)
            positions = []

            for i in range(trades.size):
                t = trades.get_row(i)

                positions.append({
                    "tradeId": t.get_cell(0),
                    "symbol": t.instrument,
                    "side": "BUY" if t.buySell == "B" else "SELL",
                    "amount": t.amount,
                    "open": t.open
                })

            return positions

        except Exception as e:
            print("[FXCM ERROR] get_open_positions failed:", e)
            return []

    # ----------------------------
    # CLOSE TRADE
    # ----------------------------
    def close_trade(self, trade_id):
        try:
            trades = self.fx.get_table(self.fx.TRADES)

            for i in range(trades.size):
                t = trades.get_row(i)

                tid = t.get_cell(0)

                if tid == trade_id:
                    request = self.fx.create_order_request(
                        order_type="CM",
                        ACCOUNT_ID=t.get_cell(0),
                        OFFER_ID=t.get_cell(1),
                        BUY_SELL="S" if t.buySell == "B" else "B",
                        AMOUNT=t.amount,
                        TRADE_ID=trade_id
                    )

                    self.fx.send_request(request)
                    print(f"[FXCM] Trade closed: {trade_id}")
                    return True

            return False

        except Exception as e:
            print("[FXCM ERROR] close_trade failed:", e)
            return False

    # ----------------------------
    # CLOSE ALL
    # ----------------------------
    def close_all(self):
        try:
            trades = self.get_open_positions()
            count = 0

            for t in trades:
                if self.close_trade(t["tradeId"]):
                    count += 1

            return count

        except Exception as e:
            print("[FXCM ERROR] close_all failed:", e)
            return 0