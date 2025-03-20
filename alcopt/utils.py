from unum import Unum
from unum import units
from sqlalchemy.orm import Session
from sqlalchemy import func
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

from alcopt.database.models import Fermentation, Review, Bottle, SpecificGravityMeasurement
from alcopt.database.utils import init_db, get_db


mL = Unum.unit('mL', 0.001 * units.L)

def unit2str(unit):
    return str(unit.strUnit())[1:-1]

str2unit = {
    "kg": units.kg,
    "g": units.g,
    "L": units.L,
    "mL": mL,
}

MASS_UNITS = [
    "kg",
    "g",
]

VOLUME_UNITS = [
    "L",
    "mL",
]


def sg_diff_to_abv(sg_diff):
    """Specific gravity difference to abv (%)"""
    return sg_diff * 131.25


def sugar_to_abv(sugar):
    """Sugar in g/L (or mass/vol) to abv (%)"""
    return sugar.asUnit(units.g/units.L) / (17*units.g/units.L)

def abv_to_sugar(abv):
    """abv (%) to Sugar in g/L (or mass/vol)"""
    return abv * 17*units.g/units.L

def sg_to_sugar(sg):
    """
    Convert specific gravity to sugar content in grams per liter.

    Parameters:
    sg (float): Specific gravity.

    Returns:
    float: Sugar content in grams per liter.
    """
    return (sg - 1) * 10_000


BENCHMARK = [
    {"name": 'Beer', "abv": 5.0, "rs": 1*units.g/units.L},
    {"name": 'Moscato', "abv": 7.0, "rs": 200*units.g/units.L},
    {"name": 'Riesling', "abv": 9.0, "rs": 7*units.g/units.L},
    {"name": 'Cabernet Sauvignon', "abv": 12.0, "rs": 6.3*units.g/units.L},
    {"name": 'Zinfandel', "abv": 15.0, "rs": 67*units.g/units.L},
    {"name": 'Port', "abv": 20.0, "rs": 100*units.g/units.L},
    {"name": 'Dry', "abv": None, "rs": 15*units.g/units.L},
    {"name": 'Semi-Sweet', "abv": None, "rs": 50*units.g/units.L},
    {"name": 'Sweet', "abv": None, "rs": 100*units.g/units.L},
]

YEAST = [
    {"name": "Lalvin ICV-D47", "max_abv": 14},
    {"name": "Lalvin EC-1118", "max_abv": 18},
]

def reviews_to_df(reviews: list) -> pd.DataFrame:
    """
    Convert a list of Review objects to a pandas DataFrame.

    Args:
        reviews (list): A list of Review objects.

    Returns:
        pd.DataFrame: A DataFrame containing the review data with columns:
                      'Name', 'Bottle ID', 'Overall Rating', 'Boldness',
                      'Tannicity', 'Sweetness', 'Acidity', 'Complexity', and 'Review Date'.
    """
    # Convert to a list of dictionaries
    reviews_list = [
        {
            'Name': review.name,
            'Bottle ID': review.bottle_id,
            'Overall Rating': review.overall_rating,
            'Boldness': review.boldness,
            'Tannicity': review.tannicity,
            'Sweetness': review.sweetness,
            'Acidity': review.acidity,
            'Complexity': review.complexity,
            'Review Date': review.review_date
        }
        for review in reviews
    ]

    # Convert list of dictionaries to a DataFrame
    reviews_df = pd.DataFrame(reviews_list)
    return reviews_df


def plot_correlation_heatmap(reviews_df):
    """Plot heatmap of correlations between different rating attributes."""
    fig = plt.figure(figsize=(8, 6))
    correlation_matrix = reviews_df[['Overall Rating', 'Boldness', 'Tannicity', 'Sweetness', 'Acidity', 'Complexity']].corr()
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".2f")
    plt.title('Correlation Between Ratings and Wine Characteristics')
    return fig

def plot_sweetness_vs_rating(reviews_df):
    """Plot average overall rating for each sweetness level."""
    fig = plt.figure(figsize=(8, 5))
    sns.boxplot(x='Sweetness', y='Overall Rating', data=reviews_df, palette="coolwarm")
    plt.xlabel('Sweetness Level')
    plt.ylabel('Overall Rating')
    plt.title('Effect of Sweetness on Overall Rating')
    plt.grid()
    return fig

def plot_user_rating_distribution(reviews_df):
    """Compare how different users rate wines."""
    fig = plt.figure(figsize=(10, 5))
    sns.boxplot(x='Name', y='Overall Rating', data=reviews_df, palette="Set2")
    plt.xticks(rotation=70)
    plt.xlabel('User')
    plt.ylabel('Overall Rating')
    plt.title('Comparison of User Ratings')
    plt.grid()
    return fig

def get_ratings_abv_data():
    with get_db() as db:
        data = db.query(
            Review.overall_rating,
            SpecificGravityMeasurement.fermentation_id,
            func.max(SpecificGravityMeasurement.specific_gravity).label('initial_sg'),
            func.min(SpecificGravityMeasurement.specific_gravity).label('final_sg')
        ).join(
            Bottle, Review.bottle_id == Bottle.id
        ).join(
            Fermentation, Bottle.fermentation_id == Fermentation.id
        ).join(
            SpecificGravityMeasurement, Fermentation.id == SpecificGravityMeasurement.fermentation_id
        ).group_by(
            Review.id
        ).all()

        ratings_abv = []
        for row in data:
            initial_sg = row.initial_sg
            final_sg = row.final_sg
            abv = (initial_sg - final_sg) * 131.25
            ratings_abv.append((row.overall_rating, abv))

        return ratings_abv

def get_ratings_rs_data():
    with get_db() as db:
        data = db.query(
            Review.overall_rating,
            SpecificGravityMeasurement.fermentation_id,
            func.min(SpecificGravityMeasurement.specific_gravity).label('final_sg')
        ).join(
            Bottle, Review.bottle_id == Bottle.id
        ).join(
            Fermentation, Bottle.fermentation_id == Fermentation.id
        ).join(
            SpecificGravityMeasurement, Fermentation.id == SpecificGravityMeasurement.fermentation_id
        ).group_by(
            Review.id
        ).all()

        ratings_rs = []
        for row in data:
            rs = sg_to_sugar(row.final_sg)
            ratings_rs.append((row.overall_rating, rs))

        return ratings_rs