from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.view import view_config
import queries as q
import graphs as g
import random_facts as r


@view_config(
    route_name='data',
    renderer='json'
)
def data(request) -> dict:
    graph: str = request.path.split('/')[2]  # determine graph from request
    return {} if graph not in g.graphs else g.graphs[graph].to_dict()


@view_config(
    route_name='home',
    renderer='../resources/index.jinja2'
)
def serve(request) -> dict:
    max_id = q.max_id()
    return {
        "ranks": q.ranks(),
        "winrates": q.winrates(),
        "random_facts": r.generate_random_facts(),
        "days_since_inception": q.days_since_inception(),
        "total_games": max_id,
        "tilt": 50,  # q.tilt(),
        "last_games": q.last_x_games_stats(5),
        "grand_total": q.general_game_stats_over_time_period(1, max_id),
        "season_data": q.general_game_stats_over_time_period(q.season_start_id(), max_id),
        "session_data": q.general_game_stats_over_time_period(q.session_start_id(), max_id),
        "fun_facts": q.build_fun_facts()
    }


if __name__ == '__main__':
    with Configurator() as config:
        config.include('pyramid_jinja2')
        config.add_route('home', '/')
        config.add_route('data', 'data/{type}')
        config.scan()
        app = config.make_wsgi_app()
    server = make_server('127.0.0.1', 6543, app)
    server.serve_forever()
