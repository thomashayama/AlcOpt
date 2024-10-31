
def sg_diff_to_abv(sg_diff):
    return sg_diff * 131.25

def sugar_to_abv(sugar):
    """Sugar in g/L"""
    return sugar / 17

BENCHMARK = [
    {"name": 'Beer', "abv": 5.0, "rs": 1},
    {"name": 'Moscato', "abv": 7.0, "rs": 200},
    {"name": 'Riesling', "abv": 9.0, "rs": 7},
    {"name": 'Cabernet Sauvignon', "abv": 12.0, "rs": 6.3},
    {"name": 'Zinfandel', "abv": 15.0, "rs": 67},
    {"name": 'Port', "abv": 20.0, "rs": 100},
    {"name": 'Dry', "abv": None, "rs": 15},
    {"name": 'Semi-Sweet', "abv": None, "rs": 50},
    {"name": 'Sweet', "abv": None, "rs": 100},
]