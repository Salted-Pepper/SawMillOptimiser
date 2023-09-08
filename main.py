import ALNS_tools
import constants
from logs import Log
from shapes import ShapeType
import ALNS
import time
import pandas as pd
import os

import tkinter as tk

"""
default measurement: millimeters
default dimensionality: height x width
"""


def gui_throw_basic_message(title, text):
    global root
    error_window = tk.Toplevel(root)
    error_window.title(title)
    error_window.geometry("300x300")
    tk.Label(error_window, text=text, padx=300, pady=300).pack()


def attempt_run_ALNS(list_of_logs: list, list_of_shape_types: list, temp_input, ite_input) -> tuple | None:
    try:
        temp = int(temp_input.get())
        if temp <= 0:
            raise ValueError
        constants.starting_temperature = temp
    except ValueError:
        gui_throw_basic_message(title="Invalid Temperature", text="Invalid Temperature Provided")
        return

    try:
        iterations = int(ite_input.get())
        if iterations <= 0:
            raise ValueError
        constants.max_iterations = iterations
    except ValueError:
        gui_throw_basic_message(title="Invalid Iteration Number",
                                text="Ensure the number of iterations is a positive integer.")
        return

    if len(list_of_logs) == 0:
        gui_throw_basic_message(title="Invalid Log Input", text="At least 1 Log Input Required")
        return

    if len(list_of_shape_types) == 0:
        gui_throw_basic_message(title="Invalid Shape Input", text="At least 1 Shape Input Required")
        return

    for log in list_of_logs:
        try:
            diameter = float(log.diameter_input.get())
            if diameter <= 0:
                raise ValueError
            log.set_diameter()
        except ValueError:
            gui_throw_basic_message(title="Invalid Log Input",
                                    text=f"Invalid Diameter Entered for log {log.log_id}")
            return

        try:
            sk = float(log.saw_kerf_input.get())
            if sk == 0:
                raise ValueError
            log.set_saw_kerf()
            print(f"Set saw kerf {log.saw_kerf} for log {log.log_id}")
        except ValueError:
            gui_throw_basic_message(title="Invalid Log Input",
                                    text=f"Invalid Saw Kerf Entered for log {log.log_id}")
            return

    for shape in list_of_shape_types:
        try:
            width = float(shape.width_input.get())
            height = float(shape.height_input.get())
            if height <= 0 or width <= 0:
                raise ValueError
            shape.set_properties(width=width, height=height, colour=shape.colour_input.get())
        except ValueError:
            gui_throw_basic_message(title="Invalid Shape Input",
                                    text=f"Entered Illegal Dimensions for Shape {shape.type_id}")
            return

    status_window = tk.Toplevel(root)
    status_window.title("Optimisation in progress...")
    status_window.geometry("500x500")
    progress_label = tk.Label(status_window, text=constants.optimising_text, padx=300, pady=300)
    progress_label.pack()

    root.update()

    t_0 = time.perf_counter()
    solution_quality_df, method_df = apply_ALNS(list_of_logs, list_of_shape_types, progress_label)
    t_1 = time.perf_counter()
    status_window.title("Optimisation Finished!")
    progress_label.config(text=f"Completed Optimisation Procedure in{(t_1 - t_0) / 60: 0.2f} Minutes!")

    return solution_quality_df, method_df


def apply_ALNS(list_of_logs: list, list_of_shape_types: list, progress_label: tk.Label) -> tuple:
    global root
    transposed_shapes = []

    progress_label.config(text=progress_label.cget("text") + " \n Creating Initial Solution...")
    root.update()

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

    progress_label.config(text=progress_label.cget("text") + " \n Established Initial Solution...")
    root.update()

    solution_quality_df, method_df, parameter_df = ALNS.run_ALNS(logs=list_of_logs,
                                                                 shape_types=list_of_shape_types,
                                                                 root=root, progress_label=progress_label)

    ALNS_tools.check_feasibility(list_of_logs=list_of_logs)

    for log in list_of_logs:
        log.show_plot()
        log.save_log_plot()

    ALNS_tools.plot_efficiency_data(logs=list_of_logs, df=solution_quality_df)
    ALNS_tools.plot_method_data(method_df)
    ALNS_tools.plot_parameter_data(parameter_df)

    return solution_quality_df, method_df


def gui_add_input_log(frame):
    global logs
    log = Log()
    logs.append(log)

    log.label = tk.Label(frame, text=f"Log {log.log_id}")
    log.diameter_input = tk.Entry(frame, width=40)
    log.saw_kerf_input = tk.Entry(frame, width=20)
    log.remove_button = tk.Button(frame, text="Delete", command=lambda: gui_remove_log(log))

    log.label.grid(row=2 + log.log_id, column=0)
    log.diameter_input.grid(row=2 + log.log_id, column=1)
    log.saw_kerf_input.grid(row=2 + log.log_id, column=2)
    log.remove_button.grid(row=2 + log.log_id, column=3)


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
    shape.remove_button.grid(row=2 + shape.type_id, column=3)


