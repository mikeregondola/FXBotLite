from forexconnect import ForexConnect


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

    # ----------------------------
    # GET PRICE
    # ----------------------------
    def get_price(self, symbol):

        offers = self.fx.get_table(ForexConnect.OFFERS)

        for offer in offers:
            if offer.instrument == symbol:
                mid = (offer.bid + offer.ask) / 2
                return {"mid": mid}

        return {"mid": 0}

    # ----------------------------
    # GET OFFER ID
    # ----------------------------
    def get_offer_id(self, symbol):

        offers = self.fx.get_table(ForexConnect.OFFERS)

        for offer in offers:
            if offer.instrument == symbol:
                return offer.offer_id

        return None

    # ----------------------------
    # EXECUTE TRADE
    # ----------------------------
    def execute_trade(self, data):

        try:
            symbol = data["symbol"]
            side = data["side"]
            sl = float(data["sl"])

            offer_id = self.get_offer_id(symbol)

            account = self.fx.login_rules.trading_settings_provider.get_account_ids()[0]

            amount = 1000  # default micro lot

            request = self.fx.create_order_request(
                order_type="OM",
                ACCOUNT_ID=account,
                OFFER_ID=offer_id,
                BUY_SELL="B" if side == "BUY" else "S",
                AMOUNT=amount
            )

            self.fx.send_request(request)

            # get latest trade
            trades = self.fx.get_table(ForexConnect.TRADES)
            trade_id = trades[-1].trade_id

            entry_price = trades[-1].open_rate

            trade = {
                "symbol": symbol,
                "side": side,
                "entry": entry_price,
                "sl": sl,
                "trade_id": trade_id,
                "amount": amount
            }

            print(f"[FXCM] Trade executed {symbol} {side}")

            return trade

        except Exception as e:
            print("[FXCM ERROR] execute_trade:", e)
            return None

    # ----------------------------
    # MODIFY SL
    # ----------------------------
    def modify_sl(self, trade, new_sl):

        try:
            request = self.fx.create_order_request(
                order_type="STOP",
                TRADE_ID=trade["trade_id"],
                RATE=new_sl
            )

            self.fx.send_request(request)

        except Exception as e:
            print("[FXCM ERROR] modify_sl:", e)

    # ----------------------------
    # PARTIAL CLOSE
    # ----------------------------
    def partial_close(self, trade, ratio):

        try:
            amount = int(trade["amount"] * ratio)

            request = self.fx.create_order_request(
                order_type="CM",
                TRADE_ID=trade["trade_id"],
                AMOUNT=amount
            )

            self.fx.send_request(request)

        except Exception as e:
            print("[FXCM ERROR] partial_close:", e)

    # ----------------------------
    # CLOSE TRADE
    # ----------------------------
    def close_trade(self, trade):

        try:
            request = self.fx.create_order_request(
                order_type="CM",
                TRADE_ID=trade["trade_id"],
                AMOUNT=trade["amount"]
            )

            self.fx.send_request(request)

            print(f"[FXCM] Trade closed {trade['symbol']}")

        except Exception as e:
            print("[FXCM CLOSE ERROR]", e)

    # ----------------------------
    # GET PROFIT (REAL)
    # ----------------------------
    def get_profit(self, trade):

        try:
            # open trades
            trades = self.fx.get_table(ForexConnect.TRADES)

            for t in trades:
                if t.trade_id == trade.get("trade_id"):
                    return float(t.pl)

            # closed trades
            closed = self.fx.get_table(ForexConnect.CLOSED_TRADES)

            for c in closed:
                if c.trade_id == trade.get("trade_id"):
                    return float(c.pl)

        except Exception as e:
            print("[FXCM ERROR] get_profit:", e)

        return 0