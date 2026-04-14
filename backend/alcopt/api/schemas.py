from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator


class ContainerOut(BaseModel):
    id: int
    container_type: str
    volume_liters: float | None = None
    material: str | None = None
    empty_mass: float | None = None
    date_added: date | None = None
    notes: str | None = None

    model_config = {"from_attributes": True}


class ContainerCreate(BaseModel):
    container_type: str
    volume_liters: float | None = None
    material: str | None = None
    empty_mass: float | None = None
    date_added: date | None = None
    notes: str | None = None


class IngredientOut(BaseModel):
    id: int
    name: str
    sugar_content: float | None = None
    ingredient_type: str | None = None
    density: float | None = None
    price: float | None = None
    notes: str | None = None

    model_config = {"from_attributes": True}


class IngredientCreate(BaseModel):
    name: str
    sugar_content: float = 0.0
    ingredient_type: str = "Liquid"
    density: float = 1.0
    price: float = 0.0
    notes: str = ""


class FermentationOut(BaseModel):
    id: int
    start_date: datetime
    end_date: datetime | None = None
    end_mass: float | None = None

    model_config = {"from_attributes": True}


class ContainerLogOut(BaseModel):
    id: int
    container_id: int
    fermentation_id: int
    start_date: datetime
    end_date: datetime | None = None
    source_container_id: int | None = None
    amount: float | None = None
    unit: str | None = None
    stage: str | None = None

    model_config = {"from_attributes": True}


class ReviewOut(BaseModel):
    id: int
    container_id: int
    name: str | None = None
    fermentation_id: int
    overall_rating: float
    boldness: float
    tannicity: float
    sweetness: float
    acidity: float
    complexity: float
    review_date: date

    model_config = {"from_attributes": True}


class ReviewCreate(BaseModel):
    container_id: int
    tasting_date: date
    email: str | None = None
    overall_rating: float = Field(ge=1.0, le=5.0)
    boldness: float = Field(ge=1.0, le=5.0)
    tannicity: float = Field(ge=1.0, le=5.0)
    sweetness: float = Field(ge=1.0, le=5.0)
    acidity: float = Field(ge=1.0, le=5.0)
    complexity: float = Field(ge=1.0, le=5.0)


class SgMeasurementOut(BaseModel):
    id: int
    fermentation_id: int
    measurement_date: date
    specific_gravity: float | None = None

    model_config = {"from_attributes": True}


class SgMeasurementCreate(BaseModel):
    container_id: int
    measurement_date: date
    measurement_datetime: datetime | None = None
    specific_gravity: float = Field(ge=0.8, le=1.2)


class MassMeasurementOut(BaseModel):
    id: int
    fermentation_id: int
    measurement_date: date
    mass: float

    model_config = {"from_attributes": True}


class MassMeasurementCreate(BaseModel):
    container_id: int
    measurement_date: date
    measurement_datetime: datetime | None = None
    mass: float = Field(gt=0)


class IngredientAdditionOut(BaseModel):
    id: int
    container_id: int
    ingredient_id: int
    added_at: datetime
    amount: float | None = None
    unit: str | None = None
    notes: str | None = None
    ingredient_name: str | None = None

    model_config = {"from_attributes": True}


VALID_UNITS = {"kg", "g", "L", "mL", "tsp", "tbsp"}


def _validate_unit(v: str) -> str:
    if v not in VALID_UNITS:
        raise ValueError(
            f"Invalid unit '{v}'. Must be one of: {', '.join(sorted(VALID_UNITS))}"
        )
    return v


class IngredientAdditionCreate(BaseModel):
    container_id: int
    ingredient_name: str
    date: date
    added_at: datetime | None = None
    starting_amount: float = 0.0
    ending_amount: float = 0.0
    unit: str = "g"

    @field_validator("unit")
    @classmethod
    def validate_unit(cls, v: str) -> str:
        return _validate_unit(v)


class StartFermentationRequest(BaseModel):
    container_id: int
    start_date: date
    start_datetime: datetime | None = None
    stage: str = "primary"


class RackRequest(BaseModel):
    from_container_id: int
    to_container_id: int
    date: date
    at: datetime | None = None
    stage: str = "secondary"


class BottleRequest(BaseModel):
    from_container_id: int
    to_container_id: int
    date: date
    at: datetime | None = None
    amount: float = 0.0
    unit: str = "g"

    @field_validator("unit")
    @classmethod
    def validate_unit(cls, v: str) -> str:
        return _validate_unit(v)


class FermentationEndRequest(BaseModel):
    end_datetime: datetime | None = None
    end_date: date | None = None
    end_mass: float | None = None


class FermentationActiveOut(BaseModel):
    fermentation_id: int
    start_date: datetime
    container_id: int
    container_type: str
    stage: str | None = None
    log_start_date: datetime


class ContainerUpdate(BaseModel):
    container_type: str | None = None
    volume_liters: float | None = None
    material: str | None = None
    empty_mass: float | None = None
    date_added: date | None = None
    notes: str | None = None


class LeaderboardEntry(BaseModel):
    rank: int
    fermentation_id: int
    avg_rating: float
    num_ratings: int


class UserInfo(BaseModel):
    email: str
    picture: str = ""
    name: str = ""
    is_admin: bool = False


class AbvCalcIngredient(BaseModel):
    ingredient_id: int
    amount: float
    unit: str


class AbvCalcRequest(BaseModel):
    container_id: int
    ingredients: list[AbvCalcIngredient]


class IngredientAdditionResponse(BaseModel):
    id: int
    fermentation_id: int | None = None
    message: str


class EmptyContainerResponse(BaseModel):
    message: str


class ContainerInfoResponse(BaseModel):
    container: ContainerOut
    fermentation: FermentationOut | None = None
    fermentation_log: ContainerLogOut | None = None
    ingredients: list[dict] = []
    sg_measurements: list[SgMeasurementOut] = []
    reviews: list[ReviewOut] = []
    abv: float | None = None
    residual_sugar: float | None = None
