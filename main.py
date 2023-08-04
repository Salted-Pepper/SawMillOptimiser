from logs import Log
from shapes import Shape, ShapeType
import ALNS

import pandas as pd

"""
default measurement: millimeters
default dimensionality: width x height
"""


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
        print("Incorrect shape placement!")
        return False


if __name__ == '__main__':

    logs = []
    shapes = []

    """
    Create Logs (to be done in UI)
    """
    # logs.append(Log(450))
    # logs.append(Log(500))
    # logs.append(Log(350))
    # logs.append(Log(460))
    # logs.append(Log(470))
    logs.append(Log(560))
    # logs.append(Log(580))
    # logs.append(Log(390))
    # logs.append(Log(608))
    # logs.append(Log(503))
    # logs.append(Log(487))
    # logs.append(Log(640))

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
    transposed_shapes = []

    for shape in shape_types:
        if shape.width != shape.height:
            transposed_shapes.append(ShapeType(width=shape.height,
                                               height=shape.width,
                                               ratio=shape.width / shape.height,
                                               demand=shape.demand,
                                               colour=shape.colour,
                                               duplicate_id=shape.type_id))

    shape_types.extend(transposed_shapes)

    """
    Create Shapes Based on Demand
    """
    ALNS.greedy_place(all_shapes=shapes,
                      logs=logs,
                      shape_types=shape_types)

    solution_quality_df = ALNS.run_ALNS(logs=logs, shape_types=shape_types)

    for log in logs:
        log.update_plot_title()
        log.show_plot()

    check_feasibility(list_of_logs=logs)
