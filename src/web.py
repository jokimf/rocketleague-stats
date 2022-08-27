from wsgiref.simple_server import make_server

import pyramid.response
from pyramid.config import Configurator
from pyramid.view import view_config

import graphs as g
import queries as q
import random_facts as r


# TODO: Links ändern zu rlstats/XD
@view_config(
    route_name='data',
    renderer='json'
)
def data(request) -> dict:
    graph: str = request.path.split('/')[2]  # determine graph from request
    return {} if graph not in g.graphs else g.graphs[graph].to_dict()


@view_config(
    route_name='main',
    renderer='../resources/index.jinja2'
)
def main(request) -> dict:
    max_id = q.max_id()
    return {
        "ranks": q.ranks(),
        "winrates": q.winrates(),
        "random_facts": r.generate_random_facts(),
        "days_since_inception": q.days_since_inception(),
        "total_games": max_id,
        "tilt": q.tilt(),
        "average_session_length": q.average_session_length(),
        "last_games": q.last_x_games_stats(5),
        "grand_total": q.general_game_stats_over_time_period(1, max_id),
        "season_data": q.general_game_stats_over_time_period(q.season_start_id(), max_id),
        "session_data": q.general_game_stats_over_time_period(q.session_start_id(), max_id),
        "fun_facts": q.build_fun_facts()
    }


@view_config(
    route_name='insert'
)
def insert_get(request):
    request_data = request.params
    if not request_data or q.insert_game_data(request_data):
        return pyramid.response.FileResponse('../resources/insert.html')
    else:
        return pyramid.response.FileResponse('../resources/insert_error.html')


@view_config(
    route_name='img'
)
def img(request):
    image = request.path.split('/')[2]
    return pyramid.response.FileResponse(f'../resources/img/{image}')


@view_config(
    route_name='static'
)
def static(request):
    file = request.path.split('/')[2]
    return pyramid.response.FileResponse(f'../resources/{file}')


if __name__ == '__main__':
    with Configurator() as config:
        config.include('pyramid_jinja2')
        config.add_route('main', '/')
        config.add_route('insert', 'insert')
        config.add_route('data', 'data/{type}')
        config.add_route('img', 'img/{img}')
        config.add_route('static', 'static/{file}')
        config.scan()
        app = config.make_wsgi_app()
    server = make_server('127.0.0.1', 6543, app)
    server.serve_forever()
