from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    # Database will be 'disconnected' or 'degraded' if docker isn't running
    assert data["status"] in ["ok", "degraded"]
