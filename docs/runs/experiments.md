# Model experiments

Comparing changes against baseline-01 (default random forest). All runs use the same train and validation split, dataset 1.0.0, starter kit 1.1.1, Python 3.12.15, scikit-learn 1.5.2. Test set not used.

## Summary

| Run | Model | What changed | Val MAE | RMSE | Underestimates | Margin | Train time |
|---|---|---|---|---|---|---|---|
| quoted baseline | supplier quote | - | 6.559 | 8.668 | 64.9% | - | - |
| historical median | median per part | - | 14.975 | 22.039 | 39.9% | - | - |
| baseline-01 | random forest | defaults | 5.244 | 7.118 | 39.7% | 7.255 | 32.4 s |
| experiment-01 | random forest | no quoted_lead_time_days | 5.180 | 7.056 | 39.4% | 7.164 | 25.2 s |
| experiment-02 | decision tree | depth 8, leaf 10 | 5.597 | 7.548 | 42.2% | 8.301 | 0.2 s |
| **experiment-03** | **gradient boosting** | **no quote, added shortage** | **4.614** | **6.393** | **39.4%** | **6.522** | **0.8 s** |

Margin is the days added for the conservative estimate (90% validation coverage for all runs).

experiment-03 is 12% better than baseline-01 and 30% better than the supplier quote, and the conservative estimate is about 0.7 days tighter.

## experiment-01

```text
Team, student ID and run ID: team-01, ASU-JKhayyati, experiment-01
Question or hypothesis: Supplier quotes are short 65% of the time. Does the model do better without the quote?
Model, parameters, features and seed: random forest, 120 trees, max depth 18, min samples leaf 3, seed 20261012
  all features except quoted_lead_time_days
What changed from the comparison run: --exclude-features quoted_lead_time_days
Model validation MAE and underestimation rate: 5.180 days (RMSE 7.056), underestimates 39.4%
Conservative margin and validation coverage: 7.164 days, 90.0%
Runtime: 25.2 s on ml.t3.medium
Keep or reject this run, and why: keep the idea (dropping the quote), used in experiment-03.
  Checked on 3 other seeds locally, better every time (see below).
S3 student ID/run ID and saved-model location:
  s3://asu-capstone-data-bucket/capstone/v1/team-01/full/runs/notebook/ASU-JKhayyati/experiment-01/
Created: 2026-11-19 15:38 UTC
```

## experiment-02

```text
Team, student ID and run ID: team-01, ASU-JKhayyati, experiment-02
Question or hypothesis: Can a single decision tree compete with the forest?
Model, parameters, features and seed: decision tree, max depth 8, min samples leaf 10, seed 20261012, all 13 features
What changed from the comparison run: --model-type decision-tree --max-depth 8 --min-samples-leaf 10
Model validation MAE and underestimation rate: 5.597 days (RMSE 7.548), underestimates 42.2%
Conservative margin and validation coverage: 8.301 days, 90.1%
Runtime: 0.2 s on ml.t3.medium
Keep or reject this run, and why: reject. Still beats the quoted baseline and is much faster and easier
  to explain, but about 0.35 days worse than the forest and needs a bigger margin (8.3 vs 7.3 days).
S3 student ID/run ID and saved-model location:
  s3://asu-capstone-data-bucket/capstone/v1/team-01/full/runs/notebook/ASU-JKhayyati/experiment-02/
Created: 2026-11-19 15:41 UTC
```

## experiment-03

```text
Team, student ID and run ID: team-01, ASU-JKhayyati, experiment-03
Question or hypothesis: Matt's gradient boosting beat the forest. Does it get better without the quote and
  with a shortage input (how many parts the supplier is missing when the order comes in)?
Code revision: src/train_boosted.py and src/lead_features.py (new), code_sha256 3594152...291c8
Model, parameters, features and seed: HistGradientBoostingRegressor, 300 iterations, learning rate 0.05,
  max leaf nodes 31, min samples leaf 20, seed 20261012
  categories are passed to the model as categories instead of one-hot
  all features except quoted_lead_time_days, plus shortage = max(0, quantity_ordered - stock_at_acceptance)
What changed from the comparison run: different model type, quote removed, shortage added
Model validation MAE and underestimation rate: 4.614 days (RMSE 6.393), underestimates 39.4%
Conservative margin and validation coverage: 6.522 days, 90.0%
Runtime: 0.8 s on ml.t3.medium
Keep or reject this run, and why: keep, best candidate. Best MAE, RMSE and margin of every run.
  Same result on 3 seeds (4.613 to 4.618) and also better on a second check inside the training data (see below).
  Saves in the same format as train.py so predict.py and evaluate.py work with it.
S3 student ID/run ID and saved-model location:
  s3://asu-capstone-data-bucket/capstone/v1/team-01/full/runs/notebook/ASU-JKhayyati/experiment-03/
  downloaded back (3 files, hash-verified) and reloaded, same 5 predictions as before upload
Created: 2026-11-19 16:24 UTC
```

