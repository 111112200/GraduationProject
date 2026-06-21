from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Table, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

# 任务-报告关联表
task_report = Table(
    "task_report",
    Base.metadata,
    Column("task_id", Integer, ForeignKey("check_task.id", ondelete="CASCADE"), primary_key=True),
    Column("report_id", Integer, ForeignKey("report.id", ondelete="CASCADE"), primary_key=True),
)


class CheckTask(Base):
    __tablename__ = "check_task"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    name = Column(String(256), nullable=False)
    experiment_id = Column(Integer, ForeignKey("experiment.id", ondelete="CASCADE"), nullable=False, index=True)
    mode = Column(String(32), nullable=False)  # IN_CLASS, HISTORY_ONLY, BOTH
    status = Column(String(32), default="PENDING")  # PENDING, RUNNING, COMPLETED, FAILED
    high_risk_threshold = Column(Float, default=0.8)
    similar_threshold = Column(Float, default=0.5)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    experiment = relationship("Experiment", back_populates="check_tasks")
    summaries = relationship("CheckResultSummary", back_populates="check_task", cascade="all, delete-orphan")
    reports = relationship("Report", secondary=task_report, backref="check_tasks")
    user = relationship("User", back_populates="check_tasks")


class CheckResultSummary(Base):
    __tablename__ = "check_result_summary"

    id = Column(Integer, primary_key=True, autoincrement=True)
    check_task_id = Column(Integer, ForeignKey("check_task.id", ondelete="CASCADE"), nullable=False)
    report_id = Column(Integer, ForeignKey("report.id", ondelete="CASCADE"), nullable=False)
    overall_score = Column(Float, default=0.0)
    risk_level = Column(String(32), default="LOW")  # HIGH, MEDIUM, LOW
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    check_task = relationship("CheckTask", back_populates="summaries")
    details = relationship("CheckResultDetail", back_populates="summary", cascade="all, delete-orphan")


class CheckResultDetail(Base):
    __tablename__ = "check_result_detail"

    id = Column(Integer, primary_key=True, autoincrement=True)
    summary_id = Column(Integer, ForeignKey("check_result_summary.id", ondelete="CASCADE"), nullable=False)
    source_block_id = Column(Integer, ForeignKey("text_block.id", ondelete="CASCADE"), nullable=True, index=True)
    target_report_id = Column(Integer, ForeignKey("report.id", ondelete="CASCADE"), nullable=False, index=True)
    target_block_id = Column(Integer, ForeignKey("text_block.id", ondelete="CASCADE"), nullable=True)
    source_text = Column(Text, nullable=True)
    target_text = Column(Text, nullable=True)
    similarity = Column(Float, nullable=False)
    mode = Column(String(32), nullable=False)  # IN_CLASS, HISTORY
    created_at = Column(DateTime, server_default=func.now())

    summary = relationship("CheckResultSummary", back_populates="details")
