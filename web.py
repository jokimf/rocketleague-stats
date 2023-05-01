from flask import Flask
from flask import render_template

import cache as c
import queries
import data_import
import time

app = Flask(__name__)


@app.route('/data/<graph>')
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


def build_context():
    context = {
        "ranks": c.data.get('RANKS'),
        "winrates": c.data.get('WINRATES'),
        "random_facts": c.data.get('RANDOM_FACTS'),
        "days_since_first": c.data.get('DAYS_SINCE_FIRST'),
        "total_games": c.data.get('TOTAL_GAMES'),
        "tilt": c.data.get('TILT'),
        "average_session_length": c.data.get('AVERAGE_SESSION_LENGTH'),
        "last_games": c.data.get('SESSION_GAMES_DETAILS'),
        "last_games_highlighting": c.LAST_GAMES_HIGHLIGHTING,
        "grand_total": c.data.get('GRAND_TOTAL'),
        "season_data": c.data.get('SEASON_DATA'),
        "session_data": c.data.get('SESSION_DATA'),
        "fun_facts": c.data.get('FUN_FACTS'),
        "k_perf": c.data.get('K_PERFORMANCE'),
        "p_perf": c.data.get('P_PERFORMANCE'),
        "s_perf": c.data.get('S_PERFORMANCE'),
        "website_date": c.data.get('WEBSITE_DATE'),
        "latest_session_date": c.data.get('LATEST_SESSION_DATE'),
        "w_and_l": c.data.get('W_AND_L'),
        "session_game_count": c.data.get('SESSION_GAME_COUNT'),
        "just_out": c.data.get('JUST_OUT'),
        "performance_score": c.data.get('PERFORMANCE_SCORE'),
        "to_beat_next": c.data.get('TO_BEAT_NEXT'),
        "seasons": c.data.get('SEASONS')
    }
    return context


@app.route('/')
def main():
    # Check cooldown
    if not c.data.get('LAST_RELOAD') + 15 > int(time.time()) and data_import.new_data_available():
        data_import.insert_new_data()
        c.reload()
    return render_template('index.jinja2', **build_context())


@app.route('/graphs')
def graphs():
    return render_template('graphs.jinja2')


@app.route('/records')
def records():  # TODO: Highlight records that happened not long ago
    context = {
        'record_games': c.data.get('RECORD_GAMES'),
        'record_headlines': ['Most stat by player in one game', 'Highest performance by player',
                             'Lowest performance by player',
                             'Most stat by team', 'Goal stats by team', 'Points stats', 'Miscellaneous'],
        'rank_highlighting': ['rgb(201, 176, 55, 0.3)', 'rgb(215, 215, 215, 0.3)', 'rgb(173, 138, 86, 0.3)'],
        'k': 'rgba(12,145,30,0.2)',
        'p': 'rgba(151,3,14,0.2)',
        's': 'rgba(12,52,145,0.2)',
        'cg': 'rgba(255, 225, 0, 0.2)'
    }
    return render_template('records.jinja2', **context)


@app.route('/games')
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
    return render_template('games.jinja2', **ctx)


if __name__ == '__main__':
    app.jinja_env.globals.update(cf=queries.conditional_formatting)
    c.reload()  # Load all data into memory
    app.run(host='127.0.0.1', port=6543)
