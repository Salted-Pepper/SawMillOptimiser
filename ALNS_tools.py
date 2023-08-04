import logging
import math
import pandas as pd
import numpy as np
import random
import datetime

import matplotlib.pyplot as plt

from ortools.linear_solver import pywraplp

import constants
from shapes import Shape
from logs import Log

date = datetime.date.today()
logging.basicConfig(level=logging.DEBUG, filename='saw_mill_app_' + str(date) + '.log',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt="%H:%M:%S")
logger = logging.getLogger("ALNS_Tools")
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
    if updated and delta != 0:
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
    return random.choices(logs, weights=[(1 - log.efficiency) / total_efficiency for log in logs])[0]


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
        orientation = "NW"
    elif x < centre and y < centre:
        orientation = "SW"
    elif x >= centre and y < centre:
        orientation = "SE"
    else:
        raise ValueError(f"No Orientation defined for ({x}, {y})")
    return orientation


def check_if_rectangle_empty(x_0: float, x_1: float, y_0: float, y_1: float, log: Log) -> list:
    """
    This function checks if there is any shape within a given rectangle in a particular log.
    It does so by checking every delta x and delta y, where these delta values are defined
    by the smallest possible width and height of a figure, ensuring that there is no figure fitting in
    these points.

    :param x_0: Smallest x coordinate
    :param x_1: Largest x coordinate
    :param y_0: Smallest y coordinate
    :param y_1: Largest x coordinate
    :param log: Log containing shapes
    :return:
    """

    min_width_check = constants.min_width_shape_type.width
    min_height_check = constants.min_height_shape_type.height

    width_steps = int(np.floor((x_1 - x_0) / (min_width_check - 1)))
    height_steps = int(np.floor((y_1 - y_0) / (min_height_check - 1)))

    x_steps = [x_0 + i * min_width_check for i in range(width_steps + 1)] + [x_1]
    y_steps = [y_0 + j * min_width_check for j in range(height_steps + 1)] + [y_1]

    violating_shapes = []
    for x_step in x_steps:
        for y_step in y_steps:
            # logger.debug(f"Checking ({x_step: .2f}, {y_step: .2f})")
            for shape in log.shapes:
                if shape.check_if_point_in_shape(x_step, y_step):
                    violating_shapes.append(shape)
    return violating_shapes


def fit_shapes_in_rect_using_lp(x_min: float, x_max: float, y_min: float, y_max: float,
                                candidate_shapes: list, shape_types: list, shapes: list) -> tuple:
    """
    This function applies an LP solver to a given space, optimising the space for the given candidate shapes.
    The given space, described by (x,y)-values, includes the saw kerf on the sides.
    It returns a new set of shapes that can be added in the described location.

    :param x_min: Left side x-value
    :param x_max: Right side x-value
    :param y_min: Bottom side y-value
    :param y_max: Top side y-value
    :param candidate_shapes: List of shapes to fill the given space
    :param shape_types: List of all available shapes
    :param shapes: List of shapes currently in the considered log, or an empty list to add to
    :return shapes: List of added shapes
    """
    solutions = []

    width = x_max - x_min - 2 * constants.saw_kerf
    height = y_max - y_min - 2 * constants.saw_kerf

    # Horizontal Solutions
    candidate_shapes = [s for s in candidate_shapes if s.width <= width]
    for shape in candidate_shapes:
        h_m = shape.height
        shorter_shapes = [s for s in candidate_shapes if s.height <= h_m]

        solver = pywraplp.Solver.CreateSolver('SAT')

        variables = []

        for short_shape in shorter_shapes:
            variables.append([solver.IntVar(0, solver.infinity(), 'x' + str(short_shape.type_id)),
                              short_shape.width, short_shape.height, short_shape.type_id])

            # add constraint for maximum length
            solver.Add(sum([v[0] * (v[1] + constants.saw_kerf) for v in variables]) <= width)
            solver.Maximize(sum([v[0] * v[1] * v[2] for v in variables]))

        status = solver.Solve()

        if status == pywraplp.Solver.OPTIMAL:
            values = [[v[3], v[0].solution_value()] for v in variables]
            usage = solver.Objective().Value()
        else:
            raise ValueError("Solution Not Converged")

        rel_usage = usage / (height * width)

        solutions.append([rel_usage,
                          values,
                          [h_m, x_min, x_max, height],
                          "Horizontal"])

    # Vertical Solutions
    candidate_shapes = [s for s in candidate_shapes if s.height <= height]
    for shape in candidate_shapes:
        w_m = shape.width
        shorter_shapes = [s for s in candidate_shapes if s.width <= w_m]

        solver = pywraplp.Solver.CreateSolver('SAT')

        variables = []

        for short_shape in shorter_shapes:
            variables.append([solver.IntVar(0, solver.infinity(), 'x' + str(short_shape.type_id)),
                              short_shape.width, short_shape.height, short_shape.type_id])

            # add constraint for maximum length
            solver.Add(sum([v[0] * (v[2] + constants.saw_kerf) for v in variables]) <= height)
            solver.Maximize(sum([v[0] * v[1] * v[2] for v in variables]))

        status = solver.Solve()

        if status == pywraplp.Solver.OPTIMAL:
            values = [[v[3], v[0].solution_value()] for v in variables]
            usage = solver.Objective().Value()
        else:
            raise ValueError("Solution Not Converged")

        rel_usage = usage / (height * width)

        solutions.append([rel_usage,
                          values,
                          [w_m, y_min, y_max, width],
                          "Vertical"])

    if len(solutions) == 0:
        logging.warning(f"No Solution Found Using ALNS_tools LP Solver in "
                        f"({x_min: .2f}, {y_min: .2f}), ({x_max: .2f}, {y_max: .2f})")
        return [], 0

    best_solution = max(solutions, key=lambda solution: solution[0])
    rel_usage = best_solution[0]
    shapes_sol = best_solution[1]
    z_minimal = best_solution[2][1]
    z_maximal = best_solution[2][2]
    orientation = best_solution[3]

    z = z_minimal + constants.saw_kerf

    # Create a list of shapes with locations corresponding to solution
    for shape_info in shapes_sol:
        shape_id = shape_info[0]
        quantity = int(shape_info[1])
        shape_type = shape_types[shape_id]

        if orientation == "Horizontal":
            for i in range(quantity):
                shapes.append(Shape(shape_type=shape_type, x=z, y=y_min))
                logger.debug(f"Suggesting shape {shape_type.type_id} with {shape_type.width}x{shape_type.height},"
                             f" at location {z: .2f}, {y_min: .2f}")
                z += shape_type.width + constants.saw_kerf
                if z > z_maximal:
                    raise ValueError(f"Exceeding maximum x-value {z} > {z_maximal}.")
        elif orientation == "Vertical":
            for i in range(quantity):
                shapes.append(Shape(shape_type=shape_type, x=x_min, y=z))
                logger.debug(f"Suggesting shape {shape_type.type_id} with {shape_type.width}x{shape_type.height}, "
                             f"at location {x_min:.2f}, {z:.2f}")
                z += shape_type.height + constants.saw_kerf
                if z > z_maximal:
                    raise ValueError(f"Exceeding maximum y-value {z} > {z_maximal}.")

    return shapes, rel_usage


