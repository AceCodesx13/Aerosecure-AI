"""Evaluate a frozen model on the test split; never fit here."""
import argparse, json
from pathlib import Path
import joblib,numpy as np,pandas as pd
from train import metric
from schema import FEATURES,TARGET

def evaluate(model_path,test_path,output):
    """Evaluate a saved model on test data and save the results.

    Load the model bundle, predict target values for the test data, calculate
    overall and part-group metrics, and save the metrics and predictions to
    the output directory. Do not fit or modify the model.

    Args:
        model_path: Path to the saved model bundle.
        test_path: Path to the test data CSV file.
        output: Directory where the evaluation report and predictions are saved.

    Returns:
        A dictionary containing overall and part-group evaluation results.
    """
    # Load the saved model bundle and read the csv.
    b=joblib.load(model_path)
    df=pd.read_csv(test_path)

    # Predict the target using the saved pipeline and required features. Set any prediction below one to one.
    pred=np.maximum(1,b['pipeline'].predict(df[FEATURES]))

    # Add the saved margin to each prediction and round each result up to the next whole number.
    conservative=np.ceil(pred+b['margin'])

    # Create historical median predictions using each row’s part category. Use the saved fallback value for categories without a matching median.
    hist=df['part_category_id'].map(b['historical_medians']).fillna(b['fallback'])
    
    report={'evaluation_split':'test','row_count':len(df),'quoted_baseline':metric(df[TARGET],df['quoted_lead_time_days']),'historical_median_baseline':metric(df[TARGET],hist),'model':metric(df[TARGET],pred),'conservative_coverage':round(float(np.mean(df[TARGET]<=conservative)),4),'mean_conservative_excess_days':round(float(np.mean(np.maximum(0,conservative-df[TARGET]))),3),'note':'Coverage is measured on synthetic examples, not a real-world guarantee.'}
    report['by_part_group']={}
    for name,mask in [('Consumable',df.part_category_id.isin([f'PC-{i:02}' for i in range(1,9)])),('Repairable',df.part_category_id.isin([f'PC-{i:02}' for i in range(9,17)])),('Major',df.part_category_id.isin([f'PC-{i:02}' for i in range(17,21)]))]:
        report['by_part_group'][name]={'rows':int(mask.sum()),**metric(df.loc[mask,TARGET],pred[mask])}

    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    
    # Write the report as indented JSON to test_metrics.json
    (output/'test_metrics.json').write_text(json.dumps(report,indent=2)+'\n')

    # Select the order ID and actual target columns. Add the model prediction rounded to two decimal places and the conservative estimate, then save the results to  without a pandas index column.
    df[['order_id',TARGET]].assign(predicted_days=pred.round(2),conservative_days=conservative).to_csv(output/'test_predictions.csv',index=False)
    
    print(json.dumps(report,indent=2));return report

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--model',default=root/'artifacts/model/model.joblib');p.add_argument('--test',default=root/'data/prepared/test/test.csv');p.add_argument('--output',default=root/'artifacts/reports');a=p.parse_args();evaluate(a.model,a.test,a.output)
