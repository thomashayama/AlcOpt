from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Date,
    DateTime,
    REAL,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()


class Container(Base):
    """A physical container that can hold liquid for a fermentation.

    Replaces the previous separate Vessel and Bottle tables. The role of the
    container (carboy, demijohn, bottle, etc.) is recorded as free-text in
    `container_type`. Containers are reusable across fermentations — the
    "what is currently in this container" relationship lives in
    ContainerFermentationLog, not on this row.
    """

    __tablename__ = "containers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    container_type = Column(String, nullable=False)
    volume_liters = Column(REAL)
    material = Column(String)
    empty_mass = Column(REAL)
    date_added = Column(Date, default=datetime.now)
    notes = Column(String)

    fermentation_logs = relationship(
        "ContainerFermentationLog",
        back_populates="container",
        foreign_keys="ContainerFermentationLog.container_id",
    )
    ingredient_additions = relationship(
        "IngredientAddition", back_populates="container"
    )
    reviews = relationship("Review", back_populates="container")


class Ingredient(Base):
    __tablename__ = "ingredients"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    sugar_content = Column(REAL)
    ingredient_type = Column(String)
    density = Column(REAL)
    price = Column(REAL)
    notes = Column(String)


class Fermentation(Base):
    __tablename__ = "fermentations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    end_mass = Column(REAL)

    container_logs = relationship(
        "ContainerFermentationLog", back_populates="fermentation"
    )
    measurements = relationship(
        "SpecificGravityMeasurement", back_populates="fermentation"
    )
    mass_measurements = relationship("MassMeasurement", back_populates="fermentation")
    reviews = relationship("Review", back_populates="fermentation")


class ContainerFermentationLog(Base):
    """Records that container X held fermentation Y over a date range.

    Replaces FermentationVesselLog and BottleLog. A row with `end_date IS NULL`
    is considered currently active. The invariant — that opening a new log row
    for a container closes any prior open row — is enforced in app code via
    `alcopt.database.utils.close_open_log`.
    """

    __tablename__ = "container_fermentation_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    container_id = Column(Integer, ForeignKey("containers.id"), nullable=False)
    fermentation_id = Column(Integer, ForeignKey("fermentations.id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    source_container_id = Column(Integer, ForeignKey("containers.id"))
    amount = Column(REAL)
    unit = Column(String)
    stage = Column(String)

    container = relationship(
        "Container", back_populates="fermentation_logs", foreign_keys=[container_id]
    )
    source_container = relationship("Container", foreign_keys=[source_container_id])
    fermentation = relationship("Fermentation", back_populates="container_logs")


class IngredientAddition(Base):
    """An ingredient added to (or removed from) a container at a specific time.

    Replaces FermentationIngredient and BottleIngredient. The container_id is
    the primary scope. The fermentation context is derived by joining against
    ContainerFermentationLog on (container_id, added_at). This lets you log
    additions to a container with no active fermentation (pre-soak, aging, etc.).

    Amount is signed: positive = added, negative = removed/sampled.
    """

    __tablename__ = "ingredient_additions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    container_id = Column(Integer, ForeignKey("containers.id"), nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)
    added_at = Column(DateTime, nullable=False)
    amount = Column(REAL)
    unit = Column(String)
    notes = Column(String)

    container = relationship("Container", back_populates="ingredient_additions")
    ingredient = relationship("Ingredient")


class SpecificGravityMeasurement(Base):
    __tablename__ = "specific_gravity_measurements"
    id = Column(Integer, primary_key=True, autoincrement=True)
    fermentation_id = Column(Integer, ForeignKey("fermentations.id"), nullable=False)
    measurement_date = Column(Date, nullable=False)
    specific_gravity = Column(REAL)
    fermentation = relationship("Fermentation", back_populates="measurements")


class MassMeasurement(Base):
    __tablename__ = "mass_measurements"
    id = Column(Integer, primary_key=True, autoincrement=True)
    fermentation_id = Column(Integer, ForeignKey("fermentations.id"), nullable=False)
    measurement_date = Column(Date, nullable=False)
    mass = Column(REAL, nullable=False)
    fermentation = relationship("Fermentation", back_populates="mass_measurements")


class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, autoincrement=True)
    container_id = Column(Integer, ForeignKey("containers.id"), nullable=False)
    name = Column(String)
    fermentation_id = Column(Integer, ForeignKey("fermentations.id"), nullable=False)
    overall_rating = Column(
        REAL,
        CheckConstraint("overall_rating >= 1.0 AND overall_rating <= 5.0"),
        nullable=False,
    )
    boldness = Column(
        REAL, CheckConstraint("boldness >= 1.0 AND boldness <= 5.0"), nullable=False
    )
    tannicity = Column(
        REAL, CheckConstraint("tannicity >= 1.0 AND tannicity <= 5.0"), nullable=False
    )
    sweetness = Column(
        REAL, CheckConstraint("sweetness >= 1.0 AND sweetness <= 5.0"), nullable=False
    )
    acidity = Column(
        REAL, CheckConstraint("acidity >= 1.0 AND acidity <= 5.0"), nullable=False
    )
    complexity = Column(
        REAL, CheckConstraint("complexity >= 1.0 AND complexity <= 5.0"), nullable=False
    )
    review_date = Column(Date, nullable=False)
    fermentation = relationship("Fermentation", back_populates="reviews")
    container = relationship("Container", back_populates="reviews")


if __name__ == "__main__":
    engine = create_engine("sqlite:///alcopt.db")
    Base.metadata.create_all(engine)
