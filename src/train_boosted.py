import argparse, hashlib, json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path

import joblib, numpy as np, pandas as pd, sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OrdinalEncoder

from schema import CATEGORICAL, NUMERIC, FEATURES, TARGET, SEED, VERSION
from train import metric, file_in
from lead_features import add_shortage


def train(train_path, validation_path, model_dir, reports_dir, iterations=300, learning_rate=0.05,
          max_leaf_nodes=31, min_samples_leaf=20, seed=SEED, exclude_features="quoted_lead_time_days", shortage=True):
    started = time.perf_counter()
    excluded = {x.strip() for x in exclude_features.split(",") if x.strip()}
    if excluded - set(FEATURES):
        raise ValueError("Unknown excluded features: " + str(sorted(excluded - set(FEATURES))))
    selected = [f for f in FEATURES if f not in excluded]
    cats = [f for f in CATEGORICAL if f in selected]
    nums = [f for f in NUMERIC if f in selected]
    if shortage:
        if "quantity_ordered" not in selected or "stock_at_acceptance" not in selected:
            raise ValueError("Shortage needs quantity_ordered and stock_at_acceptance.")
        nums = nums + ["shortage"]

    tr = pd.read_csv(train_path)
    va = pd.read_csv(validation_path)
    if list(tr.columns) != list(va.columns):
        raise ValueError("Train and validation schemas differ. Run validate_data.py.")

    historical = tr.groupby("part_category_id")[TARGET].median().to_dict()
    fallback = float(tr[TARGET].median())

    encode = ColumnTransformer([
        ("category", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=np.nan), cats),
        ("numeric", "passthrough", nums),
    ])
    regressor = HistGradientBoostingRegressor(
        max_iter=iterations, learning_rate=learning_rate, max_leaf_nodes=max_leaf_nodes,
        min_samples_leaf=min_samples_leaf, categorical_features=[True] * len(cats) + [False] * len(nums),
        random_state=seed)
    steps = [("encode", encode), ("regressor", regressor)]
    if shortage:
        steps.insert(0, ("shortage", FunctionTransformer(add_shortage)))
    model = Pipeline(steps)

    model.fit(tr[selected], tr[TARGET])
    pred = np.maximum(1, model.predict(va[selected]))

    margin = max(0, float(np.quantile(va[TARGET].to_numpy() - pred, 0.90, method="higher")))
    median_pred = va["part_category_id"].map(historical).fillna(fallback)

    report = {
        "dataset_version": VERSION,
        "evaluation_split": "validation",
        "row_count": len(va),
        "quoted_baseline": metric(va[TARGET], va["quoted_lead_time_days"]),
        "historical_median_baseline": metric(va[TARGET], median_pred),
        "model": metric(va[TARGET], pred),
        "conservative_margin_days": round(margin, 3),
        "validation_coverage": round(float(np.mean(va[TARGET] <= pred + margin)), 4),
        "parameters": {"model_type": "hist-gradient-boosting", "iterations": iterations, "learning_rate": learning_rate,
                       "max_leaf_nodes": max_leaf_nodes, "min_samples_leaf": min_samples_leaf, "seed": seed},
        "features": selected,
        "added_features": ["shortage"] if shortage else [],
        "excluded_features": sorted(excluded),
        "training_elapsed_seconds": round(time.perf_counter() - started, 3),
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "versions": {"python": sys.version.split()[0], "sklearn": sklearn.__version__,
                     "numpy": np.__version__, "pandas": pd.__version__},
        "inputs": {str(p): hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in [train_path, validation_path]},
        "created_utc": datetime.now(timezone.utc).isoformat(),
    }

    model_dir = Path(model_dir)
    reports_dir = Path(reports_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": model, "margin": margin, "historical_medians": historical, "fallback": fallback,
                 "features": selected, "metadata": report}, model_dir / "model.joblib")
    (reports_dir / "validation_metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    p = argparse.ArgumentParser()
    p.add_argument("--train", default=os.environ.get("SM_CHANNEL_TRAIN", str(root / "data/prepared/train/train.csv")))
    p.add_argument("--validation", default=os.environ.get("SM_CHANNEL_VALIDATION", str(root / "data/prepared/validation/validation.csv")))
    p.add_argument("--model-dir", default=str(root / "artifacts/boosted/model"))
    p.add_argument("--reports-dir", default=str(root / "artifacts/boosted/reports"))
    p.add_argument("--iterations", type=int, default=300)
    p.add_argument("--learning-rate", type=float, default=0.05)
    p.add_argument("--max-leaf-nodes", type=int, default=31)
    p.add_argument("--min-samples-leaf", type=int, default=20)
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--exclude-features", default="quoted_lead_time_days")
    p.add_argument("--no-shortage", action="store_true")
    a = p.parse_args()
    train(file_in(a.train, "train.csv"), file_in(a.validation, "validation.csv"), a.model_dir, a.reports_dir,
          a.iterations, a.learning_rate, a.max_leaf_nodes, a.min_samples_leaf, a.seed, a.exclude_features, not a.no_shortage)
