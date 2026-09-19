"""Per-asset indicators and the composite 'meta sentiment' score (v1).
Components are deliberately simple and transparent; the scoreboard decides
whether they earn more weight later."""
import math
import numpy as np
import pandas as pd

WEIGHTS = {"momentum": 0.40, "trend": 0.30, "stretch": 0.15, "crowd": 0.15}
HORIZON_TRADING_DAYS = 20

def rsi(close, n=14):
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return 100 - 100 / (1 + rs)

def analyse(df, kind, fear_greed=None):
    """Return a dict of indicators, component scores and composite score."""
    c = df["Close"].dropna()
    if len(c) < 60:
        return None
    last = float(c.iloc[-1])
    ret = lambda n: float(c.iloc[-1] / c.iloc[-1 - n] - 1) if len(c) > n else None
    daily = c.pct_change().dropna()
    vol = float(daily.tail(60).std() * math.sqrt(252))
    ma50 = float(c.tail(50).mean())
    ma200 = float(c.tail(200).mean()) if len(c) >= 200 else None
    r14 = float(rsi(c).iloc[-1])
    r60 = ret(60)

    comp = {}
    exp_move = vol * math.sqrt(60 / 252) or 1e-9
    comp["momentum"] = math.tanh(r60 / exp_move) if r60 is not None else 0.0
    t = (1 if last > ma50 else -1) + ((1 if ma50 > ma200 else -1) if ma200 else 0)
    comp["trend"] = t / (2 if ma200 else 1)
    comp["stretch"] = max(-1.0, min(1.0, (50 - r14) / 50))   # overbought leans down
    if kind == "crypto" and fear_greed is not None:
        comp["crowd"] = (50 - fear_greed) / 50                 # greedy crowd leans down
    w = {k: WEIGHTS[k] for k in comp}
    tot = sum(w.values())
    score = 100 * sum(comp[k] * w[k] for k in comp) / tot
    direction = "up" if score > 15 else "down" if score < -15 else "flat"
    drivers = sorted(({"factor": k, "contribution": round(100 * comp[k] * w[k] / tot, 1)} for k in comp),
                     key=lambda x: -abs(x["contribution"]))
    spark = [round(float(x), 4) for x in c.tail(90).values]
    return {
        "price": round(last, 4), "date": str(c.index[-1].date()),
        "ret_1d": ret(1), "ret_20d": ret(20), "ret_60d": r60,
        "vol": round(vol, 3), "rsi": round(r14, 1),
        "score": round(score, 1), "direction": direction,
        "horizon_days": HORIZON_TRADING_DAYS, "drivers": drivers, "spark": spark,
    }
