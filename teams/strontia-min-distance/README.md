# Date-paired Strontia to Foothills minimum-distance model

Each calendar date is one table row. Its input vector contains every Strontia depth reading that day, sorted by cast timestamp and vertical position, with the ten sensor measurements at each reading retained as separate dimensions. The same-date Foothills row supplies the outputs: TOC, alkalinity, and the treatment percentage derived from your rule.

The script both trains and classifies. By default it trains on paired dates in April through June 2026, predicts the paired July dates, prints predictions and holdout errors, and writes `teams/strontia-min-distance/july_predictions.csv`:

```powershell
python teams/strontia-min-distance/min_distance_classifier.py
```

Set the final training month with `--end-month`. To train on April through July and predict August:

```powershell
python teams/strontia-min-distance/min_distance_classifier.py --end-month 7
```

This writes `teams/strontia-min-distance/august_predictions.csv`. `--end-month 6` is the default (train April–June, predict July). Optionally choose another data year with `--year 2026`.

Both model scripts accept `--date-lag-days N`. This pairs a Strontia profile from date D with the Foothills row from D + N days; zero is same-date pairing. For example, add `--date-lag-days 2` to either command to pair each profile with the lab row two days later. The lag is applied before splitting into training and prediction months.

## Decision-tree treatment classifier

The separate tree script uses the same date-paired full-profile vectors and predicts the discrete treatment percentage directly from the user-defined Foothills classes. By default it trains on April through July and predicts August:

```powershell
python teams/strontia-min-distance/decision_tree_classifier.py --end-month 7
```

It reports exact class agreement, a confusion matrix, and per-class precision/recall, then writes `decision_tree_august_predictions.csv`. Change `--end-month` to predict the following month. `--max-depth` can limit tree complexity; `--min-samples-leaf` defaults to 2 to reduce one-row leaves. Given the short record and date-wise sample size, this is exploratory and should be compared using chronological holdouts.

## Support-vector machine treatment classifier

The SVM script uses the same full-profile daily input vectors and fits separate RBF support-vector regression models for TOC and alkalinity. It then derives the predicted treatment percentage from those two estimates using the stated bands. By default it trains April through July and predicts August:

```powershell
python teams/strontia-min-distance/svm_classifier.py --end-month 7
```

Use `--date-lag-days N` for shifted date pairing, and optionally tune `--c` and `--gamma`. Its CSV includes `toc`, `predicted_toc`, `alkalinity`, `predicted_alkalinity`, `treatment_percent`, and `predicted_treatment_percent`, so it can be passed directly to `evaluate_predictions.py`. It also prints regression metrics and exact class agreement. With so few paired dates and many profile dimensions, results are exploratory; tune parameters only on earlier chronological validation periods and preserve a later period for a final check.

## Evaluate a prediction file

Run the separate evaluator with the prediction CSV path you want to inspect:

```powershell
python teams/strontia-min-distance/evaluate_predictions.py teams/strontia-min-distance/august_predictions.csv
```

For TOC and alkalinity it reports MAE, RMSE, R squared, and the slope/intercept from the calibration line `actual = slope × prediction + intercept`. It also reports exact treatment-class agreement as matching rows / rows with both classes defined. It skips a target if its required actual/predicted columns are missing or fewer than two complete rows are available.

Daily profiles can contain different numbers of readings. The script uses the largest daily profile to define the vector width and pads shorter profiles with missing values; its model pipeline fills those from training-set medians, standardizes each dimension, then applies Euclidean k-nearest-neighbor regression with three neighbors and distance weighting. It predicts TOC and alkalinity; the treatment class is computed from those measurements.

The script pairs by calendar date using an inner join. Same-date pairing is the requested assumption, not proof that a reservoir cast corresponds to that day's plant intake. In addition, vector slots implicitly treat readings at corresponding sorted positions as comparable. Different cast timing or sampling grids can weaken that assumption. July predictions are only produced on July dates having both a Strontia profile and Foothills lab record; holdout errors are possible only where the actual Foothills measurements are present.

## Treatment rule

The percentages below are the treatment classes supplied by the user, not values learned from the CSVs. The script interprets exact boundaries as follows (concentrations in mg/L):

| TOC | Alkalinity 0–60 | >60–120 | >120 |
|---|---:|---:|---:|
| >8 | 50% | 40% | 30% |
| >4–8 | 45% | 35% | 25% |
| >2–4 | 35% | 25% | 15% |
| ≤2 | unassigned | unassigned | unassigned |

TOC exactly 8 is in >4–8; exactly 4 is in >2–4; TOC ≤2 is unassigned. Alkalinity exactly 60 belongs to the first band and exactly 120 to the second. Confirm the unassigned range and operational meaning of these percentages with plant staff before using as treatment guidance.

Denver Water's data terms in `data/TERMS.md` apply to derived outputs; keep that notice with any shared or published result. The input datasets are provisional and redistribution of derived products is restricted by those terms.
