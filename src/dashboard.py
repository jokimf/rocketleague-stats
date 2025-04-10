import util.data_import as data
from graphs import GraphQueries
from profiles import ProfileQueries
from queries import RLQueries, GeneralQueries
from randomfacts import RandomFactQueries
from records import RecordQueries
from streaks import StreakQueries


class Dashboard:
    def __init__(self) -> None:
        self.reload()
        self.RANK_HIGHLIGHTING = ["rgb(201, 176, 55, 0.3)", "rgb(215, 215, 215, 0.3)", "rgb(173, 138, 86, 0.3)"]
        self.LAST_GAMES_HIGHLIGHTING = [
            None, None, None, None,
            *[["rgba(12,145,30)", 100, 700]]*3, *[["rgba(12,145,30)", 0, 5]]*3, ("rgba(12,145,30)", 0, 10),
            *[["rgba(151,3,14)", 100, 700]]*2, *[["rgba(151,3,14)", 0, 5]]*3, ("rgba(151,3,14)", 0, 10),
            *[["rgba(12,52,145)", 100, 700]]*2, *[["rgba(12,52,145)", 0, 5]]*3, ("rgba(12,52,145)", 0, 10)]

    def reload(self):
        # Reload cache:
        # Main
        self.player_profiles = ProfileQueries.build_player_profiles()
        self.session_details = RLQueries.session_details()
        z = self.session_details.get("latest_session_date")
        self.session_information = RandomFactQueries.session_data_by_date(z)
        self.session_rank = RLQueries.session_rank()
        self.random_facts = RandomFactQueries.generate_random_facts()
        self.winrates = RLQueries.winrates()
        self.days_since_first = GeneralQueries.days_since_first_game()
        self.total_games = GeneralQueries.total_games()
        self.tilt = RLQueries.tilt()
        self.average_session_length = RLQueries.average_session_length()
        self.last_games = RLQueries.last_x_games_stats(len(RLQueries.games_from_session_date()), False)
        self.profile_streaks = [StreakQueries.generate_profile_streaks(p) for p in [0, 1, 2]]
        self.last_100_games_stats = RLQueries.last_x_games_stats(100, True)
        self.session_game_amount = len(RLQueries.games_from_session_date())
        self.session_game_details = RLQueries.last_x_games_stats(self.session_game_amount, False)
        self.fun_facts = []  # RLQueries.generate_fun_facts()

        # Records
        self.record_games = RecordQueries.generate_record_games()
        self.streaks_record = StreakQueries.generate_streaks_record_page()

        # Graphs
        self.performance_graph = GraphQueries.performance_graph(self.total_games)
        self.days_graph = GraphQueries.days_graph()
        self.weekdays_graph = GraphQueries.weekdays_graph()
        self.month_graph = GraphQueries.month_graph()
        self.year_graph = GraphQueries.year_graph()
        self.score_distribution_graph = GraphQueries.score_distribution_graph()
        self.seasons_graph = GraphQueries.seasons_graph()

    def reload_all_stats(self):
        if data.is_new_data_available(self.total_games):
            data.insert_new_data()
            self.reload()

    def build_dashboard_context(self):
        print(self.total_games)
        return {
            "players": self.player_profiles,
            "session_information": self.session_information,
            "session_rank": self.session_rank,
            "random_facts": self.random_facts,
            "winrates": self.winrates,
            "days_since_first": self.days_since_first,
            "total_games": self.total_games,
            "tilt": self.tilt,
            "average_session_length": self.average_session_length,
            "last_games": self.last_games,
            "last_games_highlighting": self.LAST_GAMES_HIGHLIGHTING,
            "performance_graph": self.performance_graph,
            "days_graph": self.days_graph,
            "weekdays_graph": self.weekdays_graph,
            "month_graph": self.month_graph,
            "year_graph": self.year_graph,
            "score_distribution_graph": self.score_distribution_graph,
            "seasons_graph": self.seasons_graph,
            "profile_stat_names": ["Score", "Goals", "Assists", "Saves", "Shots"],
            "players_stat_icons": ["MVP_points_icon", "Goal_points_icon", "Assist_points_icon", "Save_points_icon", "Shot_on_Goal_points_icon"],
            # "fun_facts": self.fun_facts,
        }

    def build_record_context(self):
        context = {
            "latest": self.total_games,
            "record_games": self.record_games,
            "streaks": self.streaks_record,
            "record_headlines": [
                "HIGHEST STATS IN ONE GAME",
                "HIGHEST STATS IN ONE GAME BY CG",
                "HIGHEST STATS IN LAST 20",
                "LOWEST STATS IN LAST 20",
                "GOAL STATS",
                "POINTS STATS",
                "MISCELLANEOUS"
            ],
            "rank_highlighting": self.RANK_HIGHLIGHTING,
            "k": "rgba(12,145,30,0.2)",
            "p": "rgba(151,3,14,0.2)",
            "s": "rgba(12,52,145,0.2)",
            "cg": "rgba(255, 225,0, 0.2)"
        }
        return context

    def build_profile_context(self, player_id):
        return {
            "name": ["Knus", "Puad", "Sticker"][player_id],
            "streaks": self.profile_streaks[player_id],
            "rank_highlighting": self.RANK_HIGHLIGHTING,
        }

    def build_games_context(self):
        return {
            "games": self.last_100_games_stats,
            "last_games_highlighting": self.LAST_GAMES_HIGHLIGHTING
        }
