import asyncio
import unittest

from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.api.reports import api_get_report_result
from app.core.database import Base
from app.models import (
    CheckResultSummary,
    CheckTask,
    Clazz,
    Course,
    Experiment,
    Report,
    User,
)
from app.services.report_service import get_reports


class ReportResultApiTest(unittest.TestCase):
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

        self.user = User(username="owner", hashed_password="hash")
        other_user = User(username="other", hashed_password="hash")
        self.db.add_all([self.user, other_user])
        self.db.flush()

        course = Course(user_id=self.user.id, name="Course")
        clazz = Clazz(user_id=self.user.id, name="Class")
        experiment = Experiment(user_id=self.user.id, course=course, title="Experiment")
        self.report = Report(
            user=self.user,
            clazz=clazz,
            experiment=experiment,
            file_name="source.docx",
            file_path="source.docx",
            status="PARSED",
        )
        self.old_task = CheckTask(
            user=self.user,
            experiment=experiment,
            name="old task",
            mode="IN_CLASS",
            status="COMPLETED",
        )
        self.new_task = CheckTask(
            user=self.user,
            experiment=experiment,
            name="new task",
            mode="IN_CLASS",
            status="COMPLETED",
        )
        self.other_task = CheckTask(
            user=other_user,
            experiment=experiment,
            name="other task",
            mode="IN_CLASS",
            status="COMPLETED",
        )
        self.db.add_all([
            course,
            clazz,
            experiment,
            self.report,
            self.old_task,
            self.new_task,
            self.other_task,
        ])
        self.db.flush()
        self.db.add_all([
            CheckResultSummary(
                check_task_id=self.old_task.id,
                report_id=self.report.id,
                overall_score=0.2,
                risk_level="LOW",
            ),
            CheckResultSummary(
                check_task_id=self.new_task.id,
                report_id=self.report.id,
                overall_score=0.9,
                risk_level="HIGH",
            ),
        ])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def _get_result(self, task_id):
        return asyncio.run(
            api_get_report_result(
                report_id=self.report.id,
                taskId=task_id,
                db=self.db,
                current_user=self.user,
            )
        )

    def test_result_is_bound_to_the_requested_task(self):
        old_result = self._get_result(self.old_task.id)
        new_result = self._get_result(self.new_task.id)

        self.assertEqual(old_result["overallScore"], 0.2)
        self.assertEqual(new_result["overallScore"], 0.9)

    def test_report_list_exposes_the_explicit_latest_result_task_id(self):
        reports = get_reports(self.db, user_id=self.user.id)

        self.assertEqual(reports[0]["latestCheckTaskId"], self.new_task.id)

    def test_report_list_without_a_user_filter_keeps_completed_results(self):
        reports = get_reports(self.db)

        self.assertEqual(reports[0]["latestCheckTaskId"], self.new_task.id)

    def test_cannot_request_a_task_owned_by_another_user(self):
        with self.assertRaises(HTTPException) as context:
            self._get_result(self.other_task.id)

        self.assertEqual(context.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
