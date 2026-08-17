import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User

def fix_admin():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "admin").first()
        if user:
            user.email = "admin@melodix.com"
            db.commit()
            print("Admin email updated to admin@melodix.com")
        else:
            print("Admin user not found.")
    finally:
        db.close()

if __name__ == "__main__":
    fix_admin()
