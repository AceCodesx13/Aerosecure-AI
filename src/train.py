"""Same CPU training program for local execution and the provided AWS container."""
import argparse, csv, hashlib, json, os, sys
from datetime import datetime, timezone
from pathlib import Path
import joblib, numpy as np, pandas as pd, sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from schema import CATEGORICAL, NUMERIC, FEATURES, TARGET, SEED, VERSION


def metric(y,p):
    """Calculate prediction error metrics for actual and predicted lead times.

    Args:
        y: Actual lead times, in days.
        p: Predicted lead times, in days.

    Returns:
        A dictionary containing:
        - ``mae_days``: Mean absolute error, in days.
        - ``rmse_days``: Root mean squared error, in days.
        - ``underestimate_rate``: Fraction of predictions below the actual lead time, from 0 to 1.
    """
    y=np.asarray(y);p=np.asarray(p)
    return {'mae_days':round(float(np.mean(np.abs(y-p))),3),'rmse_days':round(float(np.sqrt(np.mean((y-p)**2))),3),'underestimate_rate':round(float(np.mean(p<y)),4)}

def file_in(path,name):
    """Resolve a file path from a file or directory path.

    If ``path`` is a directory, append ``name`` to it. If ``path`` is a file
    path, return it unchanged.

    Args:
        path: Path to a file or directory.
        name: Filename to append when ``path`` is a directory.

    Returns:
        The resolved path as a ``Path`` object.
    """
    p=Path(path);return p/name if p.is_dir() else p

def train(train_path,validation_path,model_dir,reports_dir,trees=120):
    """Train and evaluate the lead-time prediction model.

    Loads the training and validation CSV files, checks their schemas, builds
    and fits a preprocessing and random forest pipeline, and evaluates it
    against baseline predictions. Saves the fitted model and validation report
    to their respective output directories.

    Args:
        train_path: Path to the training CSV file.
        validation_path: Path to the validation CSV file.
        model_dir: Directory where the serialized model is saved.
        reports_dir: Directory where validation metrics are saved.
        trees: Number of trees in the random forest.

    Returns:
        A dictionary containing validation metrics, model parameters,
        input file hashes, and run metadata.
    """
    
    # Read both CSV files into DataFrames. Store the training data in tr and the validation data in va.
    tr=pd.read_csv(train_path)
    va=pd.read_csv(validation_path)

    # Check that both DataFrames have the same columns in the same order. If they do not, stop and raise an error.
    if list(tr.columns)!=list(va.columns):raise ValueError('Train and validation schemas differ. Run validate_data.py.')

    #Check that the training data contains all required features and the target column. If any are missing, stop and raise an error.
    if not set(FEATURES+[TARGET]).issubset(tr.columns):raise ValueError('Required columns missing.')

    # Calculate the median target value for each part category in the training data.
    historical=tr.groupby('part_category_id')[TARGET].median().to_dict()

    # Calculate the overall training median to use as a fallback.
    fallback=float(tr[TARGET].median())

    # Set up preprocessing for both feature groups. Fill missing categorical values with the most frequent value, then one-hot encode them. Fill missing numeric values with their median.
    pre=ColumnTransformer([('category',Pipeline([('missing',SimpleImputer(strategy='most_frequent')),('encode',OneHotEncoder(handle_unknown='ignore'))]),CATEGORICAL),('numeric',SimpleImputer(strategy='median'),NUMERIC)])
    
    # Create a pipeline that preprocesses the features and fits a random forest regressor.
    # Use the requested tree count, a maximum depth of 18, a minimum leaf size of 3, the shared random seed, and two workers.
    model=Pipeline([('prepare',pre),('regressor',RandomForestRegressor(n_estimators=trees,max_depth=18,min_samples_leaf=3,random_state=SEED,n_jobs=2))])
    model.fit(tr[FEATURES],tr[TARGET])
    pred=np.maximum(1,model.predict(va[FEATURES]))

    # One-sided validation residual quantile, used only as a conservative planning estimate.
    margin=max(0,float(np.quantile(va[TARGET].to_numpy()-pred,0.90,method='higher')))

    # Predict each validation row using its category median. Use the overall training median when a category has no matching median.
    median_pred=va['part_category_id'].map(historical).fillna(fallback)

    quoted=va['quoted_lead_time_days'].to_numpy()
    report={'dataset_version':VERSION,'evaluation_split':'validation','row_count':len(va),'quoted_baseline':metric(va[TARGET],quoted),'historical_median_baseline':metric(va[TARGET],median_pred),'model':metric(va[TARGET],pred),'conservative_margin_days':round(margin,3),'validation_coverage':round(float(np.mean(va[TARGET]<=pred+margin)),4),'parameters':{'trees':trees,'max_depth':18,'min_samples_leaf':3,'seed':SEED},'versions':{'python':sys.version.split()[0],'sklearn':sklearn.__version__,'numpy':np.__version__,'pandas':pd.__version__},'inputs':{str(p):hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in [train_path,validation_path]},'created_utc':datetime.now(timezone.utc).isoformat()}
    model_dir=Path(model_dir)
    reports_dir=Path(reports_dir)
    model_dir.mkdir(parents=True,exist_ok=True)
    reports_dir.mkdir(parents=True,exist_ok=True)
    
    # Save the fitted pipeline, margin, historical medians, fallback value, feature list, and report metadata to model.joblib
    joblib.dump({'pipeline':model,'margin':margin,'historical_medians':historical,'fallback':fallback,'features':FEATURES,'metadata':report},model_dir/'model.joblib')
    (reports_dir/'validation_metrics.json').write_text(json.dumps(report,indent=2)+'\n')

    # Write the report to validation_metrics.json
    print(json.dumps(report,indent=2));return report

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser()
    p.add_argument('--train',default=os.environ.get('SM_CHANNEL_TRAIN',str(root/'data/prepared/train/train.csv')))
    p.add_argument('--validation',default=os.environ.get('SM_CHANNEL_VALIDATION',str(root/'data/prepared/validation/validation.csv')))
    p.add_argument('--model-dir',default=os.environ.get('SM_MODEL_DIR',str(root/'artifacts/model')))
    p.add_argument('--reports-dir',default=os.environ.get('SM_OUTPUT_DATA_DIR',str(root/'artifacts/reports')))
    p.add_argument('--trees',type=int,default=120);args,_=p.parse_known_args()
    train(file_in(args.train,'train.csv'),file_in(args.validation,'validation.csv'),args.model_dir,args.reports_dir,args.trees)
