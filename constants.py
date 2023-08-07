"""
Constant For Shapes (in mm)
"""

saw_kerf = 3
rect_text_margin = 0.01

"""
ALNS Parameters
"""
starting_temperature = 100
max_iterations = 30

temperature_sensitivity = 0.99
method_sensitivity_acceptance = 0.99
method_sensitivity_rejection = 0.95

fill_up_iterations = 15

repair_max_attempts = 20

min_width_shape_type = None
min_height_shape_type = None
smallest_total_shapes = []

error_margin = 0.0001

# Score parameters
usage_multiplier = 1
saw_dust_multiplier = -1.5
unused_multiplier = -0.8
