from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.core.database import init_db
from app.api import reports, checks, library, course, auth

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]


def seed_data():
    from app.core.database import SessionLocal
    from app.models import Course, Clazz, Experiment, User
    from app.core.security import get_password_hash
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "admin").first()
        if not user:
            user = User(username="admin", hashed_password=get_password_hash("123456"))
            db.add(user)
            db.commit()
            db.refresh(user)
            
        if db.query(Course).first():
            return
            
        c = Course(name="软件工程", code="SE001", user_id=user.id)
        db.add(c)
        db.flush()
        cl = Clazz(name="软件工程 21-1 班", grade="2021", user_id=user.id)
        db.add(cl)
        db.flush()
        e = Experiment(course_id=c.id, title="实验一：需求分析", description="", user_id=user.id)
        db.add(e)
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_data()
    # 预加载 embedding 模型，避免在后台线程中首次加载时出现网络问题
    from app.services.embedding_service import preload_model
    preload_model()
    yield


app = FastAPI(title="实验报告语义查重系统", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(checks.router, prefix="/api/checks", tags=["checks"])
app.include_router(library.router, prefix="/api/library", tags=["library"])
app.include_router(course.router, prefix="/api/course", tags=["course"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
