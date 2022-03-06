from wsgiref.simple_server import make_server

from pyramid.config import Configurator
from pyramid.view import view_config

import queries as q


@view_config(
    route_name='home',
    renderer='../resources/home.jinja2'
)
def serve(request):
    max_id = q.max_id()
    data = {"days_since_inception": q.days_since_inception(),
            "total_games": q.max_id(),
            "total_wins": q.total_wins(),
            "games": q.last_x_games_stats(10),
            # "weekdays": q.weekdays(),
            "days": q.dates(),
            "months": q.months(),
            "years": q.years(),
            "grand_total": q.general_game_stats_over_time_period(1, max_id),
            "season_data": q.general_game_stats_over_time_period(2135, max_id),
            "session_data": q.general_game_stats_over_time_period(2165, max_id),
            "performance_data": q.general_game_stats_over_time_period(max_id - 19, max_id),
            # "last_5": q.points_last_5(),
            "record_games": q.build_record_games(),
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
