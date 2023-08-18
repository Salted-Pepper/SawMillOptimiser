import ALNS_tools
from logs import Log
from shapes import ShapeType
import ALNS
import time
import random
import pandas as pd

import tkinter as tk

"""
default measurement: millimeters
default dimensionality: width x height
"""

# TODO: Fix Greedy place in case no block fits (now crashes on no max arg in empty list)


def attempt_run_ALNS(list_of_logs: list, list_of_shape_types: list) -> tuple:

    # TODO: Implement parameter checks here
    # TODO: Update all shapes/log values
    # TODO: Pop error if violated

    solution_quality_df, method_df = apply_ALNS(list_of_logs, list_of_shape_types)

    return solution_quality_df, method_df


def apply_ALNS(list_of_logs: list, list_of_shape_types: list) -> tuple:
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

    ALNS.greedy_place(all_shapes=[],
                      logs=list_of_logs,
                      shape_types=list_of_shape_types)

    solution_quality_df, method_df = ALNS.run_ALNS(logs=list_of_logs, shape_types=list_of_shape_types)

    for log in list_of_logs:
        log.show_plot()
        log.save_log_plot()

    ALNS_tools.check_feasibility(list_of_logs=list_of_logs)

    ALNS_tools.plot_efficiency_data(logs=list_of_logs, df=solution_quality_df)
    ALNS_tools.plot_method_data(method_df)

    return solution_quality_df, method_df


def gui_add_input_log(frame):
    global logs
    log = Log()
    logs.append(log)

    log.label = tk.Label(frame, text=f"Log {log.log_id}")
    log.diameter_input = tk.Entry(frame, width=40)
    log.remove_button = tk.Button(frame, text="Delete", command=lambda: gui_remove_log(log))

    log.label.grid(row=1 + log.log_id, column=0)
    log.diameter_input.grid(row=1 + log.log_id, column=1)
    log.remove_button.grid(row=1 + log.log_id, column=2)


def gui_add_input_shape(frame, width=None, height=None, colour=None):
    global shape_types
    shape = ShapeType()
    shape_types.append(shape)

    shape.label = tk.Label(frame, text=f"{shape.type_id}", width=10)
    shape.width_input = tk.Entry(frame, width=40)
    shape.height_input = tk.Entry(frame, width=40)
    shape.colour_input = tk.Entry(frame, width=40)
    if width is not None and height is not None and colour is not None:
        shape.width_input.insert(0, width)
        shape.height_input.insert(0, height)
        shape.colour_input.insert(0, colour)

    shape.remove_button = tk.Button(frame, text="Delete", command=lambda: gui_remove_shape(shape))

    shape.label.grid(row=2 + shape.type_id, column=0)
    shape.width_input.grid(row=2 + shape.type_id, column=1)
    shape.height_input.grid(row=2 + shape.type_id, column=2)


def gui_remove_log(log):
    global logs
    logs.remove(log)
    log.remove_labels()


def gui_remove_shape(shape):
    global shape_types
    shape_types.remove(shape)
    shape.remove_labels()


logs = []
shape_types = []

root = tk.Tk()
root.title("Sawmill Optimiser")

if __name__ == '__main__':
    """
    Import Shape Data
    """
    df_shapes = pd.read_excel("ShapeData.xlsx")
    """
    Create User Interface for inputs
    """
    title_label = tk.Label(root, text="Sawmill Optimiser")
    title_label.grid(row=0, column=0, columnspan=3)

    log_frame = tk.Frame(root)
    input_log_title = tk.Label(log_frame, text="Input Log Diameters")
    input_log_title.grid(row=0, column=0, columnspan=2)

    add_log_button = tk.Button(log_frame, text="Add Log", padx=10, command=lambda: gui_add_input_log(log_frame))
    add_log_button.grid(row=0, column=2)
    log_frame.grid(row=1, column=0, columnspan=3)

    shape_frame = tk.Frame(root)

    # Add Standard (Listed) Shape Types
    shape_types = []

    for index, row in df_shapes.iterrows():
        gui_add_input_shape(shape_frame, width=row['w'], height=row['h'], colour=row['colour'])

    input_shapes_title = tk.Label(shape_frame, text="Input Shape Sizes")
    input_shapes_title.grid(row=0, column=0, columnspan=2)
    add_shape_button = tk.Button(shape_frame, text="Add Shape", padx=10,
                                 command=lambda: gui_add_input_shape(shape_frame))

    add_shape_button.grid(row=0, column=3)
    shape_id_label = tk.Label(shape_frame, text="Shape ID")
    shape_width_label = tk.Label(shape_frame, text="Width")
    shape_height_label = tk.Label(shape_frame, text="Height")

    shape_frame.grid(row=2, column=0, columnspan=3)
    shape_id_label.grid(row=1, column=0)
    shape_width_label.grid(row=1, column=1)
    shape_height_label.grid(row=1, column=2)

    start_algorithm_button = tk.Button(root, text="Start Optimising",
                                       command=lambda: attempt_run_ALNS(logs, shape_types))

    close_button = tk.Button(root, text="Close Program", command=root.quit)

    root.mainloop()

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
    logs.append(Log(random.randint(300, 900)))
    logs.append(Log(random.randint(300, 900)))
    logs.append(Log(random.randint(300, 900)))
    logs.append(Log(random.randint(300, 900)))
    logs.append(Log(random.randint(300, 900)))
    logs.append(Log(random.randint(300, 900)))



    t_0 = time.perf_counter()
    solution_data, method_data = apply_ALNS(logs, shape_types)
    t_1 = time.perf_counter()

    print(f"Completed Optimisation Procedure in {(t_1 - t_0) / 60: 0.2f} Minutes!")
