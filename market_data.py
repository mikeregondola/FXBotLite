from forexconnect import ForexConnect
import pandas as pd
from datetime import datetime, timedelta

def get_atr(symbol="EUR/USD", timeframe="m5", period=14):

    with ForexConnect() as fx:

        fx.login(
            user_id="701902895",
            password="djwK9",
            url="http://www.fxcorporate.com/Hosts.jsp",
            connection="Demo"
        )

        date_to = datetime.utcnow()
        date_from = date_to - timedelta(minutes=period * 10)

        history = fx.get_history(symbol, timeframe, date_from, date_to)

        df = pd.DataFrame(history)

        # 🔥 FIX: correct column names
        df['tr'] = df['BidHigh'] - df['BidLow']

        atr = df['tr'].rolling(window=period).mean().iloc[-1]

        return round(atr * 10000, 1)