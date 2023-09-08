"""
Constant For Shapes (in mm)
"""

rect_text_margin = 0.01
error_margin = 0.0001

"""
ALNS Parameters
"""
optimising_text = "Optimising - This might take a while... \n"

starting_temperature = 100
max_iterations = 200
fill_up_iterations = 5

min_destroy_degree = 1
min_repair_degree = 5

max_attempts = 15
centring_attempts = 10

tuck_success_multiplier = 1.1
tuck_failure_multiplier = 0.91

# This takes the temperature down to failing level in approx ~230 failed attempts
temperature_sensitivity = 0.98

min_width_shape_type = None
min_height_shape_type = None
smallest_total_shapes = []

# Selection Parameters
log_selection_accepted = 0.99
log_selection_rejected = 0.9

method_sensitivity_acceptance = 0.999
method_sensitivity_rejection = 0.998

# Score parameters
usage_multiplier = 1
saw_dust_multiplier = -0.0001
unused_multiplier = 0
