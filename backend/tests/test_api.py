import json

from fastapi.testclient import TestClient

import api as backend_api


client = TestClient(backend_api.app)


def test_health_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_data_returns_default_when_file_missing(monkeypatch, tmp_path):
    missing_path = tmp_path / "does_not_exist.json"
    monkeypatch.setattr(backend_api, "LIVE_DATA_PATH", missing_path)

    response = client.get("/data")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_students"] == 0
    assert payload["students"] == []
    assert payload["metrics"]["most_active_student"] is None


def test_data_reads_live_json(monkeypatch, tmp_path):
    data_path = tmp_path / "live_data.json"
    expected = {
        "timestamp": 1710951234.567,
        "total_students": 2,
        "students": [
            {"student_id": 0, "role": "Active", "participation_score": 0.74},
            {"student_id": 1, "role": "Moderate", "participation_score": 0.52},
        ],
        "metrics": {
            "most_active_student": 0,
            "participation_level": 0.63,
            "discussion_balance": 0.59,
        },
    }
    data_path.write_text(json.dumps(expected), encoding="utf-8")
    monkeypatch.setattr(backend_api, "LIVE_DATA_PATH", data_path)

    response = client.get("/data")

    assert response.status_code == 200
    assert response.json() == expected
