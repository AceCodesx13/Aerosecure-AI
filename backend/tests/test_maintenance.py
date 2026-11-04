import csv
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services import maintenance_service
from supplier_selection import build_lead_times, history_estimator

client = TestClient(app)
ROOT = Path(__file__).resolve().parents[2]


def fake_rows(supplier, days):
    return [{"supplier_id": supplier, "part_category_id": "PC-02", "condition": "New",
             "destination_region_id": "REG-A", "actual_delivery_days": d} for d in days]


@pytest.fixture
def fixed_leads(monkeypatch):
    # fixed lead times so the dates are easy to check: SUP-A 30, SUP-B 8, SUP-F 80
    rows = fake_rows("SUP-A", [10, 12, 14, 30]) + fake_rows("SUP-B", [5, 6, 7, 8]) + fake_rows("SUP-F", [50, 60, 70, 80])
    monkeypatch.setattr(maintenance_service, "get_estimator", lambda: history_estimator(build_lead_times(rows)))


def body(**overrides):
    b = {
        "aircraft_part_id": "AC-01-PC-02",
        "scenario_date": "2026-10-12",
        "replacement_interval_hours": 1000,
        "hours_since_replacement": 500,
        "projected_daily_flight_hours": 5,
        "buffer_days": 5,
        "destination_region_id": "REG-A",
        "shipment_restriction_classification": "Unrestricted",
        "authorization_status": "Not required",
    }
    b.update(overrides)
    return b


def post(**overrides):
    return client.post("/maintenance/recommend", json=body(**overrides))


def test_recommends_supplier_with_most_time(fixed_leads):
    data = post().json()
    assert data["decision"] == "Recommend"
    assert data["supplier_id"] == "SUP-B"
    # 500 hours left at 5 a day = 100 days, minus 8 lead and 5 buffer
    assert data["need_date"] == "2027-01-20"
    assert data["latest_order_date"] == "2027-01-07"
    assert len(data["options"]) == 3


def test_too_late_escalates(fixed_leads):
    data = post(hours_since_replacement=990).json()
    assert data["decision"] == "Escalate: order deadline already passed"
    assert data["supplier_id"] == "SUP-B"


def test_region_c_highly_restricted_never_recommended(fixed_leads):
    for auth in ["Not required", "Valid", "Expired", "Missing", "Approved after review"]:
        data = post(destination_region_id="REG-C", shipment_restriction_classification="Highly Restricted",
                    authorization_status=auth).json()
        assert data["decision"] != "Recommend"
        assert data["supplier_id"] is None


def test_all_blocked_is_no_feasible_option(fixed_leads):
    data = post(destination_region_id="REG-C", shipment_restriction_classification="Highly Restricted",
                authorization_status="Approved after review").json()
    assert data["decision"] == "Escalate: no feasible option"
    assert all(o["result"] == "Blocked" for o in data["options"])


def test_expired_authorization_needs_review(fixed_leads):
    data = post(shipment_restriction_classification="Restricted", authorization_status="Expired").json()
    assert data["decision"] == "Escalate: human review required"


def test_no_supplier_for_condition(fixed_leads):
    data = post(condition="Repaired").json()
    assert data["decision"] == "Escalate: no supplier sells this part in that condition"
    assert data["options"] == []


def test_unknown_part(fixed_leads):
    assert post(aircraft_part_id="AC-99-PC-99").json()["decision"] == "Escalate: unknown part"


def test_bad_input_is_rejected():
    assert post(projected_daily_flight_hours=0).status_code == 422
    assert post(scenario_date="not a date").status_code == 422
    b = body()
    del b["buffer_days"]
    assert client.post("/maintenance/recommend", json=b).status_code == 422


def test_honeywell_scenarios_through_endpoint(monkeypatch):
    # the 3 scenarios all use a 20 day lead time, so fake that and check the dates
    monkeypatch.setattr(maintenance_service, "get_estimator", lambda: (lambda *args: (20, "scenario")))
    with open(ROOT / "data" / "examples" / "maintenance_scenarios.csv", newline="") as f:
        scenarios = list(csv.DictReader(f))

    for s in scenarios:
        blocked = s["policy_decision"] == "Blocked"
        data = post(
            aircraft_part_id=s["aircraft_part_id"],
            scenario_date=s["scenario_date"],
            replacement_interval_hours=float(s["replacement_interval_hours"]),
            hours_since_replacement=float(s["hours_since_replacement"]),
            projected_daily_flight_hours=float(s["projected_daily_flight_hours"]),
            buffer_days=float(s["buffer_days"]),
            destination_region_id="REG-C" if blocked else "REG-A",
            shipment_restriction_classification="Highly Restricted" if blocked else "Unrestricted",
            authorization_status="Approved after review" if blocked else "Not required",
        ).json()

        if s["expected_result"] == "Blocked":
            assert data["decision"] == "Escalate: no feasible option", s["scenario_id"]
            assert all(o["result"] == "Blocked" for o in data["options"]), s["scenario_id"]
        else:
            assert data["decision"].startswith(s["expected_result"]), s["scenario_id"]
            assert data["need_date"] == s["expected_need_date"], s["scenario_id"]
            assert data["latest_order_date"] == s["expected_latest_order_date"], s["scenario_id"]


def test_real_estimator_responds_under_a_second():
    post()  # first call loads the model, don't count it
    start = time.perf_counter()
    response = post()
    assert response.status_code == 200
    assert time.perf_counter() - start < 1
    assert response.json()["decision"] == "Recommend"
