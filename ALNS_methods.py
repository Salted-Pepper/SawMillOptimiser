import random

import constants
import numpy as np
import logging
import datetime
import math
import time

import ALNS_tools
from shapes import Shape
from logs import Log, select_random_shapes_from_log

date = datetime.date.today()
logging.basicConfig(level=logging.DEBUG, filename='saw_mill_app_' + str(date) + '.log',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt="%H:%M:%S")
logger = logging.getLogger("ALNS_Methods")
logger.setLevel(logging.DEBUG)


def tuck(name: str, log: Log, **kwargs) -> tuple:
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
                    # logger.debug(f"Moved shape {shape.shape_id} from ({shape.x:.2f},{shape.y:.2f}) "
                    #              f"to ({shape.x + space_x:.2f}, {shape.y + space_y:.2f}) using CENTRE")
                    shape.x += space_x
                    shape.y += space_y
                    successful = True
            elif abs(space_x) > abs(space_y):
                successful = True
                # logger.debug(
                #     f"Moved shape {shape.shape_id} from ({shape.x:.2f}, {shape.y:.2f})
                #     to ({shape.x + space_x:.2f}, {shape.y:.2f}) "
                #     f"- did not move y coordinates")
                shape.x += space_x
            else:
                if space_x != 0 or space_y != 0:
                    # logger.debug(
                    #     f"Moved shape {shape.shape_id} from ({shape.x:.2f}, {shape.y:.2f})
                    #     to ({shape.x:.2f}, {shape.y + space_y:.2f}) "
                    #     f"- did not move x coordinates")
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
                # logger.debug(f"Moved shape {shape.shape_id} x: {shape.x:.2f}
                # to {shape.x - space_left:.2f} using LEFT")
                shape.x = shape.x - space_left
    elif name.endswith("RIGHT"):
        for shape in random_shapes:
            space_right = log.find_shapes_closest_to_shape(c_shape=shape, orientation="right")
            if space_right > 0:
                successful = True
                # logger.debug(f"Moved shape {shape.shape_id} x: {shape.x:.2f}
                # to {shape.x + space_right:.2f} using RIGHT")
                shape.x = shape.x + space_right
    elif name.endswith("UP"):
        for shape in random_shapes:
            space_up = log.find_shapes_closest_to_shape(c_shape=shape, orientation="up")
            if space_up > 0:
                successful = True
                # logger.debug(f"Moved shape {shape.shape_id} x: {shape.y:.2f} to {shape.y + space_up:.2f} using UP")
                shape.y = shape.y + space_up
    elif name.endswith("DOWN"):
        for shape in random_shapes:
            space_down = log.find_shapes_closest_to_shape(c_shape=shape, orientation="down")
            if space_down > 0:
                successful = True
                # logger.debug(f"Moved shape {shape.shape_id} x: {shape.y:.2f}
                # to {shape.y + space_down:.2f} using DOWN")
                shape.y = shape.y - space_down
    t_1 = time.perf_counter()
    return successful, t_1 - t_0


def random_destroy(log: Log, **kwargs) -> tuple:
    """
    Randomly removes a shape from the log. Selects a shape based on distance to the centre.
    The further the centre of a shape is from the centre of the log, the higher the likelihood of it being picked.
    :param log:
    :return:
    """
    t_0 = time.perf_counter()
    successful = False

    removed_shape = select_random_shapes_from_log(log)

    logger.debug(f"Removed Shape at ({removed_shape.x}, {removed_shape.y}), "
                 f"({removed_shape.x + removed_shape.width}, {removed_shape.y + removed_shape.height})")

    removed_shape.remove_from_log()
    del removed_shape
    successful = True
    t_1 = time.perf_counter()
    return successful, t_1 - t_0


