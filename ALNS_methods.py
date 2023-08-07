import random

import constants
import numpy as np
import logging
import datetime
import math
import time

import ALNS_tools
import testing_tools
from shapes import Shape
from logs import Log, select_random_shapes_from_log

date = datetime.date.today()
logging.basicConfig(level=logging.DEBUG, filename='saw_mill_app_' + str(date) + '.log',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt="%H:%M:%S")
logger = logging.getLogger("ALNS_Methods")
logger.setLevel(logging.DEBUG)


def tuck(name: str, log: Log) -> tuple:
    """
    Selects a random number of shapes in the log.
    Tries to move all shapes as much as possible in a certain direction.
    (Starting from the direction they are shifted in)

    For the centre direction it tries to shift towards the centre
    :return:
    """
    t_0 = time.perf_counter()

    successful = False

    number_of_shapes = random.randint(0, len(log.shapes))
    random_shapes = [select_random_shapes_from_log(log, count=number_of_shapes)]

    if name.endswith("CENTRE"):
        # First see which direction to move the block in, move centre of block to centre of log
        centre_point = log.diameter / 2
        for shape in random_shapes:
            centre_x = shape.x + shape.width / 2
            centre_y = shape.y + shape.height / 2

            # Shift left if shape is right of centre, otherwise shift right
            # Can't move both areas at the same time, as there could be rectangles in the corners
            if centre_x > centre_point:
                space_x = -log.find_shapes_closest_to_shape(c_shape=shape, orientation="left")
            else:
                space_x = log.find_shapes_closest_to_shape(c_shape=shape, orientation="right")

            if centre_y > centre_point:
                space_y = -log.find_shapes_closest_to_shape(c_shape=shape, orientation="down")
            else:
                space_y = log.find_shapes_closest_to_shape(c_shape=shape, orientation="up")

            if len(ALNS_tools.check_if_rectangle_empty(x_0=shape.x + space_x,
                                                       x_1=shape.x + space_x + shape.width,
                                                       y_0=shape.y + space_y,
                                                       y_1=shape.y + space_y + shape.height,
                                                       log=log)) == 0:

                if space_x != 0 or space_y != 0:
                    logger.debug(f"Moved shape {shape.shape_id} from ({shape.x},{shape.y}) "
                                 f"to ({shape.x + space_x}, {shape.y + space_y}) using CENTRE")
                    shape.x += space_x
                    shape.y += space_y
                    successful = True
            elif abs(space_x) > abs(space_y):
                successful = True
                logger.debug(
                    f"Moved shape {shape.shape_id} from ({shape.x}, {shape.y}) to ({shape.x + space_x}, {shape.y}) "
                    f"- did not move y coordinates")
                shape.x += space_x
            else:
                if space_x != 0 or space_y != 0:
                    logger.debug(
                        f"Moved shape {shape.shape_id} from ({shape.x}, {shape.y}) to ({shape.x}, {shape.y + space_y}) "
                        f"- did not move x coordinates")
                    shape.y += space_y
                    successful = True
            if shape.x < 0 or shape.y < 0 or shape.x > log.diameter or shape.y > log.diameter:
                raise ValueError(f"Moved {shape.shape_id} to illegal location {shape.x, shape.y} "
                                 f"using {space_x}, {space_y} from ({centre_x}, {centre_y})")

    elif name.endswith("LEFT"):
        for shape in random_shapes:
            space_left = log.find_shapes_closest_to_shape(c_shape=shape, orientation="left")
            if space_left > 0:
                successful = True
                logger.debug(f"Moved shape {shape.shape_id} x: {shape.x} to {shape.x - space_left} using LEFT")
                shape.x = shape.x - space_left
    elif name.endswith("RIGHT"):
        for shape in random_shapes:
            space_right = log.find_shapes_closest_to_shape(c_shape=shape, orientation="right")
            if space_right > 0:
                successful = True
                logger.debug(f"Moved shape {shape.shape_id} x: {shape.x} to {shape.x + space_right} using RIGHT")
                shape.x = shape.x + space_right
    elif name.endswith("UP"):
        for shape in random_shapes:
            space_up = log.find_shapes_closest_to_shape(c_shape=shape, orientation="up")
            if space_up > 0:
                successful = True
                logger.debug(f"Moved shape {shape.shape_id} x: {shape.y} to {shape.y + space_up} using UP")
                shape.y = shape.y + space_up
    elif name.endswith("DOWN"):
        for shape in random_shapes:
            space_down = log.find_shapes_closest_to_shape(c_shape=shape, orientation="down")
            if space_down > 0:
                successful = True
                logger.debug(f"Moved shape {shape.shape_id} x: {shape.y} to {shape.y + space_down} using DOWN")
                shape.y = shape.y - space_down
    t_1 = time.perf_counter()
    return successful, t_1 - t_0


