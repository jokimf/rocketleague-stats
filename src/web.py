from flask import Flask, redirect, render_template, send_from_directory

import cache as c
import data_import
import queries as q
from graphs import DatasetColor, GraphBuilder, GraphQueries

app = Flask(__name__)
app.jinja_env.globals.update(cf=q.conditional_formatting, fade=q.fade_highlighting)
c.reload()  # Load all data into memory
currently_reloading = False

@app.route("/rl", methods=['GET'])
def main():
    return render_template("index.html", **c.build_context())

@app.route("/rl/graphs", methods=["GET"])
def graphs():
    return render_template("graphs.html")


@app.route("/rl/records", methods=["GET"])
def records():
    context = {
        "record_games": c.data.get("RECORD_GAMES"),
        "record_headlines": ["Most stat by player in one game",
                             "Highest performance by player",
                             "Lowest performance by player",
                             "Most stat by team",
                             "Goal stats by team",
                             "Points stats",
                             "Miscellaneous"],
        'rank_highlighting': c.RANK_HIGHLIGHTING,
        'k': 'rgba(12,145,30,0.2)',
        'p': 'rgba(151,3,14,0.2)',
        's': 'rgba(12,52,145,0.2)',
        'cg': 'rgba(255, 225, 0, 0.2)',
        'streaks': c.data.get('STREAK_RECORD_PAGE'),
        'latest': c.data.get('TOTAL_GAMES'),
    }
    return render_template('records.html', **context)


@app.route('/rl/profile/<player_id>', methods=['GET'])
def streaks(player_id: int):
    player_id = int(player_id)
    ctx = {
        'name': ['Knus', 'Puad', 'Sticker'][player_id],
        'streaks': c.data.get('PROFILE_STREAKS')[player_id],
        'rank_highlighting': c.RANK_HIGHLIGHTING,
    }
    return render_template('profile.html', **ctx)


@app.route('/rl/games', methods=['GET'])
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

@app.route("/rl/reload", methods=["GET"])
def reload():
    global currently_reloading
    if not currently_reloading:
        currently_reloading = True
        if data_import.new_data_available():
            data_import.insert_new_data()
            c.reload()
            currently_reloading = False
    return redirect("/rl")

@app.route('/rl/data/<graph>', methods=['GET'])
def data(graph):
    g = GraphQueries()
    graph_lookup = {
        "performance_knus":  g.performance_graph(),
        "days": g.days_graph(),
    }
    graph_data = graph_lookup.get(graph)
    return graph_data

@app.route('/rl/static/<filename>', methods=['GET'])
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/')
def test():
    return redirect('/rl')
