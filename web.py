from flask import Flask
from flask import render_template
from flask import jsonify

import fetch_from_google
import graphs as g
import queries as q
import random_facts as r

app = Flask(__name__)


@app.route('/data/<graph>')
def data(graph):
    '''
    new_graphs = {'goals_heatmap': g.goal_heatmap()}
    if graph in new_graphs:
        return new_graphs[graph]
    else:
        return {} if graph not in g.graphs else g.graphs[graph].to_dict()
    '''
    results_table = {
        'data': q.results_table(),
        'labels': [1, 2, 3, 4, 5]
    }
    return results_table


@app.route('/')
def main():
    fetch_from_google.fetch_from_sheets()
    max_id = q.max_id()
    session_details = q.session_details()
    last_games = q.last_x_games_stats(len(q.games_from_session_date()))
    k, p, s = 'rgba(12,145,30)', 'rgba(151,3,14)', 'rgba(12,52,145)'
    context = {
        "hhh": "cyan",
        "ranks": q.ranks(),
        "winrates": q.winrates(),
        "random_facts": r.random_facts,
        "days_since_inception": q.days_since_inception(),
        "total_games": max_id,
        "tilt": q.tilt(),
        "average_session_length": q.average_session_length(),
        "last_games": last_games,
        "last_games_highlighting": [None, None, None, None, None,
                                    (k, 100, 700), (k, 0, 5), (k, 0, 5), (k, 0, 5),
                                    (k, 0, 10), None, (p, 100, 700), (p, 0, 5), (p, 0, 5), (p, 0, 5), (p, 0, 10),
                                    None, (s, 100, 700), (s, 0, 5), (s, 0, 5), (s, 0, 5), (s, 0, 10)],
        "grand_total": q.general_game_stats_over_time_period(1, max_id),
        "season_data": q.general_game_stats_over_time_period(q.season_start_id(), max_id),
        "session_data": q.general_game_stats_over_time_period(q.session_start_id(), max_id),
        "fun_facts": q.build_fun_facts(),
        "knus_performance": q.performance_profile_view(0),
        "puad_performance": q.performance_profile_view(1),
        "st_performance": q.performance_profile_view(2),
        "website_date": q.website_date(),
        "latest_session_date": session_details['latest_session_date'],
        "w_and_l": session_details['w_and_l'],
        "session_game_count": session_details['session_game_count']
    }
    return render_template('index.jinja2', **context)


@app.route('/graphs')
def graphs():
    return render_template('graphs.jinja2')


@app.route('/records')
def records():
    record_games = q.build_record_games()
    context = {
        'record_games': record_games[0],
        'record_games2': record_games[1]
    }
    return render_template('records.jinja2', **context)


@app.route('/games')
def games():
    return render_template('games.jinja2')


if __name__ == '__main__':
    app.jinja_env.globals.update(conditional_formatting=q.conditional_formatting)
    app.run(host='127.0.0.1', port=6543)
