import matplotlib.pyplot as plt


def plot_log(diameter, x, y, w=0, h=0, title_text="") -> None:
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
    ax.set_title(title_text)


def select_shape_from_list_by_id(shapes, shape_id):
    return [s for s in shapes if s.shape_id == shape_id][0]
