from sqlalchemy import create_engine, Column, Integer, String, Date, REAL, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()

class Vessel(Base):
    __tablename__ = 'vessels'
    id = Column(Integer, primary_key=True, autoincrement=True)
    fermentation_id = Column(Integer, ForeignKey('fermentations.id'), nullable=True)
    volume_liters = Column(REAL)
    material = Column(String)
    empty_mass = Column(REAL)
    date_added = Column(Date, default=datetime.now())
    # fermentation = relationship("Fermentation", back_populates="bottles")

class Ingredient(Base):
    __tablename__ = 'ingredients'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    sugar_content = Column(REAL)
    ingredient_type = Column(String)
    density = Column(REAL)
    price = Column(REAL)
    notes = Column(String)

class Fermentation(Base):
    __tablename__ = 'fermentations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    end_mass = Column(REAL)
    vessel_logs = relationship("FermentationVesselLog", back_populates="fermentation")
    ingredients = relationship("FermentationIngredient", back_populates="fermentation")
    measurements = relationship("SpecificGravityMeasurement", back_populates="fermentation")
    bottles = relationship("Bottle", back_populates="fermentation")
    bottle_logs = relationship("BottleLog", back_populates="fermentation")
    reviews = relationship("Review", back_populates="fermentation")

class FermentationVesselLog(Base):
    __tablename__ = 'fermentation_vessel_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    fermentation_id = Column(Integer, ForeignKey('fermentations.id'), nullable=False)
    vessel_id = Column(Integer, ForeignKey('vessels.id'), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    fermentation = relationship("Fermentation", back_populates="vessel_logs")
    vessel = relationship("Vessel")

class FermentationIngredient(Base):
    __tablename__ = 'fermentation_ingredients'
    id = Column(Integer, primary_key=True, autoincrement=True)
    fermentation_id = Column(Integer, ForeignKey('fermentations.id'), nullable=False)
    ingredient_id = Column(Integer, ForeignKey('ingredients.id'), nullable=False)
    amount = Column(REAL)
    unit = Column(String)
    added_at = Column(Date, nullable=False)
    fermentation = relationship("Fermentation", back_populates="ingredients")
    ingredient = relationship("Ingredient")

class SpecificGravityMeasurement(Base):
    __tablename__ = 'specific_gravity_measurements'
    id = Column(Integer, primary_key=True, autoincrement=True)
    fermentation_id = Column(Integer, ForeignKey('fermentations.id'), nullable=False)
    measurement_date = Column(Date, nullable=False)
    specific_gravity = Column(REAL)
    fermentation = relationship("Fermentation", back_populates="measurements")

class Bottle(Base):
    __tablename__ = 'bottles'
    id = Column(Integer, primary_key=True, autoincrement=True)
    fermentation_id = Column(Integer, ForeignKey('fermentations.id'), nullable=True)
    bottling_date = Column(Date, nullable=True, default=None)
    volume_liters = Column(REAL)
    empty_mass = Column(REAL)
    date_added = Column(Date, default=datetime.now())
    fermentation = relationship("Fermentation", back_populates="bottles")
    ingredients = relationship("BottleIngredient", back_populates="bottle")
    reviews = relationship("Review", back_populates="bottle")

class BottleIngredient(Base):
    __tablename__ = 'bottle_ingredients'
    id = Column(Integer, primary_key=True, autoincrement=True)
    bottle_id = Column(Integer, ForeignKey('bottles.id'), nullable=False)
    ingredient_id = Column(Integer, ForeignKey('ingredients.id'), nullable=False)
    amount = Column(REAL)
    unit = Column(String)
    added_at = Column(Date, nullable=False)
    bottle = relationship("Bottle", back_populates="ingredients")
    ingredient = relationship("Ingredient")

class BottleLog(Base):
    __tablename__ = 'bottle_log'
    id = Column(Integer, primary_key=True, autoincrement=True)
    fermentation_id = Column(Integer, ForeignKey('fermentations.id'), nullable=False)
    vessel_id = Column(Integer, ForeignKey('vessels.id'), nullable=False)
    bottle_id = Column(Integer, ForeignKey('bottles.id'), nullable=False)
    bottling_date = Column(Date, nullable=False)
    amount = Column(REAL)
    unit = Column(String)
    fermentation = relationship("Fermentation", back_populates="bottle_logs")
    vessel = relationship("Vessel")

class Review(Base):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True, autoincrement=True)
    bottle_id = Column(Integer, ForeignKey('bottles.id'), nullable=False)
    name = Column(String)
    fermentation_id = Column(Integer, ForeignKey('fermentations.id'), nullable=False)
    overall_rating = Column(REAL, CheckConstraint('overall_rating >= 1.0 AND overall_rating <= 5.0'), nullable=False)
    boldness = Column(REAL, CheckConstraint('boldness >= 1.0 AND boldness <= 5.0'), nullable=False)
    tannicity = Column(REAL, CheckConstraint('tannicity >= 1.0 AND tannicity <= 5.0'), nullable=False)
    sweetness = Column(REAL, CheckConstraint('sweetness >= 1.0 AND sweetness <= 5.0'), nullable=False)
    acidity = Column(REAL, CheckConstraint('acidity >= 1.0 AND acidity <= 5.0'), nullable=False)
    complexity = Column(REAL, CheckConstraint('complexity >= 1.0 AND complexity <= 5.0'), nullable=False)
    review_date = Column(Date, nullable=False)
    fermentation = relationship("Fermentation", back_populates="reviews")
    bottle = relationship("Bottle", back_populates="reviews")

if __name__ == '__main__':
    # Set up the database
    engine = create_engine('sqlite:///alcopt.db')
    Base.metadata.create_all(engine)
