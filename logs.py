import math

import matplotlib.pyplot as plt


class Log:
    def __init__(self, diameter: float):
        self.diameter = diameter
        self.recovery_rate = None
        self.volume = math.pi * (diameter / 2) ** 2
        self.volume_used = 0
        self.fig = None
        self.ax = None

    def plot_log(self):
        fig, ax = plt.subplots(figsize=(9, 9))
        circle = plt.Circle((self.diameter * 1.05 / 2, self.diameter * 1.05 / 2), self.diameter / 2,
                            color='saddlebrown', fill=False)
        ax.add_patch(circle)
        ax.set_xlim(0, 1.1 * self.diameter)
        ax.set_ylim(0, 1.1 * self.diameter)
        self.fig = fig
        self.ax = ax

    def calculate_edge_positions_on_circle(self, x: float) -> tuple:
        r = self.diameter / 2
        y_min = r - math.sqrt(r**2 - (x-r)**2)
        y_plus = r + math.sqrt(r**2 - (x-r)**2)
        return y_min, y_plus
