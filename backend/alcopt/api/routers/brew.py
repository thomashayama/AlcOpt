from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from alcopt.api.dependencies import get_db, require_admin
from alcopt.api.schemas import (
    AbvCalcRequest,
    ContainerLogOut,
    EmptyContainerResponse,
    FermentationActiveOut,
    FermentationEndRequest,
    FermentationOut,
    IngredientAdditionCreate,
    IngredientAdditionResponse,
    IngredientCreate,
    IngredientOut,
    MassMeasurementCreate,
    MassMeasurementOut,
    RackRequest,
    BottleRequest,
    SgMeasurementCreate,
    SgMeasurementOut,
    StartFermentationRequest,
)
from alcopt.database.models import (
    Container,
    ContainerFermentationLog,
    Fermentation,
    Ingredient,
    IngredientAddition,
    MassMeasurement,
    SpecificGravityMeasurement,
)
from alcopt.database.utils import close_open_log, current_fermentation_log
from alcopt.streamlit_utils import (
    all_container_log_info,
    all_ingredient_additions_info,
    all_sg_measurement_info,
)
from alcopt.database.utils import all_mass_measurement_info
from alcopt.utils import (
    BENCHMARK,
    YEAST,
    calculate_max_potential_abv,
    str2unit,
)

router = APIRouter(prefix="/api/brew", tags=["brew"])


def _get_container(db: Session, container_id: int) -> Container:
    container = db.get(Container, container_id)
    if not container:
        raise HTTPException(404, f"Container {container_id} not found")
    return container


def _resolve_dt(explicit: Optional[datetime], fallback_date: date) -> datetime:
    """Use the explicit datetime if provided, else combine the date with now()."""
    if explicit is not None:
        return explicit
    return datetime.combine(fallback_date, datetime.now().time())


def _commit_or_conflict(db: Session, message: str = "Concurrent update on container"):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, message)


