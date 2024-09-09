import time

from queries import RLQueries
from random_facts import RandomFactQueries
from records import RecordQueries
from streaks import StreakQueries
from graphs import GraphQueries

# RELOADABLE
data = {}

# GLOBALS
K = 'rgba(12,145,30)'
P = 'rgba(151,3,14)'
S = 'rgba(12,52,145)'

# TABLE HIGHLIGHTING
LAST_GAMES_HIGHLIGHTING = [None, None, None, None,
                           (K, 100, 700), (K, 100, 700), (K, 0, 5), (K, 0, 5), (K, 0, 5), (K, 0, 10),
                           (P, 100, 700), (P, 100, 700), (P, 0, 5), (P, 0, 5), (P, 0, 5), (P, 0, 10),
                           (S, 100, 700), (S, 100, 700), (S, 0, 5), (S, 0, 5), (S, 0, 5), (S, 0, 10)]
RANK_HIGHLIGHTING = ['rgb(201, 176, 55, 0.3)', 'rgb(215, 215, 215, 0.3)', 'rgb(173, 138, 86, 0.3)']


def reload():
    q = RLQueries()
    rf = RandomFactQueries()
    r = RecordQueries()
    s = StreakQueries()
    
    q.set_last_reload(int(time.time()))
    data['RANDOM_FACTS'] = rf.generate_random_facts()
    data['FUN_FACTS'] = [] #q.generate_fun_facts()
    data['RECORD_GAMES'] = r.generate_record_games()
    data['STREAK_RECORD_PAGE'] = s.generate_streaks_record_page()
    data['TOTAL_GAMES'] = q.total_games()
    data['LAST_100_GAMES_STATS'] = q.last_x_games_stats(100, True)
    data['SESSION_DETAILS'] = q.session_details()
    data['SESSION_GAMES_AMOUNT'] = len(q.games_from_session_date())
    data['SESSION_GAMES_DETAILS'] = q.last_x_games_stats(data['SESSION_GAMES_AMOUNT'], False)
    data['RANKS'] = q.ranks()
    data['WINRATES'] = q.winrates()
    data['DAYS_SINCE_FIRST'] = q.days_since_first()
    data['TILT'] = q.tilt()
    data['AVERAGE_SESSION_LENGTH'] = q.average_session_length()
    data['GAMES_FROM_SESSION_DATE'] = q.games_from_session_date()
    data['LAST_GAMES'] = q.last_x_games_stats(len(data['GAMES_FROM_SESSION_DATE']), False)
    data['GRAND_TOTAL'] = q.general_game_stats_over_time_period(1, data['TOTAL_GAMES'])
    data['SEASON_DATA'] = q.general_game_stats_over_time_period(q.season_start_id(), data['TOTAL_GAMES'])
    data['SESSION_DATA'] = q.general_game_stats_over_time_period(q.session_start_id(), data['TOTAL_GAMES'])
    data['K_PERFORMANCE'] = q.performance_profile_view(0)
    data['P_PERFORMANCE'] = q.performance_profile_view(1)
    data['S_PERFORMANCE'] = q.performance_profile_view(2)
    data['WEBSITE_DATE'] = q.website_date()
    data['LATEST_SESSION_DATE'] = data['SESSION_DETAILS']['latest_session_date']
    data['W_AND_L'] = data['SESSION_DETAILS']['w_and_l']
    data['SESSION_GAME_COUNT'] = data['SESSION_DETAILS']['session_game_count']
    data['JUST_OUT'] = q.just_out()
    data['PERFORMANCE_SCORE'] = q.performance_score()
    data['TO_BEAT_NEXT'] = q.to_beat_next()
    data['SEASONS'] = q.seasons_dashboard_short()
    data['LAST_RELOAD'] = q.last_reload()
    data['PROFILE_STREAKS'] = [s.generate_profile_streaks(p) for p in [0, 1, 2]]
    data['SESSION_INFORMATION'] = rf.session_data_by_date(data['LATEST_SESSION_DATE'])

def build_context():
    g = GraphQueries()
    context = {
        "ranks": data.get('RANKS'),
        "winrates": data.get('WINRATES'),
        "random_facts": data.get('RANDOM_FACTS'),
        "days_since_first": data.get('DAYS_SINCE_FIRST'),
        "total_games": data.get('TOTAL_GAMES'),
        "tilt": data.get('TILT'),
        "average_session_length": data.get('AVERAGE_SESSION_LENGTH'),
        "last_games": data.get('SESSION_GAMES_DETAILS'),
        "last_games_highlighting": LAST_GAMES_HIGHLIGHTING,
        "grand_total": data.get('GRAND_TOTAL'),
        "season_data": data.get('SEASON_DATA'),
        "session_data": data.get('SESSION_DATA'),
        "fun_facts": data.get('FUN_FACTS'),
        "k_perf": data.get('K_PERFORMANCE'),
        "p_perf": data.get('P_PERFORMANCE'),
        "s_perf": data.get('S_PERFORMANCE'),
        "website_date": data.get('WEBSITE_DATE'),
        "latest_session_date": data.get('LATEST_SESSION_DATE'),
        "w_and_l": data.get('W_AND_L'),
        "session_game_count": data.get('SESSION_GAME_COUNT'),
        "just_out": data.get('JUST_OUT'),
        "performance_score": data.get('PERFORMANCE_SCORE'),
        "to_beat_next": data.get('TO_BEAT_NEXT'),
        "seasons": data.get('SEASONS'),
        "session_information": data.get('SESSION_INFORMATION'),

        "players": [
            {"name":"Knus", "rank": data.get('RANKS')[0], "performance": data.get("PERFORMANCE_SCORE")[0]},
            {"name":"Puad", "rank": data.get('RANKS')[1], "performance": data.get("PERFORMANCE_SCORE")[1]},
            {"name":"Sticker", "rank": data.get('RANKS')[2], "performance": data.get("PERFORMANCE_SCORE")[2]}
        ],
        "performance_graph": g.performance_graph(),
        "days_graph": g.dates_table(),
        "heatmap": g.results_table()
    }
    return context