def fit_points_in_boundaries(left_x, right_x, low_y, high_y, priority: str, log: Log):
    if priority == "height":
        x_left_boundary_low, x_right_boundary_low = log.calculate_edge_positions_on_circle(low_y)
        x_left_boundary_high, x_right_boundary_high = log.calculate_edge_positions_on_circle(high_y)
        left_x = max(left_x, x_left_boundary_low, x_left_boundary_high)
        right_x = min(right_x, x_right_boundary_low, x_right_boundary_high)

        y_bot_boundary_left, y_top_boundary_left = log.calculate_edge_positions_on_circle(left_x)
        y_bot_boundary_right, y_top_boundary_right = log.calculate_edge_positions_on_circle(right_x)
        low_y = max(low_y, y_bot_boundary_left, y_bot_boundary_right)
        high_y = min(high_y, y_top_boundary_left, y_top_boundary_right)

    elif priority == "width":
        y_bot_boundary_left, y_top_boundary_left = log.calculate_edge_positions_on_circle(left_x)
        y_bot_boundary_right, y_top_boundary_right = log.calculate_edge_positions_on_circle(right_x)
        low_y = max(low_y, y_bot_boundary_left, y_bot_boundary_right)
        high_y = min(high_y, y_top_boundary_left, y_top_boundary_right)

        x_left_boundary_low, x_right_boundary_low = log.calculate_edge_positions_on_circle(low_y)
        x_left_boundary_high, x_right_boundary_high = log.calculate_edge_positions_on_circle(high_y)
        left_x = max(left_x, x_left_boundary_low, x_left_boundary_high)
        right_x = min(right_x, x_right_boundary_low, x_right_boundary_high)
    return left_x, right_x, low_y, high_y


def check_if_shape_in_rectangle(shape: Shape, x_0, x_1, y_0, y_1) -> bool:
    sk = constants.saw_kerf
    a_x_0 = shape.x
    a_x_1 = shape.x + shape.width
    a_y_0 = shape.y
    a_y_1 = shape.y + shape.height

    b_x_0 = x_0
    b_x_1 = x_1
    b_y_0 = y_0
    b_y_1 = y_1

    if a_x_0 - sk <= b_x_1 \
            and a_x_1 + sk >= b_x_0 \
            and a_y_0 - sk <= b_y_1 \
            and a_y_1 + sk >= b_y_0:
        return True
    else:
        return False


def plot_iteration_data(logs: list, df: pd.DataFrame):
    fig, ax = plt.subplots()
    for log in range(len(logs)):
        df_log = df[df["log"] == log]
        ax.plot(df_log["iteration"], df_log["efficiency"])
    plt.show()


def check_if_logs_feasible(list_of_logs) -> bool:
    for log in list_of_logs:
        if not log.check_if_feasible():
            return False
    return True


def check_feasibility(list_of_logs):
    if check_if_logs_feasible(list_of_logs):
        return True
    else:
        print("Incorrect shape placement!")
        return False
