import pytest
from fastapi.testclient import TestClient
import uuid
from main import app

client = TestClient(app)

def get_auth_headers(email, password):
    resp = client.post("/auth/login", data={"username": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_unauthorized_access():
    resp = client.get("/lessons")
    assert resp.status_code == 401
    
    resp = client.get("/lessons/invalid-id")
    assert resp.status_code == 401
    
    resp = client.post("/lessons", json={"title": "Test"})
    assert resp.status_code == 401

def test_create_lesson_as_student_rejected():
    headers = get_auth_headers("student1@example.com", "student123")
    resp = client.post("/lessons", headers=headers, json={"title": "Test Lesson"})
    assert resp.status_code == 403

def test_create_lesson_as_teacher():
    headers = get_auth_headers("sarah.jenkins@melodix.app", "teacher123")
    data = {
        "title": "New Teacher Lesson",
        "description": "A new lesson",
        "category": "Theory",
        "difficulty": "BEGINNER",
        "estimated_duration": 30,
        "objectives": [{"id": "obj-1", "title": "Learn something", "description": "Desc"}],
        "is_published": False
    }
    resp = client.post("/lessons", headers=headers, json=data)
    assert resp.status_code == 201
    created = resp.json()
    assert created["title"] == "New Teacher Lesson"
    assert created["slug"] is not None
    assert created["is_published"] == False
    assert len(created["objectives"]) == 1

def test_list_lessons_student_sees_published_only():
    headers = get_auth_headers("student1@example.com", "student123")
    resp = client.get("/lessons", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    for item in data["items"]:
        assert item["is_published"] == True

def test_list_lessons_teacher_sees_own():
    headers = get_auth_headers("sarah.jenkins@melodix.app", "teacher123")
    resp = client.get("/lessons/teachers/me/lessons", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    
    assert "items" in data
    me_resp = client.get("/users/me", headers=headers)
    my_id = me_resp.json()["id"]
    
    for item in data["items"]:
        assert item["teacher_id"] == my_id

def test_get_lesson_detail():
    headers = get_auth_headers("student1@example.com", "student123")
    list_resp = client.get("/lessons", headers=headers)
    items = list_resp.json()["items"]
    if not items:
        pytest.skip("No published lessons available for this test")
    
    lesson_id = items[0]["id"]
    
    resp = client.get(f"/lessons/{lesson_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == lesson_id
    
    lesson_slug = resp.json()["slug"]
    slug_resp = client.get(f"/lessons/{lesson_slug}", headers=headers)
    assert slug_resp.status_code == 200
    assert slug_resp.json()["slug"] == lesson_slug

def test_update_lesson_non_owner_rejected():
    t1_headers = get_auth_headers("sarah.jenkins@melodix.app", "teacher123")
    unique_id = str(uuid.uuid4())[:8]
    create_resp = client.post("/lessons", headers=t1_headers, json={"title": f"Private Lesson {unique_id}"})
    lesson_id = create_resp.json()["id"]
    
    t2_headers = get_auth_headers("david.chen@melodix.app", "teacher123")
    patch_resp = client.patch(f"/lessons/{lesson_id}", headers=t2_headers, json={"title": "Hacked"})
    assert patch_resp.status_code == 403

def test_update_lesson_owner():
    t1_headers = get_auth_headers("sarah.jenkins@melodix.app", "teacher123")
    unique_id = str(uuid.uuid4())[:8]
    create_resp = client.post("/lessons", headers=t1_headers, json={"title": f"Original Title {unique_id}"})
    lesson_id = create_resp.json()["id"]
    
    patch_resp = client.patch(f"/lessons/{lesson_id}", headers=t1_headers, json={"title": f"Updated Title {unique_id}", "is_published": True})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["title"] == f"Updated Title {unique_id}"
    assert patch_resp.json()["is_published"] == True
    assert patch_resp.json()["published_at"] is not None

def test_delete_lesson():
    t1_headers = get_auth_headers("sarah.jenkins@melodix.app", "teacher123")
    unique_id = str(uuid.uuid4())[:8]
    create_resp = client.post("/lessons", headers=t1_headers, json={"title": f"To be deleted {unique_id}"})
    lesson_id = create_resp.json()["id"]
    
    delete_resp = client.delete(f"/lessons/{lesson_id}", headers=t1_headers)
    assert delete_resp.status_code == 204
    
    get_resp = client.get(f"/lessons/{lesson_id}", headers=t1_headers)
    assert get_resp.status_code == 404

def test_filtering_and_searching():
    headers = get_auth_headers("student1@example.com", "student123")
    
    cat_resp = client.get("/lessons?category=Theory", headers=headers)
    assert cat_resp.status_code == 200
    for item in cat_resp.json()["items"]:
        assert item["category"] == "Theory"
        
    diff_resp = client.get("/lessons?difficulty=BEGINNER", headers=headers)
    assert diff_resp.status_code == 200
    for item in diff_resp.json()["items"]:
        assert item["difficulty"] == "BEGINNER"
        
    search_resp = client.get("/lessons?search=major", headers=headers)
    assert search_resp.status_code == 200

def test_lesson_progress():
    headers = get_auth_headers("student1@example.com", "student123")
    
    list_resp = client.get("/lessons", headers=headers)
    items = list_resp.json()["items"]
    if not items:
        pytest.skip("No published lessons available for this test")
        
    lesson_id = items[0]["id"]
    
    prog_resp = client.post(
        f"/lessons/{lesson_id}/progress", 
        headers=headers, 
        json={"progress_percentage": 50.0}
    )
    assert prog_resp.status_code == 200
    assert prog_resp.json()["progress_percentage"] == 50.0
    assert prog_resp.json()["completed"] == False
    
    comp_resp = client.post(
        f"/lessons/{lesson_id}/progress", 
        headers=headers, 
        json={"progress_percentage": 100.0}
    )
    assert comp_resp.status_code == 200
    assert comp_resp.json()["progress_percentage"] == 100.0
    assert comp_resp.json()["completed"] == True
    assert comp_resp.json()["completed_at"] is not None
