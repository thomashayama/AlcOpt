from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from alcopt.api.dependencies import get_db, require_admin
from alcopt.api.schemas import (
    ContainerCreate,
    ContainerInfoResponse,
    ContainerOut,
    ReviewOut,
    SgMeasurementOut,
)
from alcopt.database.models import Container, Review, SpecificGravityMeasurement
from alcopt.database.queries import get_fermentation_ingredient_additions
from alcopt.database.utils import current_fermentation_log, latest_fermentation_log
from alcopt.utils import sg_diff_to_abv, sg_to_sugar

router = APIRouter(prefix="/api/containers", tags=["containers"])


@router.post("", response_model=ContainerOut)
def create_container(
    body: ContainerCreate,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    container = Container(
        container_type=body.container_type,
        volume_liters=body.volume_liters,
        material=body.material,
        empty_mass=body.empty_mass,
        date_added=body.date_added,
        notes=body.notes,
    )
    db.add(container)
    db.commit()
    db.refresh(container)
    return container


@router.get("", response_model=list[ContainerOut])
def list_containers(
    container_type: str | None = None,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    q = db.query(Container)
    if container_type:
        q = q.filter(Container.container_type == container_type)
    return q.all()


@router.get("/{container_id}", response_model=ContainerInfoResponse)
def get_container_info(container_id: int, db: Session = Depends(get_db)):
    container = db.query(Container).get(container_id)
    if not container:
        raise HTTPException(404, f"Container {container_id} not found")

    log = current_fermentation_log(db, container_id)
    if not log:
        log = latest_fermentation_log(db, container_id)

    fermentation = log.fermentation if log else None

    ingredients = []
    sg_measurements = []
    abv = None
    residual_sugar = None

    if fermentation:
        additions = get_fermentation_ingredient_additions(db, fermentation.id)
        start = fermentation.start_date
        for a in additions:
            days = (a.added_at.date() - start).days if a.added_at and start else 0
            ingredients.append(
                {
                    "ingredient": a.ingredient.name if a.ingredient else None,
                    "amount": a.amount,
                    "unit": a.unit,
                    "days_from_start": days,
                    "price": a.ingredient.price if a.ingredient else None,
                }
            )

        sg_rows = (
            db.query(SpecificGravityMeasurement)
            .filter(SpecificGravityMeasurement.fermentation_id == fermentation.id)
            .order_by(SpecificGravityMeasurement.measurement_date)
            .all()
        )
        sg_measurements = sg_rows

        if len(sg_rows) >= 2:
            sgs = [m.specific_gravity for m in sg_rows]
            initial_sg = max(sgs)
            final_sg = min(sgs)
            abv = sg_diff_to_abv(initial_sg - final_sg)
            residual_sugar = sg_to_sugar(final_sg)

    reviews = (
        db.query(Review)
        .filter(Review.container_id == container_id)
        .order_by(Review.review_date.desc())
        .all()
    )

    return ContainerInfoResponse(
        container=ContainerOut.model_validate(container),
        fermentation=fermentation,
        fermentation_log=log,
        ingredients=ingredients,
        sg_measurements=[SgMeasurementOut.model_validate(m) for m in sg_measurements],
        reviews=[ReviewOut.model_validate(r) for r in reviews],
        abv=abv,
        residual_sugar=residual_sugar,
    )
