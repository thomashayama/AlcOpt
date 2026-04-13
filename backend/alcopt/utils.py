from unum import Unum
from unum import units
from sqlalchemy import func
from sqlalchemy.orm import Session

from alcopt.database.models import (
    Fermentation,
    Review,
    SpecificGravityMeasurement,
    IngredientAddition,
)


mL = Unum.unit("mL", 0.001 * units.L)
tsp = Unum.unit("tsp", 0.00492892 * units.L)
tbsp = Unum.unit("tbsp", 3 * tsp)


def unit2str(unit):
    return str(unit.strUnit())[1:-1]


str2unit = {
    "kg": units.kg,
    "g": units.g,
    "L": units.L,
    "mL": mL,
    "tsp": tsp,
    "tbsp": tbsp,
    "u": units.u,
}

MASS_UNITS = [
    "kg",
    "g",
]

VOLUME_UNITS = [
    "L",
    "mL",
    "tsp",
    "tbsp",
    "cup",
]


BENCHMARK = [
    {"name": "Beer", "abv": 5.0, "rs": 1 * units.g / units.L},
    {"name": "Moscato", "abv": 7.0, "rs": 200 * units.g / units.L},
    {"name": "Riesling", "abv": 9.0, "rs": 7 * units.g / units.L},
    {"name": "Cabernet Sauvignon", "abv": 12.0, "rs": 6.3 * units.g / units.L},
    {"name": "Zinfandel", "abv": 15.0, "rs": 67 * units.g / units.L},
    {"name": "Port", "abv": 20.0, "rs": 100 * units.g / units.L},
    {"name": "Dry", "abv": None, "rs": 15 * units.g / units.L},
    {"name": "Semi-Sweet", "abv": None, "rs": 50 * units.g / units.L},
    {"name": "Sweet", "abv": None, "rs": 100 * units.g / units.L},
]

YEAST = [
    {"name": "Lalvin ICV-D47", "max_abv": 14},
    {"name": "Lalvin EC-1118", "max_abv": 18},
]


def sg_diff_to_abv(sg_diff):
    return sg_diff * 131.25


def sugar_to_abv(sugar):
    return sugar.asUnit(units.g / units.L) / (17.1 * units.g / units.L)


def abv_to_sugar(abv):
    return abv * 17.1 * units.g / units.L


def sg_to_sugar(sg):
    return (sg - 1) * 10_000


def get_volume(ingredients):
    volume = 0 * mL

    for ingredient in ingredients:
        ingredient_type = ingredient["ingredient_type"].lower()
        if ingredient_type in ["liquid", "solvent"]:
            unit = unit2str(ingredient["amount"])
            if unit in VOLUME_UNITS:
                volume += ingredient["amount"]
            elif unit in MASS_UNITS:
                volume += ingredient["amount"] / ingredient["density"]
            else:
                raise Exception(f"{unit} Not Implemented")

    return volume


def get_sugar(ingredients):
    sugar = 0 * units.g

    for ingredient in ingredients:
        if isinstance(ingredient, dict):
            ingredient_type = ingredient["ingredient_type"].lower()
            amount = ingredient["amount"]
            sugar_content = ingredient["sugar_content"]
            density = ingredient["density"]
        elif isinstance(ingredient, IngredientAddition):
            ingredient_type = ingredient.ingredient.ingredient_type.lower()
            amount = ingredient.amount * str2unit[ingredient.unit]
            sugar_content = ingredient.ingredient.sugar_content * (
                1.0 if ingredient_type in ["solid", "solute"] else units.g / units.L
            )
            density = ingredient.ingredient.density * (
                1.0 if ingredient_type in ["solid", "solute"] else units.g / mL
            )
        else:
            raise Exception(f"Unknown ingredient type: {type(ingredient)}")
        sugar_content_value = (
            sugar_content.asNumber()
            if isinstance(sugar_content, Unum)
            else sugar_content
        )
        if sugar_content is not None and sugar_content_value > 0:
            unit = unit2str(amount)
            if ingredient_type in ["liquid", "solvent"]:
                if unit in VOLUME_UNITS:
                    sugar += amount * sugar_content
                elif unit in MASS_UNITS:
                    sugar += amount * sugar_content / density
                else:
                    raise Exception(f"{unit} Not Implemented")
            elif ingredient_type in ["solid", "solute"]:
                sugar += amount * sugar_content

    return sugar


def calculate_max_potential_abv(ingredients):
    total_sugar = get_sugar(ingredients)
    fermentation_volume = get_volume(ingredients)

    if fermentation_volume > 0 * mL:
        max_potential_abv = sugar_to_abv(total_sugar / fermentation_volume)
        return (
            max_potential_abv,
            total_sugar / fermentation_volume,
            fermentation_volume,
        )
    else:
        return 0, 0 * units.g / units.L, fermentation_volume


def reviews_to_df(reviews: list) -> list[dict]:
    return [
        {
            "name": review.name,
            "container_id": review.container_id,
            "overall_rating": review.overall_rating,
            "boldness": review.boldness,
            "tannicity": review.tannicity,
            "sweetness": review.sweetness,
            "acidity": review.acidity,
            "complexity": review.complexity,
            "review_date": str(review.review_date),
        }
        for review in reviews
    ]


def get_ratings_abv_data(db: Session):
    data = (
        db.query(
            Review.overall_rating,
            func.max(SpecificGravityMeasurement.specific_gravity).label("initial_sg"),
            func.min(SpecificGravityMeasurement.specific_gravity).label("final_sg"),
        )
        .join(Fermentation, Review.fermentation_id == Fermentation.id)
        .join(
            SpecificGravityMeasurement,
            Fermentation.id == SpecificGravityMeasurement.fermentation_id,
        )
        .group_by(Review.id)
        .all()
    )

    return [
        {
            "overall_rating": row.overall_rating,
            "abv": (row.initial_sg - row.final_sg) * 131.25,
        }
        for row in data
        if row.initial_sg is not None and row.final_sg is not None
    ]


def get_ratings_rs_data(db: Session):
    data = (
        db.query(
            Review.overall_rating,
            func.min(SpecificGravityMeasurement.specific_gravity).label("final_sg"),
        )
        .join(Fermentation, Review.fermentation_id == Fermentation.id)
        .join(
            SpecificGravityMeasurement,
            Fermentation.id == SpecificGravityMeasurement.fermentation_id,
        )
        .group_by(Review.id)
        .all()
    )

    return [
        {
            "overall_rating": row.overall_rating,
            "residual_sugar": sg_to_sugar(row.final_sg),
        }
        for row in data
        if row.final_sg is not None
    ]
