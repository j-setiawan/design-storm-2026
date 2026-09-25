"""
Fetches daily discharge history for the DWR CDSS stream gages that track the
South Platte reservoir chain above Strontia Springs -- each one further
upstream than the sentinel gage (USGS 06707525) Jake's models use, so each
offers a longer lead time before the water reaches Foothills:

  SFKANTCO  South Fork of South Platte above Antero Reservoir   (top of chain)
  PLAANTCO  South Platte below Antero Reservoir
  PLAHARCO  South Platte above Eleven Mile Canyon Reservoir
  PLACHECO  South Platte below Cheesman Reservoir                (closest to sentinel)

Network: the same official DWR CDSS REST API already used by
fetch_storage_history.py (https://dwr.state.co.us/Rest/GET/Help), not a
scrape. Writes upstream_flow_history.csv, one row per day, one column per
station (cfs).

    python water-system-3d/fetch_upstream_flow_history.py
"""
import csv
import json
from datetime import date

import requests

API = "https://dwr.state.co.us/Rest/GET/api/v2/telemetrystations/telemetrytimeseriesday/"
STATIONS = {
    "SFKANTCO": "South Fork above Antero",
    "PLAANTCO": "South Platte below Antero",
    "PLAHARCO": "South Platte above Eleven Mile",
    "PLACHECO": "South Platte below Cheesman",
}
OUT = "teams/model-comparison/upstream_flow_history.csv"


def fetch_station(abbrev):
    params = {
        "format": "json", "abbrev": abbrev, "parameter": "DISCHRG",
        "startDate": "1980-01-01", "endDate": date.today().isoformat(),
        "pageSize": 50000, "pageIndex": 1,
    }
    response = requests.get(API, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    return {row["measDate"][:10]: row.get("measValue") for row in payload.get("ResultList", [])}


if __name__ == "__main__":
    series = {}
    for abbrev in STATIONS:
        print(f"Fetching {abbrev} ({STATIONS[abbrev]})...")
        series[abbrev] = fetch_station(abbrev)
        print(f"  {len(series[abbrev])} days")

    all_dates = sorted(set().union(*series.values()))
    with open(OUT, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Date"] + list(STATIONS))
        for d in all_dates:
            writer.writerow([d] + [series[abbrev].get(d, "") for abbrev in STATIONS])
    print(f"Wrote {OUT} ({len(all_dates)} days)")
