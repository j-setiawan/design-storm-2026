# Session handoff: Foothills prediction dashboard work

Context for picking this up fresh, without the original conversation. Read this, then
[AGENTS.md](AGENTS.md) / [README.md](README.md) / [guide.md](guide.md) for the base repo context.

## What this session did

Started from "poke at the data and existing models," ended up building a full prediction
dashboard (Scenario 1) with real, honestly-reported model improvements and negative results.

### 1. Reproduced and compared models (`teams/model-comparison/`)
- `model_comparison.py`: rebuilds Jake's TOC/alkalinity pipelines from `data/` CSVs, adds SVR and
  MLP alongside his linear/random-forest/CatBoost baselines.
- **Result**: MLP failed outright (negative R² both targets -- too little data, ~430-530 train
  rows). SVR was competitive for TOC (R²=0.70 vs CatBoost's 0.74) but nothing beat CatBoost.
  **Verdict: don't chase more model architectures on this dataset size.**

### 2. Investigated upstream reservoir data for longer lead times
- Found the DWR CDSS API has the actual upstream reservoir chain gages (`SFKANTCO`, `PLAANTCO`,
  `PLAHARCO`, `PLACHECO` -- South Fork above Antero, below Antero, above Eleven Mile, below
  Cheesman), 35-40 years of official daily discharge each. **This hit CDSS's own daily data
  quota mid-session ("Exceeded Daily Data Limit") and was never actually pulled or tested.**
  This is the best upstream data source available and is still untested -- see "Next steps."
- As a working alternative, scraped Denver Water's own reservoir-levels report (not an API --
  one page per day) for Antero/Eleven Mile/Cheesman/Dillon inflow+outflow+storage, back to
  2023-02-15. Script: `teams/model-comparison/fetch_reservoir_ops_history.py` (resumable, paced,
  already run to completion -- output is `teams/model-comparison/reservoir_ops_history.json`,
  1312 days). **Don't re-run this casually: it's ~1300 requests to a non-API public page, not a
  bulk endpoint.** It already has data through today; only rerun to extend the date range.
- Tested this reservoir data as a feature for alkalinity at lags 2-14 days
  (`test_upstream_reservoir_features.py`): **real, modest improvement for alkalinity**
  (R² 0.61->0.63, RMSE ~5.0->4.8 at 14-day lag), **no reliable result for TOC** (baseline itself
  was unstable on this date subset, matching Jake's own known CV instability finding).
- Folded the alkalinity improvement into the production pipeline (see below). Checked real
  feature importance afterward: **all four reservoirs combined are only ~6.3% of the model** --
  conductance (39%) and season (36%) still dominate. This is reported honestly in the UI, not
  hidden.

### 3. Tried using upstream releases to predict downstream flow (not chemistry) -- failed
- Idea: since conductance is driven by flow dilution (verified: r=-0.40 flow vs conductance,
  confirmed via monthly means), maybe upstream reservoir releases could forecast flow at the
  gage near Strontia several days out, then feed that into the chemistry model.
- Correlation check (`teams/model-comparison/reservoir_ops_history.json` outflow vs.
  `data/SouthPlatteTelemetry.csv` Flow_CFS): Cheesman/Dillon/Eleven Mile peak at **lag=0**
  (r=0.55-0.82) -- that's operational sync (Denver Water managing releases to match real-time
  conditions), not predictive lead time. Only Antero showed a genuine multi-day lead (8 days,
  r=0.43, moderate).
- Built and tested a flow-forecast model (`test_upstream_flow_prediction.py`) two ways: raw
  target and residual-from-persistence. **Both lost to naive persistence** (assume flow ~= flow
  8 days ago, R²=0.72) by a wide margin. **Verdict: this specific idea doesn't work with current
  data/models. Don't pursue further without a different approach.**

### 4. Strontia sonde (depth-profiled water chemistry, never used by Jake's models)
- `teams/model-comparison/process_sonde_data.py` turns `data/Strontia 0407_0819.xlsx` (16,093
  readings, many depths/day) into `teams/model-comparison/sonde_daily.csv` (104 days, daily mean
  + shallowest-reading aggregates).
- `test_sonde_features.py` compares gage-only vs. +sonde on the *same* 104-day window (fair
  comparison). **Inconclusive but suggestive**: both are underwater on this tiny sample
  (R² negative), but alkalinity is *consistently* less bad with sonde features at every lag
  tested (0-4 days). Not reliable enough to act on; a real pattern worth more data to confirm.
- The one depth profile checked visually showed a real turbidity plume at ~20-25m depth
  (interflow/stratification signal) with flat chlorophyll/phycocyanin (no bloom that day) --
  visible, undermodeled signal.

### 5. Built the actual Scenario 1 deliverables
- **`water-system-3d/build_foothills_prediction.py`**: generates
  `water-system-3d/foothills-prediction.json`, a backtested demo (not live forecast, always
  labeled as such) of TOC (SVR, 2-day lag) and alkalinity (RF + upstream reservoirs, 14-day lag)
  vs. measured, with per-date series, metrics, latest prediction + input snapshot, and real
  feature importance for alkalinity.
