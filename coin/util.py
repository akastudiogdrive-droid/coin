import json, os, datetime as dt
from pathlib import Path
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CONFIG = ROOT / "config"
DOCS = ROOT / "docs"
JOURNAL = ROOT / "journal"

def today() -> dt.date:
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).date()

def load_yaml(rel):
    with open(CONFIG / rel) as f:
        return yaml.safe_load(f)

def read_csv(path, **kw):
    path = Path(path)
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(path, **kw)

def write_csv(df, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)

def write_json(obj, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=str)

def safe_name(s: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in s)

class Health:
    """Records which data sources worked on this run, shown on the dashboard."""
    def __init__(self):
        self.rows = []
    def ok(self, source, detail=""):
        self.rows.append({"source": source, "status": "ok", "detail": detail})
    def fail(self, source, detail=""):
        self.rows.append({"source": source, "status": "failed", "detail": str(detail)[:200]})
    def skip(self, source, detail=""):
        self.rows.append({"source": source, "status": "not set up", "detail": detail})