To reproduce (with the two new files in src/):

```bash
.venv/bin/python src/train_boosted.py --model-dir artifacts/experiment-03/model --reports-dir artifacts/experiment-03/reports
.venv/bin/python src/predict.py --model artifacts/experiment-03/model/model.joblib --output artifacts/experiment-03/predictions.csv
```

## Extra checks (run locally, not saved to S3)

Same kit, same data and package versions, reproduced baseline-01 exactly before starting.

To avoid just tuning to the validation set, ideas were also checked on a second split: train on the first 80% of the training data (by date) and check on the last 20%. An idea only counts if it helps on both.

Seed check for experiment-01:

| Seed | Default forest | No quote |
|---|---|---|
| 20261012 | 5.244 | 5.180 |
| 1 | 5.239 | 5.195 |
| 2 | 5.257 | 5.188 |
| 3 | 5.263 | 5.163 |

How each part of experiment-03 helps (average of 3 seeds):

| Model | Second check MAE | Val MAE |
|---|---|---|
| Matt's gradient boosting (one-hot, with quote) | - | 5.08 |
| Gradient boosting, no quote, categories as categories | 4.98 | 4.86 |
| + shortage | 4.81 | 4.59 |

Ideas that did not help:

| Idea | Val MAE | Why not |
|---|---|---|
| More trees, other depth or leaf size for the forest | 5.24 to 5.34 | within seed noise |
| Extra Trees | 5.19 to 5.22 | bigger margin (7.4 to 7.7 days) |
| Separate models for in-stock and short orders | 4.77 | worse |
| Log or square-root of the target | 4.53 to 4.54 | worse on the second check, margin grows to 6.8 to 7.3 days |
| Adding supplier and part numbers from the reference tables | 4.57 | too small, and those are the simulator's own settings |
| Blending with random forest or other boosting setups | 4.55 to 4.60 | tiny or no gain for more complexity |
| Bigger and slower boosting | 4.62 | worse |
| Weighting recent orders more | 4.60 | no gain |
| Separate margins for in-stock and short orders | same coverage and excess | no gain |

Which features matter for the forest (MAE when that feature is removed, baseline 5.244):

| Removed | Val MAE |
|---|---|
| supplier_backlog_days | 5.726 |
| stock_at_acceptance | 5.519 |
| aircraft_model_id | 5.260 |
| route_customs_days | 5.243 |
| order_month | 5.200 |
| quoted_lead_time_days | 5.180 |

## Where baseline-01 makes the biggest errors (validation)

| Group | Rows | MAE | Underestimates |
|---|---|---|---|
| Consumable (PC-01 to PC-08) | 1240 | 4.12 | 36% |
| Repairable (PC-09 to PC-16) | 973 | 6.38 | 44% |
| Major (PC-17 to PC-20) | 256 | 6.40 | 42% |

Also worse for Repaired (6.58) and Overhauled (6.48) parts than New (4.66), and for suppliers C, D, E and I (about 6.2 to 6.7) compared with A, B and F (about 4.1). Destination region barely matters (5.1 to 5.4).

## Takeaways

- Stock is what really decides delivery time. When the part is in stock, delivery is mostly handling and shipping. When the supplier is short, a restock delay gets added on top. Giving the model the shortage directly was the biggest single gain.
- The supplier quote is too optimistic and slightly hurts the model.
- After experiment-03 none of the other ideas helped, so the model is close to what this data allows.
- Best candidate to freeze: experiment-03. Waiting on team and Aaron to agree before Samuel runs the final test.
- Open question for Aaron: can the final model be retrained on train + validation before the test?
- Data is synthetic, so these numbers don't mean much for real deliveries.
