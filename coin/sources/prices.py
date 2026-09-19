import time
import pandas as pd
from ..util import DATA, read_csv, write_csv, safe_name

PRICE_DIR = DATA / "prices"

def _download(symbol, period):
    import yfinance as yf
    df = yf.Ticker(symbol).history(period=period, auto_adjust=True)
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.reset_index()
    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None).dt.date.astype(str)
    return df[["Date", "Open", "High", "Low", "Close", "Volume"]]

def update(assets, health):
    """Incrementally refresh daily prices. First run backfills 2 years."""
    got, failed = 0, []
    for a in assets:
        sym = a["symbol"]
        path = PRICE_DIR / f"{safe_name(sym)}.csv"
        old = read_csv(path)
        try:
            new = _download(sym, "2y" if old.empty else "1mo")
            if new.empty:
                raise ValueError("no data returned")
            df = pd.concat([old, new]).drop_duplicates("Date", keep="last").sort_values("Date")
            write_csv(df, path)
            got += 1
        except Exception as e:
            failed.append(f"{sym}: {e}")
        time.sleep(0.5)
    if got:
        health.ok("prices (Yahoo Finance)", f"{got}/{len(assets)} assets")
    if failed:
        health.fail("prices (Yahoo Finance)", "; ".join(failed[:5]))

def load(symbol):
    df = read_csv(PRICE_DIR / f"{safe_name(symbol)}.csv")
    if df.empty:
        return df
    df["Date"] = pd.to_datetime(df["Date"])
    return df.set_index("Date").sort_index()
