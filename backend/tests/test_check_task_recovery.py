import unittest

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import CheckTask, Clazz, Course, Experiment, User
from app.services.check_task_recovery import recover_stale_check_tasks


class CheckTaskRecoveryTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
        )

        @event.listens_for(self.engine, "connect")
        def enable_foreign_keys(dbapi_connection, connection_record):
            dbapi_connection.execute("PRAGMA foreign_keys=ON")

        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()

        user = User(username="recovery", hashed_password="hash")
        course = Course(user=user, name="Course")
        experiment = Experiment(user=user, course=course, title="Experiment")
        self.db.add_all([
            user,
            course,
            experiment,
            CheckTask(
                user=user,
                experiment=experiment,
                name="pending",
                mode="BOTH",
                status="PENDING",
            ),
            CheckTask(
                user=user,
                experiment=experiment,
                name="running",
                mode="BOTH",
                status="RUNNING",
            ),
            CheckTask(
                user=user,
                experiment=experiment,
                name="completed",
                mode="BOTH",
                status="COMPLETED",
            ),
        ])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_pending_and_running_tasks_are_reset_for_retry(self):
        recovered = recover_stale_check_tasks(self.db)
        statuses = {
            task.name: task.status
            for task in self.db.query(CheckTask).all()
        }

        self.assertEqual(recovered, [1, 2])
        self.assertEqual(statuses["pending"], "PENDING")
        self.assertEqual(statuses["running"], "PENDING")
        self.assertEqual(statuses["completed"], "COMPLETED")


if __name__ == "__main__":
    unittest.main()
