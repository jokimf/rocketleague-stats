import queries as q
from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.view import view_config


@view_config(
    route_name='home',
    renderer='../resources/home.jinja2'
)
def serve(request):
    total_games = q.total_games()
    data = {"days_since_inception": 0,
            "total_games": total_games,
            "total_wins": q.total_wins(),
            "games": q.last_x_games_stats(10),
            "weekdays": "q.weekdays()",
            "grand_total": q.general_game_stats_over_time_period(1, q.max_id()),
            "season_data": q.general_game_stats_over_time_period(2135, q.max_id()),
            "session_data": q.general_game_stats_over_time_period(2165, q.max_id()),
            "last_5": q.points_last_5(),
            "FunFacts": q.build_fun_facts()}
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
