import pandas as pd

from alcopt.database.models import (
    Container,
    ContainerFermentationLog,
    IngredientAddition,
    SpecificGravityMeasurement,
)


def all_ingredient_additions_info(session):
    additions = session.query(IngredientAddition).all()
    return pd.DataFrame(
        [
            {
                "ID": a.id,
                "Container ID": a.container_id,
                "Ingredient": a.ingredient.name if a.ingredient else None,
                "Amount": a.amount,
                "Unit": a.unit,
                "Added At": a.added_at,
            }
            for a in additions
        ]
    )


def all_container_log_info(session):
    logs = session.query(ContainerFermentationLog).all()
    return pd.DataFrame(
        [
            {
                "ID": log.id,
                "Container ID": log.container_id,
                "Fermentation ID": log.fermentation_id,
                "Stage": log.stage,
                "Source Container": log.source_container_id,
                "Start": log.start_date,
                "End": log.end_date,
                "Amount": log.amount,
                "Unit": log.unit,
            }
            for log in logs
        ]
    )


def all_sg_measurement_info(session):
    measurements = session.query(SpecificGravityMeasurement).all()
    return pd.DataFrame(
        [
            {
                "ID": m.id,
                "Fermentation ID": m.fermentation_id,
                "Specific Gravity": m.specific_gravity,
                "Measurement Date": m.measurement_date,
            }
            for m in measurements
        ]
    )


def all_containers_info(session, container_type: str | None = None):
    """Return container rows. Filter by `container_type` to get just bottles or
    just carboys, or pass None to get everything.
    """
    q = session.query(Container)
    if container_type is not None:
        q = q.filter(Container.container_type == container_type)
    return pd.DataFrame(
        [
            {
                "ID": c.id,
                "Type": c.container_type,
                "Volume (L)": c.volume_liters,
                "Material": c.material,
                "Empty Mass (g)": c.empty_mass,
                "Date Added": c.date_added,
                "Notes": c.notes,
            }
            for c in q.all()
        ]
    )
