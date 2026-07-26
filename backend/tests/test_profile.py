import pytest
from fastapi.testclient import TestClient
from main import app
import uuid

client = TestClient(app)

@pytest.fixture(scope="module")
def auth_headers():
    """Register a user and return auth headers for profile tests."""
    email = f"profile_{uuid.uuid4()}@example.com"
    password = "testpass123"

    client.post("/auth/register", json={
        "email": email,
        "full_name": "Profile Test User",
        "password": password
    })

    login_res = client.post("/auth/login", data={
        "username": email,
        "password": password
    })
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_get_profile(auth_headers):
    response = client.get("/users/profile", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "user_id" in data
    assert data["skill_level"] == "BEGINNER"


def test_update_profile(auth_headers):
    response = client.patch("/users/profile", headers=auth_headers, json={
        "bio": "I love piano",
        "skill_level": "INTERMEDIATE",
        "preferred_instrument": "Electric Piano",
        "daily_practice_goal": 60,
        "preferred_genres": ["Jazz", "Classical"]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["bio"] == "I love piano"
    assert data["skill_level"] == "INTERMEDIATE"
    assert data["preferred_instrument"] == "Electric Piano"
    assert data["daily_practice_goal"] == 60
    assert data["preferred_genres"] == ["Jazz", "Classical"]


def test_update_profile_partial(auth_headers):
    """Only update one field, others should remain unchanged."""
    response = client.patch("/users/profile", headers=auth_headers, json={
        "bio": "Updated bio only"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["bio"] == "Updated bio only"
    # Previous values should persist
    assert data["skill_level"] == "INTERMEDIATE"
    assert data["daily_practice_goal"] == 60


def test_update_user_info(auth_headers):
    response = client.patch("/users/me", headers=auth_headers, json={
        "full_name": "Updated Name"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"


def test_complete_onboarding(auth_headers):
    response = client.post("/users/complete-onboarding", headers=auth_headers, json={
        "skill_level": "ADVANCED",
        "preferred_instrument": "Grand Piano",
        "daily_practice_goal": 45,
        "preferred_genres": ["Pop", "Rock"]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["onboarding_completed"] is True
    assert data["profile"]["skill_level"] == "ADVANCED"
    assert data["profile"]["daily_practice_goal"] == 45


def test_profile_unauthorized():
    response = client.get("/users/profile")
    assert response.status_code == 401

    response = client.patch("/users/profile", json={"bio": "hack"})
    assert response.status_code == 401

    response = client.post("/users/complete-onboarding", json={})
    assert response.status_code == 401
