import logging
import pandas as pd
import random
import datetime
import copy
from logs import Log
import math
from ALNS_methods import Method, update_method_probability
from ortools.linear_solver import pywraplp

import ALNS_tools
import constants
from shapes import Shape

date = datetime.date.today()
logging.basicConfig(level=logging.DEBUG, filename='saw_mill_app_' + str(date) + '.log',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt="%d-%b-%y %H:%M:%S")
logger = logging.getLogger("ALNS_Logger")
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)
logger.setLevel(logging.DEBUG)


def run_ALNS(logs: list, shape_types: list):
    solution_quality_df = pd.DataFrame(columns=["iteration", "log", "score", "saw_dust", "volume_used", "efficiency"])
    iteration = 1
    temperature = constants.starting_temperature
    destroy_degree = 4
    repair_degree = 15

    """
    Initialize methods and create pre-emptive calculations for parameters that will be re-used
    """

    ALNS_tools.calculate_smallest_shape_types(shape_types)

    destroy_methods = [Method(name="RANDOM", goal="destroy"),
                       Method(name="CLUSTER", goal="destroy"),
                       Method(name="SUBSPACE", goal="destroy"),
                       Method(name="INEFFICIENCY", goal="destroy")]
    repair_methods = [Method(name="RPE", goal="repair"),
                      Method(name="SER", goal="repair"),
                      Method(name="BER", goal="repair")]
    tuck_methods = [Method(name="TUCK-CENTRE", goal="other"),
                    Method(name="TUCK-LEFT", goal="other"),
                    Method(name="TUCK-RIGHT", goal="other"),
                    Method(name="TUCK-UP", goal="other"),
                    Method(name="TUCK-DOWN", goal="other")]
    tuck_probabilities = [0.8, 0.05, 0.05, 0.05, 0.05]

    """
    Start ALNS Sequence, select random methods to repair and destroy based on assigned probabilities
    """
    while temperature > 0 and iteration <= constants.max_iterations:

        log = ALNS_tools.select_log(logs)
        logger.debug(f"Going into iteration {iteration} with temperature {temperature}... Selected {log.log_id}")
        # Invoke copy here to ensure changes do not apply unless new solution is accepted
        log_new = Log(log.diameter)
        for shape in log.shapes:
            Shape(shape_type=shape.type, x=shape.x, y=shape.y, copy_id=shape.shape_id).assign_to_log(log_new)

        # Only run repair methods for the first couple of iterations to fill up empty space in initial solution
        if iteration < constants.fill_up_iterations:
            for i in range(math.floor(repair_degree)):
                repair_method = random.choices(repair_methods,
                                               weights=[method.probability for method in repair_methods],
                                               k=1)[0]
                logger.debug(f"Select repair method {repair_method.name} with probability {repair_method.probability}")
                repair_method.used()
                repair_method.execute(log_new, shape_types)

                tuck_method = random.choices(tuck_methods, weights=tuck_probabilities, k=1)[0]
                tuck_method.used()
                tuck_method.execute(log_new, shape_types)
        else:
            for i in range(math.floor(destroy_degree)):
                destroy_method = random.choices(destroy_methods,
                                                weights=[method.probability for method in destroy_methods], k=1)[0]
                logger.debug(f"Select destroy method {destroy_method.name} "
                             f"with probability {destroy_method.probability}")
                destroy_method.used()
                destroy_method.execute(log_new, shape_types)
            for i in range(math.floor(repair_degree)):
                repair_method = random.choices(repair_methods,
                                               weights=[method.probability for method in repair_methods], k=1)[0]
                repair_method.used()
                logger.debug(f"Select repair method {repair_method.name} with probability {repair_method.probability}")
                method_was_successful = repair_method.execute(log_new, shape_types)
                if method_was_successful:
                    logger.debug(f"Repair method {repair_method.name} was successful")
                else:
                    logger.debug(f"Repair method {repair_method.name} was unsuccessful")
                tuck_method = random.choices(tuck_methods, weights=tuck_probabilities, k=1)[0]
                tuck_method.used()
                tuck_method.execute(log_new, shape_types)

            # TODO: REMOVE FEASIBILITY CHECK AFTER EACH ITERATION - THIS IS ONLY FOR DEBUGGING AND AFFECTS PERFORMANCE
            if not ALNS_tools.check_feasibility(logs):
                raise ValueError(f"Placement not feasible")

        ALNS_tools.update_log_scores([log_new])
        accept_new_solution, delta, score = ALNS_tools.check_if_new_solution_better(log, log_new, temperature)

        """
        Single Iteration completed, process changes and update parameter values
        """
        # Optional plotting to check iterations
        # log_new.show_plot(extra_text=
        #                   f"(Accepted Iteration {iteration})" if accept_new_solution
        #                   else f"(Not Accepted Iteration {iteration})")
        # log_new.save_log_plot()
        if accept_new_solution:
            logger.debug(f"New solution has been accepted with improvement {delta} \n \n")
            log.shapes = log_new.shapes
            for shape in log.shapes:
                shape.log = log
            log.score = log_new.score
            log.volume_used = log_new.volume_used
            log.calculate_efficiency()
            log.saw_dust = log_new.saw_dust
        else:
            logger.debug(f"New solution has been declined, delta of {delta} \n \n")
            pass

        # Push shapes to centre at end
        for log in logs:
            for _ in range(constants.centring_attempts):
                tuck_methods[0].execute(log, shape_types)

        solution_quality_df = ALNS_tools.save_iteration_data(logs, solution_quality_df, iteration)
        temperature = ALNS_tools.update_temperature(temperature, accept_new_solution, delta, score)
        logger.debug(f"New temperature is {temperature: .3f}, new solution accepted: {accept_new_solution},"
                     f"delta: {delta: .2f}, score:{score: .2f}")
        update_method_probability(repair_methods, accept_new_solution)
        update_method_probability(destroy_methods, accept_new_solution)
        iteration += 1

        if iteration % 10 == 0:
            for method in repair_methods + destroy_methods + tuck_methods:
                logging.debug(f"Method {method.name} has probability {method.probability} "
                              f"and performance {method.performance}")

        # TODO: Update destroy/repair degree based on temperature

    ALNS_tools.report_method_stats(repair_methods + destroy_methods + tuck_methods)

    return solution_quality_df


