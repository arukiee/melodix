import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import verify_password

def test_login():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "admin@melodix.com").first()
        if not user:
            print("User admin@melodix.com not found!")
            return
            
        print(f"Found user: {user.email}")
        
        is_valid = verify_password("admin1233", user.password_hash)
        if is_valid:
            print("Password admin1233 is VALID!")
        else:
            print("Password admin1233 is INVALID!")
            
    finally:
        db.close()

if __name__ == "__main__":
    test_login()