def random_cluster_destroy(log: Log, **kwargs) -> tuple:
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
               + [removed_shape.x + removed_shape.width + log.saw_kerf])
    y_steps = ([removed_shape.y + j * min_width_check for j in range(height_steps + 1)]
               + [removed_shape.y + removed_shape.height + log.saw_kerf])
    removed_shapes = [removed_shape]
    if plane == "horizontal":
        # remove shapes directly left and right of the shape
        shapes_left = [s for s in log.shapes if s.x + s.width + log.saw_kerf <= removed_shape.x]
        shapes_right = [s for s in log.shapes if s.x >= removed_shape.x + removed_shape.width + log.saw_kerf]

        for y_val in y_steps:
            x_val = removed_shape.x - space_left - 2 * log.saw_kerf
            for shape in shapes_left:
                # Select x to be an x value just past the point where another shape's edge has been located
                if shape not in removed_shapes and shape.check_if_point_in_shape(x=x_val, y=y_val):
                    removed_shapes.append(shape)
            x_val = removed_shape.x + removed_shape.width + space_right + 2 * log.saw_kerf
            for shape in shapes_right:
                if shape not in removed_shapes and shape.check_if_point_in_shape(x=x_val, y=y_val):
                    removed_shapes.append(shape)
    else:
        shapes_up = [s for s in log.shapes if s.y >= removed_shape.y + removed_shape.height + log.saw_kerf]
        shapes_down = [s for s in log.shapes if s.y + s.height + log.saw_kerf <= removed_shape.y]
        for x_val in x_steps:
            y_val = removed_shape.y - space_down - 2 * log.saw_kerf
            for shape in shapes_up:
                if shape not in removed_shapes and shape.check_if_point_in_shape(x=x_val, y=y_val):
                    removed_shapes.append(shape)
            y_val = removed_shape.y + removed_shape.height + space_up + 2 * log.saw_kerf
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


def subspace_destroy(log: Log, **kwargs) -> tuple:
    """
    Create a random set of rectangles. Calculate the efficiency in the rectangles. Remove shapes overlapping
    with the lowest efficiency rectangle.
    :param log:
    :return:
    """
    successful = False
    t_0 = time.perf_counter()

    rectangles = []

    for _ in range(5):
        found_point = False
        attempts = 0
        while not found_point:
            min_value = max(constants.min_height_shape_type.height, constants.min_width_shape_type.width)
            max_value = log.diameter - min_value
            # Select a point that can fit at least a shape to prevent wasting time on small sub-rectangles
            p_x, p_y = np.random.uniform(low=min_value, high=max_value, size=2)
            if log.check_if_point_in_log(p_x, p_y):
                found_point = True

            attempts += 1
            if attempts > constants.max_iterations:
                logging.debug(f"Subspace destroy failed to find a suitable point")
                t_1 = time.perf_counter()
                return successful, t_1 - t_0

        x_min, x_max = log.calculate_edge_positions_on_circle(p_y)
        y_min, y_max = log.calculate_edge_positions_on_circle(p_x)

        max_width = x_max - p_x
        max_height = y_max - p_y

        width = np.random.uniform(low=constants.min_width_shape_type.width, high=max_width)
        height = np.random.uniform(low=constants.min_height_shape_type.height, high=max_height)
        # Place the rectangle in a way such that it fits within the boundaries
        x_0, x_1, y_0, y_1 = ALNS_tools.fit_points_in_boundaries(left_x=p_x,
                                                                 right_x=p_x + width,
                                                                 low_y=p_y,
                                                                 high_y=p_y + height,
                                                                 log=log)
        rectangles.append([x_0, x_1, y_0, y_1].copy())

    min_efficiency = math.inf

    min_rect = []
    for rectangle in rectangles:
        x_0, x_1, y_0, y_1 = rectangle
        efficiency, intersecting_shapes = log.calculate_efficiency_sub_rectangle(x_0, x_1, y_0, y_1,
                                                                                 saw_kerf=log.saw_kerf)
        if efficiency < min_efficiency and len(intersecting_shapes) != 0:
            min_rect = [x_0, x_1, y_0, y_1, intersecting_shapes]
            min_efficiency = efficiency

    if min_efficiency > 0.98:
        t_1 = time.perf_counter()
        return successful, t_1 - t_0

    if len(min_rect) == 0:
        t_1 = time.perf_counter()
        return False, t_1 - t_0

    x_0 = min_rect[0]
    x_1 = min_rect[1]
    y_0 = min_rect[2]
    y_1 = min_rect[3]
    int_shapes = min_rect[4]

    logger.debug(f"Removing rectangle (x: {x_0:.2f}, {x_1:.2f}, y: {y_0:.2f}, {y_1:.2f}) "
                 f"containing {len(int_shapes)} shapes ")
    for shape in int_shapes:
        shape.remove_from_log()

    t_1 = time.perf_counter()
    successful = True
    return successful, t_1 - t_0


