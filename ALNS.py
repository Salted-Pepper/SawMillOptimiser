import logging
import numpy as np
import math
from ortools.linear_solver import pywraplp

import ALNS_tools
import constants
from shapes import Shape


def greedy_place(shapes: list, shape_types: list, logs: list) -> None:
    """
    :param shapes: List of Shapes
    :param shape_types: List of Shape Types (Available sizes)
    :param logs: List of Logs
    :return:
    """

    for log in logs:
        """
        First we go over all shapes, we make a rectangle with that size, fill it up with similar pieces,
        and then consider the utilisation rate of that rectangle.
        """
        solutions = []
        print(f"Optimising for log with diameter {log.diameter}")

        for shape in shape_types:

            if shape.height >= log.diameter:
                continue

            w_bar, x_left, x_right = ALNS_tools.calculate_max_width_rect(height=shape.height, diameter=log.diameter)
            rectangle_volume = w_bar * shape.height

            """
            ---OPTIMISING CENTRAL RECTANGLE---
            Use shapes of same height to efficiently fill rectangle. Also look for shapes that can be rotated.
            This will always include the original shape itself.
            """
            shorter_shapes = [shape_2 for shape_2 in shape_types
                              if shape_2.height <= shape.height]

            solver = pywraplp.Solver.CreateSolver('SAT')

            # add decision variables
            var_stage_1 = []
            for short_shape in shorter_shapes:
                var_stage_1.append([solver.IntVar(0, solver.infinity(), 'x' + str(short_shape.type_id)),
                                    short_shape.width, short_shape.height, short_shape.type_id])

            # add constraint for maximum length
            solver.Add(sum([v[0] * (v[1] + constants.saw_kerf) for v in var_stage_1]) <= w_bar)
            solver.Maximize(sum([v[0] * v[1] * v[2] for v in var_stage_1]))

            status = solver.Solve()

            if status == pywraplp.Solver.OPTIMAL:
                print("\n Solution:")
                print("Obj Value = ", solver.Objective().Value())
                stage_1_values = [[v[3], v[0].solution_value()] for v in var_stage_1]
                usage = solver.Objective().Value()
                print(f"For height {shape.height}, found usage of {usage}.")
            else:
                raise ValueError("Solution Not Converged")

            """
            ---OPTIMISING NORTHERN/SOUTHERN RECTANGLE---
            STAGE 2 OPTIMISATION
            """
            height_a = (log.diameter - (shape.height + 2*constants.saw_kerf)) / 2
            stage_2_solutions = []
            shorter_a_shapes = [shape_2 for shape_2 in shape_types if shape_2.height <= height_a]

            for s in shorter_a_shapes:
                print(s.height)

            for short_shape in shorter_a_shapes:
                h_n = short_shape.height
                r = log.diameter / 2
                inner_value = r ** 2 - ((log.diameter + shape.height) / 2 + h_n - r) ** 2

                x_left_north = r - math.sqrt(inner_value)
                x_right_north = r + math.sqrt(inner_value)

                width_n = x_right_north - x_left_north

                sub_rectangle_volume = width_n * h_n

                solver = pywraplp.Solver.CreateSolver('SAT')

                shorter_h_n_shapes = [shape_2 for shape_2 in shape_types if shape_2.height <= h_n]

                var_stage_2 = []
                for s in shorter_h_n_shapes:
                    var_stage_2.append([solver.IntVar(0, solver.infinity(), 'x' + str(s.type_id)),
                                        s.width, s.height, s.type_id])

                solver.Add(sum([v[0] * (v[1] + constants.saw_kerf) for v in var_stage_2]) <= width_n)
                solver.Maximize(sum([v[0] * v[1] * v[2] for v in var_stage_2]))

                status = solver.Solve()

                if status == pywraplp.Solver.OPTIMAL:
                    print("\n Stage 2 Solution:")
                    print("Obj Value = ", solver.Objective().Value())
                    for v in var_stage_2:
                        print(v[3], " has value ", v[0].solution_value())

                    usage = solver.Objective().Value()
                    print(f"For height {shape.height}, found usage of {usage}.")
                    stage_2_solutions.append([usage,
                                              sub_rectangle_volume,
                                              [[v[3], v[0].solution_value()] for v in var_stage_2],
                                              h_n])
                else:
                    raise ValueError("Stage 2 Solution Not Converged")

            best_stage_2_solution = max(stage_2_solutions, key=lambda solution: solution[0])

            usage_stage_2 = best_stage_2_solution[0]
            rect_vol_stage_2 = best_stage_2_solution[1]
            stage_2_values = best_stage_2_solution[2]
            h_n = best_stage_2_solution[3]
            rel_usage = (usage + 2 * usage_stage_2) / (rectangle_volume + 2 * rect_vol_stage_2)
            solutions.append([rel_usage,
                              stage_1_values,
                              stage_2_values,
                              [shape.height, x_left, x_right, h_n]])

        best_complete_solution = max(solutions, key=lambda solution: solution[0])
        print(f"Optimal solution has a total usage rate of {best_complete_solution[0]}")

        shapes_in_central = best_complete_solution[1]
        shapes_in_top_bot = best_complete_solution[2]

        for var in best_complete_solution[1]:
            print(f"Shape {var[0]} has quantity {var[1]}")

        print(f"Stage two variables are given by:")
        for var in best_complete_solution[2]:
            print(f"Shape {var[0]} has quantity {var[1]}")

        """
        Creating the shapes at the corresponding locations.
        We iterate over the shapes, and place them one by one in arbitrary order, respecting saw kerf
        First we place the central pieces, then the top/bottom pieces
        """

        h, x_left_central, x_right_central, h_n = best_complete_solution[3]

        x = x_left_central
        y = (log.diameter - h) / 2

        for shape_info in shapes_in_central:
            shape_id = shape_info[0]
            quantity = int(shape_info[1])
            shape_type = shape_types[shape_id]

            for i in range(quantity):
                shapes.append(Shape(shape_type=shape_type, x=x, y=y))
                print(f"Placing shapetype {shape_id} with w:{shape_type.width}, "
                      f"h:{shape_type.height} at ({x}, {y})")
                x += shape_type.width + constants.saw_kerf

        y_plus_north = (log.diameter + (h+constants.saw_kerf)) / 2 + h_n
        x_left, x_right = log.calculate_edge_positions_on_circle(z=y_plus_north)

        x = x_left
        y_north = y + h + constants.saw_kerf
        y_south = y - h_n - constants.saw_kerf

        for shape_info in shapes_in_top_bot:
            shape_id = shape_info[0]
            quantity = int(shape_info[1])
            shape_type = shape_types[shape_id]

            for i in range(quantity):
                shapes.append(Shape(shape_type=shape_type, x=x, y=y_north))
                shapes.append(Shape(shape_type=shape_type, x=x, y=y_south + (h_n - shape_type.height)))
                print(f"Placing shapetype {shape_id} with w:{shape_type.width}, "
                      f"h:{shape_type.height} at ({x}, {y_south}) and ({x}, {y_north})")
                x += shape_type.width + constants.saw_kerf

        for shape in shapes:
            if shape.log is None:
                shape.log = log
                log.add_shape(shape)
