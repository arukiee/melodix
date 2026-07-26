import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.core.database import Base, engine
from sqlalchemy import text

print("Terminating connections...")
with engine.connect() as conn:
    conn.execute(text("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'melodix_dev' AND pid <> pg_backend_pid()"))
    conn.commit()

print("Dropping tables...")
Base.metadata.drop_all(bind=engine)
print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done")
