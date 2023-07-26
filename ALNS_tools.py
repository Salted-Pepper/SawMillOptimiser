import math

import pandas as pd

from shapes import Shape
from logs import Log


def update_log_scores(logs: list) -> None:
    """
    Calculates a score for the current set up using:
    -Volume of log used
    -Sawdust created

    :param logs:
    :return:
    """
    for log in logs:
        calculate_log_score(log)


def calculate_log_score(log: Log):
    usage_multiplier = 1
    saw_dust_multiplier = -1.5
    unused_multiplier = -1

    log.score = log.volume_used * usage_multiplier \
                + log.saw_dust * saw_dust_multiplier \
                + (log.volume - log.volume_used) * unused_multiplier

    return log.score


def calculate_max_width_rect(height, diameter):
    if height >= diameter:
        return 0

    r = diameter / 2
    inner_value = r ** 2 - (r - (diameter - height) / 2) ** 2
    x_plus = r + math.sqrt(inner_value)
    x_min = r - math.sqrt(inner_value)
    return x_plus - x_min, x_min, x_plus


def find_left_most_shape(shapes: list) -> Shape:
    right = math.inf
    minimal_shape = None

    for shape in shapes:
        if shape.x < right:
            minimal_shape = shape
            right = shape.x

    return minimal_shape


def find_right_most_shape(shapes: list) -> Shape:
    left = -1
    maximal_shape = None

    for shape in shapes:
        if shape.x > left:
            maximal_shape = shape
            left = shape.x

    return maximal_shape


def find_max_rectangle_width(log: Log, height: float, x: int, y: int, orientation: str) -> tuple:
    """
    :param log: Log Object
    :param height: Height of rectangle
    :param x: start x position
    :param y: start y position
    :param orientation: direction of the rectangle - either "NW", "NE", "SW", "SE"
    :return: float with max width
    """

    r = log.diameter / 2

    if orientation == "NW":
        x_m = r - math.sqrt(r ** 2 - (height + y - r) ** 2)
        return x - x_m, x_m, x
    elif orientation == "NE":
        x_m = r + math.sqrt(r ** 2 - (height + y - r) ** 2)
        return x_m - x, x, x_m
    elif orientation == "SW":
        raise NotImplemented("SW Not yet implemented")
    elif orientation == "SE":
        raise NotImplemented("SE Not yet implemented")


def save_iteration_data(logs: list, df: pd.DataFrame, iteration: int) -> pd.DataFrame:
    """
    :param logs: List of logs
    :param df: Dataframe keeping iteration data: columns = ["iteration", "log", "score",
                                                            "saw_dust", "volume_used", "efficiency"]
    :param iteration: Number of iteration
    :return: Mutated dataframe with new entries
    """
    for log in logs:
        df.loc[len(df)] = {"iteration": iteration, "log": log.log_id, "score": log.score,
                           "saw_dust": log.saw_dust, "volume_used": log.volume_used, "efficiency": log.efficiency}

    return df


def plot_iteration_data():
    # TODO: Plotting iteration data
    pass
