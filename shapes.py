import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

import constants

shape_id = 0
type_id = 0


class ShapeType:
    def __init__(self, width: float, height: float, demand: int):
        global type_id
        """
        :param width: General width of shape
        :param height: General height of shape
        :param demand: d_i, minimal number of items required of this shapetype
        """
        self.type_id = type_id
        type_id += 1
        self.width = width
        self.height = height
        self.demand = demand


class Shape:
    def __init__(self, shape_type: ShapeType, width: float, height: float, x=None, y=None, colour=None):
        global shape_id
        """
        :param width:
        :param height:
        :param x: x coordinate of bottom left corner of figure
        :param y: y coordinate of bottom left corner of figure
        """
        self.id = shape_id
        self.type = shape_type
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

    def shape_is_within_log(self) -> bool:
        if self.log is None:
            print("Rectangle not assigned to a log")
            return True
        """
        Checks if the corner positions are contained in the log
        """
        y_min_left, y_plus_left = self.log.calculate_edge_positions_on_circle(self.x)
        x_min_top, x_plus_top = self.log.calculate_edge_positions_on_circle(self.y + self.height)

        y_min_right, y_plus_right = self.log.calculate_edge_positions_on_circle(self.x + self.width)
        x_min_bot, x_plus_bot = self.log.calculate_edge_positions_on_circle(self.y)

        if self.x >= x_min_bot and \
                self.x >= x_min_top and \
                self.x + self.width <= x_plus_top and \
                self.x + self.width <= x_plus_bot and \
                self.y >= y_min_left and \
                self.y >= y_min_right and \
                self.y + self.height <= y_plus_left and \
                self.y + self.height <= y_plus_right:
            return True
        else:
            return False



