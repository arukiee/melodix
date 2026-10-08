from fastapi.testclient import TestClient

from ml.inference.app import app


def test_health_and_model_info_without_checkpoint(monkeypatch, tmp_path):
    import ml.inference.app as inference_app
    monkeypatch.setattr(inference_app, "CHECKPOINT", tmp_path / "missing.pt")
    monkeypatch.setattr(inference_app, "_transcriber", None)
    client = TestClient(app)
    health = client.get("/health")
    info = client.get("/model-info")

    assert health.status_code == 200
    assert info.status_code == 200
    assert info.json()["keys"] == 88
    assert isinstance(info.json()["keys"], int)
    assert info.json()["model_loaded"] is False
    assert info.json()["status"] == "trained_checkpoint_required"
