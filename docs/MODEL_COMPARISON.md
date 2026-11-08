# Final Model Comparison

All four models were evaluated on the same test split (**3,749 rows**) and validation split (**2,469 rows**).

**Symbol key:** <span style="color: #008000;"><span style="color: #008000;">★</span></span> = best; <span style="color: #d00000;">x</span> = worst.

## Test set results

| Model | MAE (days) ↓ | RMSE (days) ↓ | Underestimate rate (closest to 50%) | Conservative coverage ↑ | Mean conservative excess (days) ↓ |
|---|---:|---:|---:|---:|---:|
| Random Forest, 120 trees | <span style="color: #d00000;">x</span> 5.810 | <span style="color: #d00000;">x</span> 7.957 | <span style="color: #008000;">★</span> **45.48%** | <span style="color: #d00000;">x</span> 87.89% | <span style="color: #008000;">★</span> **8.604** |
| Random Forest, 240 trees | 5.799 | 7.947 | <span style="color: #d00000;">x</span> 45.16% | 87.94% | 8.578 |
| Extra Trees, 120 trees | 5.761 | 7.849 | 45.43% | 88.80% | <span style="color: #d00000;">x</span> 8.993 |
| Hist Gradient Boosting, 120 iterations | <span style="color: #008000;">★</span> **5.623** | <span style="color: #008000;">★</span> **7.728** | 45.43% | <span style="color: #008000;">★</span> **89.04%** | 8.732 |

## Test differences from the 120-tree Random Forest

Negative error deltas mean lower error than the base Random Forest. Underestimate-rate and coverage deltas are percentage points (pp).

| Model | MAE change (days) | RMSE change (days) | Underestimate-rate change | Coverage change | Mean excess change (days) |
|---|---:|---:|---:|---:|---:|
| Random Forest, 240 trees | -0.011 | -0.010 | -0.32 pp | +0.05 pp | -0.026 |
| Extra Trees, 120 trees | -0.049 | -0.108 | -0.05 pp | +0.91 pp | +0.389 |
| Hist Gradient Boosting, 120 iterations | **-0.187** | **-0.229** | -0.05 pp | **+1.15 pp** | +0.128 |

## Test MAE by part group

| Part group | Random Forest, 120 trees | Random Forest, 240 trees | Extra Trees, 120 trees | Hist Gradient Boosting |
|---|---:|---:|---:|---:|
| Consumable | 4.332 | 4.327 | <span style="color: #d00000;">x</span> 4.408 | <span style="color: #008000;">★</span> **4.254** |
| Repairable | <span style="color: #d00000;">x</span> 6.688 | 6.666 | 6.677 | <span style="color: #008000;">★</span> **6.454** |
| Major | 7.037 | <span style="color: #d00000;">x</span> 7.038 | <span style="color: #008000;">★</span> **6.660** | 6.727 |

## Validation results

| Model | MAE (days) ↓ | RMSE (days) ↓ | Underestimate rate | Validation coverage |
|---|---:|---:|---:|---:|
| Random Forest, 120 trees | <span style="color: #d00000;">x</span> 5.244 | 7.118 | 39.69% | 90.04% |
| Random Forest, 240 trees | 5.239 | 7.121 | <span style="color: #d00000;">x</span> 39.61% | 90.04% |
| Extra Trees, 120 trees | 5.243 | <span style="color: #d00000;">x</span> 7.126 | <span style="color: #008000;">★</span> **40.26%** | 90.04% |
| Hist Gradient Boosting, 120 iterations | <span style="color: #008000;">★</span> **5.086** | <span style="color: #008000;">★</span> **6.926** | 40.10% | 90.04% |

## Baseline reference

| Test-set predictor | MAE (days) ↓ | RMSE (days) ↓ | Underestimate rate |
|---|---:|---:|---:|
| Quoted baseline | 7.113 | 9.498 | <span style="color: #d00000;">x</span> 66.31% |
| Historical median baseline | <span style="color: #d00000;">x</span> 16.542 | <span style="color: #d00000;">x</span> 23.021 | <span style="color: #008000;">★</span> **50.87%** |
| Best model: Hist Gradient Boosting | <span style="color: #008000;">★</span> **5.623** | <span style="color: #008000;">★</span> **7.728** | 45.43% |

Hist Gradient Boosting lowered test MAE by **1.490 days (about 21%)** and RMSE by **1.770 days (about 19%)** compared with the quoted baseline.

## Summary

- **Hist Gradient Boosting had the lowest MAE and RMSE** on both validation and test data, and the highest test conservative coverage.
- Increasing Random Forest from 120 to 240 trees made only very small differences.
- Extra Trees had the lowest test MAE for the **Major** part group.
- All models improved on the quoted baseline in test MAE and RMSE.
