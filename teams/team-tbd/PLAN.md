# Plan: Inside Strontia Springs Reservoir during a storm

Team folder name is a placeholder (`team-tbd`); rename it when the team has a name.
Scenario 2 of the Design Storm, delivered as a new panel on a **copy** of the 3D map.
Worked by one person plus Claude.

## The goal in one paragraph

A profiling sonde in Strontia Springs Reservoir has taken readings from surface to depth
since 2026-04-07, and nothing in the challenge materials analyzes it. Turn it into a
depth-over-time picture of the reservoir (a "CT scan" of the water column), use it to
follow the August 14 to 15, 2026 storm from the river gage, through the reservoir by
depth, to the Foothills plant, and show the result on the Strontia Springs Dam marker of
a copy of the 3D map. This answers Cassidi's Scenario 2 bullet directly: *how do water
quality parameters change and distribute by depth in the reservoir, and how do storms and
spring runoff change that picture?*

## Why this project (decisions already made, do not relitigate)

Established in the planning session on 2026-09-24:

- **Scenario 1 machine learning was ruled out for autoresearch.** The TOC model has about
  428 training rows (856 usable rows, split 50/50). A simulated autoresearch loop improved
  the dev score but the gains did not survive a held-out 2026 season for TOC.
- **A persistence baseline beats Jake's model.** "Today = the lab value from 2 days ago"
  (4 for alkalinity) had 2 to 4 times lower MAE than the random forest in every test season
  2024 to 2026. Worth mentioning to Denver Water; not this project's focus.
- **Public data cannot extend the dataset.** The USGS gage above Strontia starts
  2022-03-31, and no public source has Foothills TOC or alkalinity.
- **The sonde data suits a descriptive project.** One season does not limit a careful
  description the way it limits a predictive model.
- Scripts behind these findings were in the planning session's scratchpad and are not in
  the repo.

## What we know about the sonde data

`data/Strontia 0407_0819.xlsx`, one sheet, 16,093 rows, 11 columns:
`Time stamp, Temp C, Conductivity , Vertical Position , pH, ORP mV, Turbidity NTU,
Chl ug/L, Phycocyanin , ODO & sat, ODO mg/L` (note the trailing spaces in some names).

- 2026-04-07 14:39 to 2026-08-19 07:08, 104 distinct days, about 176 readings a day.
- Almost every timestamp is unique (16,036 distinct), so the profiler moves continuously.
  "Casts" (one sweep top to bottom) have to be reconstructed from the movement of
  `Vertical Position`, not grouped by timestamp.
- `Vertical Position` ranges 0.8 to 47.8. **Unknown: is it depth below surface or height
  above the sensor's base?** Settle this first, for example from summer temperature
  (warmest water should be near the surface) and ask Denver Water to confirm.
- Gaps longer than 2 days: Apr 10 to 28, May 5 to 14, May 15 to 18, Jul 9 to 13.
- Aug 10 to 19 has daily coverage (1,536 readings), so the storm window is covered.
- The first rows (Apr 7) show turbidity of 50 to 113 NTU and conductivity jumping between
  readings seconds apart. Probably startup noise; needs QC.

