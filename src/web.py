from wsgiref.simple_server import make_server

from pyramid.config import Configurator
from pyramid.view import view_config
from collections.abc import Callable

import queries as q
import random_facts as r


@view_config(
    route_name='data',
    renderer='json'
)
def data(request):
    graph = request.path.split('/')[2]

    # TODO: Fetch graph data
    pfd = q.Graph('PFD', 'line', 0, 10, True, ([23, 61, 11, 34, 66], [4, 33, 21, 40, 10], [55, 44, 22, 30, 10]))
    return pfd.to_dict()


@view_config(
    route_name='home',
    renderer='../resources/home.jinja2'
)
def serve(request):
    max_id = q.max_id()
    data = {"days_since_inception": q.days_since_inception(),
            "total_games": q.max_id(),
            "total_wins": q.total_wins(),
            "games": q.last_x_games_stats(5),
            # "weekdays": q.weekdays(),
            "days": q.dates_table(),
            "months": q.month_table(),
            "years": q.year_table(),
            "grand_total": q.general_game_stats_over_time_period(1, max_id),
            "season_data": q.general_game_stats_over_time_period(2135, max_id),
            "session_data": q.general_game_stats_over_time_period(2165, max_id),
            "performance_data": q.general_game_stats_over_time_period(max_id - 19, max_id),
            # "last_5": q.points_last_5(),
            "record_games": q.build_record_games(),
            "FunFacts": "q.build_fun_facts()",
            "random_facts": r.generate_random_facts()}
    return data


if __name__ == '__main__':
    with Configurator() as config:
        config.include('pyramid_jinja2')
        config.add_route('home', '/')
        config.add_route('css', '/css')
        config.add_route('data', 'data/{type}')
        config.scan()
        app = config.make_wsgi_app()
    server = make_server('0.0.0.0', 6543, app)
    server.serve_forever()
