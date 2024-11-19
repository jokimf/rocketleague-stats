import time

from graphs import GraphQueries
from queries import RLQueries
from randomfacts import RandomFactQueries
from records import RecordQueries
from streaks import StreakQueries


class Dashboard:
    def __init__(self) -> None:
        self.q = RLQueries()
        self.rf = RandomFactQueries()
        self.r = RecordQueries()
        self.sq = StreakQueries()
        self.g = GraphQueries()

        self.RANK_HIGHLIGHTING = ['rgb(201, 176, 55, 0.3)', 'rgb(215, 215, 215, 0.3)', 'rgb(173, 138, 86, 0.3)']
        self.K = 'rgba(12,145,30)'
        self.Ktransparent = 'rgba(12,145,30,0.2)'
        self.P = 'rgba(151,3,14)'
        self.Ptransparent = 'rgba(151,3,14,0.2)'
        self.S = 'rgba(12,52,145)'
        self.Stransparent = 'rgba(12,52,145,0.2)'
        self.LAST_GAMES_HIGHLIGHTING = [
            None, None, None, None,
            (self.K, 100, 700), (self.K, 100, 700), (self.K, 0, 5), (self.K, 0, 5), (self.K, 0, 5), (self.K, 0, 10),
            (self.P, 100, 700), (self.P, 100, 700), (self.P, 0, 5), (self.P, 0, 5), (self.P, 0, 5), (self.P, 0, 10),
            (self.S, 100, 700), (self.S, 100, 700), (self.S, 0, 5), (self.S, 0, 5), (self.S, 0, 5), (self.S, 0, 10)
        ]

    def reload(self) -> None:
        self.q.set_last_reload(int(time.time()))
        self.random_facts = self.rf.generate_random_facts()
        self.fun_facts = [] #q.generate_fun_facts()
        self.record_games = self.r.generate_record_games()
        self.streaks_record = self.sq.generate_streaks_record_page()
        self.profile_streaks = [self.sq.generate_profile_streaks(p) for p in [0, 1, 2]]
        self.total_games = self.q.total_games()
        self.last_100_games_stats = self.q.last_x_games_stats(100, True)
        self.session_details = self.q.session_details()
        self.session_game_amount = len(self.q.games_from_session_date())
        self.session_game_details = self.q.last_x_games_stats(self.session_game_amount, False)
        self.ranks = self.q.ranks()
        self.winrates = self.q.winrates()
        self.days_since_first = self.q.days_since_first_game()
        self.tilt = self.q.tilt()
        self.average_session_length = self.q.average_session_length()
        self.games_from_session_date = self.q.games_from_session_date()
        self.last_games = self.q.last_x_games_stats(len(self.games_from_session_date), False)
        self.grand_total = self.q.general_game_stats_over_time_period(1, self.total_games)
        self.season_data = self.q.general_game_stats_over_time_period(self.q.season_start_id(), self.total_games)
        self.session_data = self.q.general_game_stats_over_time_period(self.q.session_start_id(), self.total_games)
        self.k_performance = self.q.performance_profile_view(0)
        self.p_performance = self.q.performance_profile_view(1)
        self.s_performance = self.q.performance_profile_view(2)
        self.website_date = self.q.website_date()
        self.latest_session_date = self.session_details['latest_session_date']
        self.w_and_l = self.session_details['w_and_l']
        self.session_game_count = self.session_details['session_game_count']
        self.just_out = self.q.just_out()
        self.performance_score = self.q.performance_score()
        self.to_beat_next = self.q.to_beat_next()
        self.seasons = self.q.seasons_dashboard_short()
        self.last_reload = self.q.last_reload()
        self.session_information = self.rf.session_data_by_date(self.latest_session_date)

    def build_dashboard_context(self):
        context = {
            "ranks": self.ranks,
            "winrates": self.winrates,
            "random_facts": self.random_facts,
            "days_since_first": self.days_since_first,
            "total_games": self.total_games,
            "tilt": self.tilt,
            "average_session_length": self.average_session_length,
            "last_games": self.last_games,
            "last_games_highlighting": self.LAST_GAMES_HIGHLIGHTING,
            "grand_total": self.grand_total,
            "season_data": self.season_data,
            "session_data": self.session_data,
            "fun_facts": self.fun_facts,
            "k_perf": self.k_performance,
            "p_perf": self.p_performance,
            "s_perf": self.s_performance,
            "website_date": self.website_date,
            "latest_session_date": self.latest_session_date,
            "w_and_l": self.w_and_l,
            "session_game_count": self.session_game_count,
            "just_out": self.just_out,
            "performance_score": self.performance_score,
            "to_beat_next": self.to_beat_next,
            "seasons": self.seasons,
            "session_information": self.session_information,
            "players": [
                {"name":"Knus", "rank": self.ranks[0], "performance": self.k_performance[0][0], "stats": self.q.profile_averages(0), "top": self.k_performance, "color":self.K},
                {"name":"Puad", "rank": self.ranks[1], "performance": self.p_performance[0][0], "stats": self.q.profile_averages(1), "top": self.p_performance, "color":self.P},
                {"name":"Sticker", "rank": self.ranks[2], "performance": self.s_performance[0][0], "stats": self.q.profile_averages(2), "top": self.s_performance, "color":self.S}
            ],
            "profile_stat_names": ["Score", "Goals", "Assists", "Saves", "Shots"],
            "players_stat_icons": ["MVP_points_icon", "Goal_points_icon", "Assist_points_icon", "Save_points_icon", "Shot_on_Goal_points_icon"],
            "session_rank": self.q.session_rank(458),
            "performance_graph": self.g.performance_graph(self.total_games),
            "days_graph": self.g.days_graph(),
            "weekdays_graph": self.g.weekdays_graph(),
            "month_graph": self.g.month_graph(),
            "year_graph": self.g.year_graph(),
            "heatmap": self.g.results_table(),
            "score_distribution": self.g.score_distribution_graph()
        }
        return context
    
    def build_record_context(self):
        context = {
            'latest': self.total_games,
            "record_games": self.record_games,
            'streaks': self.streaks_record,
            "record_headlines": ["Most stat by player in one game", "Highest performance by player", "Lowest performance by player",
                                "Most stat by team", "Goal stats by team", "Points stats", "Miscellaneous"],
            'rank_highlighting': self.RANK_HIGHLIGHTING,
            'k': self.Ktransparent,
            'p': self.Ptransparent,
            's': self.Stransparent,
            'cg': 'rgba(255, 225, 0, 0.2)'
        }
        return context 
    
    def build_profile_context(self, player_id):
        return {
            'name': ['Knus', 'Puad', 'Sticker'][player_id],
            'streaks': self.profile_streaks[player_id],
            'rank_highlighting': self.RANK_HIGHLIGHTING,
        }
    
    def build_games_context(self):
        return {
            'games': self.last_100_games_stats,
            "last_games_highlighting": [
                None, None, None, None, None, (self.K, 100, 700),
                (self.K, 100, 700), (self.K, 0, 5), (self.K, 0, 5),
                (self.K, 0, 5),
                (self.K, 0, 10), (self.P, 100, 700),
                (self.P, 100, 700), (self.P, 0, 5), (self.P, 0, 5),
                (self.P, 0, 5),
                (self.P, 0, 10),
                (self.S, 100, 700), (self.S, 100, 700),
                (self.S, 0, 5), (self.S, 0, 5), (self.S, 0, 5),
                (self.S, 0, 10)
            ]
        }