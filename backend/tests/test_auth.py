import pytest
from fastapi.testclient import TestClient
from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid

from app.core.database import Base, get_db
from app.core.config import settings
from unittest.mock import patch
import json

# Setup test client
client = TestClient(app)

@pytest.fixture(scope="module")
def unique_email():
    return f"test_{uuid.uuid4()}@example.com"

@pytest.fixture(scope="module")
def test_password():
    return "strongpassword123"

def test_register_success(unique_email, test_password):
    response = client.post("/auth/register", json={
        "email": unique_email,
        "full_name": "Test User",
        "password": test_password
    })
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["email"] == unique_email
    assert data["full_name"] == "Test User"
    assert "id" in data

def test_register_duplicate_email(unique_email, test_password):
    # Try registering again with the same email
    response = client.post("/auth/register", json={
        "email": unique_email,
        "full_name": "Test User 2",
        "password": test_password
    })
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

def test_login_success(unique_email, test_password):
    response = client.post("/auth/login", data={
        "username": unique_email,
        "password": test_password
    })
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_password(unique_email):
    response = client.post("/auth/login", data={
        "username": unique_email,
        "password": "wrongpassword"
    })
    assert response.status_code == 400
    assert "Incorrect email or password" in response.json()["detail"]

def test_login_invalid_email(test_password):
    response = client.post("/auth/login", data={
        "username": "doesnotexist@example.com",
        "password": test_password
    })
    assert response.status_code == 400
    assert "Incorrect email or password" in response.json()["detail"]

def test_get_users_me(unique_email, test_password):
    # Login to get token
    login_response = client.post("/auth/login", data={
        "username": unique_email,
        "password": test_password
    })
    token = login_response.json()["access_token"]

    # Use token
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == unique_email

def test_unauthorized_access():
    response = client.get("/users/me")
    assert response.status_code == 401

def test_refresh_token(unique_email, test_password):
    # Login to get refresh token
    login_response = client.post("/auth/login", data={
        "username": unique_email,
        "password": test_password
    })
    refresh_token = login_response.json()["refresh_token"]

    # Refresh
    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

def test_invalid_refresh_token():
    response = client.post("/auth/refresh", json={"refresh_token": "invalid.token.here"})
    assert response.status_code == 401
    assert "Invalid refresh token" in response.json()["detail"]

@patch("app.api.auth.id_token.verify_oauth2_token")
def test_google_auth_new_user(mock_verify):
    # Mock Google verification
    mock_email = f"google_{uuid.uuid4()}@example.com"
    mock_verify.return_value = {
        "email": mock_email,
        "name": "Google Test User",
        "picture": "http://example.com/pic.jpg"
    }

    response = client.post("/auth/google", json={"credential": "fake_google_token"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

    # Verify user was created
    token = data["access_token"]
    me_response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == mock_email
    assert me_response.json()["auth_provider"] == "GOOGLE"

@patch("app.api.auth.id_token.verify_oauth2_token")
def test_google_auth_invalid_token(mock_verify):
    mock_verify.side_effect = ValueError("Invalid token")
    response = client.post("/auth/google", json={"credential": "bad_token"})
    assert response.status_code == 400
    assert "Invalid Google token" in response.json()["detail"]
