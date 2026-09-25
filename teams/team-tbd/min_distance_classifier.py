"""Date-paired minimum-distance model: full Strontia profiles -> Foothills labs."""
from pathlib import Path
import argparse
import calendar
from datetime import date

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.impute import SimpleImputer
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
STRONTIA_PATH = ROOT / "data" / "Strontia 0407_0819.csv"
FOOTHILLS_PATH = ROOT / "data" / "FoothillsInfluent.csv"
FEATURES = ["Temp C", "Conductivity", "Vertical Position", "pH", "ORP mV",
            "Turbidity NTU", "Chl ug/L", "Phycocyanin", "ODO & sat", "ODO mg/L"]
TARGETS = ["toc", "alkalinity"]


def treatment_percent(toc, alkalinity):
    """User-specified treatment class; TOC <= 2 or negative alkalinity is unassigned."""
    if pd.isna(toc) or pd.isna(alkalinity) or toc <= 2 or alkalinity < 0:
        return np.nan
    i = 0 if toc > 8 else 1 if toc > 4 else 2
    j = 0 if alkalinity <= 60 else 1 if alkalinity <= 120 else 2
    return [[50, 40, 30], [45, 35, 25], [35, 25, 15]][i][j]


def prepare_strontia(path=STRONTIA_PATH):
    """Return one row/date, retaining all readings in ordered profile dimensions."""
    sonde = pd.read_csv(path)
    sonde.columns = sonde.columns.str.strip()
    sonde = sonde.rename(columns={"Time stamp": "timestamp"})
    sonde["timestamp"] = pd.to_datetime(sonde["timestamp"], errors="coerce")
    sonde["date"] = sonde["timestamp"].dt.normalize()
    for feature in FEATURES:
        sonde[feature] = pd.to_numeric(sonde[feature], errors="coerce")
    sonde = sonde.dropna(subset=["date", "Vertical Position"])
    sonde = sonde.sort_values(["date", "timestamp", "Vertical Position"], ascending=[True, True, False])

    # Fixed-width vectors: feature order is repeated at each depth slot. Shorter
    # profiles are padded with NaN and imputed from training data during fitting.
    depth_slots = int(sonde.groupby("date").size().max())
    vectors = []
    for date, group in sonde.groupby("date", sort=True):
        vals = group[FEATURES].to_numpy(dtype=float).reshape(-1)
        vals = np.pad(vals, (0, depth_slots * len(FEATURES) - len(vals)), constant_values=np.nan)
        row = {f"{feature}__reading_{slot + 1:03d}": vals[slot * len(FEATURES) + j]
               for slot in range(depth_slots) for j, feature in enumerate(FEATURES)}
        row["date"] = date
        vectors.append(row)
    return pd.DataFrame(vectors)


def build_paired_table(sonde_path=STRONTIA_PATH, foothills_path=FOOTHILLS_PATH, date_lag_days=0):
    """Inner-join full daily profiles and lab outputs by calendar date."""
    inputs = prepare_strontia(sonde_path)
    labs = pd.read_csv(foothills_path, parse_dates=["DATE"])
    labs["date"] = labs["DATE"].dt.normalize()
    labs = labs.rename(columns={"TOC_mg_L": "toc", "Alk_mg_L": "alkalinity"})
    labs["treatment_percent"] = [treatment_percent(t, a) for t, a in zip(labs.toc, labs.alkalinity)]
    inputs["date"] = inputs["date"] + pd.to_timedelta(date_lag_days, unit="D")
    return inputs.merge(labs[["date", *TARGETS, "treatment_percent"]], on="date", how="inner", validate="one_to_one")


def fit_min_distance(paired_rows, n_neighbors=3):
    """Fit standardized Euclidean KNN regression; returns model and input columns."""
    excluded = {"date", *TARGETS, "treatment_percent", "DATE"}
    predictors = [c for c in paired_rows.columns if c not in excluded]
    if not predictors:
        raise ValueError("No Strontia profile dimensions found")
    model = make_pipeline(
        SimpleImputer(strategy="median"), StandardScaler(),
        KNeighborsRegressor(n_neighbors=n_neighbors, weights="distance", metric="euclidean"),
    )
    model.fit(paired_rows[predictors], paired_rows[TARGETS])
    return model, predictors


