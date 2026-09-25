"""SVM regression for Foothills TOC/alkalinity and derived treatment classes."""
import argparse
import calendar
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             mean_absolute_error, mean_squared_error, r2_score)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR

ROOT = Path(__file__).resolve().parents[2]
SONDE_PATH = ROOT / "data" / "Strontia 0407_0819.csv"
FOOTHILLS_PATH = ROOT / "data" / "FoothillsInfluent.csv"
FEATURES = ["Temp C", "Conductivity", "Vertical Position", "pH", "ORP mV",
            "Turbidity NTU", "Chl ug/L", "Phycocyanin", "ODO & sat", "ODO mg/L"]


def treatment_percent(toc, alkalinity):
    """Apply user-defined TOC/alkalinity treatment bands; TOC <=2 is unassigned."""
    if pd.isna(toc) or pd.isna(alkalinity) or toc <= 2 or alkalinity < 0:
        return np.nan
    toc_band = 0 if toc > 8 else 1 if toc > 4 else 2
    alk_band = 0 if alkalinity <= 60 else 1 if alkalinity <= 120 else 2
    return [[50, 40, 30], [45, 35, 25], [35, 25, 15]][toc_band][alk_band]


def prepare_strontia(path=SONDE_PATH):
    """Create one fixed-width date vector retaining all readings and features."""
    sonde = pd.read_csv(path)
    sonde.columns = sonde.columns.str.strip()
    sonde["timestamp"] = pd.to_datetime(sonde["Time stamp"], errors="coerce")
    sonde["date"] = sonde["timestamp"].dt.normalize()
    for feature in FEATURES:
        sonde[feature] = pd.to_numeric(sonde[feature], errors="coerce")
    sonde = sonde.dropna(subset=["date", "Vertical Position"])
    sonde = sonde.sort_values(["date", "timestamp", "Vertical Position"], ascending=[True, True, False])
    depth_slots = int(sonde.groupby("date").size().max())
    rows = []
    for day, group in sonde.groupby("date", sort=True):
        values = group[FEATURES].to_numpy(dtype=float).reshape(-1)
        values = np.pad(values, (0, depth_slots * len(FEATURES) - len(values)), constant_values=np.nan)
        row = {f"{feature}__reading_{slot + 1:03d}": values[slot * len(FEATURES) + j]
               for slot in range(depth_slots) for j, feature in enumerate(FEATURES)}
        row["date"] = day
        rows.append(row)
    return pd.DataFrame(rows)


def build_paired_table(sonde_path=SONDE_PATH, foothills_path=FOOTHILLS_PATH, date_lag_days=0):
    """Pair Strontia profile date D with Foothills lab date D + date_lag_days."""
    inputs = prepare_strontia(sonde_path)
    labs = pd.read_csv(foothills_path, parse_dates=["DATE"])
    labs["date"] = labs["DATE"].dt.normalize()
    labs["treatment_percent"] = [
        treatment_percent(t, a) for t, a in zip(labs["TOC_mg_L"], labs["Alk_mg_L"])
    ]
    inputs["date"] += pd.to_timedelta(date_lag_days, unit="D")
    return inputs.merge(labs[["date", "TOC_mg_L", "Alk_mg_L", "treatment_percent"]],
                        on="date", how="inner", validate="one_to_one")


