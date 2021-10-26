from Database import queries as q
from matplotlib import pyplot as plt


# standard_graph('Assists Average over time', '_average', 0.65, 1, True, False)


def standard_graph(stat, mode, ymin, ymax, save, show):
    print(q.grph_stat_over_time(0, stat, mode))
    print(q.grph_stat_over_time(1, stat, mode))
    print(q.grph_stat_over_time(2, stat, mode))
    plt.title(mode + ' ' + stat.capitalize() + ' over time')
    plt.xlabel('Games')
    x_axis = [*range(1, q.game_amount() + 1)]
    plt.plot(x_axis, q.grph_stat_over_time(0, stat, mode), color='darkgreen')
    plt.plot(x_axis, q.grph_stat_over_time(1, stat, mode), color='maroon')
    plt.plot(x_axis, q.grph_stat_over_time(2, stat, mode), color='steelblue')
    if ymin is not None or ymax is not None: plt.ylim(ymin, ymax)
    if save: plt.savefig('png/' + stat + "_" + mode)
    if show: plt.show()


if __name__ == '__main__':
    q.init()
    standard_graph('assists', 'AVG', None, None, True, False)
