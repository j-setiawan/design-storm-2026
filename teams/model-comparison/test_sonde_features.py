"""
Tests Cassidi's starred question (README.md / the kickoff deck): does the
Strontia profiling sonde -- much closer to the Foothills intake than the
upstream sentinel gage -- sharpen TOC/alkalinity accuracy, at the cost of
lead time? Jake's models never use this data at all.

Honest comparison: the sonde only covers 104 days (Apr-Aug 2026), a fraction
of the gage record, so the baseline here is the *existing* gage-only model
re-scored on that same 104-day window -- not the headline numbers from
guide.md, which are scored on ~10x more data. Otherwise a "sonde helps" result
could just be an artifact of a different, smaller sample.

Run from the repository root: python teams/model-comparison/test_sonde_features.py
"""
import sys
import os

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, root_mean_squared_error
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit, train_test_split

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model_comparison import build_toc_dataset, build_alk_dataset

SONDE_CSV = "teams/model-comparison/sonde_daily.csv"
LAGS_TO_TRY = [0, 1, 2, 3, 4]
RF_PARAM_GRID = {
    "n_estimators": [100, 200], "max_depth": [3, 5, 7],
    "min_samples_leaf": [5, 10, 20], "max_features": [1.0, "sqrt"],
}


def load_sonde():
    df = pd.read_csv(SONDE_CSV)
    df["DATE"] = pd.to_datetime(df["DATE"])
    return df.set_index("DATE").sort_index()


def score_rf(X_train, y_train, X_test, y_test, weights):
    search = GridSearchCV(RandomForestRegressor(random_state=42), RF_PARAM_GRID,
                           cv=TimeSeriesSplit(n_splits=5), n_jobs=-1)
    search.fit(X_train, y_train, sample_weight=weights)
    preds = search.best_estimator_.predict(X_test)
    return r2_score(y_test, preds), root_mean_squared_error(y_test, preds)


def run_test(name, X, y, weight_condition, sonde):
    print(f"\n{name}: gage-only baseline vs. +sonde, at various sonde lags (same window each time)")
    for lag in LAGS_TO_TRY:
        sonde_lagged = sonde.shift(lag, freq="D")
        combined = X.join(sonde_lagged, how="left").join(y.rename("target")).dropna()
        if len(combined) < 40:
            print(f"  lag={lag}d: too few overlapping rows ({len(combined)}), skipping")
            continue

        base_cols = list(X.columns)
        sonde_cols = list(sonde.columns)
        y_sub = combined["target"]
        # Small sample (~60-100 rows): use a 60/40 split so there's enough to train on.
        X_train, X_test, y_train, y_test = train_test_split(combined, y_sub, test_size=0.4, shuffle=False)
        weights = np.where(weight_condition(y_train), 1.5, 1.0)

        base_r2, base_rmse = score_rf(X_train[base_cols], y_train, X_test[base_cols], y_test, weights)
        full_r2, full_rmse = score_rf(X_train[base_cols + sonde_cols], y_train,
                                       X_test[base_cols + sonde_cols], y_test, weights)
        print(f"  lag={lag}d ({len(combined)} rows, {len(y_test)} test): "
              f"gage-only R2={base_r2:.3f} RMSE={base_rmse:.3f}  "
              f"+sonde R2={full_r2:.3f} RMSE={full_rmse:.3f}  delta R2={full_r2 - base_r2:+.3f}")


if __name__ == "__main__":
    sonde = load_sonde()
    print(f"Sonde data: {sonde.index.min().date()} to {sonde.index.max().date()}, {len(sonde)} days")

    toc_X, toc_y = build_toc_dataset()
    run_test("TOC", toc_X, toc_y, weight_condition=lambda y: y > 4.0, sonde=sonde)

    alk_X, alk_y = build_alk_dataset()
    run_test("Alkalinity", alk_X, alk_y, weight_condition=lambda y: y < 60.0, sonde=sonde)
