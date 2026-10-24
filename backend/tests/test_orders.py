import csv

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services import access_service


client = TestClient(app)


@pytest.fixture(autouse=True)
def temp_log(tmp_path, monkeypatch):
    # dont write to the real log
    log_path = tmp_path / "access_log.csv"
    monkeypatch.setattr(access_service, "LOG_PATH", log_path)
    return log_path


def get_orders(role, user="jad", limit=None):
    params = {"limit": limit} if limit else {}
    return client.get("/orders", headers={"X-User": user, "X-Role": role}, params=params)


def test_student_only_gets_unrestricted():
    response = get_orders("student", limit=500)
    data = response.json()

    assert response.status_code == 200
    assert data["visible_count"] == 6637
    labels = {order["data_access_classification"] for order in data["orders"]}
    assert labels == {"Unrestricted"}


def test_mentor_does_not_get_highly_restricted():
    data = get_orders("mentor", limit=500).json()

    assert data["visible_count"] == 13377
    labels = {order["data_access_classification"] for order in data["orders"]}
    assert "Highly Restricted" not in labels


def test_administrator_gets_everything():
    data = get_orders("administrator").json()
    assert data["visible_count"] == 20000


def test_limit_controls_how_many_are_returned():
    data = get_orders("administrator", limit=10).json()
    assert data["returned"] == 10
    assert len(data["orders"]) == 10


def test_unknown_role_is_rejected():
    response = get_orders("hacker")
    assert response.status_code == 403


def test_missing_headers_are_rejected():
    response = client.get("/orders")
    assert response.status_code == 422


def test_every_request_is_logged(temp_log):
    get_orders("student", user="jad")
    get_orders("hacker", user="someone")

    with temp_log.open(encoding="utf-8", newline="") as f:
        lines = list(csv.DictReader(f))

    assert [line["user"] for line in lines] == ["jad", "someone"]
    assert lines[1]["allowed"] == "0"
