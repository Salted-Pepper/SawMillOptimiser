import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.offsetbox import AnnotationBbox, AuxTransformBox

import constants

shape_id = 0


class Shape:
    def __init__(self, width: float, height: float, x=None, y=None, colour=None):
        global shape_id
        """
        :param width:
        :param height:
        :param x: x coordinate of bottom left corner of figure
        :param y: y coordinate of bottom left corner of figure
        """
        self.id = shape_id
        shape_id += 1
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.log = None
        self.colour = colour
        self.placed = False

    def set_location(self, x=None, y=None) -> None:
        """
        :param x: Updated x Location - remains same if not entered
        :param y: Updated y Location - remains same if not entered
        """
        if x is not None:
            self.x = x
        if y is not None:
            self.y = y

    def rotate_left(self) -> None:
        """
        Rotating the shape left moves the shape to the left of the original (x, y) coordinate
        Only the X position changes.
        """
        if self.x is not None:
            self.x = self.x - self.height
        width = self.width
        self.width = self.height
        self.height = width

    def rotate_right(self) -> None:
        """
        Rotating the shape right moves the shape to the right of the original (x, y) coordinate
        Both x and y stay the same
        :return:
        """
        width = self.width
        self.width = self.height
        self.height = width

    def add_rect_to_plot(self, fig: plt.figure, ax: plt.axes) -> plt.figure:

        if self.colour is not None:
            rect = mpatches.Rectangle((self.x, self.y),
                                      self.width, self.height,
                                      color=self.colour, alpha=0.9)
        else:
            rect = mpatches.Rectangle((self.x, self.y),
                                      self.width, self.height,
                                      alpha=0.9)

        rect_kerf = mpatches.Rectangle((self.x - constants.saw_kerf,
                                        self.y - constants.saw_kerf),
                                       self.width + 2 * constants.saw_kerf,
                                       self.height + 2 * constants.saw_kerf,
                                       color="black")
        ax.add_patch(rect_kerf)
        ax.add_patch(rect)

        ax.text(self.x + constants.rect_text_margin * self.width,
                self.y + constants.rect_text_margin * self.height,
                f"{self.width}x{self.height}",
                color="white")

        return fig, ax

    def assign_to_log(self, log):
        self.log = log

    def remove_from_log(self):
        self.log = None

    def check_if_within_log(self):
        if self.log is None:
            print("Rectangle not assigned to a log")
            return
        diam = self.log.diameter


def check_shapes_intersect(shape_a: Shape, shape_b: Shape):
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

