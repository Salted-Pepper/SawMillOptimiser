import constants
import numpy as np
import logging
import math
import datetime
import random

import ALNS_tools

import testing_tools
from logs import Log

date = datetime.date.today()
logging.basicConfig(level=logging.DEBUG, filename='saw_mill_app_' + str(date) + '.log',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt="%H:%M:%S")
logger = logging.getLogger("ALNS_Methods")
logger.setLevel(logging.DEBUG)


def random_destroy(log: Log) -> bool:
    """
    Randomly removes a shape from the log. Selects a shape based on distance to the centre.
    The further the centre of a shape is from the centre of the log, the higher the likelihood of it being picked.
    :param log:
    :return:
    """
    logger.debug("Picked Random Destroy Method")
    successful = False

    probabilities = []
    total_distance = sum([math.sqrt((s.width - log.diameter)**2 + (s.height - log.diameter)**2) for s in log.shapes])

    for shape in log.shapes:
        probabilities.append(math.sqrt((shape.width - log.diameter)**2 +
                                       (shape.height - log.diameter)**2) / total_distance)

    removed_shape = random.choices(log.shapes, weights=probabilities)[0]

    removed_shape.remove_from_log()
    logger.debug(f"Removed Shape at ({removed_shape.x}, {removed_shape.y}), "
                 f"({removed_shape.x + removed_shape.width}, {removed_shape.y + removed_shape.height})")
    return successful


def subspace_destroy(log: Log, shape_types: list) -> bool:
    logger.debug("Picked Subspace Destroy Method")
    successful = False
    return successful


def inefficiency_destroy(log: Log, shape_types: list) -> bool:
    logger.debug("Picked Inefficiency Destroy Method")
    successful = False
    return successful


