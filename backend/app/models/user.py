from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    courses = relationship("Course", back_populates="user")
    experiments = relationship("Experiment", back_populates="user")
    reports = relationship("Report", back_populates="user")
    check_tasks = relationship("CheckTask", back_populates="user")
