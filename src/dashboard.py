import db
import google_import as data
import profiles
import queries
import records
import replays
import streaks
import utility
import visualizations
from structs import LatestSessionPanel

RANK_HIGHLIGHTING = [  # gold silver bronze
    "rgb(201, 176, 55, 0.3)",
    "rgb(215, 215, 215, 0.3)",
    "rgb(173, 138, 86, 0.3)",
]
PROFILE_STAT_LABELS = ["Score", "Goals", "Assists", "Saves", "Shots"]
RECORD_LABELS = [
    "HIGHEST STATS IN ONE GAME",
    "HIGHEST STATS IN ONE GAME BY CG",
    "HIGHEST STATS IN LAST 20",
    "LOWEST STATS IN LAST 20",
    "GOAL STATS",
    "POINTS STATS",
    "MISCELLANEOUS",
]


class Dashboard:
    def __init__(self) -> None:
        with db.get_db_connection() as conn:
            self.reload(conn)

    def reload(self, conn):
        active_player_ids = get_active_player_ids(conn)
        player_profiles = profiles.build_player_profiles(conn, active_player_ids)
        last_games_highlighting = generate_last_games_highlighting(player_profiles)

        self.total_games = queries.total_games(conn)
        self.player_profiles = player_profiles
        self.latest_session = latest_session(conn, active_player_ids, last_games_highlighting)
        self.last_games_highlighting = last_games_highlighting
        self.session_rank = queries.latest_session_rank(conn)
        self.random_values = queries.build_random_values(conn)
        self.winrates = queries.winrates(conn)
        self.visualizations = visualizations.get_all_visualizations(conn, self.total_games, active_player_ids)

        # 3.0
        self.team_overview = queries.build_team_overview(conn)
        self.goal_heatmap = queries.goal_heatmap(conn)

        # Records
        self.record_games = records.generate_record_games(conn)
        self.streaks_record = streaks.generate_streaks_record_page(conn)

        # Games
        self.last_100_games_stats = queries.last_x_games_stats(conn, active_player_ids, 100, with_date=True)

        # unused
        self.random_facts = []  # randomfacts.generate_random_facts(conn, active_player_ids)
        self.fun_facts = []  # queries.generate_fun_facts(active_player_ids)

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
            "latest_session": self.latest_session,
            "session_rank": self.session_rank,
            "random_facts": self.random_facts,
            "winrates": self.winrates,
            "random_values": self.random_values,
            "visualizations": self.visualizations,
            "goal_heatmap": self.goal_heatmap,
            "team_overview": self.team_overview
        }

    def build_record_context(self):
        context = {
            "latest": self.total_games,
            "record_games": self.record_games,
            "streaks": self.streaks_record,
            "record_headlines": RECORD_LABELS,
            "rank_highlighting": RANK_HIGHLIGHTING,  # TODO Use player color
            "k": "rgba(12,145,30,0.2)",
            "p": "rgba(151,3,14,0.2)",
            "s": "rgba(12,52,145,0.2)",
            "cg": "rgba(255, 225,0, 0.2)",
        }
        return context

    def build_profile_context(self, player_id: str):
        with db.get_db_connection() as conn:
            return {
                "name": queries.player_name(conn, player_id),
                "streaks": streaks.generate_profile_streaks(conn, player_id),
                "rank_highlighting": RANK_HIGHLIGHTING,
            }

    def build_games_context(self, minID: int | None, maxID: int | None):
        with db.get_db_connection() as conn:
            active_players = get_active_player_ids(conn)
            games = self.last_100_games_stats if minID is None and maxID is None else queries.get_game_stats(conn, active_players, minID, maxID)
        return {
            "games": games,
            "last_games_highlighting": [None]
            + self.last_games_highlighting,  # [None], because we have an additional column date in comparison to main page table
            "cf": utility.conditional_formatting,
        }

    def build_replay_context(self) -> dict:
        return {"game_ids_with_missing_replay": replays.get_missing_recent_game_ids()}


def generate_last_games_highlighting(active_players):
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


def latest_session(conn, active_player_ids, last_games_highlighting) -> LatestSessionPanel:
    return LatestSessionPanel(
        session=queries.latest_session_main_data(conn),
        table_data=queries.last_x_games_stats(conn, active_player_ids, len(queries.games_from_session_date(conn)), False), #TODO reduce to one query
        highlighting=last_games_highlighting,
    )


def get_active_player_ids(conn) -> list[str]:
    with conn.cursor() as cursor:
        cursor.execute("SELECT playerID FROM players WHERE active = 1 ORDER BY `order` ASC")
        player_ids = cursor.fetchall()
        if not player_ids:
            return []
        return [player_id[0] for player_id in player_ids]
