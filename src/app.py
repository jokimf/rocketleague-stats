import logging

from flask import Flask, redirect, render_template, send_from_directory
from waitress import serve
from queries import Utility

import dashboard

app = Flask(__name__)
app.jinja_env.globals.update(cf=Utility.conditional_formatting, fade=Utility.fade_highlighting)
d = dashboard.Dashboard()


@app.route("/rl", methods=["GET"])
def main():
    return render_template("index.html", **d.build_dashboard_context())


@app.route("/rl/records", methods=["GET"])
def records():
    return render_template("records.html", **d.build_record_context())


@app.route("/rl/games", methods=["GET"])
def games():
    return render_template("games.html", **d.build_games_context())


@app.route("/rl/profile/<player_id>", methods=["GET"])
def streaks(player_id: int):
    return render_template("profile.html", **d.build_profile_context(int(player_id)))


@app.route("/rl/reload", methods=["GET"])
def reload():
    d.reload_all_stats()
    return redirect("/rl")


@app.route("/rl/static/<filename>", methods=["GET"])
def static_files(filename):
    return send_from_directory("static", filename)


@app.route("/")
def test():
    return redirect("/rl")


if __name__ == "__main__":
    logger = logging.getLogger("waitress")
    logger.setLevel(logging.INFO)
    serve(app, listen="*:7823", url_scheme="https")
