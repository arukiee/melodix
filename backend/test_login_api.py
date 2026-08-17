import requests
import json

def test_login_api():
    url = "http://127.0.0.1:8000/auth/login"
    payload = {
        "username": "admin@melodix.com",
        "password": "admin1233"
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        response = requests.post(url, data=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_login_api()
