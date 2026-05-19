from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Report(Base):
    __tablename__ = "report"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(Integer, ForeignKey("experiment.id"), nullable=True)
    class_id = Column(Integer, ForeignKey("clazz.id"), nullable=False)
    student_name = Column(String(64), nullable=True)
    student_id = Column(String(64), nullable=True)
    file_name = Column(String(256), nullable=True)
    file_path = Column(String(512), nullable=False)
    status = Column(String(32), default="UPLOADED")  # UPLOADED, PARSED, FAILED
    parse_error = Column(Text, nullable=True)
    parsed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    experiment = relationship("Experiment", back_populates="reports")
    clazz = relationship("Clazz", back_populates="reports")
    text_blocks = relationship("TextBlock", back_populates="report", cascade="all, delete-orphan")


class TextBlock(Base):
    __tablename__ = "text_block"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("report.id"), nullable=False)
    section_type = Column(String(64), nullable=False)  # DESIGN_IDEA, REFLECTION 等
    order_index = Column(Integer, default=0)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    report = relationship("Report", back_populates="text_blocks")
