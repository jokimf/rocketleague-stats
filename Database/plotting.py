from Database import queries as q
from matplotlib import pyplot as plt

if __name__ == '__main__':
    q.init()
    illo = False
    if illo:
        data = q.performance_agg('score', 'AVG', games_considered=20)

        names = ([data[0][0], data[1][0], data[2][0]])
        stats = ([data[0][1], data[1][1], data[2][1]])

        plt.title('Trend')
        plt.xlabel('Player')
        plt.ylabel('Score')

        plt.bar(names, stats)
        plt.show()

    print(q.player_stats('goals', 'AVG'))
