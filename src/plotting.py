from matplotlib import pyplot as plt
import queries as q

data = q.graph_performance('goals')

print(data)
plt.title('Trend')
plt.xlabel('Player')
plt.ylabel('Score')
plt.xlim(data[1], data[2])
plt.bar(data[3])
# plt.bar(names, stats)
plt.show()
