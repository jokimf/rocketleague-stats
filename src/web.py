import time

from flask import Flask, redirect, render_template, send_from_directory

import cache as c
import data_import
import queries as q

app = Flask(__name__)
app.jinja_env.globals.update(cf=q.conditional_formatting, fade=q.fade_highlighting)
c.reload()  # Load all data into memory

@app.route('/rl')
def main():
    # Check cooldown
    if not c.data.get('LAST_RELOAD') + 15 > int(time.time()) and data_import.new_data_available():
        data_import.insert_new_data()
        c.reload()
    return render_template('index.html', **c.build_context())


@app.route('/rl/graphs')
def graphs():
    return render_template('graphs.html')


@app.route('/rl/records')
def records():
    context = {
        'record_games': c.data.get('RECORD_GAMES'),
        'record_headlines': ['Most stat by player in one game',
                             'Highest performance by player',
                             'Lowest performance by player',
                             'Most stat by team',
                             'Goal stats by team',
                             'Points stats',
                             'Miscellaneous'],
        'rank_highlighting': c.RANK_HIGHLIGHTING,
        'k': 'rgba(12,145,30,0.2)',
        'p': 'rgba(151,3,14,0.2)',
        's': 'rgba(12,52,145,0.2)',
        'cg': 'rgba(255, 225, 0, 0.2)',
        'streaks': c.data.get('STREAK_RECORD_PAGE'),
        'latest': c.data.get('TOTAL_GAMES'),
    }
    return render_template('records.html', **context)


@app.route('/rl/profile/<player_id>')
def streaks(player_id: int):
    player_id = int(player_id)
    ctx = {
        'name': ['Knus', 'Puad', 'Sticker'][player_id],
        'streaks': c.data.get('PROFILE_STREAKS')[player_id],
        'rank_highlighting': c.RANK_HIGHLIGHTING,
    }
    return render_template('profile.html', **ctx)


@app.route('/rl/games')
def games():
    k, p, s = c.K, c.P, c.S
    ctx = {
        'games': c.data.get('LAST_100_GAMES_STATS'),
        "last_games_highlighting": [None, None, None, None, None, (k, 100, 700),
                                    (k, 100, 700), (k, 0, 5), (k, 0, 5),
                                    (k, 0, 5),
                                    (k, 0, 10), (p, 100, 700),
                                    (p, 100, 700), (p, 0, 5), (p, 0, 5),
                                    (p, 0, 5),
                                    (p, 0, 10),
                                    (s, 100, 700), (s, 100, 700),
                                    (s, 0, 5), (s, 0, 5), (s, 0, 5),
                                    (s, 0, 10)]
    }
    return render_template('games.html', **ctx)

@app.route('/rl/data/<graph>')
def data(graph):
    """
    new_graphs = {'goals_heatmap': g.goal_heatmap()}
    if graph in new_graphs:
        return new_graphs[graph]
    else:
        return {} if graph not in g.graphs else g.graphs[graph].to_dict()
    """
    results_table = {
        'data': q.results_table(),
        'labels': [1, 2, 3, 4, 5]
    }
    return results_table

@app.route('/rl/static/<filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/')
def test():
    return redirect('/rl')
