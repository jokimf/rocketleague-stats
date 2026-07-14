import db
import google_import as data
import utility
import visualizations
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

        self.RANK_HIGHLIGHTING = [  # gold silver bronze
            "rgb(201, 176, 55, 0.3)",
            "rgb(215, 215, 215, 0.3)",
            "rgb(173, 138, 86, 0.3)",
        ]
        self.LAST_GAMES_HIGHLIGHTING = self._generate_last_games_highlighting(self.player_profiles)
        self.PROFILE_STAT_LABELS = ["Score", "Goals", "Assists", "Saves", "Shots"]
        self.RECORD_LABELS = [
            "HIGHEST STATS IN ONE GAME",
            "HIGHEST STATS IN ONE GAME BY CG",
            "HIGHEST STATS IN LAST 20",
            "LOWEST STATS IN LAST 20",
            "GOAL STATS",
            "POINTS STATS",
            "MISCELLANEOUS",
        ]

    def reload(self, conn):
        # Reload cache:

        active_player_ids = GeneralQueries.get_active_player_ids(conn)

        self.total_games = GeneralQueries.total_games(conn)
        self.player_profiles = ProfileQueries.build_player_profiles(conn, active_player_ids)
        self.session_information = RandomFactQueries.session_data_by_date(conn, RLQueries.session_details(conn)["latest_session_date"])
        self.session_rank = RLQueries.session_rank(conn)
        self.random_facts = []  # RandomFactQueries.generate_random_facts()
        self.winrates = RLQueries.winrates(conn)
        self.days_since_first = GeneralQueries.days_since_first_game(conn)
        self.tilt = RLQueries.tilt(conn)
        self.average_session_length = RLQueries.average_session_length(conn)
        self.last_games = RLQueries.last_x_games_stats(conn, active_player_ids, len(RLQueries.games_from_session_date(conn)), False)
        self.visualizations = visualizations.get_all_visualizations(conn, self.total_games, active_player_ids)

        # Records
        self.record_games = RecordQueries.generate_record_games(conn)
        self.streaks_record = StreakQueries.generate_streaks_record_page(conn)

        # Games
        self.last_100_games_stats = RLQueries.last_x_games_stats(conn, active_player_ids, 100, True)

        # unused
        self.latest_session = latest_session(conn, active_player_ids)
        self.session_game_amount = len(RLQueries.games_from_session_date(conn))
        self.session_game_details = RLQueries.last_x_games_stats(conn, active_player_ids, self.session_game_amount, False)
        self.fun_facts = []  # RLQueries.generate_fun_facts(active_player_ids)

        print("Session information")
        print(self.session_information)
        print("Latest session")
        print(self.latest_session)
        print("Session game details")
        print(self.session_game_details)

    def reload_all_stats(self):
        if data.is_new_data_available(self.total_games):
            with db.get_db_connection() as conn:
                data.insert_new_data(conn)
                self.reload(conn)

    def build_dashboard_context(self):
        if self.total_games == 0:
            return {"empty": True}

        return {
            "total_games": self.total_games,
            "players": self.player_profiles,
            "session_information": self.session_information,
            "session_rank": self.session_rank,
            "random_facts": self.random_facts,
            "winrates": self.winrates,
            "days_since_first": self.days_since_first,
            "tilt": self.tilt,
            "average_session_length": self.average_session_length,
            "last_games": self.last_games,
            "visualizations": self.visualizations,
            "profile_stat_names": self.PROFILE_STAT_LABELS,
            "last_games_highlighting": self.LAST_GAMES_HIGHLIGHTING,
            # "fun_facts": self.fun_facts,
        }

    def build_record_context(self):
        context = {
            "latest": self.total_games,
            "record_games": self.record_games,
            "streaks": self.streaks_record,
            "record_headlines": self.RECORD_LABELS,
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

    def _generate_last_games_highlighting(self, active_players):
        highlighting = [None, None, None]
        for player in active_players:
            color = player["color"]
            player_pattern = [
                None,  # rank
                [color, 100, 700],  # score
                *[[color, 0, 5]] * 3,  # goals, assists, saves
                (color, 0, 10),  # shots
            ]
            highlighting.extend(player_pattern)
        highlighting.append(None)

        return highlighting


def latest_session(conn, active_player_ids) -> LatestSession:
    info_panels = {"date": 0, "win_loss": (0, 0)}
    table_data = RLQueries.last_x_games_stats(conn, active_player_ids, 5, False)

    return LatestSession(
        info_panels=info_panels,
        table_data=table_data,
        player_colors=[GeneralQueries.player_color(conn, player_id) for player_id in active_player_ids],
    )