def random_point_expansion(log: Log, shape_types: list, **kwargs) -> tuple:
    """
    RPE selects a random point in the log, it then calculates the maximum rectangle it can create until there
    is a collision in every direction. It then checks if this area is empty of shapes. If so, it applies an LP to
    fill up the area. If not - it
    :param log:
    :param shape_types:
    :return:
    """
    t_0 = time.perf_counter()

    found_point = False
    attempts = 0
    while not found_point:
        p_x, p_y = np.random.uniform(low=0, high=log.diameter, size=2)

        if log.check_if_point_in_log(p_x, p_y):
            point_in_shape = False
            for shape in log.shapes:
                if shape.check_if_point_in_shape(p_x, p_y):
                    point_in_shape = True

            if not point_in_shape:
                found_point = True

        attempts += 1
        if attempts > 100:
            logging.debug(f"RPE repair failed to find a suitable point")
            t_1 = time.perf_counter()
            return False, t_1 - t_0

    #  logger.debug(f"Selected point in Log {log.log_id} at ({p_x: .2f}, {p_y: .2f})")
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
        if shape.x - log.saw_kerf <= p_x <= shape.x + shape.width + log.saw_kerf:
            # Then a y-collision is possible
            if p_y > shape.y + shape.height + log.saw_kerf > lowest_y:
                lowest_y = shape.y + shape.height + log.saw_kerf

            if p_y < shape.y - log.saw_kerf < highest_y:
                highest_y = shape.y - log.saw_kerf

        if shape.y - log.saw_kerf <= p_y <= shape.y + shape.height + log.saw_kerf:
            # Then an x-collision is possible
            if p_x > shape.x + shape.width + log.saw_kerf > left_most_x:
                left_most_x = shape.x + shape.width + log.saw_kerf

            if p_x < shape.x - log.saw_kerf < right_most_x:
                right_most_x = shape.x - log.saw_kerf
    # logger.debug(f"After checking shape collisions x_l {left_most_x: .2f}, x_r {right_most_x: .2f}, "
    #              f"y_min {lowest_y: .2f}, y_max {highest_y: .2f}.")
    successful = ALNS_tools.fit_defined_rectangle(left_most_x, right_most_x, lowest_y, highest_y, log, shape_types)

    t_1 = time.perf_counter()
    return successful, t_1 - t_0


def single_extension_repair(log: Log, shape_types: list, **kwargs) -> tuple:
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
    logger.debug(f"SER Replaced {shape.shape_id}: ({shape.x:.2f},{shape.y:.2f}) - ({shape.width}, {shape.height}) with "
                 f"({shape.x - space_left:.2f}, {shape.y - space_down:.2f}) "
                 f"- ({shape_type.width}, {shape_type.height}) "
                 f"in log {log.log_id}")
    shape.remove_from_log()
    successful = True
    t_1 = time.perf_counter()
    return successful, t_1 - t_0


def buddy_extension_repair(log: Log, shape_types: list, **kwargs) -> tuple:
    t_0 = time.perf_counter()
    successful = False

    shape = select_random_shapes_from_log(log)
    sk = log.saw_kerf
    location_pairs = [[shape.x, shape.y - 2 * sk], [shape.x - 2 * sk, shape.y],  # Bot left
                      [shape.x, shape.y + shape.height + 2 * sk], [shape.x - 2 * sk, shape.y + shape.height],
                      # Top left
                      [shape.x + shape.width, shape.y + shape.height + 2 * sk],
                      [shape.x + shape.width + 2 * sk, shape.y + shape.height],  # Top Right
                      [shape.x + shape.width + 2 * sk, shape.y], [shape.x + shape.width, shape.y - 2 * sk]]  # Bot Right
    rect_sizes = []
    for location in location_pairs:
        feasible = True
        for shape in log.shapes:
            if shape.check_if_point_in_shape(location[0], location[1]):
                feasible = False
                continue

        if log.check_if_point_in_log(location[0], location[1]) and feasible:
            # TODO: (Optional) - in theory we can save computational time
            #  by not checking the side on which the "buddy" shape is on
            space_left = log.find_distance_to_closest_shape_from_point(x=location[0],
                                                                       y=location[1],
                                                                       orientation="left")
            space_right = log.find_distance_to_closest_shape_from_point(x=location[0],
                                                                        y=location[1],
                                                                        orientation="right")
            space_up = log.find_distance_to_closest_shape_from_point(x=location[0],
                                                                     y=location[1],
                                                                     orientation="up")
            space_down = log.find_distance_to_closest_shape_from_point(x=location[0],
                                                                       y=location[1],
                                                                       orientation="down")
            rect_sizes.append([location[0], location[1],
                               (space_right - space_left) * (space_up - space_down),
                               space_left, space_right, space_up, space_down])
        else:
            rect_sizes.append([location[0], location[1], 0, 0, 0, 0, 0])

    largest_location_data = max(rect_sizes, key=lambda val: val[2])
    x = largest_location_data[0]
    y = largest_location_data[1]
    space_left = largest_location_data[3]
    space_right = largest_location_data[4]
    space_up = largest_location_data[5]
    space_down = largest_location_data[6]

    if max(space_up, space_down) == 0 or max(space_left, space_right) == 0:
        t_1 = time.perf_counter()
        return successful, t_1 - t_0

    x_0 = x - space_left
    x_1 = x + space_right
    y_0 = y - space_down
    y_1 = y + space_up
    corners = [log.check_if_point_in_log(x=x_0, y=y_0),
               log.check_if_point_in_log(x=x_0, y=y_1),
               log.check_if_point_in_log(x=x_1, y=y_0),
               log.check_if_point_in_log(x=x_1, y=y_1)]
    # Ensure all corners are in the log, if not, prioritize maintaining dimension with minimal space available
    if not all(corners):
        if y_1 - y_0 > x_1 - x_0:
            x_0, x_1, y_0, y_1 = ALNS_tools.fit_points_in_boundaries(x_0, x_1, y_0, y_1, priority="width", log=log)
        else:
            x_0, x_1, y_0, y_1 = ALNS_tools.fit_points_in_boundaries(x_0, x_1, y_0, y_1, priority="height", log=log)

    successful = ALNS_tools.fit_defined_rectangle(left_most_x=x_0, right_most_x=x_1,
                                                  lowest_y=y_0, highest_y=y_1,
                                                  log=log, shape_types=shape_types)
    t_1 = time.perf_counter()
    return successful, t_1 - t_0


