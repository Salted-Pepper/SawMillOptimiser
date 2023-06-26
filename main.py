import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from logs import Log

from shapes import Shape

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


def check_if_logs_feasible(list_of_logs) -> bool:
    for log in list_of_logs:
        if not log.check_if_feasible():
            return False
    return True


if __name__ == '__main__':
    diameter = 450

    logs = []
    shapes = []

    if check_if_logs_feasible(logs):
        print("No conflicting logs found!")
    else:
        print("Conflicting shape placement!")
