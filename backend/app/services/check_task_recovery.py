from sqlalchemy.orm import Session

from app.models import CheckTask


def recover_stale_check_tasks(db: Session) -> list[int]:
    """Reset tasks left unfinished by a process restart for retry."""
    task_ids = [
        task_id
        for (task_id,) in db.query(CheckTask.id).filter(
            CheckTask.status.in_(("PENDING", "RUNNING"))
        ).all()
    ]
    if not task_ids:
        return []

    db.query(CheckTask).filter(CheckTask.id.in_(task_ids)).update(
        {CheckTask.status: "PENDING"},
        synchronize_session=False,
    )
    db.commit()
    return task_ids
