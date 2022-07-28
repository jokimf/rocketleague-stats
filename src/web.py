from wsgiref.simple_server import make_server

from pyramid.config import Configurator
from pyramid.view import view_config
from collections.abc import Callable

import queries as q
import random_facts as r


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


def generate_graphs(graph: str, function: Callable, is_kps: bool) -> dict:
    function_data = function
    if is_kps:
        graph_data = {f"{graph}_title": function_data[0],
                      f"{graph}_xmin": function_data[1],
                      f"{graph}_xmax": function_data[2],
                      f"{graph}_k": function_data[3],
                      f"{graph}_p": function_data[4],
                      f"{graph}_s": function_data[5],
                      }
    else:
        graph_data = {f"{graph}_title": function_data[0],
                      f"{graph}_xmin": function_data[1],
                      f"{graph}_xmax": function_data[2],
                      f"{graph}_data": function_data[3],
                      }
    return graph_data


@view_config(
    route_name='css',
    renderer='../resources/charts.jinja2'
)
def ja(request):  # TODO more performance graphs
    performance = generate_graphs('performance', q.graph_performance('score'), True)
    total_performance = generate_graphs('total_performance', q.graph_total_performance('score'), True)
    grief_value = generate_graphs('grief', q.graph_grief_value(), True)
    winrate_last_20 = generate_graphs('winrate_last20', q.graph_winrate_last20(), False)
    winrate = generate_graphs('winrate', q.graph_winrate(), False)
    solo_goals = generate_graphs('solo', q.graph_solo_goals(), True)
    performance_share = generate_graphs('peformance_share', q.graph_performance_share('score'), True)
    mvp_lvp_share = generate_graphs('mvp_lvp', q.graph_average_mvp_score_over_time(), True)  # TODO Implement LVP
    cumulative_stat = generate_graphs('cumulative_stat', q.graph_cumulative_stat_over_time('score'), True)

    merged = {**performance, **total_performance, **grief_value, **winrate_last_20, **winrate, **solo_goals,
              **performance_share, **mvp_lvp_share, **cumulative_stat}
    return merged


if __name__ == '__main__':
    with Configurator() as config:
        config.include('pyramid_jinja2')
        config.add_route('home', '/')
        config.add_route('css', '/css')
        config.add_route('test', '/test')
        config.scan()
        app = config.make_wsgi_app()
    server = make_server('0.0.0.0', 6543, app)
    server.serve_forever()
