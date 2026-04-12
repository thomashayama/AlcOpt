from alcopt.database.models import (
    Container,
    ContainerFermentationLog,
    IngredientAddition,
    SpecificGravityMeasurement,
)


def all_ingredient_additions_info(session):
    additions = session.query(IngredientAddition).all()
    return [
        {
            "id": a.id,
            "container_id": a.container_id,
            "ingredient": a.ingredient.name if a.ingredient else None,
            "amount": a.amount,
            "unit": a.unit,
            "added_at": str(a.added_at) if a.added_at else None,
        }
        for a in additions
    ]


def all_container_log_info(session):
    logs = session.query(ContainerFermentationLog).all()
    return [
        {
            "id": log.id,
            "container_id": log.container_id,
            "fermentation_id": log.fermentation_id,
            "stage": log.stage,
            "source_container_id": log.source_container_id,
            "start_date": str(log.start_date) if log.start_date else None,
            "end_date": str(log.end_date) if log.end_date else None,
            "amount": log.amount,
            "unit": log.unit,
        }
        for log in logs
    ]


def all_sg_measurement_info(session):
    measurements = session.query(SpecificGravityMeasurement).all()
    return [
        {
            "id": m.id,
            "fermentation_id": m.fermentation_id,
            "specific_gravity": m.specific_gravity,
            "measurement_date": str(m.measurement_date) if m.measurement_date else None,
        }
        for m in measurements
    ]


def all_containers_info(session, container_type: str | None = None):
    q = session.query(Container)
    if container_type is not None:
        q = q.filter(Container.container_type == container_type)
    return [
        {
            "id": c.id,
            "container_type": c.container_type,
            "volume_liters": c.volume_liters,
            "material": c.material,
            "empty_mass": c.empty_mass,
            "date_added": str(c.date_added) if c.date_added else None,
            "notes": c.notes,
        }
        for c in q.all()
    ]
