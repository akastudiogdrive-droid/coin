"""Places every item within its trend and wave: lifecycle stage, position vs
parent, saturation, evidence count, margin, and the 'quiet child' gap finder."""
import pandas as pd
from .interest import load_series
from ..util import load_yaml

RISE, FALL = 0.25, -0.25

def momentum(series, recent=14, base=60):
    if series is None or len(series) < recent + 14:
        return None
    v = series["value"].astype(float)
    lvl = v.tail(recent).mean()
    b = v.iloc[-(recent + base):-recent].mean()
    return {"level": round(float(lvl), 1), "momentum": round(float((lvl - b) / (b + 5)), 3)}

def stage(level, mom, saturating=False):
    if mom is None:
        return "no data yet"
    if saturating:
        return "saturating"
    if mom > RISE:
        return "emerging" if level < 25 else "rising"
    if mom < FALL:
        return "fading"
    if level >= 50:
        return "peak"
    return "steady"

def saturation(item_id):
    e = load_series("ebay", item_id)
    if e.empty or len(e) < 10:
        return None
    now, then = e.iloc[-1], e.iloc[max(0, len(e) - 15)]
    growth = (now["total"] - then["total"]) / max(then["total"], 1)
    pchg = None
    if pd.notna(now["median_price"]) and pd.notna(then["median_price"]) and then["median_price"]:
        pchg = now["median_price"] / then["median_price"] - 1
    return {"listings": int(now["total"]), "listing_growth": round(float(growth), 3),
            "price_change": None if pchg is None else round(float(pchg), 3),
            "saturating": growth > 0.3 and (pchg is not None and pchg < -0.1)}

def margins(it, fees):
    c, p = it.get("unit_cost"), it.get("sell_price")
    if not (c and p):
        return None
    out = {}
    for k, f in fees["platforms"].items():
        profit = p - c - p * f["percent_fee"] - f["fixed_fee"] - f["postage_out"]
        out[k] = {"profit_per_unit": round(profit, 2), "roi": round(profit / c, 2)}
    return out

def analyse():
    tm = load_yaml("opportunities/trend_map.yml")
    fees = load_yaml("opportunities/fees.yml")
    waves_out, items_out = [], []
    for w in tm["waves"]:
        w_trends = []
        for t in w["trends"]:
            wiki = momentum(load_series("wiki", t["id"]), 14, 60) if t.get("wiki") else None
            t_items = []
            for it in t["items"]:
                m = momentum(load_series("trends", it["id"]))
                sat = saturation(it["id"])
                t_items.append({"it": it, "m": m, "sat": sat})
            moms = [x["m"]["momentum"] for x in t_items if x["m"]]
            lvls = [x["m"]["level"] for x in t_items if x["m"]]
            t_mom = sum(moms) / len(moms) if moms else (wiki["momentum"] if wiki else None)
            t_lvl = sum(lvls) / len(lvls) if lvls else 0
            t_stage = stage(t_lvl, t_mom)
            trend_rec = {"id": t["id"], "name": t["name"], "stage": t_stage,
                         "momentum": None if t_mom is None else round(t_mom, 3),
                         "wiki_momentum": wiki["momentum"] if wiki else None, "items": []}
            for x in t_items:
                it, m, sat = x["it"], x["m"], x["sat"]
                mom = m["momentum"] if m else None
                sib = [y["m"]["momentum"] for y in t_items if y is not x and y["m"]]
                sib_mom = sum(sib) / len(sib) if sib else None   # independent of this item
                st = stage(m["level"] if m else 0, mom, bool(sat and sat["saturating"]))
                pos = None
                if mom is not None and sib_mom is not None:
                    d = mom - sib_mom
                    pos = "leading" if d > 0.2 else "lagging" if d < -0.2 else "in step"
                evidence = []
                if mom is not None and mom > RISE: evidence.append("search interest rising")
                if wiki and wiki["momentum"] > 0.15: evidence.append("parent topic attention rising")
                if sib_mom is not None and sib_mom > RISE: evidence.append("sibling items rising")
                if sat and not sat["saturating"] and sat["listing_growth"] > 0.05:
                    evidence.append("seller supply starting to grow")
                gap = (t_stage in ("rising", "emerging") and st in ("steady", "emerging")
                       and m is not None and m["level"] < 30)
                rec = {"id": it["id"], "name": it["name"], "wave": w["name"], "trend": t["name"],
                       "stage": st, "position": pos, "level": m["level"] if m else None,
                       "momentum": mom, "saturation": sat, "evidence": evidence,
                       "confidence": len(evidence), "quiet_child": bool(gap),
                       "flags": it.get("flags", []), "attributes": it.get("attributes", {}),
                       "margins": margins(it, fees)}
                trend_rec["items"].append(rec); items_out.append(rec)
            w_trends.append(trend_rec)
        waves_out.append({"id": w["id"], "name": w["name"], "trends": w_trends})

    live = [i for i in items_out if i["stage"] in ("emerging", "rising")]
    for i in live:
        i["timing"] = ("strong evidence, later" if i["confidence"] >= 3 else
                       "enough evidence" if i["confidence"] == 2 else "thin evidence, early")
        i["pick"] = i["confidence"] >= 2       # reliability rule
    live.sort(key=lambda i: (-i["confidence"], -(i["momentum"] or 0)))
    return {"waves": waves_out, "items": items_out, "now": live[:5],
            "quiet_children": [i for i in items_out if i["quiet_child"]]}
