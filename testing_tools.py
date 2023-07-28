import math
import matplotlib.pyplot as plt


def plot_log(diameter, x, y, h=0, w=0) -> None:
    fig, ax = plt.subplots(figsize=(9, 9))
    circle = plt.Circle((diameter / 2, diameter / 2), diameter / 2,
                        color='saddlebrown', fill=False)
    ax.add_patch(circle)
    ax.scatter(x, y, c="red")
    ax.scatter(x + w, y, c="red")
    ax.scatter(x, y + h, c="red")
    ax.scatter(x + w, y + h, c="red")
    ax.set_xlim(0, 1.1 * diameter)
    ax.set_ylim(0, 1.1 * diameter)
