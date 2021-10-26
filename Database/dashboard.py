from Database import queries as q

def print_dashboard():
    print('Last 10 games')
    for game in q.allgemeine_game_stats(10):
        print(game)

    print('This life')
    print('Games: ' + str(q.game_amount()) + ' Goals F/A: ' + str(q.sum_of_game_stat('goals')) + '/' + str(
        q.sum_of_game_stat('against')) + ' W/L: ' + str(q.total_wins()) + '/' + str(q.total_losses()))


if __name__ == '__main__':
    q.init()
    print_dashboard()
