from contextlib import contextmanager
from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from alcopt.database.models import Base, ContainerFermentationLog, MassMeasurement
from alcopt.config import DATABASE_URL

DATABASE_URI = DATABASE_URL

connect_args = {}
if DATABASE_URI.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URI, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


init_db()


@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def close_open_log(
    db: Session, container_id: int, at: datetime
) -> Optional[ContainerFermentationLog]:
    """Close any currently-open fermentation log for `container_id` at time `at`.

    Returns the row that was closed, or None if there was no open log. Caller is
    responsible for committing.
    """
    open_log = (
        db.query(ContainerFermentationLog)
        .filter(
            ContainerFermentationLog.container_id == container_id,
            ContainerFermentationLog.end_date.is_(None),
        )
        .order_by(ContainerFermentationLog.start_date.desc())
        .first()
    )
    if open_log is not None:
        open_log.end_date = at
    return open_log


def current_fermentation_log(
    db: Session, container_id: int, at: Optional[datetime] = None
) -> Optional[ContainerFermentationLog]:
    """Return the fermentation log row for `container_id` active at `at`.

    If `at` is None, returns the currently-open log (end_date IS NULL). If
    multiple windows match, returns the one with the latest start_date.
    """
    q = db.query(ContainerFermentationLog).filter(
        ContainerFermentationLog.container_id == container_id
    )
    if at is None:
        q = q.filter(ContainerFermentationLog.end_date.is_(None))
    else:
        q = q.filter(ContainerFermentationLog.start_date <= at).filter(
            (ContainerFermentationLog.end_date.is_(None))
            | (ContainerFermentationLog.end_date >= at)
        )
    return q.order_by(ContainerFermentationLog.start_date.desc()).first()


def latest_fermentation_log(
    db: Session, container_id: int
) -> Optional[ContainerFermentationLog]:
    """Return the most recent log row for `container_id` regardless of state.

    Useful for resolving "what fermentation does this bottle hold" when the
    bottle's log was never explicitly closed.
    """
    return (
        db.query(ContainerFermentationLog)
        .filter(ContainerFermentationLog.container_id == container_id)
        .order_by(ContainerFermentationLog.start_date.desc())
        .first()
    )


def all_mass_measurement_info(db):
    return [
        {
            "ID": m.id,
            "Fermentation ID": m.fermentation_id,
            "Date": m.measurement_date,
            "Mass (g)": m.mass,
        }
        for m in db.query(MassMeasurement).all()
    ]
