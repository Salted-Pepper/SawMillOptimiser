import ALNS_tools
from logs import Log
from shapes import ShapeType
import ALNS
import time
import random

import pandas as pd

"""
default measurement: millimeters
default dimensionality: width x height
"""


def apply_ALNS(list_of_logs: list, list_of_shape_types: list):
    ALNS.greedy_place(all_shapes=shapes,
                      logs=list_of_logs,
                      shape_types=list_of_shape_types)

    solution_quality_df, method_df = ALNS.run_ALNS(logs=list_of_logs, shape_types=list_of_shape_types)

    for log in list_of_logs:
        log.show_plot()
        log.save_log_plot()

    ALNS_tools.check_feasibility(list_of_logs=list_of_logs)

    ALNS_tools.plot_efficiency_data(logs=list_of_logs, df=solution_quality_df)
    ALNS_tools.plot_method_data(method_df)


if __name__ == '__main__':

    logs = []
    shapes = []

    """
    Create Logs (to be done in UI)
    For now random logs to ensure thorough testing of ALNS
    """
    # logs.append(Log(450))
    # logs.append(Log(550))
    # logs.append(Log(600))
    # logs.append(Log(630))
    # logs.append(Log(720))
    # logs.append(Log(random.randint(300, 900)))
    # logs.append(Log(random.randint(300, 900)))
    # logs.append(Log(random.randint(300, 900)))
    # logs.append(Log(random.randint(300, 900)))
    logs.append(Log(random.randint(300, 900)))
    logs.append(Log(random.randint(300, 900)))
    logs.append(Log(random.randint(300, 900)))
    logs.append(Log(random.randint(300, 900)))
    logs.append(Log(random.randint(300, 900)))

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