def random_point_expansion(log: Log, shape_types: list) -> bool:
    """
    RPE selects a random point in the log, it then calculates the maximum rectangle it can create until there
    is a collision in every direction. It then checks if this area is empty of shapes. If so, it applies an LP to
    fill up the area. If not - it
    :param log:
    :param shape_types:
    :return:
    """
    logger.debug("Picked RPE Repair Method")
    successful = False
    found_point = False

    while not found_point:
        p_x, p_y = np.random.uniform(low=0, high=log.diameter, size=2)

        if log.check_if_point_in_log(p_x, p_y):
            point_in_shape = False
            for shape in log.shapes:
                if shape.check_if_point_in_shape(p_x, p_y):
                    point_in_shape = True

            if not point_in_shape:
                found_point = True

    logger.debug(f"Attempting Random Point Expansion in Log {log.log_id} at ({p_x: .2f}, {p_y: .2f})")
    orientation = ALNS_tools.find_orientation_from_points(centre=log.diameter / 2, x=p_x, y=p_y)

    """
    Feasible point has been found, attempt to expand towards the center point, and find first collision
    Here we use the minimum width shape and the minimum height shape to ensure that we do not have to check every point.
    Hence, we initially check the point the minimum distance away. 
    If it is not occupied, we expand again with the same width.
    If the tile is occupied, we find the shape the point is contained in, and go to the edge of that shape
    """

    left_most_x, right_most_x = log.calculate_edge_positions_on_circle(p_y)
    lowest_y, highest_y = log.calculate_edge_positions_on_circle(p_x)

    logger.debug(f"Initialized x_l {left_most_x: .2f}, x_r {right_most_x: .2f}, "
                 f"y_min {lowest_y: .2f}, y_max {highest_y: .2f}.")

    for shape in log.shapes:
        # see if shape is in same p_x dimension
        if shape.x - constants.saw_kerf <= p_x <= shape.x + shape.width + constants.saw_kerf:
            # Then a y-collision is possible
            if p_y > shape.y + shape.height + constants.saw_kerf > lowest_y:
                lowest_y = shape.y + shape.height + constants.saw_kerf

            if p_y < shape.y - constants.saw_kerf < highest_y:
                highest_y = shape.y - constants.saw_kerf

        if shape.y - constants.saw_kerf <= p_y <= shape.y + shape.height + constants.saw_kerf:
            # Then an x-collision is possible
            if p_x > shape.x + shape.width + constants.saw_kerf > left_most_x:
                left_most_x = shape.x + shape.width + constants.saw_kerf

            if p_x < shape.x - constants.saw_kerf < right_most_x:
                right_most_x = shape.x - constants.saw_kerf
    logger.debug(f"After checking shape collisions x_l {left_most_x: .2f}, x_r {right_most_x: .2f}, "
                 f"y_min {lowest_y: .2f}, y_max {highest_y: .2f}.")
    # Check if rectangle is empty
    violating_shapes = ALNS_tools.check_if_rectangle_empty(x_0=left_most_x, x_1=right_most_x,
                                                           y_0=lowest_y, y_1=highest_y, log=log)
    logging.debug(f"Found {len(violating_shapes)} violating shapes.")
    for s in violating_shapes:
        logging.debug(f"Violating Shape at ({s.x: .2f}, {s.y: .2f} with w:{s.width: .2f}, h:{s.height: .2f}) in"
                      f"x:({left_most_x: .2f}, {right_most_x: .2f}), y:({lowest_y: .2f}, {highest_y: .2f})")

    # For all violating shapes we have to make a cut in the plane to ensure the rectangle is clean
    for shape in violating_shapes:
        # Check if shape still violates cut, as previous cuts could have put this shape out of violation
        violates = ALNS_tools.check_if_shape_in_rectangle(shape=shape, x_0=left_most_x, x_1=right_most_x,
                                                          y_0=lowest_y, y_1=highest_y)
        if not violates:
            continue

        # There are 4 possible cuts - find the cut that loses the least surface area
        cut_upper_off = (right_most_x - left_most_x) * ((shape.y-constants.saw_kerf) - lowest_y)
        cut_lower_off = (right_most_x - left_most_x) * (highest_y - (shape.y+shape.height+constants.saw_kerf))
        cut_left_off = (right_most_x - (shape.x+shape.width+constants.saw_kerf)) * (highest_y - lowest_y)
        cut_right_off = ((shape.x-constants.saw_kerf) - left_most_x)
        cuts = [cut_upper_off, cut_lower_off, cut_left_off, cut_right_off]

        # Update Values Based On Selected Optimal Cut
        largest_remaining_cut = max(cuts)
        if cut_upper_off == largest_remaining_cut:
            highest_y = shape.y - constants.saw_kerf
            logging.debug(f"Cutting off top past {highest_y: .2f}")
        elif cut_lower_off == largest_remaining_cut:
            lowest_y = shape.y + shape.height+constants.saw_kerf
            logging.debug(f"Cutting off lower under {lowest_y: .2f}")
        elif cut_left_off == largest_remaining_cut:
            left_most_x = shape.x + shape.width+constants.saw_kerf
            logging.debug(f"Cutting off left of {left_most_x: .2f}")
        else:
            right_most_x = shape.x - constants.saw_kerf
            logging.debug(f"Cutting off right of {right_most_x: .2f}")

    logger.debug(f"Post Calculations: x_l {left_most_x: .2f}, x_r {right_most_x: .2f}, "
                 f"y_min {lowest_y: .2f}, y_max {highest_y: .2f}.")

    # Recheck the log boundaries
    (left_x_width, right_x_width,
     low_y_width, top_y_width) = ALNS_tools.fit_points_in_boundaries(left_most_x, right_most_x,
                                                                     lowest_y, highest_y,
                                                                     priority="width",
                                                                     log=log)
    (left_x_height, right_x_height,
     low_y_height, top_y_height) = ALNS_tools.fit_points_in_boundaries(left_most_x, right_most_x,
                                                                       lowest_y, highest_y,
                                                                       priority="height",
                                                                       log=log)
    logger.debug(f"Outcome prioritizing width: xy: "
                 f"({left_x_width: .2f}, {low_y_width: .2f}) ({right_x_width: .2f}, {top_y_width: .2f})")
    logger.debug(f"Outcome prioritizing height: xy: "
                 f"({left_x_height: .2f}, {low_y_height: .2f}) ({right_x_height: .2f}, {top_y_height: .2f})")
    wide_candidate_shapes = [s for s in shape_types if s.width <= right_x_width - left_x_width
                             and s.height <= top_y_width - low_y_width]
    high_candidate_shapes = [s for s in shape_types if s.width <= right_x_height - left_x_height
                             and s.height <= top_y_height - low_y_height]
    new_shapes_wide, usage_wide = ALNS_tools.fit_shapes_in_rect_using_lp(x_min=left_x_width, x_max=right_x_width,
                                                                         y_min=low_y_width, y_max=top_y_width,
                                                                         candidate_shapes=wide_candidate_shapes,
                                                                         shape_types=shape_types, shapes=[])
    new_shapes_high, usage_high = ALNS_tools.fit_shapes_in_rect_using_lp(x_min=left_x_height, x_max=right_x_height,
                                                                         y_min=low_y_height, y_max=top_y_height,
                                                                         candidate_shapes=high_candidate_shapes,
                                                                         shape_types=shape_types, shapes=[])

    if usage_wide == usage_high == 0:
        logging.debug("No feasible solution")
    elif usage_wide > usage_high:
        logging.debug("Picking solution prioritising width")
        for shape in new_shapes_wide:
            shape.assign_to_log(log)
        successful = True
    elif usage_wide < usage_high:
        logging.debug("Picking solution prioritising height")
        for shape in new_shapes_high:
            shape.assign_to_log(log)
        successful = True
    return successful


def single_extension_repair(log: Log, shape_types: list) -> bool:
    logger.debug("Picked Single Extension Repair Method")
    successful = False
    return successful


def buddy_extension_repair(log: Log, shape_types: list) -> bool:
    logger.debug("Picked Buddy Extension Repair Method")
    successful = False
    return successful


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

    def execute(self, log, shape_types: list) -> bool:

        if self.name == "RANDOM":
            succeeded = random_destroy(log)
        elif self.name == "SUBSPACE":
            succeeded = subspace_destroy(log, shape_types)
        elif self.name == "INEFFICIENCY":
            succeeded = inefficiency_destroy(log, shape_types)
        elif self.name == "RPE":
            succeeded = random_point_expansion(log, shape_types)
        elif self.name == "SER":
            succeeded = single_extension_repair(log, shape_types)
        elif self.name == "BER":
            succeeded = buddy_extension_repair(log, shape_types)
        else:
            raise ValueError(f"ALNS Method {self.name} Not Implemented")
        return succeeded

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
