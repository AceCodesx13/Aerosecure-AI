import argparse
from pathlib import Path
import joblib,numpy as np,pandas as pd
from schema import FEATURES

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--model',default=root/'artifacts/model/model.joblib');p.add_argument('--input',default=root/'data/examples/new_orders.csv');p.add_argument('--output',default=root/'artifacts/predictions.csv');a=p.parse_args()
    
    # Load the saved model bundle into b.
    b=joblib.load(a.model)

    # read the input CSV into df, and find any required feature columns missing from the input.
    df=pd.read_csv(a.input)
    missing=set(FEATURES)-set(df.columns)

    # Check whether any required features are missing. If they are, stop and list their names in an error.
    if missing:raise ValueError('Missing input columns: '+str(sorted(missing)))

    # Predict delivery times using the saved pipeline and the required features in their expected order. Set any prediction below one to one.
    pred=np.maximum(1,b['pipeline'].predict(df[FEATURES]))

    # Create the output DataFrame with a copy of the input order_id column
    out=df[['order_id']].copy()
    # Add the model predictions to the output, rounded to two decimal places.
    out['predicted_delivery_days']=np.round(pred,2)
    # Add the saved margin to each prediction, round the result up to a whole day, and store it as an integer.
    out['conservative_delivery_days']=np.ceil(pred+b['margin']).astype(int)

    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    
    out.to_csv(a.output,index=False)
    print(out.to_string(index=False))
