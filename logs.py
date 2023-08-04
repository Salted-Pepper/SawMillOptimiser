import logging

import constants
from shapes import Shape

import datetime
import math
import random
import numpy as np
import matplotlib.pyplot as plt

date = datetime.date.today()
logging.basicConfig(level=logging.DEBUG, filename='saw_mill_app_' + str(date) + '.log',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt="%H:%M:%S")
logger = logging.getLogger("Logs")
logger.setLevel(logging.DEBUG)

log_id = 0


class Log:
    def __init__(self, diameter: float) -> None:
        global log_id

        # Log data
        self.log_id = log_id
        log_id += 1
        self.diameter = diameter

        # Efficiency Measures
        self.recovery_rate = None
        self.volume = math.pi * (diameter / 2) ** 2
        self.volume_used = 0
        self.saw_dust = 0
        self.efficiency = 0
        self.score = -math.inf

        # Plotting Variables
        self.fig = None
        self.ax = None
        self.shapes = []
        self.patches = []
        self.plot_log()

    def plot_log(self) -> None:
        fig = plt.figure(figsize=(9, 9))
        ax = fig.add_subplot(111)

        ax.set_xlim(0, 1.1 * self.diameter)
        ax.set_ylim(0, 1.1 * self.diameter)

        self.fig = fig
        self.ax = ax

    def update_plot(self) -> None:
        for patch in self.patches:
            patch.remove()
        for shape in self.shapes:
            self.patches.extend(shape.add_rect_to_plot())
        circle = plt.Circle((self.diameter / 2, self.diameter / 2), self.diameter / 2,
                            color='saddlebrown', fill=False)
        self.ax.add_patch(circle)
        self.ax.set_title(f"id: {self.log_id}, "
                          r"$d_i$:" + f"{self.diameter}, "
                                      r"$\phi_i$:" + f"{self.calculate_efficiency():.2f}, "
                                                     r"$\alpha_i$:" + f"{self.calculate_sawdust_created():.2f}")

    def calculate_efficiency(self) -> float:
        self.efficiency = self.volume_used / self.volume
        return self.efficiency

    def return_plot(self) -> tuple:
        return self.fig, self.ax

    def show_plot(self) -> None:
        global date
        self.update_plot()
        self.fig.savefig(f"plots/log_{self.log_id}_{date.strftime('%d_%m_%Y_%H_%M_%S')}.png")
        self.fig.show()

    def calculate_edge_positions_on_circle(self, z: float) -> tuple:
        r = self.diameter / 2
        try:
            z_min = r - math.sqrt(r ** 2 - (z - r) ** 2)
            z_plus = r + math.sqrt(r ** 2 - (z - r) ** 2)
        except ValueError:
            raise ValueError(f"Math domain error for {z}")
        return z_min, z_plus

    def check_if_feasible(self) -> bool:
        for index_1, s1 in enumerate(self.shapes):
            if not s1.shape_is_within_log():
                print(f"Shape {s1.shape_id} falls outside of log {self.log_id}")
                return False

            for s2 in self.shapes[index_1 + 1:]:
                if check_shapes_intersect(s1, s2):
                    print(f"Shapes {s1.shape_id} and {s2.shape_id} intersect!")
                    print(f"Coordinates are: (({s1.x},{s1.y}), "
                          f"({s1.x + s1.width} {s1.y + s1.height})),"
                          f"(({s2.x}, {s2.y}), ({s2.x + s2.width, s2.y + s2.height}))")
                    return False
                else:
                    print(f"Shapes {s1.shape_id} and {s2.shape_id} do not intersect")
        return True

    def add_shape(self, shape: Shape) -> None:
        logger.debug(f"Adding shape {shape.shape_id} to log {self.log_id}.")
        self.shapes.append(shape)
        self.volume_used += shape.get_volume()
        self.calculate_efficiency()

    def calculate_sawdust_created(self) -> float:
        # TODO: Create function to calculate sawdust (circumference - shared circumference)
        return -1 / self.volume

    def remove_shape(self, shape: Shape) -> None:
        logger.debug(f"Removing shape {shape.shape_id} from log {self.log_id}.")
        try:
            self.shapes.remove(shape)
            self.volume_used -= shape.get_volume()
            self.calculate_efficiency()
        except ValueError as e:
            print(f"Was not able to remove shape {shape.shape_id} from log {self.log_id}."
                  f"Error {e}")

    def check_if_point_in_log(self, x: float, y: float) -> bool:
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
            other_shapes = [s for s in other_shapes if s.x + s.width + constants.saw_kerf
                            <= c_shape.x + constants.error_margin]
            # Check if shapes are on the same height, and whether the shape is on the left (direction of orientation)
            for shape in other_shapes:
                if not (shape.y + shape.height + constants.saw_kerf <= c_shape.y or
                        shape.y >= c_shape.y + c_shape.height + constants.saw_kerf):
                    if c_shape.x - (shape.x + shape.width + constants.saw_kerf) < min_space:
                        min_space = c_shape.x - (shape.x + shape.width + constants.saw_kerf)
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
                            c_shape.x + c_shape.width + constants.saw_kerf]
            for shape in other_shapes:
                if not (shape.y + shape.height + constants.saw_kerf <= c_shape.y or
                        shape.y >= c_shape.y + c_shape.height + constants.saw_kerf):
                    if shape.x - (c_shape.x + c_shape.width + constants.saw_kerf) < min_space:
                        min_space = shape.x - (c_shape.x + c_shape.width + constants.saw_kerf)
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
                            c_shape.y + c_shape.height + constants.saw_kerf]
            for shape in other_shapes:
                if not (shape.x + shape.width + constants.saw_kerf <= c_shape.x or
                        shape.x >= c_shape.x + c_shape.width + constants.saw_kerf):
                    if shape.y - (c_shape.y + c_shape.height + constants.saw_kerf) < min_space:
                        min_space = shape.y - (c_shape.y + c_shape.height + constants.saw_kerf)
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
            other_shapes = [s for s in other_shapes if s.y + s.height + constants.saw_kerf <=
                            c_shape.y + constants.error_margin]
            for shape in other_shapes:
                if not (shape.x + shape.width + constants.saw_kerf <= c_shape.x or
                        shape.x >= c_shape.x + c_shape.width + constants.saw_kerf):
                    if c_shape.y - (shape.y + shape.height + constants.saw_kerf) < min_space:
                        min_space = c_shape.y - (shape.y + shape.height + constants.saw_kerf)
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

        if min_space < 0:
            logger.error(f"Found minimum space between pieces of {min_space} for shape at "
                         f"({c_shape.x}, {c_shape.y}) with (w,h)=({c_shape.width},{c_shape.height}) "
                         f"in log {self.log_id}, with orientation {orientation}")
        return min_space


def check_shapes_intersect(shape_a: Shape, shape_b: Shape) -> bool:
    sk = constants.saw_kerf
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