def random_destroy(log: Log) -> tuple:
    """
    Randomly removes a shape from the log. Selects a shape based on distance to the centre.
    The further the centre of a shape is from the centre of the log, the higher the likelihood of it being picked.
    :param log:
    :return:
    """
    t_0 = time.perf_counter()
    successful = False

    if len(log.shapes) == 0:
        t_1 = time.perf_counter()
        return successful, t_1 - t_0

    removed_shape = select_random_shapes_from_log(log)

    logger.debug(f"Removed Shape at ({removed_shape.x}, {removed_shape.y}), "
                 f"({removed_shape.x + removed_shape.width}, {removed_shape.y + removed_shape.height})")

    removed_shape.remove_from_log()
    del removed_shape
    successful = True
    t_1 = time.perf_counter()
    return successful, t_1 - t_0


def random_cluster_destroy(log: Log) -> tuple:
    t_0 = time.perf_counter()
    successful = False
    removed_shape = select_random_shapes_from_log(log)

    space_left = log.find_shapes_closest_to_shape(c_shape=removed_shape, orientation="left")
    space_right = log.find_shapes_closest_to_shape(c_shape=removed_shape, orientation="right")
    space_up = log.find_shapes_closest_to_shape(c_shape=removed_shape, orientation="up")
    space_down = log.find_shapes_closest_to_shape(c_shape=removed_shape, orientation="down")

    plane = random.choices(["horizontal", "vertical"], [0.5, 0.5], k=1)[0]

    min_width_check = constants.min_width_shape_type.width
    min_height_check = constants.min_height_shape_type.height

    width_steps = int(np.floor(removed_shape.width / (min_width_check - 1)))
    height_steps = int(np.floor(removed_shape.height / (min_height_check - 1)))

    x_steps = ([removed_shape.x + i * min_width_check for i in range(width_steps + 1)]
               + [removed_shape.x + removed_shape.width + constants.saw_kerf])
    y_steps = ([removed_shape.y + j * min_width_check for j in range(height_steps + 1)]
               + [removed_shape.y + removed_shape.height + constants.saw_kerf])
    removed_shapes = [removed_shape]
    if plane == "horizontal":
        # remove shapes directly left and right of the shape
        shapes_left = [s for s in log.shapes if s.x + s.width + constants.saw_kerf <= removed_shape.x]
        shapes_right = [s for s in log.shapes if s.x >= removed_shape.x + removed_shape.width + constants.saw_kerf]
        x_val = removed_shape.x - space_left - 2 * constants.saw_kerf
        for y_val in y_steps:
            for shape in shapes_left:
                # Select x to be an x value just past the point where another shape's edge has been located
                if shape not in removed_shapes and shape.check_if_point_in_shape(x=x_val, y=y_val):
                    removed_shapes.append(shape)
            for shape in shapes_right:
                if shape not in removed_shapes and shape.check_if_point_in_shape(x=x_val, y=y_val):
                    removed_shapes.append(shape)
    else:
        shapes_up = [s for s in log.shapes if s.y >= removed_shape.y + removed_shape.height + constants.saw_kerf]
        shapes_down = [s for s in log.shapes if s.y + s.height + constants.saw_kerf <= removed_shape.y]
        y_val = removed_shape.y - space_down - 2 * constants.saw_kerf
        for x_val in x_steps:
            for shape in shapes_up:
                if shape not in removed_shapes and shape.check_if_point_in_shape(x=x_val, y=y_val):
                    removed_shapes.append(shape)
            for shape in shapes_down:
                if shape not in removed_shapes and shape.check_if_point_in_shape(x=x_val, y=y_val):
                    removed_shapes.append(shape)

    if len(removed_shapes) > 0:
        successful = True
    debug_string = "Removed cluster containing: "
    for shape in removed_shapes:
        debug_string += f"{shape.shape_id}, "
        shape.remove_from_log()
        del shape

    t_1 = time.perf_counter()
    return successful, t_1 - t_0


def subspace_destroy(log: Log, shape_types: list) -> tuple:
    successful = False
    t_0 = time.perf_counter()

    t_1 = time.perf_counter()
    return successful, t_1 - t_0


def inefficiency_destroy(log: Log, shape_types: list) -> tuple:
    successful = False
    t_0 = time.perf_counter()

    t_1 = time.perf_counter()
    return successful, t_1 - t_0


