"""Decision-tree classification of user-defined Foothills treatment classes."""
import argparse
import calendar
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.pipeline import make_pipeline
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parents[2]
SONDE_PATH = ROOT / "data" / "Strontia 0407_0819.csv"
FOOTHILLS_PATH = ROOT / "data" / "FoothillsInfluent.csv"
FEATURES = ["Temp C", "Conductivity", "Vertical Position", "pH", "ORP mV",
            "Turbidity NTU", "Chl ug/L", "Phycocyanin", "ODO & sat", "ODO mg/L"]


def treatment_percent(toc, alkalinity):
    """Map the user's TOC/alkalinity bands to a class; leave TOC <= 2 unassigned."""
    if pd.isna(toc) or pd.isna(alkalinity) or toc <= 2 or alkalinity < 0:
        return np.nan
    toc_band = 0 if toc > 8 else 1 if toc > 4 else 2
    alk_band = 0 if alkalinity <= 60 else 1 if alkalinity <= 120 else 2
    return [[50, 40, 30], [45, 35, 25], [35, 25, 15]][toc_band][alk_band]


def prepare_strontia(path=SONDE_PATH):
    """Create a fixed-width daily vector retaining every reading and sensor dimension."""
    sonde = pd.read_csv(path)
    sonde.columns = sonde.columns.str.strip()
    sonde["timestamp"] = pd.to_datetime(sonde["Time stamp"], errors="coerce")
    sonde["date"] = sonde["timestamp"].dt.normalize()
    for feature in FEATURES:
        sonde[feature] = pd.to_numeric(sonde[feature], errors="coerce")
    sonde = sonde.dropna(subset=["date", "Vertical Position"])
    sonde = sonde.sort_values(["date", "timestamp", "Vertical Position"], ascending=[True, True, False])
    slots = int(sonde.groupby("date").size().max())
    rows = []
    for day, group in sonde.groupby("date", sort=True):
        values = group[FEATURES].to_numpy(dtype=float).reshape(-1)
        values = np.pad(values, (0, slots * len(FEATURES) - len(values)), constant_values=np.nan)
        row = {f"{feature}__reading_{slot + 1:03d}": values[slot * len(FEATURES) + j]
               for slot in range(slots) for j, feature in enumerate(FEATURES)}
        row["date"] = day
        rows.append(row)
    return pd.DataFrame(rows)


def build_paired_table(sonde_path=SONDE_PATH, foothills_path=FOOTHILLS_PATH, date_lag_days=0):
    """Inner join daily Strontia vectors with same-date Foothills observations."""
    inputs = prepare_strontia(sonde_path)
    labs = pd.read_csv(foothills_path, parse_dates=["DATE"])
    labs["date"] = labs["DATE"].dt.normalize()
    labs["treatment_percent"] = [treatment_percent(t, a) for t, a in zip(labs["TOC_mg_L"], labs["Alk_mg_L"])]
    inputs["date"] = inputs["date"] + pd.to_timedelta(date_lag_days, unit="D")
    return inputs.merge(labs[["date", "TOC_mg_L", "Alk_mg_L", "treatment_percent"]],
                        on="date", how="inner", validate="one_to_one")


def run_month(end_month, year=2026, max_depth=None, min_samples_leaf=2, output_path=None, date_lag_days=0):
    """Fit through end_month, then classify the next month's date-paired rows."""
    if not 4 <= end_month <= 11:
        raise ValueError("end_month must be between 4 and 11")
    train_end = pd.Timestamp(date(year, end_month, calendar.monthrange(year, end_month)[1]))
    predict_month = end_month + 1
    test_start = pd.Timestamp(date(year, predict_month, 1))
    test_end = pd.Timestamp(date(year, predict_month, calendar.monthrange(year, predict_month)[1]))

    paired = build_paired_table(date_lag_days=date_lag_days)
    feature_cols = [c for c in paired.columns if c not in
                    {"date", "TOC_mg_L", "Alk_mg_L", "treatment_percent"}]
    eligible = paired.dropna(subset=["treatment_percent"]).copy()
    train = eligible[eligible.date.between(pd.Timestamp(year, 4, 1), train_end)]
    test = paired[paired.date.between(test_start, test_end)].copy()
    print(f"Paired dates: {len(paired)}; train rows with defined class: {len(train)}; test dates: {len(test)}")
    print(f"Training: {year}-04-01 through {train_end.date()}; prediction: {test_start.date()} through {test_end.date()}")
    print(f"Pairing: Foothills date = Strontia date + {date_lag_days} days")
    if train.empty or test.empty:
        print("No model fit or predictions: training or test window has no paired rows.")
        return pd.DataFrame()

    model = make_pipeline(
        SimpleImputer(strategy="median"),
        DecisionTreeClassifier(max_depth=max_depth, min_samples_leaf=min_samples_leaf,
                               class_weight="balanced", random_state=42),
    )
    model.fit(train[feature_cols], train["treatment_percent"].astype(int))
    result = test[["date", "TOC_mg_L", "Alk_mg_L", "treatment_percent"]].copy()
    result["predicted_treatment_percent"] = model.predict(test[feature_cols]).astype(int)
    known = result.treatment_percent.notna()
    if known.any():
        actual = result.loc[known, "treatment_percent"].astype(int)
        predicted = result.loc[known, "predicted_treatment_percent"]
        print(f"Treatment-class exact agreement: {int((actual == predicted).sum())}/{len(actual)} "
              f"({accuracy_score(actual, predicted):.1%})")
        labels = sorted(set(actual) | set(predicted))
        print("Confusion matrix (rows=actual, columns=predicted; class order " + str(labels) + "):")
        print(confusion_matrix(actual, predicted, labels=labels))
        print(classification_report(actual, predicted, labels=labels, zero_division=0))
    else:
        print("Test dates have no defined actual classes, so agreement cannot be scored.")

    if output_path is None:
        output_path = ROOT / "teams" / "strontia-min-distance" / f"decision_tree_{calendar.month_name[predict_month].lower()}_predictions.csv"
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
                        help="pair Strontia date D with Foothills date D + this many days; default 0")
    parser.add_argument("--max-depth", type=int, default=None,
                        help="optional tree depth limit; default is unrestricted")
    parser.add_argument("--min-samples-leaf", type=int, default=2,
                        help="minimum training examples per leaf; default 2")
    args = parser.parse_args()
    run_month(args.end_month, args.year, args.max_depth, args.min_samples_leaf, date_lag_days=args.date_lag_days)


if __name__ == "__main__":
    main()
