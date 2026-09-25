"""
Stage 1 of the two-stage idea: can we predict flow at the DWR gage near
Strontia 8 days out, using Antero Reservoir release (the one upstream signal
that showed a genuine multi-day lead, not just same-day operational sync --
see the correlation test in conversation) plus snowpack and precipitation?

Compares three things honestly:
  - naive persistence (today's flow = flow 8 days ago) -- the bar any real
    model has to clear, since river flow is highly autocorrelated on its own
  - linear regression on Antero release + SWE + precip
  - random forest on the same features

Run from the repository root: python teams/model-comparison/test_upstream_flow_prediction.py
"""
import json

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, root_mean_squared_error
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit, train_test_split

LAG_DAYS = 8
RF_PARAM_GRID = {
    "n_estimators": [100, 200], "max_depth": [3, 5, 7],
    "min_samples_leaf": [5, 10, 20], "max_features": [1.0, "sqrt"],
}


def load_antero_outflow():
    with open("teams/model-comparison/reservoir_ops_history.json") as f:
        raw = json.load(f)
    rows = [{"DATE": day, "Antero_outflow": r.get("Antero", {}).get("outflow_cfs")} for day, r in raw.items()]
    df = pd.DataFrame(rows)
    df["DATE"] = pd.to_datetime(df["DATE"])
    return df.set_index("DATE").sort_index()


def build_dataset():
    dwr = pd.read_csv("data/SouthPlatteTelemetry.csv")
    dwr["DATE"] = pd.to_datetime(dwr["Date"])
    dwr = dwr.set_index("DATE")[["Flow_CFS"]]

    sntl = pd.read_csv("data/HoosierPass.csv")
    sntl["DATE"] = pd.to_datetime(sntl["DATE"])
    sntl = sntl.set_index("DATE")

    precip = pd.read_csv("data/USC00058022.csv")
    precip["DATE"] = pd.to_datetime(precip["DATE"])
    precip = precip.set_index("DATE")

    antero = load_antero_outflow()

    combined = dwr.join(antero.shift(LAG_DAYS, freq="D"), how="left")
    combined = combined.join(sntl.shift(LAG_DAYS, freq="D"), how="left")
    combined = combined.join(precip.shift(LAG_DAYS, freq="D"), how="left")

    combined["antero_3day"] = combined["Antero_outflow"].rolling(3).mean()
    combined["swe_7day"] = combined["SWE"].rolling(7).mean()
    combined["precip_7day"] = combined["PRCP"].rolling(7).mean()
    month_radians = 2 * np.pi * (combined.index.month - 1) / 12
    combined["month_sin"] = np.sin(month_radians)
    combined["month_cos"] = np.cos(month_radians)

    # Naive persistence baseline: flow LAG_DAYS ago, no other information.
    combined["flow_persistence"] = combined["Flow_CFS"].shift(LAG_DAYS, freq="D")

    features = ["antero_3day", "swe_7day", "precip_7day", "month_sin", "month_cos", "flow_persistence"]
    df = combined[features + ["Flow_CFS"]].dropna()
    return df[features], df["Flow_CFS"]


if __name__ == "__main__":
    X, y = build_dataset()
    print(f"{len(X)} rows with all features available")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.45, shuffle=False)

    # Naive persistence: predict using only the flow_persistence column.
    persist_preds = X_test["flow_persistence"]
    print(f"\nNaive persistence (flow {LAG_DAYS}d ago): "
          f"R2={r2_score(y_test, persist_preds):.3f} RMSE={root_mean_squared_error(y_test, persist_preds):.1f}")

    # Linear regression on all features (includes persistence as one input).
    lin = LinearRegression().fit(X_train, y_train)
    lin_preds = lin.predict(X_test)
    print(f"Linear (all features):            "
          f"R2={r2_score(y_test, lin_preds):.3f} RMSE={root_mean_squared_error(y_test, lin_preds):.1f}")

    # Random forest, grid-searched.
    search = GridSearchCV(RandomForestRegressor(random_state=42), RF_PARAM_GRID,
                           cv=TimeSeriesSplit(n_splits=5), n_jobs=-1)
    search.fit(X_train, y_train)
    rf_preds = search.best_estimator_.predict(X_test)
    print(f"Random forest (grid search):      "
          f"R2={r2_score(y_test, rf_preds):.3f} RMSE={root_mean_squared_error(y_test, rf_preds):.1f}")

    importance = pd.Series(search.best_estimator_.feature_importances_, index=X.columns).sort_values(ascending=False)
    print("\nFeature importance:")
    print(importance)

    # --- Residual framing: model only what persistence gets wrong. ---
    print("\n--- Modeling the residual (actual - persistence) instead ---")
    resid_features = ["antero_3day", "swe_7day", "precip_7day", "month_sin", "month_cos"]
    resid_y = y - X["flow_persistence"]
    Xr_train, Xr_test, yr_train, yr_test = train_test_split(
        X[resid_features], resid_y, test_size=0.45, shuffle=False)

    resid_search = GridSearchCV(RandomForestRegressor(random_state=42), RF_PARAM_GRID,
                                 cv=TimeSeriesSplit(n_splits=5), n_jobs=-1)
    resid_search.fit(Xr_train, yr_train)
    resid_preds = resid_search.best_estimator_.predict(Xr_test)
    final_preds = X_test["flow_persistence"] + resid_preds
    print(f"Persistence + RF-predicted residual: "
          f"R2={r2_score(y_test, final_preds):.3f} RMSE={root_mean_squared_error(y_test, final_preds):.1f}")

    resid_importance = pd.Series(resid_search.best_estimator_.feature_importances_,
                                  index=resid_features).sort_values(ascending=False)
    print("\nResidual model feature importance:")
    print(resid_importance)
