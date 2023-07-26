import logging
import numpy as np
import datetime
from logs import Log
import math
from ortools.linear_solver import pywraplp

import ALNS_tools
import constants
from shapes import Shape

date = datetime.date.today()
logging.basicConfig(level=logging.DEBUG, filename='saw_mill_app_' + str(date) + '.log',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt="%d-%b-%y %H:%M:%S")


def fit_shapes_in_rect_by_lp(x_min: float, x_max: float, y_min: float, y_max: float,
                             candidate_shapes: list, shape_types: list, shapes: list,  log: Log) -> list:
    """
    :param x_min: Left side x-value
    :param x_max: Right side x-value
    :param y_min: Bottom side y-value
    :param y_max: Top side y-value
    :param candidate_shapes: List of shapes to fill the given space
    :param shape_types: List of all available shapes
    :param shapes: List of shapes currently in the considered log
    :param log: Log to which the shapes will be added
    :return shapes: List of added shapes

    This function applies an LP solver to the given space, optimising the space for the given candidate shapes.
    The given space, described by (x,y)-values, includes the saw kerf on the sides.
    It returns a new set of shapes that can be added in the described location.
    """
    solutions = []

    width = x_max - x_min - 2 * constants.saw_kerf
    height = y_max - y_min - 2 * constants.saw_kerf

    candidate_shapes = [s for s in candidate_shapes if s.width <= width]

    for shape in candidate_shapes:
        h_m = shape.height
        shorter_shapes = [s for s in candidate_shapes if s.height <= h_m]

        solver = pywraplp.Solver.CreateSolver('SAT')

        variables = []

        for short_shape in shorter_shapes:
            variables.append([solver.IntVar(0, solver.infinity(), 'x' + str(short_shape.type_id)),
                              short_shape.width, short_shape.height, short_shape.type_id])

            # add constraint for maximum length
            solver.Add(sum([v[0] * (v[1] + constants.saw_kerf) for v in variables]) <= width)
            solver.Maximize(sum([v[0] * v[1] * v[2] for v in variables]))

        status = solver.Solve()

        if status == pywraplp.Solver.OPTIMAL:
            values = [[v[3], v[0].solution_value()] for v in variables]
            usage = solver.Objective().Value()
        else:
            raise ValueError("Solution Not Converged")

        rel_usage = usage / (height * width)

        solutions.append([rel_usage,
                          values,
                          [h_m, x_min, x_max, height]])

    best_solution = max(solutions, key=lambda solution: solution[0])
    shapes_top = best_solution[1]

    x_minimal = best_solution[2][1]
    x_maximal = best_solution[2][2]

    x = x_minimal + constants.saw_kerf

    for shape_info in shapes_top:
        shape_id = shape_info[0]
        quantity = int(shape_info[1])
        shape_type = shape_types[shape_id]

        for i in range(quantity):
            shapes.append(Shape(shape_type=shape_type, x=x, y=y_min))
            logging.debug(f"Added shape {shape_type.type_id}, at location {x, y_min}")
            x += shape_type.width + constants.saw_kerf
            if x > x_maximal:
                raise ValueError(f"Exceeding maximum x-value {x} > {x_maximal}.")

    return shapes


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
        logging.debug(f"Optimising for log with diameter {log.diameter}")

        for shape in shape_types:

            if shape.height >= log.diameter:
                continue

            w_bar, x_left, x_right = ALNS_tools.calculate_max_width_rect(height=shape.height, diameter=log.diameter)
            rectangle_volume = w_bar * shape.height

            """
            ---OPTIMISING CENTRAL RECTANGLE---
            Use shapes of same height or smaller to efficiently fill rectangle.
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
                # print("\n Solution:")
                # print("Obj Value = ", solver.Objective().Value())
                stage_1_values = [[v[3], v[0].solution_value()] for v in var_stage_1]
                usage = solver.Objective().Value()
                # print(f"For height {shape.height}, found usage of {usage}.")
            else:
                raise ValueError("Solution Not Converged")

            """
            ---OPTIMISING NORTHERN/SOUTHERN RECTANGLE---
            STAGE 2 OPTIMISATION
            """
            height_a = (log.diameter - (shape.height + 2 * constants.saw_kerf)) / 2
            stage_2_solutions = []
            shorter_a_shapes = [shape_2 for shape_2 in shape_types if shape_2.height <= height_a]

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
                    # print("\n Stage 2 Solution:")
                    # print("Obj Value = ", solver.Objective().Value())
                    # for v in var_stage_2:
                    #     print(v[3], " has value ", v[0].solution_value())
                    usage = solver.Objective().Value()
                    # print(f"For height {shape.height}, found usage of {usage}.")
                    stage_2_solutions.append([usage,
                                              sub_rectangle_volume,
                                              [[v[3], v[0].solution_value()] for v in var_stage_2],
                                              h_n])
                else:
                    raise ValueError("Stage 2 Solution Not Converged")

            if len(stage_2_solutions) > 0:
                best_stage_2_solution = max(stage_2_solutions, key=lambda solution: solution[0])

                usage_stage_2 = best_stage_2_solution[0]
                rect_vol_stage_2 = best_stage_2_solution[1]
                stage_2_values = best_stage_2_solution[2]
                h_n = best_stage_2_solution[3]
                rel_usage = (usage + 2 * usage_stage_2) / (rectangle_volume + 2 * rect_vol_stage_2)
            else:
                stage_2_values = []
                rel_usage = usage / rectangle_volume
                h_n = 0

            solutions.append([rel_usage,
                              stage_1_values,
                              stage_2_values,
                              [shape.height, x_left, x_right, h_n]])

        best_complete_solution = max(solutions, key=lambda solution: solution[0])
        logging.debug(f"Optimal solution has a total usage rate of {best_complete_solution[0]}")

        shapes_in_central = best_complete_solution[1]
        shapes_in_top_bot = best_complete_solution[2]

        for var in best_complete_solution[1]:
            logging.debug(f"Shape {var[0]} has quantity {var[1]}")

        logging.debug(f"Stage two variables are given by:")
        for var in best_complete_solution[2]:
            logging.debug(f"Shape {var[0]} has quantity {var[1]}")

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
                logging.debug(f"Placing shapetype {shape_id} with w:{shape_type.width}, "
                              f"h:{shape_type.height} at ({x}, {y})")
                x += shape_type.width + constants.saw_kerf

        y_plus = (log.diameter + (h + constants.saw_kerf)) / 2 + h_n
        x_left, x_right = log.calculate_edge_positions_on_circle(z=y_plus)

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
                logging.debug(f"Placing shapetype {shape_id} with w:{shape_type.width}, "
                              f"h:{shape_type.height} at ({x}, {y_south}) and ({x}, {y_north})")
                x += shape_type.width + constants.saw_kerf

        shapes = create_corner_solution(shapes, log, shape_types, h, h_n, y_north, y_south, "NW")
        shapes = create_corner_solution(shapes, log, shape_types, h, h_n, y_north, y_south, "NE")

        shapes = create_edge_solutions(shapes, log, shape_types, h, h_n)

        """
        Register Shapes to assigned log
        """
        for shape in shapes:
            if shape.log is None:
                shape.log = log
                log.add_shape(shape)


def create_corner_solution(shapes: list, log: Log, shape_types: list, h: float, h_n: float,
                           y_north: float, y_south: float, orientation: str):
    """
    Fill out log corner positions
    Step 1 - Locate left and right corner triangles (Mirror for north and south)
    Step 2 - Solve LP for corner options
    h_n : Height of north/south solution
    h: Height of center row
    """

    candidate_shapes = [s for s in shape_types if s.height < h_n]
    top_shapes = [s for s in shapes if s.y >= y_north]

    # Step 1 - Locating Corner
    if orientation == "NW":
        left_most_rect = ALNS_tools.find_left_most_shape(top_shapes)
        rect = left_most_rect
        x_val = rect.x - constants.saw_kerf
    elif orientation == "NE":
        right_most_rect = ALNS_tools.find_right_most_shape(top_shapes)
        rect = right_most_rect
        x_val = rect.x + rect.width + constants.saw_kerf
    else:
        raise NotImplementedError(f"Orientation {orientation} not implemented.")

    corner = []
    for shape in candidate_shapes:
        h_m = shape.height
        w_m, x_minimal, x_maximal = ALNS_tools.find_max_rectangle_width(log=log, height=h_m,
                                                                        x=x_val,
                                                                        y=rect.y,
                                                                        orientation=orientation)

        # Step 2 - Solve LP for corner options
        if shape.width < (w_m - constants.saw_kerf):
            shorter_shapes = [s for s in candidate_shapes
                              if s.height <= h_m]

            solver = pywraplp.Solver.CreateSolver('SAT')

            # add decision variables
            var_north_west = []
            for short_shape in shorter_shapes:
                var_north_west.append([solver.IntVar(0, solver.infinity(), 'x' + str(short_shape.type_id)),
                                       short_shape.width, short_shape.height, short_shape.type_id])

            # add constraint for maximum length
            solver.Add(sum([v[0] * (v[1] + constants.saw_kerf) for v in var_north_west]) <= w_m)
            solver.Maximize(sum([v[0] * v[1] * v[2] for v in var_north_west]))

            status = solver.Solve()

            if status == pywraplp.Solver.OPTIMAL:
                corner_values = [[v[3], v[0].solution_value()] for v in var_north_west]
                usage = solver.Objective().Value()
            else:
                raise ValueError("Solution Not Converged")

            rel_usage = usage / (h_m * w_m)

            corner.append([rel_usage,
                           corner_values,
                           [shape.height, x_minimal, x_maximal, h_m]])
    if len(corner) > 0:
        best_corner_solution = max(corner, key=lambda solution: solution[0])
        shapes_corner = best_corner_solution[1]

        x_minimal = best_corner_solution[2][1]
        x_maximal = best_corner_solution[2][2]
        h_m = best_corner_solution[2][3]

        if orientation == "NW":
            x = x_maximal + constants.saw_kerf
        elif orientation == "NE":
            x = x_minimal
        else:
            raise NotImplementedError("Orientation not found")

        for shape_info in shapes_corner:
            shape_id = shape_info[0]
            quantity = int(shape_info[1])
            shape_type = shape_types[shape_id]

            for i in range(quantity):

                if orientation == "NW":
                    x -= shape_type.width + constants.saw_kerf
                    shapes.append(Shape(shape_type=shape_type, x=x, y=y_north))
                    shapes.append(Shape(shape_type=shape_type, x=x,
                                        y=(log.diameter - h) / 2 - shape_type.height - constants.saw_kerf))
                    logging.debug(f"Placing shapetype {shape_id} with w:{shape_type.width}, "
                                  f"h:{shape_type.height} at ({x}, {log.diameter / 2 + h / 2 - shape_type.height}) "
                                  f"and ({x}, {y_north})")
                    if x < x_minimal:
                        raise ValueError(f"x exceeds minimum value for sub-rectangle. x is {x}, x_min is {x_minimal}.")

                elif orientation == "NE":

                    shapes.append(Shape(shape_type=shape_type, x=x, y=y_north))
                    shapes.append(Shape(shape_type=shape_type, x=x,
                                        y=(log.diameter - h) / 2 - shape_type.height - constants.saw_kerf))
                    logging.debug(f"Placing shapetype {shape_id} with w:{shape_type.width}, "
                                  f"h:{shape_type.height} at ({x}, {log.diameter / 2 + h / 2 - shape_type.height}) "
                                  f"and ({x}, {y_north})")
                    x += shape_type.width + constants.saw_kerf
                    if x > x_maximal:
                        raise ValueError(f"x exceeds maximum value for sub-rectangle. x is {x}, x_max is {x_maximal}")
    return shapes


def create_edge_solutions(shapes: list, log: Log, shape_types: list, h: float, h_n: float, ) -> list:
    min_y = (log.diameter + h) / 2 + h_n + 2 * constants.saw_kerf
    max_y = log.diameter
    max_height = max_y - min_y

    candidate_shapes = [s for s in shape_types if s.height < max_height]

    top = []

    # If no feasible candidate shape, space can't be filled
    if len(candidate_shapes) == 0:
        return shapes

    # Otherwise, cycle over shapes and solve LP for height h_t
    for shape in candidate_shapes:
        h_t = shape.height
        shorter_shapes = [s for s in candidate_shapes if s.height <= h_t]

        # Find x-coords where the height available is at least h_t
        x_min, x_max = log.calculate_edge_positions_on_circle(log.diameter - (max_height - h_t))
        w_t = x_max - x_min

        # If the shape is wider than that maximum space, it is not a feasible candidate solution
        if shape.width + constants.saw_kerf > w_t:
            continue
        else:

            solver = pywraplp.Solver.CreateSolver('SAT')

            var_top = []
            for short_shape in shorter_shapes:
                var_top.append([solver.IntVar(0, solver.infinity(), 'x' + str(short_shape.type_id)),
                                short_shape.width, short_shape.height, short_shape.type_id])

            # add constraint for maximum length
            solver.Add(sum([v[0] * (v[1] + constants.saw_kerf) for v in var_top]) <= w_t)
            solver.Maximize(sum([v[0] * v[1] * v[2] for v in var_top]))

            status = solver.Solve()

            if status == pywraplp.Solver.OPTIMAL:
                top_values = [[v[3], v[0].solution_value()] for v in var_top]
                usage = solver.Objective().Value()
            else:
                raise ValueError("Solution Not Converged")

            rel_usage = usage / (h_t * w_t)

            top.append([rel_usage,
                        top_values,
                        [shape.height, x_min, x_max, h_t]])

    if len(top) > 0:
        best_top_solution = max(top, key=lambda solution: solution[0])
        shapes_top = best_top_solution[1]

        x_minimal = best_top_solution[2][1]
        x_maximal = best_top_solution[2][2]
        h_m = best_top_solution[2][3]

        x = x_minimal

        for shape_info in shapes_top:
            shape_id = shape_info[0]
            quantity = int(shape_info[1])
            shape_type = shape_types[shape_id]

            for i in range(quantity):
                shapes.append(Shape(shape_type=shape_type, x=x, y=min_y))
                shapes.append(Shape(shape_type=shape_type, x=x,
                                    y=(log.diameter - h) / 2 - h_n - shape_type.height - 2 * constants.saw_kerf))
                logging.debug(f"Placing shapetype {shape_id} with w:{shape_type.width}, "
                              f"h:{shape_type.height} at ({x}, "
                              f"{(log.diameter - h) / 2 - h_n - shape_type.height - constants.saw_kerf})"
                              f"and ({x}, {min_y})")
                x += shape_type.width + constants.saw_kerf

    return shapes