def greedy_place(all_shapes: list, shape_types: list, logs: list) -> None:
    """
    :param all_shapes: List of all Shapes
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
        logger.debug(f"Optimising for log with diameter {log.diameter}")
        shapes = []

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
            solver.Add(sum([v[0] * (v[1] + constants.saw_kerf)
                            for v in var_stage_1]) <= w_bar)
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
            height_a = (log.diameter - (shape.height + 2*constants.saw_kerf)) / 2
            stage_2_solutions = []
            shorter_a_shapes = [shape_2 for shape_2 in shape_types if shape_2.height <= height_a]

            for short_shape in shorter_a_shapes:
                h_n = short_shape.height
                r = log.diameter / 2
                inner_value = r ** 2 - ((log.diameter + (shape.height + 2*constants.saw_kerf)) / 2 + h_n - r) ** 2

                x_left_north = r - math.sqrt(inner_value)
                x_right_north = r + math.sqrt(inner_value)

                width_n = x_right_north - x_left_north
                sub_rectangle_volume = width_n * h_n
                shorter_h_n_shapes = [shape_2 for shape_2 in shape_types if shape_2.height <= h_n]

                solver = pywraplp.Solver.CreateSolver('SAT')
                var_stage_2 = []
                for s in shorter_h_n_shapes:
                    var_stage_2.append([solver.IntVar(0, solver.infinity(), 'x' + str(s.type_id)),
                                        s.width, s.height, s.type_id])

                solver.Add(sum([v[0] * (v[1] + constants.saw_kerf)
                                for v in var_stage_2]) <= width_n)
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
        logger.debug(f"Optimal solution has a total usage rate of {best_complete_solution[0]}")

        shapes_in_central = best_complete_solution[1]
        shapes_in_top_bot = best_complete_solution[2]

        for var in best_complete_solution[1]:
            logger.debug(f"Shape {var[0]} has quantity {var[1]}")

        logger.debug(f"Stage two variables are given by:")
        for var in best_complete_solution[2]:
            logger.debug(f"Shape {var[0]} has quantity {var[1]}")

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
                logger.debug(f"Placing shapetype {shape_id} with w:{shape_type.width}, "
                             f"h:{shape_type.height} at ({x}, {y})")
                x += shape_type.width + constants.saw_kerf

        y_plus = (log.diameter + (h + 2 * constants.saw_kerf)) / 2 + h_n
        x_left, x_right = log.calculate_edge_positions_on_circle(z=y_plus)

        x = x_left
        y_north = y + h + constants.saw_kerf
        y_south = y - h_n - constants.saw_kerf

        for shape_info in shapes_in_top_bot:
            shape_id = shape_info[0]
            quantity = int(shape_info[1])
            shape_type = shape_types[shape_id]

            for i in range(quantity):
                shapes.append(Shape(shape_type=shape_type, x=x,
                                    y=y_north))
                shapes.append(Shape(shape_type=shape_type, x=x,
                                    y=y_south + (h_n - shape_type.height)))
                logger.debug(f"Placing shapetype {shape_id} with w:{shape_type.width}, "
                             f"h:{shape_type.height} at ({x}, {y_south + (h_n - shape_type.height)}) "
                             f"and ({x}, {y_north})")
                x += shape_type.width + constants.saw_kerf

        shapes = create_corner_solution(shapes, log, shape_types, h, h_n, y_north, "NW")
        shapes = create_corner_solution(shapes, log, shape_types, h, h_n, y_north, "NE")

        shapes = create_edge_solutions(shapes, log, shape_types, h, h_n)

        """
        Register Shapes to assigned log
        """
        for shape in shapes:
            if shape.log is None:
                shape.log = log
                log.add_shape(shape)

        all_shapes.extend(shapes)


def create_corner_solution(shapes: list, log: Log, shape_types: list, h: float, h_n: float,
                           y_north: float, orientation: str):
    """
    Fill out log corner positions - area A/B in Figure 3 (Second Stage Initial Solution)
    Step 1 - Locate left and right corner triangles (Mirror for north and south)
    Step 2 - Solve LP for corner options
    h_n : Height of north/south solution
    h: Height of center row
    """

    candidate_shapes = [s for s in shape_types if s.height <= h_n]
    logger.debug(f"h_n is {h_n}, h is {h} for log {log.log_id} with d {log.diameter}")
    top_shapes = [s for s in shapes if s.y >= y_north]

    # Step 1 - Locating Corner
    if orientation == "NW":
        left_most_rect = ALNS_tools.find_left_most_shape(top_shapes)
        rect = left_most_rect
        x_val = rect.x - constants.saw_kerf
        logger.debug(f"Left most shape is at ({rect.x}, {rect.y}), with h: {rect.height}, w: {rect.width}")
    elif orientation == "NE":
        right_most_rect = ALNS_tools.find_right_most_shape(top_shapes)
        rect = right_most_rect
        x_val = rect.x + rect.width + constants.saw_kerf
        logger.debug(f"Right most shape is at ({rect.x}, {rect.y}), with h: {rect.height}, w: {rect.width}")
    else:
        raise NotImplementedError(f"Orientation {orientation} not implemented.")

    corner = []
    for shape in candidate_shapes:
        h_m = shape.height
        logger.debug(f"Considering shape {shape.type_id} with height {shape.height}, y_north {y_north}")
        w_m, x_minimal, x_maximal = ALNS_tools.find_max_rectangle_width(log=log, height=h_m,
                                                                        x=x_val,
                                                                        y=y_north,
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
            solver.Add(sum([v[0] * (v[1] + constants.saw_kerf)
                            for v in var_north_west]) <= w_m)
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
                    logger.debug(f"Placing shapetype {shape_id} with w:{shape_type.width}, "
                                 f"h:{shape_type.height} at ({x}, "
                                 f"{(log.diameter - h) / 2 - shape_type.height - constants.saw_kerf}) "
                                 f"and ({x}, {y_north})")
                    if x < x_minimal:
                        raise ValueError(f"x exceeds minimum value for sub-rectangle. x is {x}, x_min is {x_minimal}.")

                elif orientation == "NE":

                    shapes.append(Shape(shape_type=shape_type, x=x, y=y_north))
                    shapes.append(Shape(shape_type=shape_type, x=x,
                                        y=(log.diameter - h) / 2 - shape_type.height
                                          - constants.saw_kerf))
                    logger.debug(f"Placing shapetype {shape_id} with w:{shape_type.width}, "
                                 f"h:{shape_type.height} at ({x}, "
                                 f"{(log.diameter - h) / 2 - shape_type.height - constants.saw_kerf}) "
                                 f"and ({x}, {y_north})")
                    x += shape_type.width + constants.saw_kerf
                    if x > x_maximal:
                        raise ValueError(f"x exceeds maximum value for sub-rectangle. x is {x}, x_max is {x_maximal}")
    return shapes


def create_edge_solutions(shapes: list, log: Log, shape_types: list, h: float, h_n: float, ) -> list:
    """
    Creates solutions for areas D in Figure 3
    :param shapes: List of Shapes
    :param log: Log Object
    :param shape_types: List of all shape types
    :param h: Height of centre shapes
    :param h_n: Height of North/South rectangles
    :return:
    """
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

        x = x_minimal

        for shape_info in shapes_top:
            shape_id = shape_info[0]
            quantity = int(shape_info[1])
            shape_type = shape_types[shape_id]

            for i in range(quantity):
                shapes.append(Shape(shape_type=shape_type, x=x, y=min_y))
                shapes.append(Shape(shape_type=shape_type, x=x,
                                    y=(log.diameter - h) / 2 - h_n - shape_type.height - 2 * constants.saw_kerf))
                logger.debug(f"Placing shapetype {shape_id} with w:{shape_type.width}, "
                             f"h:{shape_type.height} at ({x}, "
                             f"{(log.diameter - h) / 2 - h_n - shape_type.height - constants.saw_kerf})"
                             f"and ({x}, {min_y})")
                x += shape_type.width + constants.saw_kerf

    return shapes
