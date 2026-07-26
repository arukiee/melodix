from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db

router = APIRouter()

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    status = {
        "status": "ok",
        "app_version": "1.0.0",
        "database": "disconnected"
    }
    
    try:
        # Check database connection
        db.execute(text("SELECT 1"))
        status["database"] = "connected"
    except Exception as e:
        status["status"] = "degraded"
        status["database_error"] = str(e)
        
    return status
