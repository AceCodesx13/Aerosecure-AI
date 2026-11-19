# Model experiments

Comparing changes against baseline-01 (default random forest). All runs use the same train and validation split, dataset 1.0.0, starter kit 1.1.1 (code_sha256 a9fd7138...0930e), Python 3.12.15, scikit-learn 1.5.2. Test set not used.

## Summary

| Run | Model | What changed | Val MAE | RMSE | Underestimates | Margin | Train time |
|---|---|---|---|---|---|---|---|
| quoted baseline | supplier quote | - | 6.559 | 8.668 | 64.9% | - | - |
| historical median | median per part | - | 14.975 | 22.039 | 39.9% | - | - |
| baseline-01 | random forest | defaults | 5.244 | 7.118 | 39.7% | 7.255 | 32.4 s |
| **experiment-01** | random forest | no quoted_lead_time_days | **5.180** | **7.056** | **39.4%** | **7.164** | 25.2 s |
| experiment-02 | decision tree | depth 8, leaf 10 | 5.597 | 7.548 | 42.2% | 8.301 | 0.2 s |

Margin is the days added for the conservative estimate (90% validation coverage for all runs).

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
Keep or reject this run, and why: keep, best candidate so far. Better than baseline-01 on MAE, RMSE,
  underestimates and margin. Also checked on 3 other seeds locally, it was better every time (see below).
  Needs team/Aaron OK before freezing since it drops the supplier quote.
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
Keep or reject this run, and why: reject. Still beats the quoted baseline and is way faster and easier
  to explain, but about 0.35 days worse than the forest and needs a bigger safety margin (8.3 vs 7.3 days).
S3 student ID/run ID and saved-model location:
  s3://asu-capstone-data-bucket/capstone/v1/team-01/full/runs/notebook/ASU-JKhayyati/experiment-02/
Created: 2026-11-19 15:41 UTC
```

## Extra checks (run locally, not saved to S3)

Same kit, same data and package versions, reproduced baseline-01 exactly before starting.

Seed check, to make sure experiment-01 isn't just luck:

| Seed | Default forest | No quote |
|---|---|---|
| 20261012 | 5.244 | 5.180 |
| 1 | 5.239 | 5.195 |
| 2 | 5.257 | 5.188 |
| 3 | 5.263 | 5.163 |

No quote was better on every seed, by about 0.07 days.

Settings that did not help (all within seed noise, 5.24 to 5.34): 300 trees (twice as slow), max depth 12 or 24, min samples leaf 1, 8 or 15. Extra Trees got 5.19 to 5.22 but needed a bigger margin (7.4 to 7.7 days), so not worth it.

Which features matter (MAE when that feature is removed, baseline 5.244):

| Removed | Val MAE |
|---|---|
| supplier_backlog_days | 5.726 |
| stock_at_acceptance | 5.519 |
| aircraft_model_id | 5.260 |
| route_customs_days | 5.243 |
| order_month | 5.200 |
| quoted_lead_time_days | 5.180 |

Backlog and stock are the most useful inputs. The quote and order month don't help.

## Where baseline-01 makes the biggest errors (validation)

| Group | Rows | MAE | Underestimates |
|---|---|---|---|
| Consumable (PC-01 to PC-08) | 1240 | 4.12 | 36% |
| Repairable (PC-09 to PC-16) | 973 | 6.38 | 44% |
| Major (PC-17 to PC-20) | 256 | 6.40 | 42% |

Also worse for Repaired (6.58) and Overhauled (6.48) parts than New (4.66), and for suppliers C, D, E and I (about 6.2 to 6.7) compared with A, B and F (about 4.1). Destination region barely matters (5.1 to 5.4). Longer, more complicated orders are harder to predict.

## Takeaways

- The forest beats the supplier quote by about 1.3 to 1.4 days (around 20%). Tuning only adds about 1% on top of that, so the model is close to what this data allows.
- Best candidate to freeze: experiment-01. Waiting on team and Aaron to agree before Samuel runs the final test.
- Data is synthetic, so these numbers don't mean much for real deliveries.
