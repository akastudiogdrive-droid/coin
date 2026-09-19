import requests, pandas as pd
from ..util import DATA, write_csv, read_csv

NAME = "weather, London (Open-Meteo)"
PATH = DATA / "context" / "weather_london.csv"

def fetch(lat, lon, past_days=92, forecast_days=10):
    r = requests.get("https://api.open-meteo.com/v1/forecast", params={
        "latitude": lat, "longitude": lon, "timezone": "Europe/London",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "past_days": past_days, "forecast_days": forecast_days}, timeout=30)
    r.raise_for_status()
    d = r.json()["daily"]
    return pd.DataFrame({"Date": d["time"], "tmax": d["temperature_2m_max"],
                         "tmin": d["temperature_2m_min"], "precip": d["precipitation_sum"]})

def update(health):
    try:
        new = fetch(51.51, -0.13)
        old = read_csv(PATH)
        df = pd.concat([old, new]).drop_duplicates("Date", keep="last").sort_values("Date")
        write_csv(df, PATH)
        health.ok(NAME, f"{len(df)} days stored")
    except Exception as e:
        health.fail(NAME, e)
