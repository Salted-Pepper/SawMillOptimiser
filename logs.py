import logging

import ALNS_tools
import constants
from shapes import Shape

import datetime
import math
import random
import numpy as np
import matplotlib.pyplot as plt
import os

date = datetime.date.today()
logging.basicConfig(level=logging.DEBUG, filename=os.path.join(os.getcwd(), 'logs/saw_mill_app' + str(date) + '.log'),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt="%H:%M:%S")
logger = logging.getLogger("Logs")
logger.setLevel(logging.DEBUG)

log_id = 0


class Log:
    def __init__(self, diameter: float = 0, saw_kerf=None, copy_id: int = None) -> None:
        global log_id

        # Keep track of copies of logs using same id
        if copy_id is None:
            self.log_id = log_id
            log_id += 1
        else:
            self.log_id = copy_id
        self.diameter = diameter
        self.saw_kerf = saw_kerf

        # Efficiency Measures
        self.recovery_rate = None
        self.volume = math.pi * (diameter / 2) ** 2
        self.volume_used = 0
        self.saw_dust = 0
        self.efficiency = 0
        self.score = -math.inf
        self.selection_weight = 100

        # Plotting Variables
        self.fig = None
        self.ax = None
        self.shapes = []
        self.patches = []

        # Log buttons for inputs
        self.label = None
        self.diameter_input = None
        self.saw_kerf_input = None
        self.remove_button = None

    def set_diameter(self):
        self.diameter = float(self.diameter_input.get())
        self.volume = math.pi * (self.diameter / 2) ** 2

    def set_saw_kerf(self):
        self.saw_kerf = float(self.saw_kerf_input.get())

    def remove_labels(self):
        global log_id
        log_id -= 1
        self.label.grid_remove()
        self.diameter_input.grid_remove()
        self.saw_kerf_input.grid_remove()
        self.remove_button.grid_remove()

    def plot_log(self) -> None:
        fig = plt.figure(figsize=(9, 9))
        ax = fig.add_subplot(111)

        ax.set_xlim(0, 1.1 * self.diameter)
        ax.set_ylim(0, 1.1 * self.diameter)

        self.fig = fig
        self.ax = ax

    def update_plot(self, extra_text="") -> None:
        for patch in self.patches:
            patch.remove()
        for shape in self.shapes:
            self.patches.extend(shape.add_rect_to_plot())
        circle = plt.Circle((self.diameter / 2, self.diameter / 2), self.diameter / 2,
                            color='saddlebrown', fill=False)
        self.ax.add_patch(circle)
        self.ax.set_title(f"id: {self.log_id}, "
                          r"$d_i$:" + f"{self.diameter}, "
                                      f"Usage:" + f"{self.calculate_efficiency():.2f}, "
                                                  f"Saw dust:" + f"{self.calculate_sawdust_created() / self.volume:.2f}" + extra_text)
        self.patches.append(circle)

    def calculate_efficiency(self) -> float:
        self.efficiency = self.volume_used / self.volume
        return self.efficiency

    def calculate_efficiency_sub_rectangle(self, x_0, x_1, y_0, y_1, saw_kerf: float) -> tuple:
        intersecting_shapes = []
        for shape in self.shapes:
            if ALNS_tools.check_if_shape_in_rectangle(shape, x_0, x_1, y_0, y_1, saw_kerf=saw_kerf):
                intersecting_shapes.append(shape)

        if len(intersecting_shapes) == 0:
            return 0, intersecting_shapes

        volume_rect = (x_1 - x_0) * (y_1 - y_0)
        shape_volume_in_rect = 0
        for shape in intersecting_shapes:
            # calculate shape volume in rect
            shape_volume_in_rect += ((min(x_1, shape.x + shape.width) - max(x_0, shape.x)) *
                                     (min(y_1, shape.y + shape.height) - max(y_0, shape.y)))
        rel_usage = shape_volume_in_rect / volume_rect, intersecting_shapes
        # logging.debug(f"Efficiency of sub-rectangle (({x_0}, {y_0}), ({x_1},{y_1})) is {rel_usage}")
        return rel_usage

    def return_plot(self) -> tuple:
        return self.fig, self.ax

    def show_plot(self, extra_text="", show=True) -> None:
        global date
        self.plot_log()
        self.update_plot(extra_text)
        if show:
            self.fig.show()

    def save_log_plot(self):
        date_time = datetime.datetime.now()
        self.fig.savefig(os.path.join(os.getcwd(),
                                      f"plots/log_{self.log_id}_{date_time.strftime('%d_%m_%Y_%H_%M_%S')}.png"))

    def calculate_edge_positions_on_circle(self, z: float) -> tuple:
        r = self.diameter / 2
        try:
            z_min = r - math.sqrt(r ** 2 - (z - r) ** 2)
            z_plus = r + math.sqrt(r ** 2 - (z - r) ** 2)
        except ValueError as e:
            self.show_plot()
            logger.critical(f"Math domain error for {z} in log {self.log_id}: {e}")
            raise ValueError(f"Math domain error for {z} in log {self.log_id}")
        return z_min, z_plus

    def check_if_feasible(self) -> bool:
        for index_1, s1 in enumerate(self.shapes):
            if not s1.shape_is_within_log():
                logger.critical(f"Shape {s1.shape_id} falls outside of log {self.log_id}")
                return False

            for s2 in self.shapes[index_1 + 1:]:
                if check_shapes_intersect(s1, s2, self.saw_kerf):
                    logger.critical(f"Shapes {s1.shape_id} and {s2.shape_id} intersect in log {self.log_id}!")
                    logger.critical(f"Coordinates are: (({s1.x},{s1.y}), "
                                    f"({s1.x + s1.width} {s1.y + s1.height})),"
                                    f"(({s2.x}, {s2.y}), ({s2.x + s2.width, s2.y + s2.height}))")
                    return False
                else:
                    pass
        return True

    def add_shape(self, shape: Shape) -> None:
        #  logger.debug(f"Adding shape {shape.shape_id} to log {self.log_id}.")
        self.shapes.append(shape)
        self.volume_used += shape.get_volume()
        self.calculate_efficiency()

    def calculate_sawdust_created(self) -> float:
        # First calculate total sawdust
        saw_dust_m_2 = 0
        for shape in self.shapes:
            saw_dust = (2 * shape.width * self.saw_kerf
                        + 2 * shape.height * self.saw_kerf
                        + 4 * (self.saw_kerf ** 2))
            saw_dust_m_2 += saw_dust
        # Calculate the shared sawdust - we consider each combination of shape once, hence we only slice forward
        for index, shape_1 in enumerate(self.shapes):
            for shape_2 in self.shapes[index + 1:]:
                saw_dust_m_2 = saw_dust_m_2 - calculate_sawdust_shared_between_shapes(shape_1, shape_2, self.saw_kerf)
        return saw_dust_m_2

    def remove_shape(self, shape: Shape) -> None:
        try:
            self.shapes.remove(shape)
            self.volume_used -= shape.get_volume()
            self.calculate_efficiency()
        except ValueError as e:
            print(f"Was not able to remove shape {shape.shape_id} from log {self.log_id}."
                  f"Error {e}")

    def check_if_point_in_log(self, x: float, y: float) -> bool:
        if x < 0 or x > self.diameter:
            return False
        elif y < 0 or y > self.diameter:
            return False
        x_min, x_max = self.calculate_edge_positions_on_circle(y)
        y_min, y_max = self.calculate_edge_positions_on_circle(x)

        if y_min <= y <= y_max and x_min <= x < x_max:
            return True
        else:
            return False

    def find_closest_point_on_edge(self, x: float, y: float) -> tuple:
        r = self.diameter / 2
        v_x = x - r
        v_y = y - r
        mag_v = math.sqrt(v_x ** 2 + v_y ** 2)
        x_edge = r + v_x / mag_v * r
        y_edge = r + v_y / mag_v * r
        return x_edge, y_edge

    def find_shapes_closest_to_shape(self, c_shape: Shape, orientation: str) -> float:
        """
        :param c_shape: central shape (shape of which we consider the surrounding shapes)
        :param orientation: left, right, up, down
        :return:
        """
        other_shapes = [s for s in self.shapes if s.shape_id != c_shape.shape_id]
        if orientation == "left":
            # Set log boundaries for the shape
            min_space_bot, _ = c_shape.log.calculate_edge_positions_on_circle(c_shape.y)
            min_space_top, _ = c_shape.log.calculate_edge_positions_on_circle((c_shape.y + c_shape.height))
            min_space = c_shape.x - max(min_space_bot, min_space_top)
            other_shapes = [s for s in other_shapes if s.x + s.width + self.saw_kerf
                            <= c_shape.x + constants.error_margin]
            # Check if shapes are on the same height, and whether the shape is on the left (direction of orientation)
            for shape in other_shapes:
                if not (shape.y + shape.height + self.saw_kerf <= c_shape.y or
                        shape.y >= c_shape.y + c_shape.height + self.saw_kerf):
                    if c_shape.x - (shape.x + shape.width + self.saw_kerf) < min_space:
                        min_space = c_shape.x - (shape.x + shape.width + self.saw_kerf)
                        if min_space < -constants.error_margin:
                            logger.error(f"Min space is {min_space} with shape {shape.shape_id}: {shape.x},{shape.y}, "
                                         f"cshape {c_shape.shape_id}:{c_shape.x}, {c_shape.y}")
                            raise ValueError
            # Check Log Boundaries
            min_x_left_top, _ = self.calculate_edge_positions_on_circle(c_shape.y + c_shape.height)
            min_x_left_bot, _ = self.calculate_edge_positions_on_circle(c_shape.y)
            minimum_x_left = max(min_x_left_top, min_x_left_bot)
            if c_shape.x - minimum_x_left < min_space:
                min_space = c_shape.x - minimum_x_left

        elif orientation == "right":
            _, max_space_bot = c_shape.log.calculate_edge_positions_on_circle(c_shape.y)
            _, max_space_top = c_shape.log.calculate_edge_positions_on_circle((c_shape.y + c_shape.height))
            min_space = min(max_space_bot, max_space_top) - (c_shape.x + c_shape.width)
            other_shapes = [s for s in other_shapes if s.x + constants.error_margin >=
                            c_shape.x + c_shape.width + self.saw_kerf]
            for shape in other_shapes:
                if not (shape.y + shape.height + self.saw_kerf <= c_shape.y or
                        shape.y >= c_shape.y + c_shape.height + self.saw_kerf):
                    if shape.x - (c_shape.x + c_shape.width + self.saw_kerf) < min_space:
                        min_space = shape.x - (c_shape.x + c_shape.width + self.saw_kerf)
                        if min_space < -constants.error_margin:
                            logger.error(f"Min space is {min_space} with shape {shape.shape_id}: {shape.x},{shape.y}, "
                                         f"cshape {c_shape.shape_id}:{c_shape.x}, {c_shape.y}")
                            raise ValueError
            # Check Log Boundaries
            _, max_x_right_top = self.calculate_edge_positions_on_circle(c_shape.y + c_shape.height)
            _, max_x_right_bot = self.calculate_edge_positions_on_circle(c_shape.y)
            maximum_x_right = min(max_x_right_top, max_x_right_bot)
            if maximum_x_right - (c_shape.x + c_shape.width) < min_space:
                min_space = maximum_x_right - c_shape.x

        elif orientation == "up":
            _, max_space_left = c_shape.log.calculate_edge_positions_on_circle(c_shape.x)
            _, max_space_right = c_shape.log.calculate_edge_positions_on_circle((c_shape.x + c_shape.width))
            min_space = min(max_space_left, max_space_right) - (c_shape.y + c_shape.height)
            other_shapes = [s for s in other_shapes if s.y + constants.error_margin >=
                            c_shape.y + c_shape.height + self.saw_kerf]
            for shape in other_shapes:
                if not (shape.x + shape.width + self.saw_kerf <= c_shape.x or
                        shape.x >= c_shape.x + c_shape.width + self.saw_kerf):
                    if shape.y - (c_shape.y + c_shape.height + self.saw_kerf) < min_space:
                        min_space = shape.y - (c_shape.y + c_shape.height + self.saw_kerf)
                        if min_space < -constants.error_margin:
                            logger.error(f"Min space is {min_space} with shape {shape.shape_id}: {shape.x},{shape.y}, "
                                         f"cshape {c_shape.shape_id}:{c_shape.x}, {c_shape.y}")
                            raise ValueError
            # Check Log Boundaries
            _, max_y_top_left = self.calculate_edge_positions_on_circle(c_shape.x)
            _, max_y_top_right = self.calculate_edge_positions_on_circle(c_shape.x + c_shape.width)
            maximum_y_top = min(max_y_top_left, max_y_top_right)
            if maximum_y_top - (c_shape.y + c_shape.height) < min_space:
                min_space = maximum_y_top - (c_shape.y + c_shape.height)
                if min_space < 0:
                    raise ValueError

        elif orientation == "down":
            min_space_left, _ = c_shape.log.calculate_edge_positions_on_circle(c_shape.x)
            min_space_right, _ = c_shape.log.calculate_edge_positions_on_circle((c_shape.x + c_shape.width))
            min_space = c_shape.y - max(min_space_left, min_space_right)
            other_shapes = [s for s in other_shapes if s.y + s.height + self.saw_kerf <=
                            c_shape.y + constants.error_margin]
            for shape in other_shapes:
                if not (shape.x + shape.width + self.saw_kerf <= c_shape.x or
                        shape.x >= c_shape.x + c_shape.width + self.saw_kerf):
                    if c_shape.y - (shape.y + shape.height + self.saw_kerf) < min_space:
                        min_space = c_shape.y - (shape.y + shape.height + self.saw_kerf)
                        if min_space < -constants.error_margin:
                            logger.error(f"Min space is {min_space} with shape {shape.shape_id}: {shape.x},{shape.y}, "
                                         f"cshape {c_shape.shape_id}:{c_shape.x}, {c_shape.y}")
                            raise ValueError
            # Check Log Boundaries
            min_y_bot_left, _ = self.calculate_edge_positions_on_circle(c_shape.x)
            min_y_bot_right, _ = self.calculate_edge_positions_on_circle(c_shape.x + c_shape.width)
            minimum_y_bot = max(min_y_bot_left, min_y_bot_right)
            if c_shape.y - minimum_y_bot < min_space:
                min_space = c_shape.y - minimum_y_bot

        else:
            logger.error(f"Unknown Orientation {orientation}")
            raise NotImplementedError(f"No orientation {orientation}")
        return min_space

    def find_distance_to_closest_shape_from_point(self, x: float, y: float, orientation: str) -> float:
        """
        Locates closest shapes or log boundary in a certain direction
        Returns distance to **ACTUAL SHAPE**, not the saw kerf
        :param x:
        :param y:
        :param orientation: left, right, up, down
        :return:
        """
        for shape in self.shapes:
            if shape.check_if_point_in_shape(x, y):
                return 0

        if orientation == "left":
            # Set log boundaries for the shape
            min_space, _ = self.calculate_edge_positions_on_circle(y)
            min_space = x - min_space
            other_shapes = [s for s in self.shapes if s.x + s.width + self.saw_kerf <= x + constants.error_margin]
            # Check if shapes are on the same height, and whether the shape is on the left (direction of orientation)
            for shape in other_shapes:
                if not (shape.y + shape.height + self.saw_kerf <= y or shape.y >= y):
                    if x - (shape.x + shape.width + self.saw_kerf) < min_space:
                        min_space = x - (shape.x + shape.width + self.saw_kerf)
                        if min_space < -constants.error_margin:
                            raise ValueError
            # Check Log Boundaries
            minimum_x_left, _ = self.calculate_edge_positions_on_circle(y)
            if x - minimum_x_left < min_space:
                min_space = x - minimum_x_left

        elif orientation == "right":
            _, max_space = self.calculate_edge_positions_on_circle(y)
            min_space = max_space - x
            other_shapes = [s for s in self.shapes if s.x + constants.error_margin >= x]
            for shape in other_shapes:
                if not (shape.y + shape.height + self.saw_kerf <= y or
                        shape.y >= y):
                    if shape.x - x < min_space:
                        min_space = shape.x - x
                        if min_space < -constants.error_margin:
                            raise ValueError
            # Check Log Boundaries
            _, maximum_x_right = self.calculate_edge_positions_on_circle(y)
            if maximum_x_right - x < min_space:
                min_space = maximum_x_right - x

        elif orientation == "up":
            _, max_space = self.calculate_edge_positions_on_circle(x)
            min_space = max_space - y
            other_shapes = [s for s in self.shapes if s.y + constants.error_margin >= y]
            for shape in other_shapes:
                if not shape.x + shape.width + self.saw_kerf <= x or shape.x >= x:
                    if shape.y - y < min_space:
                        min_space = shape.y - y
                        if min_space < -constants.error_margin:
                            raise ValueError
            # Check Log Boundaries
            _, maximum_y_top = self.calculate_edge_positions_on_circle(x)
            if maximum_y_top - y < min_space:
                min_space = maximum_y_top - y
                if min_space < 0:
                    raise ValueError

        elif orientation == "down":
            min_space, _ = self.calculate_edge_positions_on_circle(x)
            min_space = y - min_space
            other_shapes = [s for s in self.shapes if s.y + s.height + self.saw_kerf <=
                            y + constants.error_margin]
            for shape in other_shapes:
                if not shape.x + shape.width + self.saw_kerf <= x or shape.x >= x:
                    if y - (shape.y + shape.height + self.saw_kerf) < min_space:
                        min_space = y - (shape.y + shape.height + self.saw_kerf)
                        if min_space < -constants.error_margin:
                            raise ValueError
            # Check Log Boundaries
            minimum_y_bot, _ = self.calculate_edge_positions_on_circle(x)
            if y - minimum_y_bot < min_space:
                min_space = y - minimum_y_bot

        else:
            logger.error(f"Unknown Orientation {orientation}")
            raise NotImplementedError(f"No orientation {orientation}")
        return min_space