- **Map integration** (`design-storm-water-system-3d.html`): Foothills plant panel shows the
  predicted-vs-measured charts (fixed: predicted line uses a *different* color, gold dashed, from
  measured -- same-color overlapping noisy lines were unreadable, this was reported as "looks
  worse" and was actually just a legibility bug, not a regression). Antero/Eleven Mile/Cheesman/
  Dillon reservoirs and the sentinel gage (`gage-06707525`) each show a small callout: their own
  *actual* latest reading (`latest_ops`, genuinely different per reservoir) + their *real*
  feature-importance weight in the alkalinity model (also genuinely different per reservoir,
  e.g. Antero 0.5%, Dillon 3.0%) + a link to the full Foothills prediction. This wiring lives in
  `water-system-3d/build_system.py` (`FEEDS_PREDICTION_BY_POINT_ID`, `attach_latest_ops`), not
  hand-edited into `system.json`, so it survives regeneration.
  - **Fixed a real pre-existing bug** in `build_system.py`: `INFLUENT_CSV` pointed at a folder
    structure (`../../design-storm/data/...`) that doesn't exist in this repo. Running the
    unpatched script truncates `foothills-influent.json` to 0 bytes before crashing. Now fixed
    to `../data/FoothillsInfluent.csv`.
- **Standalone dashboard** (`prediction-dashboard.html`, new top-level page, data from
  `water-system-3d/build_dashboard_extra.py` -> `water-system-3d/dashboard-extra.json`): full
  backtest charts, feature-importance bars (with the honest 6.3% finding highlighted), upstream
  reservoir snapshot table, sonde section (time series + honest lag-test table + depth-profile
  chart), all with real hover tooltips (crosshair + value popup, not static).
  - Opens as an **overlay panel** from the map (button `#open-dashboard` -> iframe
    `prediction-dashboard.html?embedded=1` inside `#dashboard-overlay`/`#dashboard-panel`), sized
    `min(1080px, 92vw) x min(860px, 88vh)`, not full-screen, single close button (the panel's own
    x; the in-page "back to map" link auto-hides itself when `?embedded=1` is present to avoid a
    second close control). Visiting `prediction-dashboard.html` directly (no query param) shows
    a normal "<- Back to map" link instead.

## Key numbers to cite (don't re-derive, already verified this session)

| What | Value |
|---|---|
| Jake's baseline, TOC (CatBoost, from guide.md) | R²=0.74, RMSE=0.33 mg/L |
| Jake's baseline, Alkalinity (CatBoost, from guide.md) | R²=0.68, RMSE=5.20 mg/L |
| Our TOC (SVR, 2-day lag) | R²=0.70, RMSE=0.353 mg/L (428 test days) |
| Our Alkalinity (RF + upstream reservoirs, 14-day lag) | R²=0.629, RMSE=4.821 mg/L (287 test days) |
| Reservoirs' real combined importance in alk model | 6.3% (conductance 39%, season 36% dominate) |
| Naive persistence for flow 8 days out | R²=0.72 (nothing we tried beat this) |
| FoothillsInfluent.csv total rows | 1,115 (Apr 2022-Aug 2026, no Jan-Mar) |
| Rows after TOC feature engineering/dropna | 856 (USGS sentinel gage has real gaps, not just winter) |
| Sonde daily data available | 104 days only (Apr 7-Aug 19 2026) |
| Reservoir ops scrape coverage | 2023-02-19 to today, 1312 days |

## Repo conventions learned/reinforced this session

- `data/`, `scripts/`, `figures/`, `reference/` are Denver Water originals -- never edit, work on
  copies. `water-system-3d/` is *not* in that list -- it's living app infra, safe to extend.
- Files with `"_comment": "Generated by X.py. Do not edit by hand."` should be edited via their
  generator script, not by hand -- otherwise the next regeneration silently reverts your change
  (or, as happened this session, a half-crashed regeneration can truncate a file to 0 bytes).
- New exploratory/team work goes in `teams/<name>/` per the top-level README -- used
  `teams/model-comparison/` for all the ad hoc analysis scripts this session.
- The DWR CDSS API (`dwr.state.co.us/Rest/GET/...`) enforces a daily data quota. Hit it once
  this session; back off and retry later rather than working around it (e.g. no proxy rotation --
  refused that request earlier in this session on request).
- Denver Water's reservoir-levels page is not an API; treat it politely (paced, resumable,
  bounded), and prefer the official CDSS gages when they cover what you need.
- The local server: `python serve.py` from repo root, then
  `http://localhost:8765/design-storm-water-system-3d`.

## Suggested next steps (in priority order)

1. **Retry the CDSS upstream chain fetch** (`teams/model-comparison/fetch_upstream_flow_history.py`
   -- already written, just hit the quota last time). This is the *better* version of the
   reservoir-ops idea (decades of official data vs. ~3.5 years scraped, real physical gages
   instead of Denver Water's operationally-synced release data). Re-run the lag/importance test
   against it the same way `test_upstream_reservoir_features.py` did for the scrape.
2. If that CDSS data shows a stronger signal than the scrape did, replace the scrape-based
   feature in `build_foothills_prediction.py` with it (same 14-day-lag slot).
3. Sonde data: only 104 days exist. If Denver Water can share more history (the file is named
   `Strontia 0407_0819.xlsx` -- ask if a longer export exists), the "consistently less bad"
   pattern from section 4 above is worth re-testing properly.
4. Consider the HAB/stratification angle flagged early this session but not pursued: sonde
   chlorophyll+phycocyanin+ORP by depth as an early-warning signal for algal blooms/reservoir
   turnover -- a different target than TOC/alkalinity, genuinely unexplored.
5. TOC has no validated way to extend lead time yet (unlike alkalinity's 14-day reservoir
   feature) -- open problem if more lead time is wanted there too.
