"""
Tests whether upstream reservoir inflow/outflow (Antero, Eleven Mile, Cheesman,
Dillon -- from teams/model-comparison/reservoir_ops_history.json) adds any
predictive signal on top of the existing TOC/alkalinity soft sensor, at a
range of lag times longer than Jake's 2-4 days.

Honest framing (see conversation): this data has no water-quality readings,
only flow/storage, so it can only test a "timing/magnitude" hypothesis, not a
composition one. Compares like-for-like: baseline-only vs. baseline+upstream
features, on the exact same rows (same date range) for each lag, so the
comparison isn't biased by a shrinking sample.

Run from the repository root: python teams/model-comparison/test_upstream_reservoir_features.py
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, root_mean_squared_error
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model_comparison import build_toc_dataset, build_alk_dataset

RESERVOIRS = ["Antero", "Eleven Mile", "Cheesman", "Dillon"]
LAGS_TO_TRY = [2, 4, 6, 8, 10, 12, 14]

RF_PARAM_GRID = {
    "n_estimators": [100, 200], "max_depth": [3, 5, 7],
    "min_samples_leaf": [5, 10, 20], "max_features": [1.0, "sqrt"],
}
SVR_PARAM_GRID = {"kernel": ["rbf", "linear"], "C": [1, 10, 100], "epsilon": [0.1, 0.01]}


def load_reservoir_ops():
    with open("teams/model-comparison/reservoir_ops_history.json") as f:
        raw = json.load(f)
    rows = []
    for day, reservoirs in raw.items():
        row = {"DATE": day}
        for name in RESERVOIRS:
            r = reservoirs.get(name, {})
            col = name.replace(" ", "")
            row[f"{col}_inflow"] = r.get("inflow_cfs")
            row[f"{col}_outflow"] = r.get("outflow_cfs")
            row[f"{col}_storage"] = r.get("storage_af")
        rows.append(row)
    df = pd.DataFrame(rows)
    df["DATE"] = pd.to_datetime(df["DATE"])
    return df.set_index("DATE").sort_index()


def score_svr(X_train, y_train, X_test, y_test, weights):
    scaler = StandardScaler().fit(X_train)
    search = GridSearchCV(SVR(), SVR_PARAM_GRID, cv=TimeSeriesSplit(n_splits=5), n_jobs=-1)
    search.fit(scaler.transform(X_train), y_train, sample_weight=weights)
    preds = search.best_estimator_.predict(scaler.transform(X_test))
    return r2_score(y_test, preds), root_mean_squared_error(y_test, preds)


def score_rf(X_train, y_train, X_test, y_test, weights):
    search = GridSearchCV(RandomForestRegressor(random_state=42), RF_PARAM_GRID, cv=TimeSeriesSplit(n_splits=5), n_jobs=-1)
    search.fit(X_train, y_train, sample_weight=weights)
    preds = search.best_estimator_.predict(X_test)
    return r2_score(y_test, preds), root_mean_squared_error(y_test, preds)


def run_test(name, X, y, test_size, weight_condition, scorer, ops):
    print(f"\n{name}: testing upstream reservoir lags")
    results = []
    for lag in LAGS_TO_TRY:
        ops_lagged = ops.shift(lag, freq="D")
        combined = X.join(ops_lagged, how="left")
        joined = combined.join(y.rename("target"))
        joined = joined.dropna()
        if len(joined) < 100:
            print(f"  lag={lag}d: too few overlapping rows ({len(joined)}), skipping")
            continue

        base_cols = list(X.columns)
        ops_cols = list(ops.columns)
        y_sub = joined["target"]

        X_train, X_test, y_train, y_test = train_test_split(joined, y_sub, test_size=test_size, shuffle=False)
        weights = np.where(weight_condition(y_train), 1.5, 1.0)

        base_r2, base_rmse = scorer(X_train[base_cols], y_train, X_test[base_cols], y_test, weights)
        full_r2, full_rmse = scorer(X_train[base_cols + ops_cols], y_train, X_test[base_cols + ops_cols], y_test, weights)

        print(f"  lag={lag:>2}d ({len(joined)} rows): baseline R2={base_r2:.3f} RMSE={base_rmse:.3f}  "
              f"+upstream R2={full_r2:.3f} RMSE={full_rmse:.3f}  delta R2={full_r2 - base_r2:+.3f}")
        results.append({"lag": lag, "rows": len(joined), "base_r2": base_r2, "full_r2": full_r2})
    return results


if __name__ == "__main__":
    ops = load_reservoir_ops()
    print(f"Reservoir ops data: {ops.index.min().date()} to {ops.index.max().date()}, {len(ops)} days")

    toc_X, toc_y = build_toc_dataset()
    run_test("TOC", toc_X, toc_y, test_size=0.5, weight_condition=lambda y: y > 4.0, scorer=score_svr, ops=ops)

    alk_X, alk_y = build_alk_dataset()
    run_test("Alkalinity", alk_X, alk_y, test_size=0.45, weight_condition=lambda y: y < 60.0, scorer=score_rf, ops=ops)
