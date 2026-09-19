import requests, pandas as pd
from ..util import DATA, write_csv, read_csv

NAME = "crypto fear & greed (alternative.me)"
PATH = DATA / "context" / "fear_greed.csv"

def update(health):
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=0&format=json", timeout=30)
        r.raise_for_status()
        rows = r.json()["data"]
        df = pd.DataFrame({
            "Date": pd.to_datetime(pd.to_numeric([x["timestamp"] for x in rows]), unit="s").date.astype(str),
            "value": [int(x["value"]) for x in rows],
            "label": [x["value_classification"] for x in rows],
        }).sort_values("Date")
        write_csv(df, PATH)
        health.ok(NAME, f"latest {df.iloc[-1]['value']} ({df.iloc[-1]['label']})")
    except Exception as e:
        health.fail(NAME, e)

def latest():
    df = read_csv(PATH)
    return None if df.empty else df.iloc[-1].to_dict()
