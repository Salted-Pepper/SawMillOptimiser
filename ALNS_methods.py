from logs import Log


class Method:
    adjust_rate = 0.95

    def __init__(self, name):
        self.name = name
        self.performance = 100
        self.probability = 1

    def reject_method(self):
        self.performance = self.performance * self.adjust_rate

    def execute(self, log):

        if self.name == "TUCK":
            tuck(log)
        elif self.name == "SWITCH":
            switch(log)
        elif self.name == "REPACK":
            repack(log)


def tuck(log: Log):
    pass


def switch(log: Log):
    pass


def repack(log: Log):
    pass