def gui_remove_log(log):
    global logs
    logs.remove(log)
    log.remove_labels()
    for l in logs:
        if l.log_id > log.log_id:
            l.log_id -= 1
            l.label.config(text=f"Log {l.log_id}")

            l.label.grid(row=2 + log.log_id, column=0)
            l.diameter_input.grid(row=2 + log.log_id, column=1)
            l.saw_kerf_input.grid(row=2 + log.log_id, column=2)
            l.remove_button.grid(row=2 + log.log_id, column=3)


def gui_remove_shape(shape):
    global shape_types
    shape_types.remove(shape)
    shape.remove_labels()
    for s in shape_types:
        if s.type_id > shape.type_id:
            s.type_id -= 1
            s.label.config(text=s.type_id)

            s.label.grid(row=2 + s.type_id, column=0)
            s.height_input.grid(row=2 + s.type_id, column=1)
            s.width_input.grid(row=2 + s.type_id, column=2)
            s.remove_button.grid(row=2 + s.type_id, column=3)


logs = []
shape_types = []

root = tk.Tk()
root.title("Sawmill Optimiser")
root.geometry("1200x900")
root.iconbitmap("saw.ico")

if __name__ == '__main__':
    """
    Import Shape Data
    """
    path = os.getcwd()
    try:
        df_shapes = pd.read_excel(os.path.join(path, "ShapeData.xlsx"))
    except FileNotFoundError:
        df_shapes = pd.DataFrame()
    """
    Create User Interface for inputs
    """
    title_label = tk.Label(root, text="Sawmill Optimiser", font='Helvetica 30 bold')
    title_label.grid(row=0, column=0, columnspan=3)

    """
    Inputs for Log Information
    """
    log_frame = tk.Frame(root)
    input_log_title = tk.Label(log_frame, text="Input Log Information", font='Helvetica 20 bold')
    input_log_title.grid(row=0, column=0, columnspan=3)

    log_id_label = tk.Label(log_frame, text="Log ID")
    log_diameter_label = tk.Label(log_frame, text="Diameter")
    log_saw_kerf_label = tk.Label(log_frame, text="Saw Kerf")
    add_log_button = tk.Button(log_frame, text="Add Log", padx=10, command=lambda: gui_add_input_log(log_frame))

    log_id_label.grid(row=1, column=0)
    log_diameter_label.grid(row=1, column=1)
    log_saw_kerf_label.grid(row=1, column=2)
    add_log_button.grid(row=1, column=3)

    log_frame.grid(row=1, column=0, columnspan=3)

    """
    Add Shapes + Import Standard Information
    """
    shape_frame = tk.Frame(root)

    shape_types = []

    for index, row in df_shapes.iterrows():
        if 'colour' in df_shapes.columns:
            gui_add_input_shape(shape_frame, width=row['w'], height=row['h'], colour=row['colour'])
        else:
            gui_add_input_shape(shape_frame, width=row['w'], height=row['h'])

    input_shapes_title = tk.Label(shape_frame, text="Input Shape Sizes", font='Helvetica 20 bold')
    input_shapes_title.grid(row=0, column=0, columnspan=3)
    shape_id_label = tk.Label(shape_frame, text="Shape ID")
    shape_height_label = tk.Label(shape_frame, text="Height")
    shape_width_label = tk.Label(shape_frame, text="Width")
    add_shape_button = tk.Button(shape_frame, text="Add Shape", padx=10,
                                 command=lambda: gui_add_input_shape(shape_frame))
    shape_id_label.grid(row=1, column=0)
    shape_height_label.grid(row=1, column=1)
    shape_width_label.grid(row=1, column=2)
    add_shape_button.grid(row=1, column=3)
    shape_frame.grid(row=2, column=0, columnspan=3)

    """
    Input ALNS Parameters
    """
    iteration_label = tk.Label(root, text="Max Iterations (Per Log)")
    iteration_input = tk.Entry(root)
    iteration_input.insert(0, constants.max_iterations)

    temperature_label = tk.Label(root, text="Starting Temperature")
    temperature_input = tk.Entry(root)
    temperature_input.insert(0, constants.starting_temperature)

    iteration_label.grid(row=3, column=0)
    iteration_input.grid(row=3, column=1)
    temperature_label.grid(row=3, column=2)
    temperature_input.grid(row=3, column=3)

    """
    Final Buttons
    """
    start_algorithm_button = tk.Button(root, text="Start Optimising",
                                       command=lambda: attempt_run_ALNS(logs, shape_types,
                                                                        temperature_input, iteration_input))

    close_button = tk.Button(root, text="Quit Program", command=root.destroy)

    start_algorithm_button.grid(row=4, column=0)
    close_button.grid(row=4, column=3)

    root.mainloop()
