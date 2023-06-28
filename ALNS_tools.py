import math


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
    return x_plus - x_min

