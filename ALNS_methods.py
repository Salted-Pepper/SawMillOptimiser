from logs import Log


class Method:
    adjust_rate = 0.95

    def __init__(self, name):
        self.name = name
        self.performance = 100
        self.probability = 1

    def reject_method(self):
        self.performance = self.performance * self.adjust_rate

    def execute(self, log, shape_types):

        if self.name == "TUCK":
            tuck(log, shape_types)
        elif self.name == "SWITCH":
            switch(log, shape_types)
        elif self.name == "REPACK":
            repack(log, shape_types)


def tuck(log: Log, shape_types: list):
    pass


def switch(log: Log, shape_types: list):
    pass


def repack(log: Log, shape_types: list):
    pass
