from wsgiref.simple_server import make_server

import pyramid.response
from pyramid.config import Configurator
from pyramid.view import view_config

import fetch_from_google
import graphs as g
import queries as q
import random_facts as r


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
    fetch_from_google.fetch_from_sheets()
    max_id = q.max_id()
    record_games = q.build_record_games()
    session_details = q.session_details()
    return {
        "ranks": q.ranks(),
        "winrates": q.winrates(),
        "random_facts": r.random_facts,
        "days_since_inception": q.days_since_inception(),
        "total_games": max_id,
        "tilt": q.tilt(),
        "average_session_length": q.average_session_length(),
        "last_games": q.last_x_games_stats(5),
        "grand_total": q.general_game_stats_over_time_period(1, max_id),
        "season_data": q.general_game_stats_over_time_period(q.season_start_id(), max_id),
        "session_data": q.general_game_stats_over_time_period(q.session_start_id(), max_id),
        "fun_facts": q.build_fun_facts(),
        "record_games": record_games[0],
        "record_games2": record_games[1],
        "knus_performance": q.performance_profile_view(0),
        "puad_performance": q.performance_profile_view(1),
        "st_performance": q.performance_profile_view(2),
        "website_date": q.website_date(),
        "latest_session_date": session_details['latest_session_date'],
        "w_and_l": session_details['w_and_l'],
        "session_game_count": session_details['session_game_count']
    }


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
        config.add_route('data', 'data/{type}')
        config.add_route('img', 'img/{img}')
        config.add_route('static', 'static/{file}')
        config.scan()
        app = config.make_wsgi_app()
    server = make_server('127.0.0.1', 6543, app)
    server.serve_forever()
