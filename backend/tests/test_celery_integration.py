import pytest
from fastapi.testclient import TestClient
from main import app
from app.celery_app import celery_app
from app.tasks.maintenance.health_check import health_check

client = TestClient(app)

def test_celery_health_endpoint():
    response = client.get("/api/v1/celery/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert isinstance(data.get("workers"), int)
    assert data.get("broker") == "connected"

def test_maintenance_health_check_task():
    # Dispatch the task asynchronously and wait for the result
    result = health_check.delay()
    # Wait up to 10 seconds for the task to complete
    outcome = result.get(timeout=10)
    assert outcome == {"status": "ok"}
