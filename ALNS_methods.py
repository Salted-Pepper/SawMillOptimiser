from logs import Log


def random_repair(log, shape_types):
    pass


def subspace_repair(log, shape_types):
    pass


def inefficiency_repair(log, shape_types):
    pass


def random_point_expension(log, shape_types):
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

    def reject_method(self):
        self.performance = self.performance * self.adjust_rate

    def execute(self, log, shape_types):

        if self.name == "RANDOM":
            random_repair(log, shape_types)
        elif self.name == "SUBSPACE":
            subspace_repair(log, shape_types)
        elif self.name == "INEFFICIENCY":
            inefficiency_repair(log, shape_types)
        elif self.name == "RPE":
            random_point_expension(log, shape_types)
        elif self.name == "SER":
            single_extension_repair(log, shape_types)
        elif self.name == "BER":
            buddy_extension_repair(log, shape_types)
        else:
            raise ValueError(f"ALNS Method {self.name} Not Implemented")

