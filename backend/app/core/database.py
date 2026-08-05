from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})

if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app.models import Course, Clazz, Experiment, Report, TextBlock
    from app.models import CheckTask, CheckResultSummary, CheckResultDetail, LibraryReport
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_columns()


def _ensure_sqlite_columns():
    """Add nullable metadata columns to databases created by older versions."""
    if not DATABASE_URL.startswith("sqlite"):
        return

    additions = {
        "report": {
            "parse_warning": "TEXT",
            "parser_version": "VARCHAR(32)",
        },
        "text_block": {
            "source_kind": "VARCHAR(32)",
            "source_index": "INTEGER",
            "source_location": "TEXT",
            "section_title": "VARCHAR(256)",
            "heading_level": "INTEGER",
            "is_fallback": "INTEGER NOT NULL DEFAULT 0",
            "parser_version": "VARCHAR(32)",
        },
        "check_result_detail": {
            "source_start": "INTEGER",
            "source_end": "INTEGER",
            "target_start": "INTEGER",
            "target_end": "INTEGER",
        },
    }

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    with engine.begin() as connection:
        for table_name, columns in additions.items():
            if table_name not in table_names:
                continue
            existing = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, ddl in columns.items():
                if column_name in existing:
                    continue
                connection.execute(
                    text(
                        f'ALTER TABLE "{table_name}" '
                        f'ADD COLUMN "{column_name}" {ddl}'
                    )
                )
