import sys
from functools import lru_cache
from pathlib import Path

# so we can import from src/
SRC = Path(__file__).resolve().parents[3] / "src"
sys.path.insert(0, str(SRC))

from supplier_selection import load_estimator, load_reference, select_supplier

from ..schemas.maintenance import MaintenanceRequest, MaintenanceResponse, SupplierOption


@lru_cache
def get_reference():
    return load_reference()


@lru_cache
def get_estimator():
    # loads the model once, falls back to past deliveries if there's no model file
    estimate, _ = load_estimator(get_reference())
    return estimate


def recommend(request: MaintenanceRequest) -> MaintenanceResponse:
    data = request.model_dump()
    data["scenario_date"] = request.scenario_date.isoformat()

    decision, chosen, candidates = select_supplier(data, get_reference(), get_estimator())

    return MaintenanceResponse(
        decision=decision,
        supplier_id=chosen["supplier_id"] if chosen else None,
        supplier_name=chosen["supplier_name"] if chosen else None,
        need_date=chosen["need_date"] if chosen else None,
        latest_order_date=chosen["latest_order_date"] if chosen else None,
        lead_time_source=chosen["lead_time_source"] if chosen else None,
        options=[SupplierOption(**c) for c in candidates],
    )