def check_shapes_intersect(shape_a: Shape, shape_b: Shape, sk: float) -> bool:
    a_x_1 = shape_a.x
    a_x_2 = shape_a.x + shape_a.width
    a_y_1 = shape_a.y
    a_y_2 = shape_a.y + shape_a.height

    b_x_1 = shape_b.x
    b_x_2 = shape_b.x + shape_b.width
    b_y_1 = shape_b.y
    b_y_2 = shape_b.y + shape_b.height

    if a_x_1 - sk + constants.error_margin <= b_x_2 \
            and a_x_2 + sk >= b_x_1 + constants.error_margin \
            and a_y_1 - sk + constants.error_margin <= b_y_2 \
            and a_y_2 + sk >= b_y_1 + constants.error_margin:
        return True
    else:
        return False


def calculate_sawdust_shared_between_shapes(shape_a, shape_b, saw_kerf=None) -> float:
    # Check if shapes are within saw kerf reach of each other
    if shape_a.x - saw_kerf <= shape_b.x + shape_b.width + saw_kerf \
            and shape_a.x + shape_a.width + saw_kerf >= shape_b.x - saw_kerf \
            and shape_a.y - saw_kerf <= shape_b.y + shape_b.height + saw_kerf \
            and shape_a.y + shape_a.height + saw_kerf >= shape_b.y - saw_kerf:
        if 0 < shape_a.x - (shape_b.x + shape_b.width) <= 2 * saw_kerf:
            # Shape b is to left of shape a
            y_min = max(shape_a.y - saw_kerf, shape_b.y - saw_kerf)
            y_max = min(shape_a.y + shape_a.height + saw_kerf, shape_b.y + shape_b.height + saw_kerf)
            # The shared sawdust is the overlap in sawkerf, times the length of the overlap
            return (2 * saw_kerf - (shape_a.x - (shape_b.x + shape_b.width))) * (y_max - y_min)
        elif 0 < shape_b.x - (shape_a.x + shape_a.width) <= 2 * saw_kerf:
            # Shape b is right of shape a
            y_min = max(shape_a.y - saw_kerf, shape_b.y - saw_kerf)
            y_max = min(shape_a.y + shape_a.height + saw_kerf, shape_b.y + shape_b.height + saw_kerf)
            # The shared sawdust is the overlap in sawkerf, times the length of the overlap
            return (2 * saw_kerf - (shape_b.x - (shape_a.x + shape_a.width))) * (y_max - y_min)
        elif 0 < shape_a.y - (shape_b.y + shape_b.height) <= 2 * saw_kerf:
            # Shape b is below shape a
            x_min = max(shape_a.x - saw_kerf, shape_b.x - saw_kerf)
            x_max = min(shape_a.x + shape_a.width + saw_kerf, shape_b.x + shape_b.width + saw_kerf)
            # The shared sawdust is the overlap in sawkerf, times the length of the overlap
            return (2 * saw_kerf - (shape_a.y - (shape_b.y + shape_b.height))) * (x_max - x_min)
        elif 0 < shape_a.y + shape_a.height - shape_b.y <= 2 * saw_kerf:
            # Shape b is above shape a
            x_min = max(shape_a.x - saw_kerf, shape_b.x - saw_kerf)
            x_max = min(shape_a.x + shape_a.width + saw_kerf, shape_b.x + shape_b.width + saw_kerf)
            # The shared sawdust is the overlap in sawkerf, times the length of the overlap
            return (2 * saw_kerf - (shape_a.y + shape_a.height - shape_b.y)) * (x_max - x_min)
        else:
            # TODO: Check sawdust calculation for only corners overlapping
            return saw_kerf ** 2
    else:
        return 0


def select_random_shapes_from_log(log: Log, count: int = 1) -> Shape or list:
    """
    Returns a random shape from a log.
    :param log:
    :param count:
    :return:
    """
    probabilities = []
    total_distance = sum(
        [math.sqrt((s.width - log.diameter) ** 2 + (s.height - log.diameter) ** 2) for s in log.shapes])

    for shape in log.shapes:
        probabilities.append(math.sqrt((shape.width - log.diameter) ** 2 +
                                       (shape.height - log.diameter) ** 2) / total_distance)
    if count == 1:
        return random.choices(log.shapes, weights=probabilities)[0]
    else:
        return np.random.choice(log.shapes, p=probabilities, replace=False)
