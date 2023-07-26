import math
from shapes import Shape
from logs import Log


def calculate_total_score(shapes: list, shape_types: list, logs: list) -> None:
    """
    Calculates a score for the current set up using:
    -Volume of log used
    -Sawdust created


    :param shapes: SORTED List of Shapes (Required Sizes)
    :param shape_types: List of Shape Types (Available Sizes)
    :param logs:
    :return:
    """
    pass


def calculate_max_width_rect(height, diameter):
    if height >= diameter:
        return 0

    r = diameter / 2
    inner_value = r ** 2 - (r - (diameter - height)/2)**2
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
        x_m = r - math.sqrt(r**2 - (height + y - r)**2)
        return x - x_m, x_m, x
    elif orientation == "NE":
        x_m = r + math.sqrt(r**2 - (height + y - r)**2)
        return x_m - x, x, x_m
    elif orientation == "SW":
        raise NotImplemented("SW Not yet implemented")
    elif orientation == "SE":
        raise NotImplemented("SE Not yet implemented")