class Method:
    failure_adjust_rate = 0.95
    success_adjust_rate = 0.99

    def __init__(self, name: str, goal: str):
        self.name = name
        self.performance = 100
        self.probability = 1/3
        self.method_used = False
        self.times_called = 0
        self.total_attempted = 0
        self.total_succeeded = 0
        self.goal = goal
        self.seconds_success = 0
        self.seconds_failure = 0
        self.iteration_succeed = 0

        if name.startswith("TUCK"):
            self.method_function = tuck
        elif name == "RANDOM":
            self.method_function = random_destroy
        elif name == "CLUSTER":
            self.method_function = random_cluster_destroy
        elif name == "SUBSPACE":
            self.method_function = subspace_destroy
        elif name == "RPE":
            self.method_function = random_point_expansion
        elif name == "SER":
            self.method_function = single_extension_repair
        elif name == "BER":
            self.method_function = buddy_extension_repair
        else:
            raise ValueError(f"Method {self.name} not defined")

    def method_failed(self) -> None:
        self.performance = self.performance * self.failure_adjust_rate

    def method_success(self) -> None:
        self.performance = self.performance * self.success_adjust_rate
        self.iteration_succeed += 1

    def execute(self, log, shape_types: list) -> bool:
        self.times_called += 1
        attempts = 0
        repeat = True
        duration = 0

        self.method_used = True

        while attempts < constants.max_attempts and repeat:
            if len(log.shapes) > 0:
                succeeded, duration = self.method_function(name=self.name, log=log, shape_types=shape_types)
            else:
                succeeded = False
                repeat = False

            attempts += 1

            if succeeded:
                logger.debug(f"Method {self.name} succeeded in {attempts} attempts.")
                self.total_attempted += attempts
                self.total_succeeded += 1
                self.seconds_success += duration
                return succeeded
            else:
                self.seconds_failure += duration
        # If we exceed max iterations, the method failed.
        logger.debug(f"Did not succeed using method {self.name} within the maximum iterations")
        self.total_attempted += attempts
        return False


def update_method_probability(methods: list, accepted_solution) -> None:
    for method in methods:
        if accepted_solution and method.method_used:
            method.performance = (method.performance * constants.method_sensitivity_acceptance *
                                  max(0.1, math.sqrt(method.total_succeeded / method.total_attempted)))
        elif method.method_used:
            method.performance = (method.performance * constants.method_sensitivity_rejection **
                                  (1 + method.iteration_succeed/constants.max_attempts))

    total_performance = sum([method.performance for method in methods])
    for method in methods:
        logger.debug(f"Updating method {method.name} from {method.probability} to "
                     f"{method.performance / total_performance} - Method Used?: {method.method_used}")
        method.probability = method.performance / total_performance
        method.performance = method.performance * 10
        method.method_used = False
        method.iteration_succeed = 0
