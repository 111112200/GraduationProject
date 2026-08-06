import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import (
    CheckResultDetail,
    CheckTask,
    Clazz,
    Course,
    Experiment,
    Report,
    TextBlock,
    User,
)
from app.services.check_task_service import execute_check_task


class CheckTaskBlockIdTest(unittest.TestCase):
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

        user = User(username="tester", hashed_password="hash")
        self.db.add(user)
        self.db.flush()

        course = Course(user_id=user.id, name="Course", code="C-1")
        clazz = Clazz(user_id=user.id, name="Class", grade="2026")
        experiment = Experiment(user_id=user.id, course=course, title="Experiment")
        source_report = Report(
            user_id=user.id,
            experiment=experiment,
            clazz=clazz,
            file_name="source.docx",
            file_path="source.docx",
            status="PARSED",
        )
        target_report = Report(
            user_id=user.id,
            experiment=experiment,
            clazz=clazz,
            file_name="target.docx",
            file_path="target.docx",
            status="PARSED",
        )
        source_block = TextBlock(
            report=source_report,
            section_type="REFLECTION",
            order_index=0,
            content="This is a sufficiently long source paragraph for matching.",
        )
        target_block = TextBlock(
            report=target_report,
            section_type="REFLECTION",
            order_index=0,
            content="This is a sufficiently long target paragraph for matching.",
        )
        task = CheckTask(
            user_id=user.id,
            experiment=experiment,
            name="Block id regression",
            mode="IN_CLASS",
            high_risk_threshold=0.8,
            similar_threshold=0.5,
        )
        task.reports.extend([source_report, target_report])
        self.db.add_all([
            user,
            course,
            clazz,
            experiment,
            source_report,
            target_report,
            source_block,
            target_block,
            task,
        ])
        self.db.commit()

        self.task_id = task.id
        self.source_report_id = source_report.id
        self.target_report_id = target_report.id
        self.source_block_id = source_block.id
        self.target_block_id = target_block.id

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_check_result_uses_text_block_ids(self):
        indexed_blocks = []

        def fake_add_blocks(blocks, task_id):
            indexed_blocks.extend(dict(block) for block in blocks)

        def fake_embed_texts(texts):
            return [[0.0] for _ in texts]

        def fake_query_similar_task(
            query_vectors,
            task_id,
            top_k,
            exclude_report_ids=None,
            per_source_limit=None,
        ):
            if self.target_report_id in (exclude_report_ids or set()):
                return []
            target_chunk = next(
                block
                for block in indexed_blocks
                if block["report_id"] == self.target_report_id
            )
            return [
                {
                    "source_index": 0,
                    "target_text": "matching target text",
                    "target_report_id": self.target_report_id,
                    "target_block_id": target_chunk["block_id"],
                    "similarity": 0.9,
                    "mode": "IN_CLASS",
                }
            ]

        with patch(
            "app.services.check_task_service.embed_texts",
            side_effect=fake_embed_texts,
        ), patch(
            "app.services.check_task_service.add_blocks_to_task",
            side_effect=fake_add_blocks,
        ), patch(
            "app.services.check_task_service.query_similar_task",
            side_effect=fake_query_similar_task,
        ), patch(
            "app.services.check_task_service.delete_task_collection",
        ):
            execute_check_task(self.db, self.task_id)

        task = self.db.get(CheckTask, self.task_id)
        detail = self.db.query(CheckResultDetail).one()

        self.assertEqual(task.status, "COMPLETED")
        self.assertEqual(detail.source_block_id, self.source_block_id)
        self.assertEqual(detail.target_block_id, self.target_block_id)
        self.assertNotEqual(detail.target_block_id, 0)

    def test_history_query_excludes_the_report_being_checked(self):
        task = self.db.get(CheckTask, self.task_id)
        task.mode = "HISTORY_ONLY"
        self.db.commit()
        exclusions = []

        def fake_embed_texts(texts):
            return [[0.0] for _ in texts]

        def fake_query_similar_library(
            query_vectors,
            user_id,
            top_k,
            exclude_report_ids=None,
            per_source_limit=None,
        ):
            exclusions.append(set(exclude_report_ids or set()))
            return []

        with patch(
            "app.services.report_service.reparse_report_if_needed",
        ), patch(
            "app.services.library_service.ensure_user_library_index",
        ), patch(
            "app.services.check_task_service.embed_texts",
            side_effect=fake_embed_texts,
        ), patch(
            "app.services.check_task_service.query_similar_library",
            side_effect=fake_query_similar_library,
        ), patch(
            "app.services.check_task_service.delete_task_collection",
        ):
            execute_check_task(self.db, self.task_id)

        self.assertEqual(
            exclusions,
            [{self.source_report_id}, {self.target_report_id}],
        )


if __name__ == "__main__":
    unittest.main()
