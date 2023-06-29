import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from logs import Log
from shapes import Shape, ShapeType, sort_shapes_on_size
import ALNS

import pandas as pd

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


def check_feasibility(list_of_logs):
    if check_if_logs_feasible(list_of_logs):
        print("No conflicting logs found!")
        return True
    else:
        print("Conflicting shape placement!")
        return False


if __name__ == '__main__':
    diameter = 450

    logs = []
    shapes = []

    """
    Create Logs
    """
    logs.append(Log(450))
    logs.append(Log(500))

    """
    Import Shape Data
    """
    df_shapes = pd.read_excel("ShapeData.xlsx")

    """
    Create Shape Types
    """
    shape_types = []

    for index, row in df_shapes.iterrows():
        shape_types.append(ShapeType(width=row['w'],
                                     height=row['h'],
                                     ratio=row['ratio'],
                                     demand=row['demand'],
                                     colour=row['colour']
                                     ))

    """
    Create Shapes Based on Demand
    """
    for s_type in shape_types:
        for i in range(s_type.demand):
            shapes.append(Shape(shape_type=s_type,
                                width=s_type.width,
                                height=s_type.height,
                                ratio=s_type.ratio,
                                colour=s_type.colour))

    ALNS.greedy_place(logs=logs,
                      shape_types=shape_types)

    for shape in shapes:
        shape.add_rect_to_plot()

    check_feasibility(list_of_logs=logs)

