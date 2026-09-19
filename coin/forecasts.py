"""Timestamped forecast log with automatic grading and an honest baseline."""
import datetime as dt
import pandas as pd
from .util import DATA, read_csv, write_csv, today

PATH = DATA / "forecasts.csv"
COLS = ["id", "issued", "strand", "symbol", "name", "direction", "score", "horizon_days",
        "due", "entry", "status", "exit", "return", "correct"]

def load():
    df = read_csv(PATH)
    return pd.DataFrame(columns=COLS) if df.empty else df

def issue(results, strand):
    """One open forecast per asset/item at a time; a new one is issued once the
    previous one has been graded. results: {key: {name, direction, score,
    horizon_days, price}}."""
    df = load()
    t = today()
    open_syms = set(df.loc[(df["status"] == "open") & (df["strand"] == strand), "symbol"])
    new = []
    for sym, r in results.items():
        if not r:
            continue
        if sym in open_syms:
            continue
        due = t + dt.timedelta(days=int(r["horizon_days"] * 7 / 5) + 1)
        new.append({"id": f"{t}-{sym}", "issued": str(t), "strand": strand, "symbol": sym,
                    "name": r["name"], "direction": r["direction"], "score": r["score"],
                    "horizon_days": r["horizon_days"], "due": str(due), "entry": r["price"],
                    "status": "open", "exit": None, "return": None, "correct": None})
    if new:
        df = pd.concat([df, pd.DataFrame(new)], ignore_index=True)
        write_csv(df, PATH)
    return len(new)

def grade(price_lookup, strand):
    """price_lookup(symbol, date) -> value on/after date, or None."""
    df = load()
    t = str(today())
    graded = 0
    for i, row in df[(df["status"] == "open") & (df["strand"] == strand)].iterrows():
        if row["due"] > t:
            continue
        px = price_lookup(row["symbol"], row["due"])
        if px is None:
            continue
        r = px / float(row["entry"]) - 1
        d = row["direction"]
        ok = (r > 0) if d == "up" else (r < 0) if d == "down" else (abs(r) < 0.02)
        df.loc[i, ["status", "exit", "return", "correct"]] = ["graded", round(px, 4), round(r, 4), bool(ok)]
        graded += 1
    if graded:
        write_csv(df, PATH)
    return graded

def scoreboard(strand):
    df = load()
    df = df[df["strand"] == strand]
    g = df[df["status"] == "graded"].copy()
    out = {"open": int((df["status"] == "open").sum()), "graded": int(len(g))}
    if len(g):
        g["correct"] = g["correct"].astype(str).str.lower() == "true"
        g["return"] = g["return"].astype(float)
        out["hit_rate"] = round(g["correct"].mean(), 3)
        out["baseline_always_up"] = round((g["return"] > 0).mean(), 3)
        g["issued"] = pd.to_datetime(g["issued"])
        wk = g.set_index("issued").resample("W")["correct"].mean().dropna()
        out["weekly"] = [{"week": str(k.date()), "hit_rate": round(v, 3)} for k, v in wk.items()]
    out["recent"] = df.sort_values("issued").tail(40).fillna("").to_dict("records")
    return out