def random_point_expansion(log: Log, shape_types: list) -> tuple:
    """
    RPE selects a random point in the log, it then calculates the maximum rectangle it can create until there
    is a collision in every direction. It then checks if this area is empty of shapes. If so, it applies an LP to
    fill up the area. If not - it
    :param log:
    :param shape_types:
    :return:
    """
    t_0 = time.perf_counter()
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

    logger.debug(f"Selected point in Log {log.log_id} at ({p_x: .2f}, {p_y: .2f})")
    """
    Feasible point has been found, attempt to expand towards the center point, and find first collision
    Here we use the minimum width shape and the minimum height shape to ensure that we do not have to check every point.
    Hence, we initially check the point the minimum distance away. 
    If it is not occupied, we expand again with the same width.
    If the tile is occupied, we find the shape the point is contained in, and go to the edge of that shape
    """

    left_most_x, right_most_x = log.calculate_edge_positions_on_circle(p_y)
    lowest_y, highest_y = log.calculate_edge_positions_on_circle(p_x)

    # logger.debug(f"Initialized x_l {left_most_x: .2f}, x_r {right_most_x: .2f}, "
    #              f"y_min {lowest_y: .2f}, y_max {highest_y: .2f}.")

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
    # logger.debug(f"After checking shape collisions x_l {left_most_x: .2f}, x_r {right_most_x: .2f}, "
    #              f"y_min {lowest_y: .2f}, y_max {highest_y: .2f}.")
    # Check if rectangle is empty
    violating_shapes = ALNS_tools.check_if_rectangle_empty(x_0=left_most_x, x_1=right_most_x,
                                                           y_0=lowest_y, y_1=highest_y, log=log)

    # For all violating shapes we have to make a cut in the plane to ensure the rectangle is clean
    for shape in violating_shapes:
        # Check if shape still violates cut, as previous cuts could have put this shape out of violation
        violates = ALNS_tools.check_if_shape_in_rectangle(shape=shape, x_0=left_most_x, x_1=right_most_x,
                                                          y_0=lowest_y, y_1=highest_y)
        if not violates:
            continue

        # There are 4 possible cuts - find the cut that loses the least surface area
        cut_upper_off = (right_most_x - left_most_x) * ((shape.y - constants.saw_kerf) - lowest_y)
        cut_lower_off = (right_most_x - left_most_x) * (highest_y - (shape.y + shape.height + constants.saw_kerf))
        cut_left_off = (right_most_x - (shape.x + shape.width + constants.saw_kerf)) * (highest_y - lowest_y)
        cut_right_off = ((shape.x - constants.saw_kerf) - left_most_x)
        cuts = [cut_upper_off, cut_lower_off, cut_left_off, cut_right_off]

        # Update Values Based On Selected Optimal Cut
        largest_remaining_cut = max(cuts)
        if cut_upper_off == largest_remaining_cut:
            highest_y = shape.y - constants.saw_kerf
        elif cut_lower_off == largest_remaining_cut:
            lowest_y = shape.y + shape.height + constants.saw_kerf
        elif cut_left_off == largest_remaining_cut:
            left_most_x = shape.x + shape.width + constants.saw_kerf
        else:
            right_most_x = shape.x - constants.saw_kerf

    # logger.debug(f"Post Calculations: x_l {left_most_x: .2f}, x_r {right_most_x: .2f}, "
    #              f"y_min {lowest_y: .2f}, y_max {highest_y: .2f}.")

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
        # logger.debug("No feasible solution")
        pass
    elif usage_wide > usage_high:
        for shape in new_shapes_wide:
            shape.assign_to_log(log)
        successful = True
    elif usage_wide < usage_high:
        for shape in new_shapes_high:
            shape.assign_to_log(log)
        successful = True

    t_1 = time.perf_counter()
    return successful, t_1 - t_0


def single_extension_repair(log: Log, shape_types: list) -> tuple:
    t_0 = time.perf_counter()
    successful = False

    shape = select_random_shapes_from_log(log)
    # Select Candidate shape ensuring the new shape is larger in at least one direction
    candidate_shapes = [s for s in shape_types if (s.height > shape.height and s.width >= shape.width) or
                        (s.height >= shape.height and s.width > shape.width)]

    if len(candidate_shapes) == 0:
        t_1 = time.perf_counter()
        return successful, t_1 - t_0

    space_left = log.find_shapes_closest_to_shape(shape, orientation="left")
    space_right = log.find_shapes_closest_to_shape(shape, orientation="right")
    space_up = log.find_shapes_closest_to_shape(shape, orientation="up")
    space_down = log.find_shapes_closest_to_shape(shape, orientation="down")

    # Now expand in either horizontal or vertical direction
    total_horizontal_space = space_left + space_right + shape.width
    total_vertical_space = space_up + space_down + shape.height
    wider_pieces = [s for s in candidate_shapes if s.width <= total_horizontal_space
                    and s.height == shape.height]
    higher_pieces = [s for s in candidate_shapes if s.width == shape.width
                     and s.height <= total_vertical_space]
    if len(wider_pieces) == 0 == len(higher_pieces):
        t_1 = time.perf_counter()
        return successful, t_1 - t_0

    shape_type = max(wider_pieces + higher_pieces, key=lambda option: option.width * option.height)
    # Either the new piece is higher, and it stays at same x, or it's wider and stays at same y
    if shape_type.width == shape.width:
        replacement_piece = Shape(shape_type=shape_type, x=shape.x, y=shape.y - space_down)
    else:
        replacement_piece = Shape(shape_type=shape_type, x=shape.x - space_left, y=shape.y)
    replacement_piece.assign_to_log(log)
    logger.debug(f"SER Replaced {shape.shape_id}: ({shape.x},{shape.y}) - ({shape.width}, {shape.height}) with "
                 f"({shape.x - space_left}, {shape.y - space_down}) - ({shape_type.width}, {shape_type.height}) "
                 f"in log {log.log_id}")
    shape.remove_from_log()
    successful = True
    t_1 = time.perf_counter()
    return successful, t_1 - t_0


