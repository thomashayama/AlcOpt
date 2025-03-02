from unum import Unum
from unum import units


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