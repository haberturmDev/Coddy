from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def create_sqlite_engine(db_path: str = "coddy.db") -> Engine:
    return create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
