from flask import Flask
from flask import render_template

import fetch_from_google
import queries as q
import random_facts as r

app = Flask(__name__)

# TODO: Highligh MVP player in SESSION DETAILS
# TODO: Session stats


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


def fetch_data():
    k, p, s = 'rgba(12,145,30)', 'rgba(151,3,14)', 'rgba(12,52,145)'
    fetch_from_google.fetch_from_sheets()
    max_id = q.max_id()
    session_details = q.session_details()
    last_games = q.last_x_games_stats(len(q.games_from_session_date()))

    context = {
        "ranks": q.ranks(),
        "winrates": q.winrates(),
        "random_facts": r.random_facts,
        "days_since_inception": q.days_since_inception(),
        "total_games": max_id,
        "tilt": q.tilt(),
        "average_session_length": q.average_session_length(),
        "last_games": last_games,
        "last_games_highlighting": [None, None, None, None, (k, 100, 700),
                                    (k, 100, 700), (k, 0, 5), (k, 0, 5), (k, 0, 5),
                                    (k, 0, 10), (p, 100, 700), (p, 100, 700), (p, 0, 5), (p, 0, 5), (p, 0, 5), (p, 0, 10),
                                    (s, 100, 700), (s, 100, 700), (s, 0, 5), (s, 0, 5), (s, 0, 5), (s, 0, 10)],
        "grand_total": q.general_game_stats_over_time_period(1, max_id),
        "season_data": q.general_game_stats_over_time_period(q.season_start_id(), max_id),
        "session_data": q.general_game_stats_over_time_period(q.session_start_id(), max_id),
        "fun_facts": q.build_fun_facts(),
        "k_perf": q.performance_profile_view(0),
        "p_perf": q.performance_profile_view(1),
        "s_perf": q.performance_profile_view(2),
        "website_date": q.website_date(),
        "latest_session_date": session_details['latest_session_date'],
        "w_and_l": session_details['w_and_l'],
        "session_game_count": session_details['session_game_count'],
        "just_out": q.just_out(),
        "performance_score": q.performance_score(),
        "to_beat_next": q.to_beat_next()
    }
    return context


@app.route('/')
def main():
    return render_template('index.jinja2', **fetch_data())


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
    app.jinja_env.globals.update(cf=q.conditional_formatting)
    app.run(host='127.0.0.1', port=6543)
