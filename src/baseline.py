"""Baseline uses training outcomes only and evaluates on validation only."""
import json, statistics
from collections import defaultdict
from pathlib import Path
from validate_data import read
from schema import TARGET

root=Path(__file__).resolve().parents[1]
if __name__=='__main__':

    # Read the prepared training CSV
    train=read(root/'data/prepared/train/train.csv')
    # Read the prepared validation CSV
    validation=read(root/'data/prepared/validation/validation.csv')
    # Collect training target values by part category to calculate each category's median.
    group=defaultdict(list)

    for r in train:
        # Add the row’s target value to the list for its part_category_id.
        group[r['part_category_id']].append(int(r[TARGET]))
    
    # Calculate the median target value for each category
    medians={k:statistics.median(v) for k,v in group.items()}

    # Calculate the overall median target value in the training data to use when a validation category has no matching category median.
    fallback=statistics.median([int(r[TARGET]) for r in train])

    def score(predictions):
        """Calculate validation error metrics for a list of predictions.

        Compare each prediction with its validation target and calculate the
        mean absolute error and underestimate rate.

        Args:
            predictions: Predicted target values, in the same order as
                ``validation``.

        Returns:
            A dictionary containing ``mae_days`` and ``underestimate_rate``.
        """
        # Calculate each error as actual target minus prediction by pairing each validation row with its prediction.
        errors=[int(r[TARGET])-p for r,p in zip(validation,predictions)]
        return dict(mae_days=round(statistics.mean(abs(e) for e in errors),3),underestimate_rate=round(statistics.mean(e>0 for e in errors),4))
    
    report=dict(evaluation_split='validation',row_count=len(validation),quoted_baseline=score([int(r['quoted_lead_time_days']) for r in validation]),historical_median_baseline=score([medians.get(r['part_category_id'],fallback) for r in validation]))
    
    out=root/'artifacts/reports'
    out.mkdir(parents=True,exist_ok=True)
    
    # Write the report as indented JSON to baseline_metrics.json
    (out/'baseline_metrics.json').write_text(json.dumps(report,indent=2)+'\n')

    print(json.dumps(report,indent=2))