def run_train_test(train_end="2026-06-30", test_start="2026-07-01", test_end="2026-07-31", output_path=None, date_lag_days=0):
    """Train through train_end; predict and score paired dates in the test window."""
    paired = build_paired_table(date_lag_days=date_lag_days)
    predictors = [c for c in paired if c not in {"date", *TARGETS, "treatment_percent"}]
    train = paired[paired.date <= pd.Timestamp(train_end)].copy()
    test = paired[paired.date.between(pd.Timestamp(test_start), pd.Timestamp(test_end))].copy()
    print(f"Paired dates available: {len(paired)} (Foothills date = Strontia date + {date_lag_days} days)")
    print(f"Training dates through {train_end}: {len(train)}")
    print(f"Test dates {test_start} through {test_end}: {len(test)}")
    print(f"Input dimensions per date: {len(predictors)}")
    if train.empty or test.empty:
        print("Cannot fit and predict: the training or test window has no date-paired rows.")
        return pd.DataFrame()

    model, predictors = fit_min_distance(train, n_neighbors=3)
    predicted = model.predict(test[predictors])
    result = test[["date", *TARGETS, "treatment_percent"]].copy()
    result["predicted_toc"] = predicted[:, 0]
    result["predicted_alkalinity"] = predicted[:, 1]
    result["predicted_treatment_percent"] = [
        treatment_percent(t, a) for t, a in zip(result.predicted_toc, result.predicted_alkalinity)
    ]
    result["toc_absolute_error"] = (result.predicted_toc - result.toc).abs()
    result["alkalinity_absolute_error"] = (result.predicted_alkalinity - result.alkalinity).abs()
    scored = result[TARGETS].notna().all(axis=1)
    if scored.any():
        print("Test metrics on dates with observed Foothills labels (mg/L):")
        for target, col in (("toc", "predicted_toc"), ("alkalinity", "predicted_alkalinity")):
            print(f"  {target}: MAE={mean_absolute_error(result.loc[scored, target], result.loc[scored, col]):.3f}, "
                  f"RMSE={mean_squared_error(result.loc[scored, target], result.loc[scored, col]) ** 0.5:.3f}, "
                  f"R2={r2_score(result.loc[scored, target], result.loc[scored, col]):.3f}")
    else:
        print("No test labels are available for scoring.")
    print(result.to_string(index=False))
    if output_path:
        result.to_csv(output_path, index=False)
        print(f"Predictions written to {output_path}")
    return result


def run_month(end_month, year=2026, output_path=None, date_lag_days=0):
    """Train April through end_month, then predict the immediately following month."""
    if not 4 <= end_month <= 11:
        raise ValueError("end_month must be between 4 and 11 so the following month is in the same year")
    month_end = calendar.monthrange(year, end_month)[1]
    train_end = date(year, end_month, month_end).isoformat()
    predict_month = end_month + 1
    test_start = date(year, predict_month, 1).isoformat()
    test_end = date(year, predict_month, calendar.monthrange(year, predict_month)[1]).isoformat()
    if output_path is None:
        output_path = ROOT / "teams" / "team-tbd" / f"{calendar.month_name[predict_month].lower()}_predictions.csv"
    print(f"Training starts 2026-04-01 and ends {train_end}; prediction month is {calendar.month_name[predict_month]} {year}.")
    return run_train_test(train_end, test_start, test_end, output_path, date_lag_days)


def main():
    parser = argparse.ArgumentParser(description="Train on April through a chosen month; predict the next month.")
    parser.add_argument("--end-month", type=int, default=6,
                        help="last training month (4=April through 11=November); default: 6 (train through June, predict July)")
    parser.add_argument("--year", type=int, default=2026, help="data year; default: 2026")
    parser.add_argument("--date-lag-days", type=int, default=0,
                        help="pair Strontia date D with Foothills date D + this many days; default 0")
    args = parser.parse_args()
    run_month(args.end_month, args.year, date_lag_days=args.date_lag_days)


if __name__ == "__main__":
    main()
