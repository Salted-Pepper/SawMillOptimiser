import ALNS_tools
from logs import Log
from shapes import ShapeType
import ALNS
import time

import pandas as pd

"""
default measurement: millimeters
default dimensionality: width x height
"""


def apply_ALNS(list_of_logs: list, list_of_shape_types: list):
    ALNS.greedy_place(all_shapes=shapes,
                      logs=list_of_logs,
                      shape_types=list_of_shape_types)

    solution_quality_df = ALNS.run_ALNS(logs=list_of_logs, shape_types=list_of_shape_types)

    for log in list_of_logs:
        log.show_plot()
        log.save_log_plot()

    ALNS_tools.check_feasibility(list_of_logs=list_of_logs)

    ALNS_tools.plot_iteration_data(logs=list_of_logs, df=solution_quality_df)


if __name__ == '__main__':

    logs = []
    shapes = []

    """
    Create Logs (to be done in UI)
    """
    logs.append(Log(450))
    logs.append(Log(500))
    logs.append(Log(350))
    logs.append(Log(460))
    logs.append(Log(470))
    logs.append(Log(560))
    logs.append(Log(580))
    logs.append(Log(390))
    logs.append(Log(608))
    logs.append(Log(503))
    logs.append(Log(487))
    logs.append(Log(640))
    logs.append(Log(750))
    logs.append(Log(835))

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

    t_0 = time.perf_counter()
    apply_ALNS(logs, shape_types)
    t_1 = time.perf_counter()

    print(f"Completed Optimisation Procedure in {(t_1 - t_0) / 60: 0.2f} Minutes!")
