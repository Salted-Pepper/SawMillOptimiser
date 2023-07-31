import ALNS_tools
import constants
import numpy as np

from logs import Log


def random_destroy(log, shape_types):
    pass


def subspace_destroy(log, shape_types):
    pass


def inefficiency_destroy(log, shape_types):
    pass


def random_point_expansion(log, shape_types):
    """
    RPE selects a random point in the log
    :param log:
    :param shape_types:
    :return:
    """
    found_point = False

    while not found_point:
        x, y = np.random.uniform(low=0, high=log.diameter, size=2)

        if log.check_if_point_in_log(x, y):
            point_in_shape = False
            for shape in log.shapes:
                if shape.check_if_point_in_shape(x, y):
                    point_in_shape = True
                    continue

            if not point_in_shape:
                found_point = True

    orientation = ALNS_tools.find_orientation_from_points(centre=log.diameter / 2, x=x, y=y)

    """
    Feasible point has been found, attempt to expand towards the center point, and find first collision
    Here we use the minimum width shape and the minimum height shape to ensure that we do not have to check every point.
    Hence, we initially check the point the minimum distance away. 
    If it is not occupied, we expand again with the same width.
    If the tile is occupied, we find the shape the point is contained in, and go to the edge of that shape
    """

    # Define parameter to track expansion
    w_min = constants.min_width_shape_type.width
    h_min = constants.min_height_shape_type.height

    """
    x_to_centre:    maximum x we can move towards centre x without collision
    x_away_centre:  maximum x we can move away from centre x without collision
    y_to_centre:    maximum y we can move towards centre y without collision
    y_away_centre:  maximum y we can move away from centre y without collision
    """






def single_extension_repair(log, shape_types):
    pass


def buddy_extension_repair(log, shape_types):
    pass


class Method:
    adjust_rate = 0.95

    def __init__(self, name):
        self.name = name
        self.performance = 100
        self.probability = 1
        self.method_used = False
        self.times_used = 0

    def reject_method(self):
        self.performance = self.performance * self.adjust_rate

    def execute(self, log, shape_types):

        if self.name == "RANDOM":
            random_destroy(log, shape_types)
        elif self.name == "SUBSPACE":
            subspace_destroy(log, shape_types)
        elif self.name == "INEFFICIENCY":
            inefficiency_destroy(log, shape_types)
        elif self.name == "RPE":
            random_point_expansion(log, shape_types)
        elif self.name == "SER":
            single_extension_repair(log, shape_types)
        elif self.name == "BER":
            buddy_extension_repair(log, shape_types)
        else:
            raise ValueError(f"ALNS Method {self.name} Not Implemented")

    def used(self):
        self.method_used = True
        self.times_used += 1


def update_method_probability(methods: list, updated):
    total_performance = sum([method.performance for method in methods])

    for method in methods:
        if updated and method.used:
            method.performance = method.performance * constants.method_sensitivity_acceptance
            method.used = False
        elif method.used:
            method.performance = method.performance * constants.method_sensitivity_rejection

    for method in methods:
        method.probability = method.performance / total_performance

