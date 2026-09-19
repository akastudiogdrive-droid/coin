"""Interest and saturation signals for the trend map.
- Google Trends (unofficial; can be rate-limited, so items are rotated)
- Wikipedia pageviews (reliable, trend-level where an article exists)
- eBay Browse API (listing counts and prices; needs free developer keys)"""
import os, time, json, datetime as dt, statistics
import requests
import pandas as pd
from ..util import DATA, read_csv, write_csv, today

OPPS = DATA / "opps"
STATE = OPPS / "fetch_state.json"
MAX_TRENDS_PER_RUN = 10
REFRESH_DAYS = 2
UA = {"User-Agent": "CoinResearch/0.1 (github.com/akastudiogdrive-droid/coin)"}

def _state():
    return json.loads(STATE.read_text()) if STATE.exists() else {}

def _save_state(s):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(s, indent=1))

def google_trends(items, health):
    try:
        from pytrends.request import TrendReq
    except Exception as e:
        return health.fail("Google Trends", e)
    st = _state().get("trends", {})
    cutoff = str(today() - dt.timedelta(days=REFRESH_DAYS))
    due = sorted([i for i in items if st.get(i["id"], "") <= cutoff], key=lambda i: st.get(i["id"], ""))
    due = due[:MAX_TRENDS_PER_RUN]
    ok, fails = 0, []
    py = TrendReq(hl="en-GB", tz=0, timeout=(10, 30))
    for it in due:
        kw = it["keywords"][0]
        try:
            py.build_payload([kw], timeframe="today 3-m", geo="GB")
            df = py.interest_over_time()
            if df is None or df.empty:
                raise ValueError("empty")
            out = pd.DataFrame({"Date": df.index.date.astype(str), "value": df[kw].values})
            write_csv(out, OPPS / "trends" / f"{it['id']}.csv")   # latest 3-month window
            st[it["id"]] = str(today()); ok += 1
        except Exception as e:
            fails.append(f"{it['id']}: {str(e)[:60]}")
            if "429" in str(e):
                break
        time.sleep(8)
    s = _state(); s["trends"] = st; _save_state(s)
    if ok:
        health.ok("Google Trends", f"refreshed {ok} items this run (rotating)")
    if fails:
        health.fail("Google Trends", "; ".join(fails[:4]))

def wikipedia(trends, health):
    end = today(); start = end - dt.timedelta(days=120)
    ok = 0
    for t in trends:
        art = t.get("wiki")
        if not art:
            continue
        url = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/"
               f"all-access/user/{art}/daily/{start:%Y%m%d}/{end:%Y%m%d}")
        try:
            r = requests.get(url, headers=UA, timeout=30); r.raise_for_status()
            rows = r.json()["items"]
            df = pd.DataFrame({"Date": [pd.to_datetime(x["timestamp"][:8]).date() for x in rows],
                               "value": [x["views"] for x in rows]})
            write_csv(df, OPPS / "wiki" / f"{t['id']}.csv"); ok += 1
        except Exception as e:
            health.fail("Wikipedia pageviews", f"{art}: {e}")
    if ok:
        health.ok("Wikipedia pageviews", f"{ok} trends")

def _ebay_token():
    cid, sec = os.getenv("EBAY_CLIENT_ID"), os.getenv("EBAY_CLIENT_SECRET")
    if not (cid and sec):
        return None
    r = requests.post("https://api.ebay.com/identity/v1/oauth2/token", auth=(cid, sec),
                      data={"grant_type": "client_credentials",
                            "scope": "https://api.ebay.com/oauth/api_scope"}, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]

def ebay(items, health):
    try:
        tok = _ebay_token()
    except Exception as e:
        return health.fail("eBay listings", e)
    if not tok:
        return health.skip("eBay listings", "add EBAY_CLIENT_ID / EBAY_CLIENT_SECRET secrets to enable")
    ok = 0
    for it in items:
        q = it.get("ebay_query")
        if not q:
            continue
        try:
            r = requests.get("https://api.ebay.com/buy/browse/v1/item_summary/search",
                             params={"q": q, "limit": 50},
                             headers={"Authorization": f"Bearer {tok}", "X-EBAY-C-MARKETPLACE-ID": "EBAY_GB"},
                             timeout=30)
            r.raise_for_status(); j = r.json()
            prices = [float(x["price"]["value"]) for x in j.get("itemSummaries", []) if "price" in x]
            row = pd.DataFrame([{"Date": str(today()), "total": j.get("total", 0),
                                 "median_price": statistics.median(prices) if prices else None}])
            path = OPPS / "ebay" / f"{it['id']}.csv"
            df = pd.concat([read_csv(path), row]).drop_duplicates("Date", keep="last")
            write_csv(df, path); ok += 1
        except Exception as e:
            health.fail("eBay listings", f"{it['id']}: {e}")
        time.sleep(0.5)
    if ok:
        health.ok("eBay listings", f"{ok} items")

def load_series(kind, key):
    df = read_csv(OPPS / kind / f"{key}.csv")
    if df.empty:
        return df
    df["Date"] = pd.to_datetime(df["Date"])
    return df.set_index("Date").sort_index()
