from Database import queries as q
from matplotlib import pyplot as plt


def standard_graph(stat, mode, ymin, ymax, save, show, xmax):
    plt.title(mode + ' ' + stat.capitalize() + ' over time')
    plt.xlabel('Games')

    plt.figure(figsize=(16, 4), dpi=100)
    plt.gca().xaxis.set_major_locator(plt.MultipleLocator(100))
    plt.xlim(0, xmax)
    plt.grid()

    x_axis = [*range(1, q.game_amount() + 1)]
    plt.plot(x_axis, q.grph_stat_over_time(0, stat, mode), color='darkgreen')
    plt.plot(x_axis, q.grph_stat_over_time(1, stat, mode), color='maroon')
    plt.plot(x_axis, q.grph_stat_over_time(2, stat, mode), color='steelblue')
    if ymin is not None or ymax is not None: plt.ylim(ymin, ymax)
    if save: plt.savefig('png/' + stat + "_" + mode)
    if show: plt.show()
    plt.close()


def trend_graph(stat, mode, trend, ymin, ymax, save, show, xmax):
    plt.title('Trend ' + mode + ' ' + stat.capitalize() + ' over last ' + str(trend) + ' games')
    plt.xlabel('Games')

    plt.figure(figsize=(16, 4), dpi=100)
    plt.gca().xaxis.set_major_locator(plt.MultipleLocator(100))
    plt.xlim(0, xmax)
    plt.grid()

    x_axis = [*range(1, q.game_amount() + 1)]
    plt.plot(x_axis, q.grph_trend_over_time(0, stat, mode, trend), color='darkgreen')
    plt.plot(x_axis, q.grph_trend_over_time(1, stat, mode, trend), color='maroon')
    plt.plot(x_axis, q.grph_trend_over_time(2, stat, mode, trend), color='steelblue')
    if ymin is not None or ymax is not None: plt.ylim(ymin, ymax)
    if save: plt.savefig('png/' + stat + "_" + mode + "_trend" + str(trend))
    if show: plt.show()
    plt.close()


def mass_produce():
    for mode in ['AVG', 'SUM', 'MAX', 'MIN']:
        for stat in ['score', 'goals', 'assists', 'saves', 'shots']:
            for amount in [20, 50, 100]:
                trend_graph(stat, mode, amount, None, None, True, False, q.game_amount() + 1)
            standard_graph(stat, mode, None, None, True, False, q.game_amount() + 1)


if __name__ == '__main__':
    q.init()
    mass_produce()

    # TODO: Calculate yMin and yMax based on values
