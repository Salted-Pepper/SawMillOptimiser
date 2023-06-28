import logging


def greedy_place(shapes: list, shape_types: list, logs: list) -> None:
    """
    :param shapes: SORTED List of Shapes (Required Sizes)
    :param shape_types: List of Shape Types (Available sizes)
    :param logs: List of Logs
    :return:
    """

    for shape in shapes:
        height = shape.height