def buddy_extension_repair(log: Log, shape_types: list) -> tuple:
    t_0 = time.perf_counter()
    successful = False

    shape = select_random_shapes_from_log(log)
    sk = constants.saw_kerf
    location_pairs = [[shape.x, shape.y - 2*sk], [shape.x - 2*sk, shape.y],  # Bot left
                      [shape.x, shape.y + shape.height + 2*sk], [shape.x - 2*sk, shape.y + shape.height],  # Top left
                      [shape.x + shape.width, shape.y + shape.height + 2*sk],
                      [shape.x + shape.width + 2*sk, shape.y + shape.height],  # Top Right
                      [shape.x + shape.width + 2*sk, shape.y], [shape.x + shape.width, shape.y - 2*sk]]  # Bot Right
    rect_sizes = []
    for location in location_pairs:
        space_left = log.find_distance_to_closest_shape_from_point(x=location[0], y=location[1], orientation="left")
        space_right = log.find_distance_to_closest_shape_from_point(x=location[0], y=location[1], orientation="right")
        space_up = log.find_distance_to_closest_shape_from_point(x=location[0], y=location[1], orientation="up")
        space_down = log.find_distance_to_closest_shape_from_point(x=location[0], y=location[1], orientation="down")
        rect_sizes.append((space_right - space_left) * (space_up - space_down))

    t_1 = time.perf_counter()
    return successful, t_1 - t_0


class Method:
    failure_adjust_rate = 0.95
    success_adjust_rate = 0.99

    def __init__(self, name: str, goal: str):
        self.name = name
        self.performance = 100
        self.probability = 1
        self.method_used = False
        self.times_called = 0
        self.total_attempted = 0
        self.total_succeeded = 0
        self.goal = goal
        self.seconds_success = 0
        self.seconds_failure = 0

    def method_failed(self) -> None:
        self.performance = self.performance * self.failure_adjust_rate

    def method_success(self) -> None:
        self.performance = self.performance * self.success_adjust_rate

    def execute(self, log, shape_types: list) -> bool:
        attempts = 0
        while attempts < constants.repair_max_attempts:
            if self.name.startswith("TUCK"):
                succeeded, duration = tuck(self.name, log)
            elif self.name == "RANDOM":
                succeeded, duration = random_destroy(log)
            elif self.name == "CLUSTER":
                succeeded, duration = random_cluster_destroy(log)
            elif self.name == "SUBSPACE":
                succeeded, duration = subspace_destroy(log, shape_types)
            elif self.name == "INEFFICIENCY":
                succeeded, duration = inefficiency_destroy(log, shape_types)
            elif self.name == "RPE":
                succeeded, duration = random_point_expansion(log, shape_types)
            elif self.name == "SER":
                succeeded, duration = single_extension_repair(log, shape_types)
            elif self.name == "BER":
                succeeded, duration = buddy_extension_repair(log, shape_types)
            else:
                raise ValueError(f"ALNS Method {self.name} Not Implemented")

            if succeeded:
                logger.debug(f"Method {self.name} succeeded in {attempts} attempts.")
                self.total_attempted += attempts
                self.total_succeeded += 1
                self.seconds_success += duration
                return succeeded
            else:
                attempts += 1
                self.seconds_failure += duration
        # If we exceed max iterations, the method failed.
        logger.debug(f"Did not succeed using method {self.name} within the maximum iterations")
        self.total_attempted += attempts
        return False

    def used(self) -> None:
        self.method_used = True
        self.times_called += 1


def update_method_probability(methods: list, updated) -> None:
    total_performance = sum([method.performance for method in methods])

    for method in methods:
        if updated and method.used:
            if method.total_attempted != 0:
                method.performance = (method.performance * constants.method_sensitivity_acceptance *
                                      math.sqrt(method.method_used / method.total_attempted))
            else:
                method.performance = method.performance * constants.method_sensitivity_acceptance
            method.method_used = False
        elif method.used:
            method.performance = method.performance * constants.method_sensitivity_rejection

    for method in methods:
        method.probability = method.performance / total_performance

