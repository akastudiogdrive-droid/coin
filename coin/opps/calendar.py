"""Event calendar with buy-by / sell-by dates, plus weather triggers."""
import datetime as dt
from ..util import load_yaml, today
from ..sources.weather import fetch as weather_fetch

def events(health):
    cfg = load_yaml("opportunities/events.yml")
    fees = load_yaml("opportunities/fees.yml")
    lead = fees["shipping_in_days"] + fees["buffer_days"]
    t = today()
    out = []
    for e in cfg.get("events", []):
        d = dt.date.fromisoformat(str(e["date"]))
        sell_start = d - dt.timedelta(days=e.get("sell_days", 21))
        buy_by = sell_start - dt.timedelta(days=lead)
        if t > d: status = "past"
        elif t >= sell_start: status = "selling window"
        elif t > buy_by: status = "too late to source"
        elif (buy_by - t).days <= 21: status = "buy now"
        else: status = "planning"
        days_away = (d - t).days
        bucket = ("now" if status in ("buy now", "selling window") else
                  "calendar" if days_away <= 365 else "planning")
        out.append({**{k: e.get(k) for k in ("id", "name", "items", "note", "verified")},
                    "date": str(d), "sell_start": str(sell_start), "buy_by": str(buy_by),
                    "status": status, "days_away": days_away, "bucket": bucket})
    trig = []
    for w in cfg.get("weather_triggers", []):
        try:
            df = weather_fetch(w["lat"], w["lon"], past_days=0, forecast_days=10)
            cold = df[df["tmin"] < w["min_temp_below"]]
            trig.append({"id": w["id"], "name": w["name"], "items": w["items"],
                         "triggered": not cold.empty,
                         "first_date": None if cold.empty else cold.iloc[0]["Date"]})
        except Exception as ex:
            health.fail("weather trigger", ex)
    return {"events": sorted(out, key=lambda x: x["date"]), "weather_triggers": trig}
