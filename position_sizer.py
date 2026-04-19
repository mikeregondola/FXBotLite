def compute_lot_size(capital, risk_percent, sl_pips, pip_value_per_lot=10):
    """
    capital: account balance
    risk_percent: % risk per trade (e.g. 1.0)
    sl_pips: stop loss in pips
    pip_value_per_lot: EURUSD ≈ $10 per lot per pip
    """

    if capital <= 0 or sl_pips <= 0:
        return 0.0

    risk_amount = capital * (risk_percent / 100.0)

    lot_size = risk_amount / (sl_pips * pip_value_per_lot)

    return round(lot_size, 2)