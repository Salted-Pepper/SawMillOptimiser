import ALNS_tools
import constants
import numpy as np
import logging
import datetime

import testing_tools
from logs import Log

date = datetime.date.today()
logging.basicConfig(level=logging.DEBUG, filename='saw_mill_app_' + str(date) + '.log',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt="%d-%b-%y %H:%M:%S")
logger = logging.getLogger("ALNS_Methods Logger")
logger.setLevel(logging.DEBUG)


def random_destroy(log, shape_types):
    logger.debug("Picked Random Destroy Method")
    pass


def subspace_destroy(log, shape_types):
    logger.debug("Picked Subspace Destroy Method")
    pass


def inefficiency_destroy(log, shape_types):
    logger.debug("Picked Inefficiency Destroy Method")
    pass


def random_point_expansion(log, shape_types) -> None:
    """
    RPE selects a random point in the log, it then calculates the maximum rectangle it can create until there
    is a collision in every direction. It then checks if this area is empty of shapes. If so, it applies an LP to
    fill up the area. If not - it
    :param log:
    :param shape_types:
    :return:
    """
    logger.debug("Picked RPE Repair Method")

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
    logger.debug(f"Attempting Random Point Expansion in Log {log.log_id} at ({x}, {y})")
    orientation = ALNS_tools.find_orientation_from_points(centre=log.diameter / 2, x=x, y=y)

    """
    Feasible point has been found, attempt to expand towards the center point, and find first collision
    Here we use the minimum width shape and the minimum height shape to ensure that we do not have to check every point.
    Hence, we initially check the point the minimum distance away. 
    If it is not occupied, we expand again with the same width.
    If the tile is occupied, we find the shape the point is contained in, and go to the edge of that shape

    x_edge: X coord of point closest log edge
    y_edge: Y coord of point closest log edge
    
    x_centre:  X Coordinate closest in direction of centre before collision
    y_centre:  Y Coordinate closest in direction of centre before collision
    """

    x_edge, y_edge = log.find_closest_point_on_edge(x, y)

    if orientation.startswith("N"):
        y_centre, _ = log.calculate_edge_positions_on_circle(x)
    else:
        _, y_centre = log.calculate_edge_positions_on_circle(x)

    if orientation.endswith("E"):
        x_centre, _ = log.calculate_edge_positions_on_circle(y)
    else:
        _, x_centre = log.calculate_edge_positions_on_circle(y)

    # find first collision based on just looking at x and y coordinates
    for shape in log.shapes:
        if shape.y <= y <= shape.y + shape.height:
            if shape.x + shape.width > x_centre and (orientation == "NE" or orientation == "SE"):
                x_centre = shape.x + shape.width
            elif shape.x < x_centre and (orientation == "NW" or orientation == "SW"):
                x_centre = shape.x

        if shape.x <= x <= shape.x + shape.width:
            if shape.y > y_centre and (orientation == "NE" or orientation == "NW"):
                y_centre = shape.y
            elif shape.y + shape.height < y_centre and (orientation == "SE" or orientation == "SW"):
                y_centre = shape.y + shape.height

    logger.debug(f"x_centre: {x_centre}, y_centre: {y_centre}, closest edge point: ({x_edge}, {y_edge})")

    """
    We now create a set of candidate shapes that would fit in the largest possible rectangle.
    However, it could be that there is a corner blocked in this largest rectangle. Hence we check
    if the area is clear or not.
    """

    w_m = abs(x_edge - x_centre)
    h_m = abs(y_edge - x_centre)

    candidate_shapes = []

    for shape in shape_types:
        if shape.width <= w_m and shape.height <= h_m:
            candidate_shapes.append(shape)

    if len(candidate_shapes) == 0:
        # No feasible candidate for set up shape
        # We attempt to salve by resizing it purely in a vertical or horizontal manner
        # (instead of going to the closest edge point)
        # TODO: ^
        _, x_max = log.calculate_edge_positions_on_circle(z=y)
        _, y_max = log.calculate_edge_positions_on_circle(z=x)
        # TODO: Implement check for grabbing either max or min based on orientation

    is_empty, violating_shapes = ALNS_tools.check_if_rectangle_empty(x_0=min(x_edge, x_centre),
                                                                     x_1=max(x_edge, x_centre),
                                                                     y_0=min(y_edge, y_centre),
                                                                     y_1=max(y_edge, y_centre),
                                                                     log=log)

    # if there are shapes that exist in the defined rectangle, we have to shave off that area
    # and then see if we can re-expand the rectangle in a different ratio
    for s in violating_shapes:
        if orientation == "NE":
            if s.x + s.width + constants.saw_kerf >= x_centre:
                x_centre = s.x + s.width + constants.saw_kerf
            if s.y + s.height + constants.saw_kerf >= y_centre:
                y_centre = s.y + s.height + constants.saw_kerf
        elif orientation == "SE":
            if s.x + s.width + constants.saw_kerf >= x_centre:
                x_centre = s.x + s.width + constants.saw_kerf
            if s.y - constants.saw_kerf <= y_centre:
                y_centre = s.y - constants.saw_kerf
        elif orientation == "SW":
            if s.x - constants.saw_kerf <= x_centre:
                x_centre = s.x - constants.saw_kerf
            if s.y - constants.saw_kerf <= y_centre:
                y_centre = s.y - constants.saw_kerf
        elif orientation == "NW":
            if s.x - constants.saw_kerf <= x_centre:
                x_centre = s.x - constants.saw_kerf
            if s.y + s.height + constants.saw_kerf >= y_centre:
                y_centre = s.y + s.height + constants.saw_kerf
        else:
            raise NotImplementedError(f"No such orientation as {orientation}.")

    testing_tools.plot_log(diameter=log.diameter, x=x_centre, y=y_centre,
                           w=(x_centre - x_edge), h=(y_centre - y_edge))

    # Solve LP
    new_shapes = ALNS_tools.fit_shapes_in_rect_using_lp(x_min=min(x_edge, x_centre),
                                                        x_max=max(x_edge, x_centre),
                                                        y_min=min(y_edge, y_centre),
                                                        y_max=max(y_edge, y_centre),
                                                        candidate_shapes=candidate_shapes,
                                                        shape_types=shape_types,
                                                        shapes=[])

    for shape in new_shapes:
        logger.debug(f"Adding shape {shape.shape_id} to log {log.log_id}")
        shape.assign_to_log(log)


def single_extension_repair(log, shape_types):
    logger.debug("Picked Single Extension Repair Method")
    pass


def buddy_extension_repair(log, shape_types):
    logger.debug("Picked Buddy Extension Repair Method")
    pass


class Method:
    failure_adjust_rate = 0.95
    success_adjust_rate = 0.99

    def __init__(self, name):
        self.name = name
        self.performance = 100
        self.probability = 1
        self.method_used = False
        self.times_used = 0

    def method_failed(self):
        self.performance = self.performance * self.failure_adjust_rate

    def method_success(self):
        self.performance = self.performance * self.success_adjust_rate

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
