import random
import pandas as pd


# ----------------------------
# GENERATE PRICE SERIES
# ----------------------------
def generate_price_series(length=200):

    price = 1.1000
    prices = []

    trend = random.choice(["UP", "DOWN", "RANGE"])

    for _ in range(length):

        if trend == "UP":
            move = random.uniform(0, 0.0005)
        elif trend == "DOWN":
            move = random.uniform(-0.0005, 0)
        else:
            move = random.uniform(-0.0002, 0.0002)

        price += move
        prices.append(price)

    return prices


# ----------------------------
# TREND FILTER (SIMULATED)
# ----------------------------
def is_trending(prices, threshold=0.1):

    higher = 0
    lower = 0

    for i in range(1, len(prices)):
        if prices[i] > prices[i - 1]:
            higher += 1
        elif prices[i] < prices[i - 1]:
            lower += 1

    total = higher + lower

    if total == 0:
        return False

    strength = abs(higher - lower) / total

    return strength > threshold


# ----------------------------
# SIMULATE ONE TRADE
# ----------------------------
def simulate_trade(config):

    prices = generate_price_series()

    # 🔥 APPLY TREND FILTER
    if not is_trending(prices):
        return 0  # skip trade

    entry = prices[0]
    side = random.choice(["BUY", "SELL"])

    sl_pips = random.choice([15, 20, 25])
    initial_sl_pips = sl_pips

    if side == "BUY":
        sl = entry - sl_pips / 10000
    else:
        sl = entry + sl_pips / 10000

    be_done = False
    partial_done = False

    be_ratio = config["be_ratio"]
    partial_trigger = config["partial"]

    profit = 0

    for price in prices:

        # PIPS
        if side == "BUY":
            pips = (price - entry) * 10000
        else:
            pips = (entry - price) * 10000

        # STOP LOSS
        if (side == "BUY" and price <= sl) or (side == "SELL" and price >= sl):
            return profit - initial_sl_pips

        # BREAK EVEN
        if not be_done and pips >= initial_sl_pips * be_ratio:
            sl = entry
            be_done = True

        # PARTIAL
        if not partial_done and pips >= partial_trigger:
            profit += partial_trigger * 0.5
            partial_done = True

        # TAKE PROFIT
        if pips >= 40:
            return profit + 40

    return profit


# ----------------------------
# TEST CONFIG (WITH EQUITY)
# ----------------------------
def test_config(config, runs=100):

    results = []

    equity = 0
    equity_curve = []
    peak = 0
    drawdowns = []

    trade_count = 0

    for _ in range(runs):

        trade_result = simulate_trade(config)

        # skip non-trades
        if trade_result == 0:
            continue

        trade_count += 1
        results.append(trade_result)

        equity += trade_result
        equity_curve.append(equity)

        peak = max(peak, equity)
        drawdown = equity - peak
        drawdowns.append(drawdown)

    if trade_count == 0:
        return {
            "total_pips": 0,
            "win_rate": 0,
            "profit_factor": 0,
            "expectancy": 0,
            "max_drawdown": 0,
            "trades": 0
        }

    df = pd.DataFrame(results, columns=["pips"])

    total = df["pips"].sum()
    wins = len(df[df["pips"] > 0])
    losses = len(df[df["pips"] <= 0])

    win_rate = (wins / trade_count) * 100

    avg_win = df[df["pips"] > 0]["pips"].mean() if wins > 0 else 0
    avg_loss = df[df["pips"] <= 0]["pips"].mean() if losses > 0 else 0

    profit_sum = df[df["pips"] > 0]["pips"].sum()
    loss_sum = df[df["pips"] <= 0]["pips"].sum()

    profit_factor = abs(profit_sum / loss_sum) if loss_sum != 0 else 0

    expectancy = (win_rate / 100 * avg_win) + ((1 - win_rate / 100) * avg_loss)

    max_drawdown = min(drawdowns) if drawdowns else 0

    return {
        "total_pips": round(total, 2),
        "win_rate": round(win_rate, 2),
        "profit_factor": round(profit_factor, 2),
        "expectancy": round(expectancy, 2),
        "max_drawdown": round(max_drawdown, 2),
        "trades": trade_count
    }


# ----------------------------
# OPTIMIZATION LOOP
# ----------------------------
def optimize():

    configs = []

    for be in [0.4, 0.5, 0.6, 0.7]:
        for partial in [10, 15, 20, 25]:

            config = {
                "be_ratio": be,
                "partial": partial
            }

            result = test_config(config)

            configs.append({
                "be_ratio": be,
                "partial": partial,
                **result
            })

    # Risk-adjusted sorting
    configs.sort(
        key=lambda x: (x["total_pips"] + x["max_drawdown"]),
        reverse=True
    )

    return configs


# ----------------------------
# RUN
# ----------------------------
if __name__ == "__main__":

    results = optimize()

    print("\n=== TOP CONFIGS (WITH TREND FILTER) ===\n")

    for r in results[:10]:
        print(r)