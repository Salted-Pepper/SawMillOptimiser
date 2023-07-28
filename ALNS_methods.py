import constants
from logs import Log


def random_destroy(log, shape_types):
    pass


def subspace_destroy(log, shape_types):
    pass


def inefficiency_destroy(log, shape_types):
    pass


def random_point_expansion(log, shape_types):
    pass


def single_extension_repair(log, shape_types):
    pass


def buddy_extension_repair(log, shape_types):
    pass


class Method:
    adjust_rate = 0.95

    def __init__(self, name):
        self.name = name
        self.performance = 100
        self.probability = 1
        self.method_used = False
        self.times_used = 0

    def reject_method(self):
        self.performance = self.performance * self.adjust_rate

    def execute(self, log, shape_types):

        if self.name == "RANDOM":
            random_destroy(log, shape_types)
        elif self.name == "SUBSPACE":
            subspace_destroy(log, shape_types)
        elif self.name == "INEFFICIENCY":
            inefficiency_destroy(log, shape_types)
        elif self.name == "RPE":
            random_point_expansion(log, shape_types)
        elif self.name == "SER":
            single_extension_repair(log, shape_types)
        elif self.name == "BER":
            buddy_extension_repair(log, shape_types)
        else:
            raise ValueError(f"ALNS Method {self.name} Not Implemented")

    def used(self):
        self.method_used = True
        self.times_used += 1


def update_method_probability(methods: list, updated):
    total_performance = sum([method.performance for method in methods])

    for method in methods:
        if updated and method.used:
            method.performance = method.performance * constants.method_sensitivity_acceptance
            method.used = False
        else:
            method.performance = method.performance * constants.method_sensitivity_rejection

    for method in methods:
        method.probability = method.performance / total_performance

