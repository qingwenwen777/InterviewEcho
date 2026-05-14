from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db import models
from db.database import SessionLocal, engine

# Create DB tables if they don't exist (useful for testing, though we have init_db.sql)
models.Base.metadata.create_all(bind=engine)

try:
    from db.seed_code_problems import seed_code_problems

    db = SessionLocal()
    try:
        seed_code_problems(db)
    finally:
        db.close()
except Exception as e:
    print(f"Warning: Could not seed code problems: {e}")

from core.config import settings

app = FastAPI(title="InterviewEcho API", description="AI Mock Interview MVP")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to InterviewEcho API"}

from routers.auth import router as auth_router
from routers.code import router as code_router
from routers.interview import router as interview_router

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(interview_router, prefix="/api/interview", tags=["interview"])
app.include_router(code_router, prefix="/api/code", tags=["code"])
