import logging
import numpy as np
import math
from ortools.linear_solver import pywraplp

import ALNS_tools

import constants


def greedy_place(shape_types: list, logs: list) -> None:
    """
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
                break

            w_bar = ALNS_tools.calculate_max_width_rect(height=shape.height, diameter=log.diameter)
            rectangle_volume = w_bar * shape.height

            """
            Use shapes of same height to efficiently fill rectangle. Also look for shapes that can be rotated.
            This will always include the original shape itself.
            """
            shorter_shapes = [shape_2 for shape_2 in shape_types
                              if shape_2.height <= shape.height]

            solver = pywraplp.Solver.CreateSolver('SAT')

            # add decision variables
            variables = []
            for short_shape in shorter_shapes:
                variables.append([solver.IntVar(0, solver.infinity(), 'x' + str(short_shape.type_id)),
                                  short_shape.width, short_shape.height, short_shape.type_id])

            # add constraint for maximum length
            solver.Add(sum([v[0] * (v[1] + constants.saw_kerf) for v in variables]) <= w_bar)
            solver.Maximize(sum([v[0] * v[1] * v[2] for v in variables]))

            status = solver.Solve()

            if status == pywraplp.Solver.OPTIMAL:
                print("\n Solution:")
                print("Obj Value = ", solver.Objective().Value())
                for v in variables:
                    print(v[3], " has value ", v[0].solution_value())

                usage = solver.Objective().Value() / rectangle_volume
                print(f"For height {shape.height}, found usage of {usage}.")
            else:
                print("Problem has no optimal solution.")
                raise ValueError("Solution Not Converged")

            """
            Optimise north rectangle
            """
            height_a = (log.diameter - shape.height) / 2
            stage_2_solutions = []
            shorter_a_shapes = [shape_2 for shape_2 in shape_types if shape_2.height <= height_a]
            print(f"Height a is {height_a}")
            print("Checking heights...")
            for s in shorter_a_shapes:
                print(s.height)

            for short_shape in shorter_a_shapes:
                h_n = short_shape.height
                print(f"Height of subproblem is {h_n}")

                r = log.diameter / 2
                inner_value = r ** 2 - ((log.diameter + shape.height) / 2 + h_n - r) ** 2

                x_left_north = r - math.sqrt(inner_value)
                x_right_north = r + math.sqrt(inner_value)

                width_n = x_right_north - x_left_north
                print(f"Dimension of north/south rectangle is {width_n:.2f}x{h_n}")

                solver = pywraplp.Solver.CreateSolver('SAT')

                variables_sp = []
                for s in shorter_a_shapes:
                    variables_sp.append([solver.IntVar(0, solver.infinity(), 'x' + str(s.type_id)),
                                         s.width, s.height, s.type_id])

                solver.Add(sum([v[0] * (v[1] + constants.saw_kerf) for v in variables_sp]) <= width_n)
                solver.Maximize(sum([v[0] * v[1] * v[2] for v in variables_sp]))

                status = solver.Solve()

                if status == pywraplp.Solver.OPTIMAL:
                    print("\n Stage 2 Solution:")
                    print("Obj Value = ", solver.Objective().Value())
                    for v in variables_sp:
                        print(v[3], " has value ", v[0].solution_value())

                    usage = solver.Objective().Value() / rectangle_volume
                    print(f"For height {shape.height}, found usage of {usage}.")
                    stage_2_solutions.append([usage, variables_sp])
                else:
                    print("Problem has no optimal solution.")
                    raise ValueError("Stage 2 Solution Not Converged")

            best_stage_2_solution = max(stage_2_solutions, key=lambda x: x[0])
            solutions.append([usage, variables, best_stage_2_solution[0], best_stage_2_solution[1]])


