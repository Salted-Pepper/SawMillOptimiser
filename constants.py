"""
Constant For Shapes (in mm)
"""

saw_kerf = 3
rect_text_margin = 0.01
error_margin = 0.0001

"""
ALNS Parameters
"""
starting_temperature = 100
max_iterations = 400
fill_up_iterations = 40

max_attempts = 10
centring_attempts = 20

tuck_success_multiplier = 1.1
tuck_failure_multiplier = 0.91

# This takes the temperature down to failing level in approx ~230 failed attempts
temperature_sensitivity = 0.98

min_width_shape_type = None
min_height_shape_type = None
smallest_total_shapes = []

# Selection Parameters
log_selection_accepted = 0.98
log_selection_rejected = 0.9

method_sensitivity_acceptance = 0.99
method_sensitivity_rejection = 0.95

# Score parameters
usage_multiplier = 1
saw_dust_multiplier = -0.0001
unused_multiplier = 0
