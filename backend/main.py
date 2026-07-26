from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.lessons import router as lessons_router

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Melodix Full-Stack API"
)

# CORS Middleware Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler Example
# @app.exception_handler(Exception)
# async def global_exception_handler(request, exc):
#     return JSONResponse(status_code=500, content={"message": "An unexpected error occurred."})

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(lessons_router)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Melodix Backend...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Melodix Backend...")
