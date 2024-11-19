from flask import Flask, redirect, render_template, send_from_directory

import queries as q
import util.data_import as data
from dashboard import Dashboard

app = Flask(__name__)
app.jinja_env.globals.update(cf=q.conditional_formatting, fade=q.fade_highlighting)
currently_reloading = False

dashboard = Dashboard()
dashboard.reload()

@app.route("/rl", methods=["GET"])
def main():
    return render_template("index.html", **dashboard.build_dashboard_context())

@app.route("/rl/records", methods=["GET"])
def records():
    return render_template("records.html", **dashboard.build_record_context())

@app.route("/rl/games", methods=["GET"])
def games():
    return render_template("games.html", **dashboard.build_games_context())

@app.route("/rl/profile/<player_id>", methods=["GET"])
def streaks(player_id: int):
    return render_template("profile.html", **dashboard.build_profile_context(int(player_id)))

@app.route("/rl/reload", methods=["GET"])
def reload():
    global currently_reloading
    global dashboard
    if not currently_reloading:
        currently_reloading = True
        if data.is_new_data_available(dashboard.total_games):
            data.insert_new_data(dashboard)
            dashboard.reload()
            currently_reloading = False
    return redirect("/rl")

@app.route("/rl/static/<filename>", methods=["GET"])
def static_files(filename):
    return send_from_directory("static", filename)

@app.route("/")
def test():
    return redirect("/rl")