Other data for the storm trace:
- `strontia-brief/series/06707525-turbidity-conductance-aug14-15.json`: 15-minute
  turbidity and conductance at the gage above Strontia, Aug 14 to 15 (already used by the
  map's storm replay).
- `strontia-brief/series/06701900-discharge-aug14-15.json`: 15-minute flow near Trumbull.
- `data/USGS_South_Platte.csv`: daily gage values through 2026-08-19.
- `data/FoothillsInfluent.csv`: daily plant TOC and alkalinity through 2026-08-19.

## Ground rules (from AGENTS.md, apply throughout)

- Never edit `data/`, `scripts/`, `figures/`, `reference/`, or the original
  `design-storm-water-system-3d.html`. All work goes in `teams/team-tbd/`.
- Denver Water's data terms travel with any derived dataset, including the generated
  sonde JSON. Put the terms (or a pointer to `data/TERMS.md`) next to it, and show a
  short attribution in the map panel. Do not publish anything built on this data
  outside the repo without checking the terms.
- Readings are provisional. Say so in every finding and in the panel.
- Never invent numbers. Every number in findings comes from a script in the team folder.
- Label general limnology knowledge as general knowledge, not as a finding.

## Phases

Each phase ends with a checkpoint: stop, show the result to Miles, and agree before moving on.

### Phase 0: Setup

- Python venv for the team folder (`teams/team-tbd/.venv`, gitignored) with pandas,
  numpy, openpyxl, scipy, matplotlib, scikit-learn. The system python has no pandas.
- Copy the map into `teams/team-tbd/map/`. The original fetches data by relative paths
  (`water-system-3d/...`, `strontia-brief/...`), which break from a subfolder. Either
  prefix them (e.g. `../../../`) or add a single `DATA_ROOT` constant. Prefer the
  constant, as the smaller diff.
- Confirm the copy runs under `python3 serve.py` (repo root, port 8765) at
  `http://localhost:8765/teams/team-tbd/map/design-storm-water-system-3d`.
- Note: `water-system-3d/build_system.py` reads the influent CSV from
  `../../design-storm/data/`, a path that does not exist in this repo. Don't rerun it;
  write a separate generator for the new JSON.

**Checkpoint:** the copied map loads and behaves like the original.

### Phase 1: Clean and structure the sonde data

Script `teams/team-tbd/analysis/clean_sonde.py`:
- Load, strip column names, parse times.
- Settle what `Vertical Position` means (see above) and convert to depth below surface.
- Reconstruct casts from direction changes in position. Report how many casts there are,
  how many per day, the typical depth range and duration.
- QC: physical range checks per parameter, spike removal (a value far from its neighbors
  in the same cast), flag the Apr 7 startup rows. Record every rule and how many rows it
  removed, in `analysis/QC.md`.
- Output `analysis/out/sonde_clean.csv` (not committed if large; regenerable).

**Checkpoint:** QC summary, depth-meaning decision, cast statistics.

### Phase 2: The baseline depth picture

Script `analysis/grid_sonde.py`:
- Grid each parameter onto time by depth (start with 1 hour by 1 m) using simple linear
  interpolation within each cast, then across time. No interpolation across the long
  gaps: leave them blank.
- Static heatmap PNGs per parameter, full season plus an Aug 10 to 19 zoom, in
  `analysis/out/`.

**Checkpoint:** Look at the pictures together. Is stratification visible (warm layer on
top by summer)? Does the Aug 14 to 15 storm show up, and at what depth? If the storm is
not visible, stop and rethink before building the map panel.

### Phase 3: The storm story

Script `analysis/storm_trace.py`, for Aug 10 to 19:
- Align on one timeline: gage turbidity and conductance (15-minute series for Aug 14 to 15,
  daily beyond), sonde by depth, plant TOC and alkalinity (daily).
- Measure: when the turbidity pulse passes the gage, when and at which depths it appears
  in the reservoir, how deep it goes, how long it stays, and whether the plant's TOC and
  alkalinity move afterward, with what delay.
- Write `FINDINGS.md`: each finding in plain language with the number behind it, which
  script produced it, and the provisional caveat. Separate "measured" from "interpreted".
- Also describe the season briefly: when stratification set up, any algae (chlorophyll,
  phycocyanin) layer, dissolved oxygen at depth.

**Checkpoint:** the findings read clearly and each has evidence.

### Phase 4: The map panel

- Generator `analysis/build_profile_json.py` writes `map/strontia-profile.json`: the
  gridded parameters (compact: rounded values, nulls for gaps), the time and depth axes,
  the storm window, and a terms/attribution field. Keep it small enough to load fast
  (target under 2 MB; downsample the full season if needed).
- In the copied HTML, add a panel for the `dam-strontia` item, following the existing
  `influent: true` / `renderInfluent()` pattern: a `profile: true` flag and a
  `renderProfile()` function drawing a canvas heatmap. Plan:
  - parameter toggle (temperature, turbidity, conductivity, dissolved oxygen, chlorophyll)
  - full season and storm zoom
  - hover readout (time, depth, value)
  - a few sentences of findings from `FINDINGS.md`
  - caveat: provisional readings, one season, and the unknown intake depth
- Match the page's existing style and plain-language tone. Check it works at phone width.
- Add the `profile` flag to the copied page's data. Don't regenerate `system.json`. Either
  set the flag in the page code by item id, or load a small override. Choose the smaller
  change.

**Checkpoint:** demo the panel in the browser.

### Phase 5 (side track): Autoresearch loop for the fill-in method

Start after Phase 2 works, run in the background, and swap into the map only if it wins.
- **Locked harness** (agent may not edit): `autoresearch/prepare.py` builds fixed
  held-out sets from `sonde_clean.csv` by hiding **contiguous time blocks** (e.g. 6-hour
  windows), not scattered single readings. Neighboring readings are nearly identical, so
  random holdout would flatter every method. Split the hidden blocks into **dev** (the
  loop sees its score) and a **lockbox** (scored once, at the end).
  `autoresearch/evaluate.py` prints one number: RMSE on dev blocks, normalized per
  parameter (divide by each parameter's standard deviation) and averaged.
- **Agent edits only** `autoresearch/interpolate.py`: given the clean readings minus the
  hidden blocks, return values at requested (time, depth) points.
- **Loop:** try a change, run evaluate (budget: about 60 seconds per experiment), keep if
  better, else revert; log every attempt to `autoresearch/results.tsv`. A human edits
  `autoresearch/program.md` (the agent's instructions), not the harness.
- **Baseline** to beat: the Phase 2 linear method.
- **Guardrails:** no reading of lockbox blocks; flag any result that beats the baseline by
  an implausible margin for a leakage check; prefer simpler methods at equal scores.
- **Done:** report dev and lockbox scores for baseline vs best. Use the winner in Phase 4
  only if it also wins on the lockbox and its picture looks physically sensible.
- Scale: one agent looping, maybe a second exploring a different method family. No swarm.

### Phase 6: Wrap up

- `teams/team-tbd/README.md`: what this is, how to regenerate everything (commands in
  order), how to view the map copy, data terms, the findings summary.
- List of open questions for Denver Water (below), updated with anything learned.
- Nothing is committed or pushed unless Miles asks.

## Questions for Denver Water (Cassidi or Jake)

1. What is the Foothills intake depth (or elevation) in Strontia Springs? It decides which
   layer matters.
2. Is `Vertical Position` depth below the surface? Where is the sonde, relative to the dam
   and intake?
3. What do you already do with the sonde data, so we build on it rather than repeat it?
4. How soon after sampling are Foothills lab results available? (Relevant to the
   persistence baseline finding.)
5. How far back do Foothills TOC and alkalinity lab records go?

## Definition of done

- Copied map with a working Strontia depth panel, runnable with `python3 serve.py`.
- `FINDINGS.md` with evidence-backed storm and season findings.
- All derived data regenerable from scripts in `teams/team-tbd/`, with the data terms alongside.
- Originals untouched (`git status` shows changes only under `teams/`).
