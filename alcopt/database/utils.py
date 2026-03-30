from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

from alcopt.database.models import Base, MassMeasurement
from alcopt.config import DATABASE_URL

DATABASE_URI = DATABASE_URL

connect_args = {}
if DATABASE_URI.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URI, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    import alcopt.database.models  # Ensure models are imported
    Base.metadata.create_all(bind=engine)
init_db()

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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