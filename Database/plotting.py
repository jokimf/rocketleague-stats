from Database import queries as q
from matplotlib import pyplot as plt


def plot_trend():
    data = q.grph_average_goals('assists')
    x = []
    k = []
    p = []
    s = []
    for i in data:
        x.append(i[0])
        k.append(i[1])
        p.append(i[2])
        s.append(i[3])

    standard_graph('Assists Average over time', 'assist_average', 0.65, 1, k, p, s, True, False)


def standard_graph(title, pngname, ymin, ymax, k, p, s, save, show):
    plt.title(title)
    plt.xlabel('Games')
    x_axis = [*range(1, q.game_amount() + 1)]
    plt.plot(x_axis, k, color='darkgreen')
    plt.plot(x_axis, p, color='maroon')
    plt.plot(x_axis, s, color='steelblue')
    plt.ylim(ymin, ymax)
    if save: plt.savefig('png/' + pngname)
    if show: plt.show()


if __name__ == '__main__':
    q.init()
    plot_trend()
