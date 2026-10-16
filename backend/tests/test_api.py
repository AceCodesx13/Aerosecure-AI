from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_predict_endpoint():
    request_data = {
        "aircraft_model_id": "aircraft-1",
        "part_category_id": "engine",
        "supplier_id": "supplier-1",
        "condition": "new",
        "origin_region_id": "region-1",
        "destination_region_id": "region-2",
        "quantity_ordered": 10,
        "stock_at_acceptance": 4,
        "supplier_backlog_days": 7,
        "quoted_lead_time_days": 20,
        "route_transit_days": 4,
        "route_customs_days": 2,
        "order_month": 10,
    }

    response = client.post("/predict", json=request_data)

    assert response.status_code == 200
    assert response.json() == {
        "predicted_delivery_days": 20.0,
        "conservative_delivery_days": 25.0,
        "model_source": "temporary-placeholder",
    }