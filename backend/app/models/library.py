from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base


class LibraryReport(Base):
    """底库报告登记表：记录哪些报告已加入语义指纹底库"""
    __tablename__ = "library_report"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("report.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (UniqueConstraint("report_id", name="uq_library_report_id"),)
