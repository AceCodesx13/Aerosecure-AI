# Run record: baseline-01

First T3 run in SageMaker Studio using starter kit 1.1.1. Done for S5AAPB-23 (SageMaker test run).

```text
Team, student ID and run ID: team-01, ASU-JKhayyati, baseline-01
Question or hypothesis: Does the default random forest train and run in our Studio JupyterLab space, and does it beat both baselines?
Dataset version and training/validation file hashes: 1.0.0
  train.csv      b4931a0e694130e3221701eaa49d97f9320852e63ba9c1e6beb540df4ad73010
  validation.csv af26cb6963b843f51b77bd9fb3f95a990158f778b3997ee33ad07558b2a7adc4
Code revision or release hash: starter kit 1.1.1
  zip sha256  f554841e1ab6af9f4598027aa508d42eed19b4862c080d4ba61a12166c380bac
  code_sha256 a9fd7138b842f50c1b30ce6d461202088e852960bbcb57c1bbaca1eb0af0930e
Python and dependency versions: Python 3.12.15, scikit-learn 1.5.2, numpy 1.26.4, pandas 2.2.3
Model, parameters, features and seed: random forest, 120 trees, max depth 18, min samples leaf 3, seed 20261012
  features: aircraft_model_id, part_category_id, supplier_id, condition, origin_region_id,
  destination_region_id, quantity_ordered, stock_at_acceptance, supplier_backlog_days,
  quoted_lead_time_days, route_transit_days, route_customs_days, order_month
What changed from the comparison run: nothing, this is the default settings run
Quoted baseline validation MAE: 6.559 days (RMSE 8.668, underestimates 64.9%)
Historical median validation MAE: 14.975 days (RMSE 22.039, underestimates 39.9%)
Model validation MAE and underestimation rate: 5.244 days (RMSE 7.118), underestimates 39.7%
Conservative margin and validation coverage: 7.255 days, 90.0% coverage
Runtime: 32.4 s training on ml.t3.medium
Keep or reject this run, and why: keep as the reference to compare experiments against. Beats both baselines on MAE and RMSE.
Model-selection/freeze date: not frozen yet
Final test MAE and both baseline MAEs: not run (done once after the model is frozen)
Final test conservative coverage and excess days: not run
Errors by part group: not run yet
S3 student ID/run ID and saved-model location:
  s3://asu-capstone-data-bucket/capstone/v1/team-01/full/runs/notebook/ASU-JKhayyati/baseline-01/
  (4 files: model, baseline_metrics.json, validation_metrics.json, predictions.csv)
Steps to reproduce and recover: see below
Limitations and remaining work: data is synthetic. Settings not tuned yet, next step is the experiments in 04_EXPERIMENTS.md
```

## Environment

- AWS account 818267500533, Students role, us-east-2
- Studio project AWSReservedSSO_Students_5a64106b4b62eeb1 (domain d-yn4pfjqbzahk)
- Private JupyterLab space jkhayyati-capstone: ml.t3.medium, SageMaker Distribution CPU 4.5, 16 GB, 60 min idle
- No training image, ECR or Docker needed for 1.1.1

## Checks before training

- `validate_data.py`: PASS (hashes, 20 aircraft, 400 part associations, schemas, split counts, no leakage)
- starter tests: 6 ran, OK
- `aws/storage.py fetch-data`: 17 files downloaded and hash-verified

## Example predictions

| order_id | predicted days | conservative days |
|---|---|---|
| ORD-016003 | 23.50 | 31 |
| ORD-016020 | 86.41 | 94 |
| ORD-016023 | 13.21 | 21 |
| ORD-016036 | 38.17 | 46 |
| ORD-016038 | 28.64 | 36 |

Same 5 predictions came out after downloading the model back from S3 and reloading it, so the saved copy works.

## How to reproduce

In a JupyterLab terminal in the Studio space:

```bash
aws s3 cp s3://asu-capstone-data-bucket/datasets/releases/1.1.1/ASU_Capstone_T3_1.1.1.zip . --region us-east-2
python3 -m zipfile -e ASU_Capstone_T3_1.1.1.zip .
cd ASU_Capstone_T3_1.1.1
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-notebooks.txt
.venv/bin/python src/validate_data.py
.venv/bin/python aws/storage.py fetch-data
.venv/bin/python src/baseline.py
.venv/bin/python src/train.py
.venv/bin/python src/predict.py
```

To get the saved run back:

```bash
.venv/bin/python aws/storage.py download --student-id ASU-JKhayyati --run-id baseline-01 --directory recovered/baseline-01
.venv/bin/python src/predict.py --model recovered/baseline-01/model/model.joblib --output recovered/baseline-01/predictions-reloaded.csv
```

Stop the space in Code Spaces after use (closing the tab does not stop it).
