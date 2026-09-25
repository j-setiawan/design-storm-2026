# Refreshing the prediction dashboard

The dashboard (`prediction-dashboard.html`, and the same view embedded as an
overlay from `design-storm-water-system-3d.html`) reads two generated files:
`teams/dashboard/dashboard-extra.json` and `teams/dashboard/foothills-prediction.json`.
Both are build artifacts -- edit their generator scripts, not the JSON directly.

## One-command refresh

From the repository root:

```bash
python water-system-3d/refresh_dashboard.py
```

This runs, in order:

1. `teams/dashboard/process_sonde_data.py` -- rebuilds `sonde_daily.csv`
   from `data/Strontia *.xlsx`.
2. `water-system-3d/build_foothills_prediction.py` -- rebuilds
   `teams/dashboard/foothills-prediction.json`.
3. `wteams/dashboard/build_dashboard_extra.py` -- rebuilds `dashboard-extra.json`
   (depends on step 1's CSV, so it must run last).

It stops at the first failure rather than continuing with stale or partial
data. Reload `prediction-dashboard.html` (or the map overlay) afterward --
no separate build step for the HTML itself.

## What this does NOT do

It does not re-run `teams/dashboard/fetch_reservoir_ops_history.py`.
That script scrapes Denver Water's reservoir-levels page page-by-page and is
already run to completion. Re-run it by hand, and only to extend the date
range -- see its own docstring and `HANDOFF.md` before doing so.

## Local preview

```bash
python serve.py
```
then open `http://localhost:8765/design-storm-water-system-3d`.