def run_month(end_month=7, year=2026, date_lag_days=0, c_value=1.0, gamma="scale",
              output_path=None):
    """Train on April through end_month, then classify paired rows in next month."""
    if not 4 <= end_month <= 11:
        raise ValueError("end_month must be between 4 and 11")
    train_end = pd.Timestamp(date(year, end_month, calendar.monthrange(year, end_month)[1]))
    predict_month = end_month + 1
    test_start = pd.Timestamp(date(year, predict_month, 1))
    test_end = pd.Timestamp(date(year, predict_month, calendar.monthrange(year, predict_month)[1]))

    paired = build_paired_table(date_lag_days=date_lag_days)
    excluded = {"date", "TOC_mg_L", "Alk_mg_L", "treatment_percent"}
    predictors = [c for c in paired.columns if c not in excluded]
    train = paired[paired.date.between(pd.Timestamp(year, 4, 1), train_end)].copy()
    train = train.dropna(subset=["TOC_mg_L", "Alk_mg_L"])
    test = paired[paired.date.between(test_start, test_end)].copy()
    print(f"Paired dates: {len(paired)}; complete training rows: {len(train)}; test dates: {len(test)}")
    print(f"Pairing: Foothills date = Strontia date + {date_lag_days} days")
    print(f"Training through {train_end.date()}; testing {test_start.date()} through {test_end.date()}")
    if train.empty or test.empty:
        print("Cannot fit or predict: training or test window has no paired rows.")
        return pd.DataFrame()

    result = test[["date", "TOC_mg_L", "Alk_mg_L", "treatment_percent"]].copy()
    result["toc"] = result["TOC_mg_L"]
    result["alkalinity"] = result["Alk_mg_L"]
    for target_col, prediction_col in (("TOC_mg_L", "predicted_toc"),
                                       ("Alk_mg_L", "predicted_alkalinity")):
        train_target = train.dropna(subset=[target_col])
        regression = make_pipeline(
            SimpleImputer(strategy="median"),
            StandardScaler(),
            SVR(C=c_value, gamma=gamma, kernel="rbf"),
        )
        regression.fit(train_target[predictors], train_target[target_col])
        result[prediction_col] = regression.predict(test[predictors])

    result["predicted_treatment_percent"] = [
        treatment_percent(t, a) for t, a in zip(result.predicted_toc, result.predicted_alkalinity)
    ]
    result["predicted_alkalinity_mg_L"] = result["predicted_alkalinity"]
    result["toc_absolute_error"] = (result.predicted_toc - result.TOC_mg_L).abs()
    result["alkalinity_absolute_error"] = (result.predicted_alkalinity - result.Alk_mg_L).abs()

    known = result.treatment_percent.notna() & result.predicted_treatment_percent.notna()
    if known.any():
        actual = result.loc[known, "treatment_percent"].astype(int)
        predicted = result.loc[known, "predicted_treatment_percent"].astype(int)
        labels = sorted(set(actual) | set(predicted))
        print(f"Treatment-class exact agreement: {int((actual == predicted).sum())}/{len(actual)} "
              f"({accuracy_score(actual, predicted):.1%})")
        print("Confusion matrix (rows=actual, columns=predicted; order " + str(labels) + "):")
        print(confusion_matrix(actual, predicted, labels=labels))
        print(classification_report(actual, predicted, labels=labels, zero_division=0))
    else:
        print("No defined actual treatment classes in test period; agreement cannot be scored.")

    for label, actual_col, predicted_col in (("TOC", "TOC_mg_L", "predicted_toc"),
                                             ("Alkalinity", "Alk_mg_L", "predicted_alkalinity")):
        valid = result[actual_col].notna()
        if valid.any():
            actual_values = result.loc[valid, actual_col]
            predicted_values = result.loc[valid, predicted_col]
            print(f"{label} SVR metrics (mg/L): "
                  f"MAE={mean_absolute_error(actual_values, predicted_values):.3f}, "
                  f"RMSE={mean_squared_error(actual_values, predicted_values) ** 0.5:.3f}, "
                  f"R2={r2_score(actual_values, predicted_values):.3f}")

    if output_path is None:
        output_path = ROOT / "teams" / "team-tbd" / f"svm_{calendar.month_name[predict_month].lower()}_predictions.csv"
    result.to_csv(output_path, index=False)
    print(f"Predictions written to {output_path}")
    print(result.to_string(index=False))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--end-month", type=int, default=7,
                        help="last training month (4=April through 11=November); default 7 predicts August")
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--date-lag-days", type=int, default=0,
                        help="pair Strontia date D with Foothills date D + this many days")
    parser.add_argument("--c", type=float, default=1.0, help="SVM regularization parameter C")
    parser.add_argument("--gamma", default="scale", help="RBF kernel gamma: scale, auto, or numeric value")
    args = parser.parse_args()
    gamma = args.gamma if args.gamma in {"scale", "auto"} else float(args.gamma)
    run_month(args.end_month, args.year, args.date_lag_days, args.c, gamma)


if __name__ == "__main__":
    main()
