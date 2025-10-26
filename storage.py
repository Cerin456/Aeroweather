# utils/storage.py
import json
from pathlib import Path
from datetime import datetime

AIR_FILE = Path("data/aircrafts.json")
AIR_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_aircrafts():
    if not AIR_FILE.exists():
        return []
    return json.loads(AIR_FILE.read_text(encoding="utf-8"))

def save_aircrafts(lst):
    AIR_FILE.write_text(json.dumps(lst, indent=2, default=str), encoding="utf-8")

def add_aircraft(record: dict):
    lst = load_aircrafts()
    record = record.copy()
    record["id"] = (lst[-1]["id"] + 1) if lst else 1
    record["created_at"] = datetime.utcnow().isoformat()
    lst.append(record)
    save_aircrafts(lst)
    return record

def csv_export_string():
    import pandas as pd
    df = pd.DataFrame(load_aircrafts())
    return df.to_csv(index=False)
