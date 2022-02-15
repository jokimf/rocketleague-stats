from matplotlib import pyplot as plt
import queries as q

data = q.performance_agg('score', 'AVG', games_considered=60)

names = ([data[0][0], data[1][0], data[2][0]])
stats = ([data[0][1], data[1][1], data[2][1]])
print(names, stats)
plt.title('Trend')
plt.xlabel('Player')
plt.ylabel('Score')

plt.bar(names, stats)
plt.show()
