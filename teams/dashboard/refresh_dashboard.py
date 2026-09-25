"""
One-command refresh for everything the prediction dashboard needs.

Runs, in the required order, from the repository root:
  1. teams/dashboard/process_sonde_data.py
       data/Strontia *.xlsx -> teams/dashboard/sonde_daily.csv
  2. teams/dashboard/build_foothills_prediction.py
       -> teams/dashboard/foothills-prediction.json
  3. teams/dashboard/build_dashboard_extra.py
       -> teams/dashboard/dashboard-extra.json (needs sonde_daily.csv from
          step 1; imports build_toc_dataset/build_alk_dataset from
          teams/dashboard/model_comparison.py)

Order matters: step 3 reads the CSV step 1 writes, so 1 must run before 3.
Step 2 is independent of 1 and 3 but is listed first for a single clear
top-to-bottom read of "what feeds the dashboard."

This does NOT re-run teams/dashboard/fetch_reservoir_ops_history.py.
That script scrapes ~1,300 individual pages from a non-API public page and
is already run to completion -- see HANDOFF.md. Re-run it manually, and only
to extend the date range, never as part of a routine refresh.

Then open prediction-dashboard.html (or the map's dashboard overlay button)
and reload -- both files it reads (dashboard-extra.json,
foothills-prediction.json) will now be current.
"""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

STEPS = [
    ("Processing sonde depth profiles into daily aggregates",
     "teams/dashboard/process_sonde_data.py"),
    ("Building` Foothills TOC/alkalinity backtest",
     "teams/dashboard/build_foothills_prediction.py"),
    ("Building dashboard extras (sonde series, depth profile, reservoir snapshot, lag test)",
     "teams/dashboard/build_dashboard_extra.py"),
]


def run_step(description: str, relative_script_path: str) -> None:
    script = REPO_ROOT / relative_script_path
    if not script.exists():
        print(f"ERROR: expected script not found: {relative_script_path}", file=sys.stderr)
        sys.exit(1)

    print(f"\n== {description} ==")
    print(f"$ python {relative_script_path}")
    result = subprocess.run([sys.executable, str(script)], cwd=REPO_ROOT)
    if result.returncode != 0:
        print(f"\nERROR: {relative_script_path} failed (exit code {result.returncode}). "
              f"Stopping -- later steps may depend on its output.", file=sys.stderr)
        sys.exit(result.returncode)


if __name__ == "__main__":
    for description, relative_script_path in STEPS:
        run_step(description, relative_script_path)
    print("\nAll dashboard data refreshed. Reload prediction-dashboard.html to see the changes.")
