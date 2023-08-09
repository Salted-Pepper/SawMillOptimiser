import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import logging
import datetime
import constants

shape_id = 0
type_id = 0

date = datetime.date.today()
logging.basicConfig(level=logging.DEBUG, filename='saw_mill_app_' + str(date) + '.log',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt="%H:%M:%S")
logger = logging.getLogger("Shapes")
logger.setLevel(logging.DEBUG)


class ShapeType:
    def __init__(self, width: float, height: float, ratio: float, demand: int, colour: str, duplicate_id: int = None):
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
        self.ratio = ratio
        self.demand = demand
        self.colour = colour
        self.duplicate_id = duplicate_id


class Shape:
    def __init__(self, shape_type: ShapeType, x=None, y=None, copy_id: int = None):
        global shape_id
        """
        :param width:
        :param height:
        :param x: x coordinate of bottom left corner of figure
        :param y: y coordinate of bottom left corner of figure
        :param copy_id: Allows you to set the id of a shape to allow consistency across duplicated logs
        """
        if copy_id is None:
            self.shape_id = shape_id
            shape_id += 1
        else:
            self.shape_id = copy_id
        self.type = shape_type
        self.width = shape_type.width
        self.height = shape_type.height
        self.ratio = shape_type.ratio
        self.x = x
        self.y = y
        self.log = None
        self.colour = shape_type.colour
        self.placed = False
        self.rect = None
        self.rect_kerf = None
        self.text = None

        #  logger.debug(f"Created Shape {self.shape_id} at ({self.x}, {self.y})")

    def __str__(self):
        if self.x is not None and self.y is not None:
            return (f"Shape {self.shape_id} - at ({self.x}, {self.y}) in log {self.log.log_id}, "
                    f"with w/h: {self.width}, {self.height}")
        else:
            return f"Shape {self.shape_id} without Log or location"

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

    def add_rect_to_plot(self) -> list or None:
        if self.log is None:
            print("Piece not attributed to log, not able to show figure")
            return None

        if self.x is None:
            print("X coordinate not set.")
            return
        if self.y is None:
            print("Y coordinate not set.")
            return

        if self.colour is not None:
            self.rect = mpatches.Rectangle((self.x, self.y),
                                           self.width, self.height,
                                           facecolor=(mcolors.to_rgb(self.colour) + (0.5,)))
        else:
            self.rect = mpatches.Rectangle((self.x, self.y),
                                           self.width, self.height,
                                           facecolor=(0, 1, 0, 0.5))

        self.rect_kerf = mpatches.Rectangle((self.x - constants.saw_kerf,
                                             self.y - constants.saw_kerf),
                                            self.width + 2 * constants.saw_kerf,
                                            self.height + 2 * constants.saw_kerf,
                                            color="black")
        self.log.ax.add_patch(self.rect_kerf)
        self.log.ax.add_patch(self.rect)

        if self.width > self.height:
            self.text = self.log.ax.text(self.x + constants.rect_text_margin * self.width,
                                         self.y + constants.rect_text_margin * self.height,
                                         r"$\bf{{{i}}}$".format(i=self.shape_id) + f":{self.width}x{self.height}",
                                         color="white", fontsize="small")
        else:
            self.text = self.log.ax.text(self.x + constants.rect_text_margin * self.width,
                                         self.y + constants.rect_text_margin * self.height,
                                         r"$\bf{{{i}}}$".format(i=self.shape_id) + f":\n{self.width}x \n {self.height}",
                                         color="white", fontsize="small")
        return [self.rect, self.rect_kerf, self.text]

    def get_volume(self) -> float:
        return self.width * self.height

    def assign_to_log(self, log):
        self.log = log
        self.log.add_shape(self)

    def remove_from_log(self):
        if self.log is None:
            raise ValueError(f"No log assigned to shape {self.shape_id}")
        logger.debug(f"Removing shape {self.shape_id} from log {self.log.log_id}")
        self.log.remove_shape(self)
        self.log = None
        self.x = None
        self.y = None

    def check_if_point_in_shape(self, x: float, y: float):
        if (self.x - constants.saw_kerf <= x <= self.x + self.width + constants.saw_kerf
                and self.y - constants.saw_kerf <= y <= self.y + self.height + constants.saw_kerf):
            return True
        else:
            return False

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

        if self.x + constants.error_margin >= x_min_bot and \
                self.x + constants.error_margin >= x_min_top and \
                self.x + self.width <= x_plus_top + constants.error_margin and \
                self.x + self.width <= x_plus_bot + constants.error_margin and \
                self.y + constants.error_margin >= y_min_left and \
                self.y + constants.error_margin >= y_min_right and \
                self.y + self.height <= y_plus_left + constants.error_margin and \
                self.y + self.height <= y_plus_right + constants.error_margin:
            return True
        else:
            return False


def sort_shapes_on_size(shapes):
    """
    :param shapes: List of Shapes
    :return: Sorted List of Shapes

    This function sorts the set of produced shapes by size, prioritizing height and then width.
    """
    sorted_list = [shapes[0]]
    for shape in shapes[1:]:
        for index, s_shape in enumerate(sorted_list.copy()):
            if shape.height < s_shape.height:
                sorted_list.insert(index, shape)
                continue
            elif shape.height == s_shape.height and shape.width < s_shape.width:
                sorted_list.insert(index, shape)
                continue
    sorted_list.reverse()
    return sorted_list
