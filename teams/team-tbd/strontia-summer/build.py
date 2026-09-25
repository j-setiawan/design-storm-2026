#!/usr/bin/env python3
"""Build the Strontia Springs summer page.

Everything the page needs is in this folder: sonde_data.py cleans the sonde
export and the upstream series from the repository's data/ folder (found by
walking up from this file), template.html is the page, and the result is written
to index.html here. The water level comes from the committed DWR storage record in
water-system-3d/storage-history.json at the repository root.

    uv run --with pandas --with openpyxl teams/team-tbd/strontia-summer/build.py
"""
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from sonde_data import ROOT, sonde, upstream  # noqa: E402


def main():
    s = sonde()
    first, last = pd.Timestamp(s["days"][0]), pd.Timestamp(s["days"][-1])
    up, updf = upstream(first - pd.Timedelta(days=14), last)
    # Daily storage for Strontia Springs from the map's DWR record, water year 2026 (index 0 is 2025-10-01).
    hist = json.loads((ROOT / "water-system-3d" / "storage-history.json").read_text())["reservoirs"]["STRRESCO"]["years"]["2026"]
    wy0 = pd.Timestamp("2025-10-01")
    up["Storage_AF"] = [(lambda i: hist[i] if 0 <= i < len(hist) else None)((pd.Timestamp(d) - wy0).days) for d in up["dates"]]
    window = updf.loc[first:last]
    presets = [
        {"label": "Spring begins", "date": s["days"][0]},
        {"label": "The big rain", "date": window["PRCP"].idxmax().strftime("%Y-%m-%d")},
        {"label": "Snowmelt peak", "date": window["Flow_CFS"].loc[: "2026-06-30"].idxmax().strftime("%Y-%m-%d")},
        {"label": "Peak river flow", "date": window["Flow_CFS"].idxmax().strftime("%Y-%m-%d")},
        {"label": "The August storm", "date": "2026-08-14"},
        {"label": "Summer ends", "date": s["days"][-1]},
    ]
    payload = {"built": pd.Timestamp.today().strftime("%Y-%m-%d"), "sonde": s, "upstream": up, "presets": presets}
    template = (HERE / "template.html").read_text()
    marker = "/*__DATA__*/"
    assert marker in template
    out = HERE / "index.html"
    out.write_text(template.replace(marker, json.dumps(payload, separators=(",", ":"))))
    print(f"wrote {out} ({out.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
