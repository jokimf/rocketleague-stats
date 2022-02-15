from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.view import view_config
import queries as q


def hello_world(request):
    data = open("../resources/index.html").read()
    return Response(data)


@view_config(
    route_name='home',
    renderer='../resources/home.jinja2'
)
def serve(request):
    data = {}
    total_games = q.total_games()
    data["days_since_inception"] = 0
    data["total_games"] = total_games
    data["total_wins"] = q.total_wins()
    data["games"] = q.allgemeine_game_stats(10)
    data["weekdays"] = "XD"
    data["grand_total"] = q.general_game_stats_over_time_period(1, total_games)
    data["season_data"] = q.general_game_stats_over_time_period(2135, total_games)
    data["session_data"] = q.general_game_stats_over_time_period(2165, total_games)
    return data


if __name__ == '__main__':
    with Configurator() as config:
        config.include('pyramid_jinja2')
        config.add_route('home', '/')
        config.scan()
        # config.add_view(hello_world, route_name='home')
        app = config.make_wsgi_app()
    server = make_server('0.0.0.0', 6543, app)
    server.serve_forever()
