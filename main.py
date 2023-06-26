import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from logs import Log

from shapes import Shape, check_shapes_intersect

"""
default measurement: millimeters
default dimensionality: width x height
"""


def plot_circle(fig, ax, diam, ) -> plt.figure:
    circle = plt.Circle((diam * 1.05 / 2, diam * 1.05 / 2), diam / 2, color='saddlebrown', fill=False)
    ax.add_patch(circle)
    ax.set_xlim(0, 1.1*diam)
    ax.set_ylim(0, 1.1*diam)
    return fig, ax


def check_if_feasible(list_of_shapes):
    for index_1, s1 in enumerate(list_of_shapes):

        if not s1.shape_is_within_log():
            return False

        for s2 in list_of_shapes[index_1 + 1:]:
            if check_shapes_intersect(s1, s2):
                print(f"Shapes {s1.id} and {s2.id} intersect!")
                print(f"Coordinates are: (({s1.x},{s1.y}), "
                      f"({s1.x + s1.width} {s1.y + s1.height})),"
                      f"(({s2.x}, {s2.y}), ({s2.x + s2.width, s2.y + s2.height}))")
                return False
            else:
                print(f"Shapes {s1.id} and {s2.id} do not intersect")
    return True


if __name__ == '__main__':
    diameter = 450

    logs = []
    shapes = []

    if check_if_feasible(shapes):
        print("No conflicting rectangles found!")
    else:
        print("Conflicting shape placement!")
