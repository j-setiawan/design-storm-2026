"""Evaluate actual-versus-predicted TOC and alkalinity in a prediction CSV."""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


TARGET_PAIRS = {
    "TOC (mg/L)": ("toc", "predicted_toc"),
    "Alkalinity (mg/L)": ("alkalinity", "predicted_alkalinity"),
}
CLASS_COLUMNS = ("treatment_percent", "predicted_treatment_percent")


def evaluate(path):
    """Print and return regression metrics for each available actual/predicted pair."""
    path = Path(path)
    table = pd.read_csv(path)
    reports = {}
    print(f"File: {path}")
    for label, (actual_col, predicted_col) in TARGET_PAIRS.items():
        missing = [c for c in (actual_col, predicted_col) if c not in table.columns]
        if missing:
            print(f"\n{label}: skipped; missing column(s): {', '.join(missing)}")
            continue

        paired = table[[actual_col, predicted_col]].apply(pd.to_numeric, errors="coerce").dropna()
        if len(paired) < 2:
            print(f"\n{label}: skipped; need at least two complete actual/predicted rows (found {len(paired)}).")
            continue

        actual = paired[actual_col].to_numpy()
        predicted = paired[predicted_col].to_numpy()
        # Fit actual = slope * predicted + intercept, matching the common
        # calibration plot convention (actual on y-axis, prediction on x-axis).
        slope, intercept = np.polyfit(predicted, actual, 1)
        metrics = {
            "n": len(paired),
            "MAE": mean_absolute_error(actual, predicted),
            "RMSE": mean_squared_error(actual, predicted) ** 0.5,
            "R_squared": r2_score(actual, predicted),
            "actual_vs_prediction_slope": slope,
            "actual_vs_prediction_intercept": intercept,
        }
        reports[label] = metrics
        print(f"\n{label} (n={metrics['n']}):")
        print(f"  MAE: {metrics['MAE']:.4f}")
        print(f"  RMSE: {metrics['RMSE']:.4f}")
        print(f"  R squared: {metrics['R_squared']:.4f}")
        print(f"  Slope (actual vs prediction): {metrics['actual_vs_prediction_slope']:.4f}")
        print(f"  Intercept (actual vs prediction): {metrics['actual_vs_prediction_intercept']:.4f}")

    actual_class_col, predicted_class_col = CLASS_COLUMNS
    missing_classes = [c for c in CLASS_COLUMNS if c not in table.columns]
    if missing_classes:
        print(f"\nTreatment class agreement: skipped; missing column(s): {', '.join(missing_classes)}")
    else:
        classes = table[list(CLASS_COLUMNS)].apply(pd.to_numeric, errors="coerce").dropna()
        if classes.empty:
            print("\nTreatment class agreement: skipped; no rows have both classes defined.")
        else:
            matches = classes[actual_class_col] == classes[predicted_class_col]
            count = int(matches.sum())
            percent = 100 * count / len(classes)
            reports["Treatment class exact agreement"] = {
                "n": len(classes), "matches": count, "percent": percent,
            }
            print(f"\nTreatment class exact agreement: {count}/{len(classes)} ({percent:.2f}%)")

    if not reports:
        raise ValueError("No actual/predicted column pairs could be evaluated in this file.")
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", help="prediction CSV, e.g. teams/team-tbd/august_predictions.csv")
    args = parser.parse_args()
    evaluate(args.csv_file)


if __name__ == "__main__":
    main()