@router.post("/fermentations", response_model=ContainerLogOut)
def start_fermentation(
    body: StartFermentationRequest,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    _get_container(db, body.container_id)
    start_dt = body.start_datetime or datetime.combine(
        body.start_date, datetime.min.time()
    )
    fermentation = Fermentation(start_date=start_dt)
    db.add(fermentation)
    db.flush()
    close_open_log(db, body.container_id, start_dt)

    log = ContainerFermentationLog(
        container_id=body.container_id,
        fermentation_id=fermentation.id,
        start_date=start_dt,
        stage=body.stage,
    )
    db.add(log)
    _commit_or_conflict(db)
    db.refresh(log)
    return log


@router.get("/fermentations")
def list_fermentation_logs(
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    return all_container_log_info(db)


@router.get("/fermentations/active", response_model=list[FermentationActiveOut])
def list_active_fermentations(
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    rows = (
        db.query(ContainerFermentationLog, Container, Fermentation)
        .join(Container, Container.id == ContainerFermentationLog.container_id)
        .join(Fermentation, Fermentation.id == ContainerFermentationLog.fermentation_id)
        .filter(
            ContainerFermentationLog.end_date.is_(None),
            Fermentation.end_date.is_(None),
        )
        .order_by(Fermentation.start_date.desc())
        .all()
    )
    return [
        FermentationActiveOut(
            fermentation_id=f.id,
            start_date=f.start_date,
            container_id=c.id,
            container_type=c.container_type,
            stage=log.stage,
            log_start_date=log.start_date,
        )
        for log, c, f in rows
    ]


@router.patch("/fermentations/{fermentation_id}", response_model=FermentationOut)
def end_fermentation(
    fermentation_id: int,
    body: FermentationEndRequest,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    fermentation = db.get(Fermentation, fermentation_id)
    if not fermentation:
        raise HTTPException(404, f"Fermentation {fermentation_id} not found")

    if body.end_datetime is not None:
        end_dt = body.end_datetime
    elif body.end_date is not None:
        end_dt = datetime.combine(body.end_date, datetime.now().time())
    else:
        end_dt = datetime.now()

    fermentation.end_date = end_dt
    if body.end_mass is not None:
        fermentation.end_mass = body.end_mass

    open_logs = (
        db.query(ContainerFermentationLog)
        .filter(
            ContainerFermentationLog.fermentation_id == fermentation_id,
            ContainerFermentationLog.end_date.is_(None),
        )
        .all()
    )
    for log in open_logs:
        log.end_date = end_dt

    db.commit()
    db.refresh(fermentation)
    return fermentation


@router.post("/ingredients", response_model=IngredientOut)
def create_ingredient(
    body: IngredientCreate,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    ingredient = Ingredient(
        name=body.name,
        sugar_content=body.sugar_content,
        ingredient_type=body.ingredient_type,
        density=body.density,
        price=body.price,
        notes=body.notes,
    )
    db.add(ingredient)
    db.commit()
    db.refresh(ingredient)
    return ingredient


@router.get("/ingredients", response_model=list[IngredientOut])
def list_ingredients(
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    return db.query(Ingredient).order_by(Ingredient.name).all()


@router.post("/additions", response_model=IngredientAdditionResponse)
def add_ingredient_addition(
    body: IngredientAdditionCreate,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    _get_container(db, body.container_id)
    ingredient = (
        db.query(Ingredient).filter(Ingredient.name == body.ingredient_name).first()
    )
    if not ingredient:
        raise HTTPException(404, f"Ingredient '{body.ingredient_name}' not found")

    amount = body.ending_amount - body.starting_amount
    added_at = _resolve_dt(body.added_at, body.date)

    addition = IngredientAddition(
        container_id=body.container_id,
        ingredient_id=ingredient.id,
        amount=amount,
        unit=body.unit,
        added_at=added_at,
    )
    db.add(addition)
    db.commit()
    db.refresh(addition)

    log = current_fermentation_log(db, body.container_id, added_at)
    return {
        "id": addition.id,
        "fermentation_id": log.fermentation_id if log else None,
        "message": "Ingredient added",
    }


@router.get("/additions")
def list_additions(
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    return all_ingredient_additions_info(db)


@router.post("/sg-measurements", response_model=SgMeasurementOut)
def add_sg_measurement(
    body: SgMeasurementCreate,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    _get_container(db, body.container_id)
    measurement_dt = _resolve_dt(body.measurement_datetime, body.measurement_date)
    log = current_fermentation_log(db, body.container_id, measurement_dt)
    if not log:
        raise HTTPException(400, "No active fermentation for this container")

    measurement = SpecificGravityMeasurement(
        fermentation_id=log.fermentation_id,
        measurement_date=body.measurement_date,
        specific_gravity=body.specific_gravity,
    )
    db.add(measurement)
    db.commit()
    db.refresh(measurement)
    return measurement


@router.get("/sg-measurements")
def list_sg_measurements(
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    return all_sg_measurement_info(db)


@router.post("/mass-measurements", response_model=MassMeasurementOut)
def add_mass_measurement(
    body: MassMeasurementCreate,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    _get_container(db, body.container_id)
    measurement_dt = _resolve_dt(body.measurement_datetime, body.measurement_date)
    log = current_fermentation_log(db, body.container_id, measurement_dt)
    if not log:
        raise HTTPException(400, "No active fermentation for this container")

    measurement = MassMeasurement(
        fermentation_id=log.fermentation_id,
        measurement_date=body.measurement_date,
        mass=body.mass,
    )
    db.add(measurement)
    db.commit()
    db.refresh(measurement)
    return measurement


@router.get("/mass-measurements")
def list_mass_measurements(
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    return all_mass_measurement_info(db)


@router.post("/rack", response_model=ContainerLogOut)
def rack(
    body: RackRequest,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    if body.from_container_id == body.to_container_id:
        raise HTTPException(400, "Source and destination must differ")
    _get_container(db, body.from_container_id)
    _get_container(db, body.to_container_id)

    rack_dt = _resolve_dt(body.at, body.date)
    source_log = current_fermentation_log(db, body.from_container_id, rack_dt)
    if not source_log:
        raise HTTPException(400, "No active fermentation on source container")

    close_open_log(db, body.from_container_id, rack_dt)
    db.flush()
    close_open_log(db, body.to_container_id, rack_dt)
    db.flush()

    log = ContainerFermentationLog(
        container_id=body.to_container_id,
        fermentation_id=source_log.fermentation_id,
        start_date=rack_dt,
        source_container_id=body.from_container_id,
        stage=body.stage,
    )
    db.add(log)
    _commit_or_conflict(db, "Another rack/bottle/start happened for this container")
    db.refresh(log)
    return log


@router.post("/bottle", response_model=ContainerLogOut)
def bottle(
    body: BottleRequest,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    if body.from_container_id == body.to_container_id:
        raise HTTPException(400, "Source and destination must differ")
    _get_container(db, body.from_container_id)
    _get_container(db, body.to_container_id)

    bottle_dt = _resolve_dt(body.at, body.date)
    source_log = current_fermentation_log(db, body.from_container_id, bottle_dt)
    if not source_log:
        raise HTTPException(400, "No active fermentation on source container")

    close_open_log(db, body.to_container_id, bottle_dt)
    db.flush()

    log = ContainerFermentationLog(
        container_id=body.to_container_id,
        fermentation_id=source_log.fermentation_id,
        start_date=bottle_dt,
        source_container_id=body.from_container_id,
        amount=body.amount,
        unit=body.unit,
        stage="bottled",
    )
    db.add(log)
    _commit_or_conflict(db, "Another rack/bottle/start happened for this container")
    db.refresh(log)
    return log


@router.post("/empty/{container_id}", response_model=EmptyContainerResponse)
def empty_container(
    container_id: int,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    _get_container(db, container_id)
    closed = close_open_log(db, container_id, datetime.now())
    db.commit()
    if closed:
        return {"message": f"Container {container_id} emptied"}
    return {"message": f"Container {container_id} had no open log"}


@router.post("/calculate-abv")
def calculate_abv(
    body: AbvCalcRequest,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    container = _get_container(db, body.container_id)

    ingredients_data = []
    for item in body.ingredients:
        ingredient = db.get(Ingredient, item.ingredient_id)
        if not ingredient:
            raise HTTPException(404, f"Ingredient {item.ingredient_id} not found")
        if item.unit not in str2unit:
            raise HTTPException(400, f"Unknown unit: {item.unit}")
        ingredients_data.append(
            {
                "ingredient_type": ingredient.ingredient_type or "Liquid",
                "amount": item.amount * str2unit[item.unit],
                "sugar_content": ingredient.sugar_content or 0,
                "density": ingredient.density or 1.0,
            }
        )

    max_abv, sugar_content, volume = calculate_max_potential_abv(ingredients_data)

    benchmarks = []
    for b in BENCHMARK:
        entry = {"name": b["name"], "abv": b["abv"]}
        try:
            entry["rs"] = float(b["rs"].asNumber())
        except (AttributeError, TypeError):
            entry["rs"] = 0
        benchmarks.append(entry)

    return {
        "max_abv": float(max_abv) if max_abv else 0,
        "sugar_content_g_per_l": float(sugar_content.asNumber())
        if sugar_content
        else 0,
        "volume_l": float(volume.asNumber()) if volume else 0,
        "container_volume_l": container.volume_liters,
        "benchmarks": benchmarks,
        "yeast": YEAST,
    }
