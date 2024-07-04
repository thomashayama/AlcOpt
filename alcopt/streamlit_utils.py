import pandas as pd

from alcopt.sqlalchemy_models import FermentationIngredient, Bottle, FermentationVesselLog, SpecificGravityMeasurement, Vessel

def all_ferm_ingredients_info(session):
    fermentation_ingredients = session.query(FermentationIngredient).all()
    fermentation_ingredients_list = [
        {
        "ID": fermentation_ingredient.id,
        "Amount": fermentation_ingredient.amount,
        "Unit": fermentation_ingredient.unit,
        "Date Added": fermentation_ingredient.added_at,
        "Fermentation ID": fermentation_ingredient.fermentation_id
        }
        for fermentation_ingredient in fermentation_ingredients
    ]
    return pd.DataFrame(fermentation_ingredients_list)

def all_vessel_log_info(session):
    vessel_logs = session.query(FermentationVesselLog).all()
    vessel_logs_list = [
        {
        "ID": vessel_log.id,
        "Fermentation ID": vessel_log.fermentation_id,
        "Vessel ID": vessel_log.vessel_id,
        "Start Date": vessel_log.start_date,
        "End Date": vessel_log.end_date,
        }
        for vessel_log in vessel_logs
    ]
    return pd.DataFrame(vessel_logs_list)

def all_measurement_info(session):
    measurements = session.query(SpecificGravityMeasurement).all()
    measurements_list = [
        {
        "ID": measurement.id,
        "Fermentation ID": measurement.fermentation_id,
        "Specific Gravity": measurement.specific_gravity,
        "Measurement Date": measurement.measurement_date,
        }
        for measurement in measurements
    ]
    return pd.DataFrame(measurements_list)

def all_bottle_info(session):
    bottles = session.query(Bottle).all()
    bottles_list = [
        {
        "ID": bottle.id,
        "Volume (L)": bottle.volume_liters,
        "Empty Mass (g)": bottle.empty_mass,
        "Date Added": bottle.date_added,
        "Fermentation ID": bottle.fermentation_id,
        "Bottling Date": bottle.bottling_date
        }
        for bottle in bottles
    ]
    return pd.DataFrame(bottles_list)

def all_vessels_info(session):
    vessels = session.query(Vessel).all()
    vessels_list = [
        {
        "ID": vessel.id,
        "Volume (L)": vessel.volume_liters,
        "Empty Mass (g)": vessel.empty_mass,
        "Date Added": vessel.date_added,
        "Fermentation ID": vessel.fermentation_id
        }
        for vessel in vessels
    ]
    return pd.DataFrame(vessels_list)