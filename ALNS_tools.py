import logging
import math
import pandas as pd
import random
import datetime

import constants
from shapes import Shape
from logs import Log

date = datetime.date.today()
logging.basicConfig(level=logging.DEBUG, filename='saw_mill_app_' + str(date) + '.log',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt="%d-%b-%y %H:%M:%S")
logger = logging.getLogger("ALNS_Tools Logger")
logger.setLevel(logging.DEBUG)


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
        if shape.x + shape.width > left:
            maximal_shape = shape
            left = shape.x + shape.width

    return maximal_shape


def find_max_rectangle_width(log: Log, height: float, x: float, y: float, orientation: str) -> tuple:
    """
    :param log: Log Object
    :param height: Height of rectangle
    :param x: start x position
    :param y: start y position
    :param orientation: direction of the rectangle - either "NW", "NE", "SW", "SE"
    :return: float with max width
    """
    logger.debug(f"Find max width rectangle for log {log.log_id}, with coords ({x}, {y}), with height {height}"
                 f" and orientation {orientation}")

    r = log.diameter / 2

    # No feasible point
    if y + height > log.diameter:
        logger.warning("Tried creating LP for point exceeding log diameter - violates math domain")
        return 0, -1, -1

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


def check_if_new_solution_better(log_old: Log, log: Log, temperature: float) -> tuple:
    log_old_score = calculate_log_score(log_old)
    log_score = calculate_log_score(log)
    # TODO: Probability based acceptance using temperature
    if log_old_score > log_score:
        return False, 0, log_old_score
    else:
        return True, log_score - log_old_score, log_score


def update_temperature(temperature: float, updated: bool, delta: float, score: float) -> float:
    if updated:
        temperature = temperature * (delta / score) ** (1 / 10)
    else:
        temperature = temperature * constants.temperature_sensitivity
    return temperature


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


def calculate_smallest_shape_types(shape_types: list) -> None:
    """
    Calculates shapes with minimum properties to check if there exists any shape that fits in a certain height/width

    :param shape_types: List of shapetypes
    :return:
    """
    min_width_shape = None
    min_height_shape = None
    smallest_shape = None

    min_width = math.inf
    min_height = math.inf
    smallest_shape_total = math.inf

    for shape in shape_types:
        if shape.height < min_height:
            min_height_shape = shape
            min_height = shape.height

        if shape.width < min_width:
            min_width_shape = shape
            min_width = shape.width

        if shape.width + shape.height < smallest_shape_total:
            smallest_shape = shape
            smallest_shape_total = shape.width + shape.height

    constants.min_height_shape_type = min_height_shape
    constants.min_width_shape_type = min_width_shape
    constants.smallest_total_shapes = smallest_shape


def select_log(logs: list) -> Log:
    """
    Selects a random log based on the relative inefficiency

    :param logs:
    :return:
    """
    total_efficiency = sum([1 - log.efficiency for log in logs])
    return random.choices(logs, weights=[(1 - log.efficiency) / total_efficiency for log in logs])


def find_orientation_from_points(centre: float, x: float, y: float) -> str:
    """
    :param centre: Radius of circle (r, r) is centre position
    :param x: x position
    :param y: y position
    :return:
    """

    if x >= centre and y >= centre:
        orientation = "NE"
    elif x < centre and y >= centre:
        orientation = "SE"
    elif x < centre and y < centre:
        orientation = "SW"
    elif x >= centre and y < centre:
        orientation = "NW"
    else:
        raise ValueError(f"No Orientation defined for ({x}, {y})")
    return orientation


def plot_iteration_data():
    # TODO: Plotting iteration data
    pass
