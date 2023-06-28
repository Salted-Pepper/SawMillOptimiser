import constants
from shapes import Shape

import math
import matplotlib.pyplot as plt

log_id = 0


class Log:
    def __init__(self, diameter: float) -> None:
        global log_id
        self.log_id = log_id
        log_id += 1
        self.diameter = diameter
        self.recovery_rate = None
        self.volume = math.pi * (diameter / 2) ** 2
        self.volume_used = 0
        self.fig = None
        self.ax = None
        self.shapes = []

    def plot_log(self) -> None:
        fig, ax = plt.subplots(figsize=(9, 9))
        circle = plt.Circle((self.diameter * 1.05 / 2, self.diameter * 1.05 / 2), self.diameter / 2,
                            color='saddlebrown', fill=False)
        ax.add_patch(circle)
        ax.set_xlim(0, 1.1 * self.diameter)
        ax.set_ylim(0, 1.1 * self.diameter)
        self.fig = fig
        self.ax = ax

    def return_plot(self) -> tuple:
        return self.fig, self.ax

    def calculate_edge_positions_on_circle(self, x: float) -> tuple:
        r = self.diameter / 2
        y_min = r - math.sqrt(r**2 - (x-r)**2)
        y_plus = r + math.sqrt(r**2 - (x-r)**2)
        return y_min, y_plus

    def check_if_feasible(self) -> bool:
        for index_1, s1 in enumerate(self.shapes):
            if not s1.shape_is_within_log():
                print(f"Shape {s1.id} falls outside of log {self.log_id}")
                return False

            for s2 in self.shapes[index_1 + 1:]:
                if check_shapes_intersect(s1, s2):
                    print(f"Shapes {s1.id} and {s2.id} intersect!")
                    print(f"Coordinates are: (({s1.x},{s1.y}), "
                          f"({s1.x + s1.width} {s1.y + s1.height})),"
                          f"(({s2.x}, {s2.y}), ({s2.x + s2.width, s2.y + s2.height}))")
                    return False
                else:
                    print(f"Shapes {s1.id} and {s2.id} do not intersect")
        return True

    def add_shape(self, shape) -> None:
        self.shapes.append(shape)

    def remove_shape(self, shape) -> None:
        try:
            self.shapes.remove(shape)
        except ValueError:
            print(f"Was not able to remove shape {shape.id} from ")


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

    if a_x_1 - sk <= b_x_2 \
            and a_x_2 + sk >= b_x_1 \
            and a_y_1 - sk <= b_y_2 \
            and a_y_2 + sk >= b_y_1:
        return True
    else:
        return False
