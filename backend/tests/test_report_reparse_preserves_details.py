import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import (
    CheckResultDetail,
    CheckResultSummary,
    CheckTask,
    Clazz,
    Course,
    Experiment,
    Report,
    TextBlock,
    User,
)
from app.services.docx_parser_service import PARSER_VERSION
from app.services.report_service import reparse_report_if_needed


class ReportReparsePreservesDetailsTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
        )

        @event.listens_for(self.engine, "connect")
        def enable_foreign_keys(dbapi_connection, connection_record):
            dbapi_connection.execute("PRAGMA foreign_keys=ON")

        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        self.db = self.session_factory()

        user = User(username="owner", hashed_password="hash")
        self.db.add(user)
        self.db.flush()
        course = Course(user_id=user.id, name="Course")
        clazz = Clazz(user_id=user.id, name="Class")
        experiment = Experiment(user_id=user.id, course=course, title="Experiment")
        self.source_report = Report(
            user_id=user.id,
            clazz=clazz,
            experiment=experiment,
            file_name="source.docx",
            file_path="source.docx",
            status="PARSED",
            parser_version="1",
        )
        self.target_report = Report(
            user_id=user.id,
            clazz=clazz,
            experiment=experiment,
            file_name="target.docx",
            file_path="target.docx",
            status="PARSED",
            parser_version="1",
        )
        task = CheckTask(
            user_id=user.id,
            experiment=experiment,
            name="completed task",
            mode="IN_CLASS",
            status="COMPLETED",
        )
        self.db.add_all([course, clazz, experiment, self.source_report, self.target_report, task])
        self.db.flush()
        self.source_block = TextBlock(
            report_id=self.source_report.id,
            section_type="REFLECTION",
            content="old source block",
        )
        self.target_block = TextBlock(
            report_id=self.target_report.id,
            section_type="REFLECTION",
            content="old target block",
        )
        self.db.add_all([self.source_block, self.target_block])
        self.db.flush()
        summary = CheckResultSummary(
            check_task_id=task.id,
            report_id=self.source_report.id,
            overall_score=0.9,
            risk_level="HIGH",
        )
        self.db.add(summary)
        self.db.flush()
        self.detail = CheckResultDetail(
            summary_id=summary.id,
            source_block_id=self.source_block.id,
            target_report_id=self.target_report.id,
            target_block_id=self.target_block.id,
            source_text="saved source evidence",
            target_text="saved target evidence",
            similarity=0.9,
            mode="IN_CLASS",
        )
        self.db.add(self.detail)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def _reparse(self, report):
        parsed_blocks = [
            {
                "section_type": "REFLECTION",
                "content": "new parsed block",
                "parser_version": PARSER_VERSION,
            }
        ]
        with patch(
            "app.services.report_service._resolve_report_file_path",
            return_value=Path("placeholder.docx"),
        ), patch(
            "app.services.report_service.parse_docx_report",
            return_value=parsed_blocks,
        ):
            self.assertTrue(reparse_report_if_needed(self.db, report))

    def test_reparse_preserves_detail_after_source_and_target_blocks_are_replaced(self):
        self._reparse(self.source_report)
        self.db.expire_all()
        detail = self.db.query(CheckResultDetail).one()

        self.assertIsNone(detail.source_block_id)
        self.assertEqual(detail.target_block_id, self.target_block.id)
        self.assertEqual(detail.source_text, "saved source evidence")
        self.assertEqual(self.db.query(CheckResultSummary).count(), 1)

        self._reparse(self.target_report)
        self.db.expire_all()
        detail = self.db.query(CheckResultDetail).one()

        self.assertIsNone(detail.source_block_id)
        self.assertIsNone(detail.target_block_id)
        self.assertEqual(detail.target_text, "saved target evidence")
        self.assertEqual(self.db.query(CheckResultSummary).count(), 1)


if __name__ == "__main__":
    unittest.main()
