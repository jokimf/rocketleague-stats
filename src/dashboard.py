import db
import google_import as data
import utility
from graphs import GraphQueries
from profiles import ProfileQueries
from queries import GeneralQueries, RLQueries
from randomfacts import RandomFactQueries
from records import RecordQueries
from streaks import StreakQueries
from structs import LatestSession


class Dashboard:
    def __init__(self) -> None:
        with db.get_db_connection() as conn:
            self.reload(conn)

        self.RANK_HIGHLIGHTING = [
            "rgb(201, 176, 55, 0.3)",
            "rgb(215, 215, 215, 0.3)",
            "rgb(173, 138, 86, 0.3)",
        ]  # gold silver bronze
        self.LAST_GAMES_HIGHLIGHTING = self.generate_last_games_highlighting(
            self.player_profiles
        )

    def reload(self, conn):

        # Reload cache:
        if GeneralQueries.total_games(conn) == 0:
            self.total_games = 0
            return

        active_player_ids = GeneralQueries.get_active_player_ids(conn)
        stats = Stats(conn)

        # Main
        self.player_profiles = ProfileQueries.build_player_profiles(
            conn, active_player_ids
        )
        self.session_details = RLQueries.session_details(conn)
        self.session_information = RandomFactQueries.session_data_by_date(
            conn,
            self.session_details.get("latest_session_date")
        )
        self.session_rank = RLQueries.session_rank(conn)
        self.random_facts = []  # RandomFactQueries.generate_random_facts()
        self.winrates = RLQueries.winrates(conn)
        self.days_since_first = GeneralQueries.days_since_first_game(conn)
        self.total_games = GeneralQueries.total_games(conn)
        self.tilt = RLQueries.tilt(conn)
        self.average_session_length = RLQueries.average_session_length(conn)
        self.last_games = RLQueries.last_x_games_stats(
            conn,
            active_player_ids, len(RLQueries.games_from_session_date(conn)), False
        )
        self.latest_session = stats.latest_session(active_player_ids)
        self.session_game_amount = len(RLQueries.games_from_session_date(conn))
        self.session_game_details = RLQueries.last_x_games_stats(
            conn,
            active_player_ids, self.session_game_amount, False
        )
        self.fun_facts = []  # RLQueries.generate_fun_facts(active_player_ids)

        # Records
        self.record_games = RecordQueries.generate_record_games(conn)
        self.streaks_record = StreakQueries.generate_streaks_record_page(conn)

        # Graphs
        self.performance_graph = GraphQueries.performance_graph(
            conn,
            self.total_games, active_player_ids
        )
        self.score_distribution_graph = GraphQueries.score_distribution_graph(
            conn,
            active_player_ids
        )
        self.days_graph = GraphQueries.days_graph(conn)
        self.weekdays_graph = GraphQueries.weekdays_graph(conn)
        self.month_graph = GraphQueries.month_graph(conn)
        self.year_graph = GraphQueries.year_graph(conn)
        self.seasons_graph = GraphQueries.seasons_graph(conn)

        # Games
        self.last_100_games_stats = RLQueries.last_x_games_stats(
            conn,
            active_player_ids, 100, True
        )

    def reload_all_stats(self):
        if data.is_new_data_available(self.total_games):
            with db.get_db_connection() as conn:
                data.insert_new_data(conn)
                self.reload(conn)

    def build_dashboard_context(self):
        if self.total_games == 0:
            return {"empty": True}

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
            "players_stat_icons": [
                "MVP_points_icon",
                "Goal_points_icon",
                "Assist_points_icon",
                "Save_points_icon",
                "Shot_on_Goal_points_icon",
            ],
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
                "MISCELLANEOUS",
            ],
            "rank_highlighting": self.RANK_HIGHLIGHTING,  # TODO Use player color
            "k": "rgba(12,145,30,0.2)",
            "p": "rgba(151,3,14,0.2)",
            "s": "rgba(12,52,145,0.2)",
            "cg": "rgba(255, 225,0, 0.2)",
        }
        return context

    def build_profile_context(self, player_id: str):
        with db.get_db_connection() as conn:
            return {
                "name": GeneralQueries.player_name(conn, player_id),
                "streaks": StreakQueries.generate_profile_streaks(conn, player_id),
                "rank_highlighting": self.RANK_HIGHLIGHTING,
            }

    def build_games_context(self):
        return {
            "games": self.last_100_games_stats,
            "last_games_highlighting": self.LAST_GAMES_HIGHLIGHTING,
            "cf": utility.conditional_formatting,
        }

    def generate_last_games_highlighting(self, active_players):
        # 1. Start with the fixed leading None values (gameID, G, GA)
        highlighting = [None, None, None]

        # 2. Iterate through each player profile and append their specific pattern
        for player in active_players:
            color = player["color"]
            player_pattern = [
                None,  # rank
                [color, 100, 700],  # score
                *[[color, 0, 5]] * 3,  # goals, assists, saves
                (color, 0, 10),  # shots
            ]
            highlighting.extend(player_pattern)

        # 3. Add the trailing None for replays
        highlighting.append(None)

        return highlighting


class Stats:
    def __init__(self, conn) -> None:
        self.conn = conn
        self.total_games = GeneralQueries.total_games(conn)
        self.active_player_ids = GeneralQueries.get_active_player_ids(conn)

    def latest_session(self, active_player_ids) -> LatestSession:
        info_panels = {"date": 0, "win_loss": (0, 0)}

        table_data = RLQueries.last_x_games_stats(
            self.conn, active_player_ids, 5, False
        )

        return LatestSession(
            info_panels={"id": 0, "date": "2026-12-31", "win_loss": (424, 421)},
            table_data=[],#RLQueries.latest_session_games(self.conn, active_player_ids),
            player_colors=[
                GeneralQueries.player_color(self.conn, player_id)
                for player_id in active_player_ids
            ],
        )
