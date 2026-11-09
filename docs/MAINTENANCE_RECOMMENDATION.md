# Maintenance supplier recommendation

When a part on an aircraft needs replacing, this checks every supplier that sells that part and tells you who to order from, or that a person needs to step in.

## How it works

1. Figure out when the part is needed: hours left until replacement divided by flight hours per day.
2. Find every supplier that sells that part category in the right condition (New, Repaired, Overhauled).
3. For each supplier:
   - check the shipment rules (label, destination, authorization), same rules as `policy.py`
   - get the conservative delivery days from the trained model (prediction + safety margin, same as `predict.py`)
   - work out the latest day we can order and still get the part in time (need date - delivery days - buffer)
4. Pick the answer:

| Result | When |
|---|---|
| **Recommend** | at least one allowed supplier can still make it in time, pick the one that gives us the most time to order |
| **Escalate: order deadline already passed** | allowed, but it's already too late for everyone, points to the fastest one |
| **Escalate: human review required** | authorization is missing or expired |
| **Escalate: no feasible option** | every supplier is blocked or we can't estimate any of them |
| **Escalate: no supplier sells this part in that condition** | nobody to pick from |
| **Escalate: unknown part** | part id isn't in the catalog |

A fast delivery prediction can never turn a blocked shipment into an allowed one.

### About the model input

The model was trained on real orders, which have a supplier quote (stock, backlog, quoted lead time). Before ordering we don't have a quote yet, so we use the normal values for that supplier + part from the training data. If there's no `artifacts/model/model.joblib`, it falls back to the 90th percentile of past deliveries.

## Files

| File | What it does |
|---|---|
| `src/supplier_selection.py` | the logic above |
| `backend/app/api/routes/maintenance.py` | `POST /maintenance/recommend` |
| `backend/app/schemas/maintenance.py` | request and response format |
| `backend/app/services/maintenance_service.py` | loads the model once and calls `select_supplier` |
| `tests/test_supplier_selection.py` | 19 tests on the logic |
| `backend/tests/test_maintenance.py` | 10 tests on the endpoint |

## Try it

```
.venv\Scripts\python.exe -m uvicorn backend.app.main:app
```

Open `http://127.0.0.1:8000/docs`, then **POST /maintenance/recommend** → Try it out, and send:

```json
{
  "aircraft_part_id": "AC-01-PC-02",
  "scenario_date": "2026-10-12",
  "replacement_interval_hours": 1000,
  "hours_since_replacement": 500,
  "projected_daily_flight_hours": 5,
  "buffer_days": 5,
  "destination_region_id": "REG-A",
  "shipment_restriction_classification": "Unrestricted",
  "authorization_status": "Not required"
}
```

With our model this recommends SUP-A (23 days), order by 2026-12-23.

## Test results

- Honeywell's 3 maintenance scenarios (M-01 to M-03) match the expected dates and result through the endpoint
- Highly Restricted to Region C is never recommended, for every authorization status
- no allowed supplier always escalates
- bad input (0 flight hours, bad date, missing field) gets a 422
- responds in well under 1 second after the model is loaded

## Still to do

- merge into main once everyone's branches are combined
- the model only runs locally for now, it'll use the SageMaker model once we have the training image
- the dashboard needs to call this endpoint
