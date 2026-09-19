"""Daily entry point: python -m coin.run"""
import datetime as dt
import pandas as pd
from .util import DATA, DOCS, JOURNAL, load_yaml, write_json, write_csv, read_csv, today, Health
from .sources import prices, CONTEXT_SOURCES
from .sources import fear_greed
from . import signals, forecasts
from .opps import interest, analyse as opps_analyse, calendar as opps_calendar

def markets(health):
    assets = load_yaml("watchlist.yml")["assets"]
    prices.update(assets, health)
    for src in CONTEXT_SOURCES:
        src.update(health)
    fg = fear_greed.latest()
    fgv = fg["value"] if fg else None
    results = {}
    for a in assets:
        df = prices.load(a["symbol"])
        r = signals.analyse(df, a["kind"], fgv) if not df.empty else None
        if r:
            r.update(name=a["name"], kind=a["kind"], symbol=a["symbol"])
        results[a["symbol"]] = r

    def lookup(sym, due):
        df = prices.load(sym)
        after = df[df.index >= pd.Timestamp(due)]
        return None if after.empty else float(after["Close"].iloc[0])

    graded = forecasts.grade(lookup, "markets")
    issued = forecasts.issue(results, "markets")
    return {"assets": [r for r in results.values() if r], "fear_greed": fg,
            "graded": graded, "issued": issued}

def opportunities(health):
    tm = load_yaml("opportunities/trend_map.yml")
    trends = [t for w in tm["waves"] for t in w["trends"]]
    items = [i for t in trends for i in t["items"]]
    interest.google_trends(items, health)
    interest.wikipedia(trends, health)
    interest.ebay(items, health)
    a = opps_analyse.analyse()
    cal = opps_calendar.events(health)

    fc = forecasts.load()
    def lookup(item_id, due):
        s = interest.load_series("trends", item_id)
        row = fc[(fc["symbol"] == item_id) & (fc["status"] == "open")]
        if s.empty or row.empty or s.index.max() < pd.Timestamp(due):
            return None
        iss = pd.Timestamp(row.iloc[0]["issued"])
        before = s[s.index <= iss]["value"].tail(7).mean()
        after = s[s.index <= pd.Timestamp(due)]["value"].tail(7).mean()
        return float(row.iloc[0]["entry"]) * (after / before) if before else None

    graded = forecasts.grade(lookup, "opps")
    picks = {i["id"]: {"name": i["name"], "direction": "up", "score": i["confidence"],
                       "horizon_days": 20, "price": i["level"]}
             for i in a["now"] if i.get("pick")}
    issued = forecasts.issue(picks, "opps")
    return {**a, **cal, "graded": graded, "issued": issued}

def journal(m, o, health):
    t = today()
    lines = [f"# {t} daily run", "", "## Markets"]
    movers = sorted(m["assets"], key=lambda r: -abs(r.get("ret_1d") or 0))[:5]
    for r in movers:
        lines.append(f"- {r['name']}: {100*(r['ret_1d'] or 0):+.1f}% on the day, score {r['score']:+.0f} ({r['direction']})")
    if m["fear_greed"]:
        lines.append(f"- Crypto fear & greed: {m['fear_greed']['value']} ({m['fear_greed']['label']})")
    lines.append(f"- Forecasts issued {m['issued']}, graded {m['graded']}")
    lines += ["", "## Opportunities"]
    for i in o["now"]:
        lines.append(f"- {i['name']} ({i['trend']}): {i['stage']}, {i['timing']}, evidence: {', '.join(i['evidence']) or 'none'}")
    for e in o["events"]:
        if e["status"] in ("buy now", "selling window"):
            lines.append(f"- Event: {e['name']}: {e['status']} (buy by {e['buy_by']})")
    lines += ["", "## Source health"] + [f"- {h['source']}: {h['status']} {h['detail']}" for h in health.rows]
    lines += ["", "_Analysis of why things changed is added by Claude in chat._"]
    JOURNAL.mkdir(exist_ok=True)
    (JOURNAL / f"{t}.md").write_text("\n".join(lines) + "\n")

def main():
    health = Health()
    try:
        m = markets(health)
    except Exception as e:
        health.fail("markets strand", e); m = {"assets": [], "fear_greed": None, "graded": 0, "issued": 0}
    try:
        o = opportunities(health)
    except Exception as e:
        health.fail("opportunities strand", e)
        o = {"waves": [], "items": [], "now": [], "quiet_children": [], "events": [],
             "weather_triggers": [], "graded": 0, "issued": 0}
    journal(m, o, health)
    log = read_csv(DATA / "run_log.csv")
    log = pd.concat([log, pd.DataFrame([{**h, "date": str(today())} for h in health.rows])])
    write_csv(log.tail(2000), DATA / "run_log.csv")
    write_json({
        "generated": dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat(timespec="minutes") + "Z",
        "markets": {**m, "scoreboard": forecasts.scoreboard("markets")},
        "opportunities": {**o, "scoreboard": forecasts.scoreboard("opps")},
        "health": health.rows,
    }, DOCS / "data" / "dashboard.json")
    print("\n".join(f"{h['status']:>10}  {h['source']}  {h['detail']}" for h in health.rows))

if __name__ == "__main__":
    main()
