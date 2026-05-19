from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Course(Base):
    __tablename__ = "course"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    code = Column(String(64), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    experiments = relationship("Experiment", back_populates="course")


class Clazz(Base):
    __tablename__ = "clazz"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    grade = Column(String(32), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    reports = relationship("Report", back_populates="clazz")


class Experiment(Base):
    __tablename__ = "experiment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("course.id"), nullable=False)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    course = relationship("Course", back_populates="experiments")
    reports = relationship("Report", back_populates="experiment")
    check_tasks = relationship("CheckTask", back_populates="experiment")
