import sys
import os

# Add backend directory to sys.path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.profile import Profile
from app.core.security import get_password_hash

def create_admin():
    db = SessionLocal()
    try:
        email = "admin"
        # Check if already exists
        user = db.query(User).filter(User.email == email).first()
        if user:
            print("Admin user already exists.")
            return

        new_admin = User(
            email=email,
            full_name="Administrator",
            password_hash=get_password_hash("admin1233"),
            auth_provider="EMAIL",
            role="ADMIN",
            onboarding_completed=True
        )
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)

        profile = Profile(user_id=new_admin.id)
        db.add(profile)
        db.commit()

        print(f"Admin user created successfully with ID: {new_admin.id}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
