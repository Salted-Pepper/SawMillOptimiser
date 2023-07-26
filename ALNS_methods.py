class Method:
    adjust_rate = 0.95

    def __init__(self, name):
        self.name = name
        self.performance = 100
        self.probability = 1

    def reject_method(self):
        self.performance = self.performance * self.adjust_rate

    def execute(self):

        if self.name == ""