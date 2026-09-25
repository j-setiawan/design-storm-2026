"""
Fetches Denver Water's own daily reservoir-levels report (inflow/outflow,
elevation, storage, % full) for every day it has published, one request per
day since this is a page-per-day CSV export, not a bulk API.

Source: https://www.denverwater.org/your-water/water-supply-and-planning/
        supply-data-and-reports/reservoir-levels
Preliminary, subject to change, per the page footer -- carries the same
caveat as everything else under data/TERMS.md.

Resumable: re-running skips dates already saved in the output file, and
progress is saved every SAVE_EVERY requests so an interruption loses at most
that many days. Paced with a delay between requests to be polite to a
non-API public page.

    python teams/model-comparison/fetch_reservoir_ops_history.py
"""
import csv
import io
import json
import os
import time
from datetime import date, timedelta

import requests

CSV_URL = "https://www.denverwater.org/your-water/water-supply-and-planning/reservoir-levels/csv"
START_DATE = date(2023, 2, 15)  # confirmed empty before ~2023-02-01, present by 2023-03-01
OUT = "teams/model-comparison/reservoir_ops_history.json"
SAVE_EVERY = 40
DELAY_SECONDS = 0.4
HEADERS = {"User-Agent": "design-storm-2026 research script (contact via github.com/paulrayner/design-storm-2026)"}


def fetch_day(day):
    resp = requests.get(CSV_URL, params={"field_valid_date_value": day.isoformat(), "page": "", "_format": "csv"},
                         headers=HEADERS, timeout=20)
    resp.raise_for_status()
    reader = csv.DictReader(io.StringIO(resp.text))
    rows = {}
    for row in reader:
        name = row["Reservoir"]
        rows[name] = {
            "inflow_cfs": to_num(row["Inflow (cfs)"]),
            "outflow_cfs": to_num(row["Outflow (cfs)"]),
            "elevation_ft": to_num(row["Elevation (feet)"]),
            "storage_af": to_num(row["Storage (acre-feet)"]),
            "capacity_af": to_num(row["Capacity (acre-feet)"]),
            "pct_full": to_num(row["Reservoir % Full"]),
        }
    return rows


def to_num(s):
    s = (s or "").replace(",", "").strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def load_existing():
    if os.path.exists(OUT):
        with open(OUT) as f:
            return json.load(f)
    return {}


def save(data):
    with open(OUT, "w") as f:
        json.dump(data, f, indent=1)


if __name__ == "__main__":
    data = load_existing()
    print(f"Resuming with {len(data)} days already saved")
    day = START_DATE
    end = date.today()
    fetched_since_save = 0
    while day <= end:
        key = day.isoformat()
        if key not in data:
            try:
                rows = fetch_day(day)
                if rows:
                    data[key] = rows
            except requests.RequestException as err:
                print(f"  {key}: request failed ({err}), will retry on next run")
            fetched_since_save += 1
            time.sleep(DELAY_SECONDS)
            if fetched_since_save >= SAVE_EVERY:
                save(data)
                print(f"  ...saved through {key} ({len(data)} days total)")
                fetched_since_save = 0
        day += timedelta(days=1)
    save(data)
    print(f"Done. {len(data)} days written to {OUT}")
