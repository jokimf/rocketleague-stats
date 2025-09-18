import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Final

from dateutil.relativedelta import relativedelta

from connect import Database
from queries import GeneralQueries, RLQueries
from records import RecordQueries


@dataclass
class RandomFact:
    fact: str
    rarity: int


class RandomFactQueries:
    POSSIBLE_STATS: Final[tuple[str]] = ("score", "goals", "assists", "saves", "shots")

    def generate_random_facts() -> list:
        all_facts: list[RandomFact] = \
            RandomFactQueries.record_session() + \
            RandomFactQueries.milestone_facts() + \
            RandomFactQueries.last_session_facts() + \
            RandomFactQueries.last_month_summary() + \
            RandomFactQueries.result_facts() + \
            RandomFactQueries.game_count_facts() + \
            RandomFactQueries.close_to_record() + \
            RandomFactQueries.outclassed() + \
            RandomFactQueries.at_least_1_streak() + \
            RandomFactQueries.streak()
        return sorted(all_facts, key=lambda i: i[1], reverse=True)

    # Last session was xy
    @staticmethod
    def last_session_facts() -> list[RandomFact]:
        facts = []
        latest_session_data = RLQueries.latest_session_main_data()  # TODO: fix overhead
        if not latest_session_data:
            return []

        session_id = latest_session_data[0]
        # Session ID milestone
        if session_id % 50 == 0:
            facts.append((f"This session is the {session_id}th session!", 4))

        # Last session was x days ago
        today: datetime.datetime = datetime.today()
        day_difference = (
            today - datetime.strptime(RandomFactQueries.last_two_sessions_dates()[0][0], "%Y-%m-%d")).days
        if day_difference >= 21:
            facts.append((f"The last session was as far back as {day_difference} days ago!", 4))
        elif day_difference >= 12:
            facts.append((f"The last session was {day_difference} days ago...", 3))
        elif day_difference >= 5:
            facts.append((f"The last session was {day_difference} days ago.", 2))

        # At the same date x years ago
        for years_ago in range(1, today.year - 2018):
            same_date = RandomFactQueries.session_data_by_date(
                (today - relativedelta(years=years_ago)).strftime("%Y-%m-%d"))
            if same_date:
                facts.append(
                    (f"On this day, {years_ago} years ago, you played a session with {same_date[2]} wins and {same_date[3]} losses!", 3))
        return facts

    @staticmethod
    def game_count_facts() -> list[RandomFact]:
        facts = []
        month = RandomFactQueries.game_amount_this_month()
        year = RandomFactQueries.game_amount_this_year()
        total = GeneralQueries.total_games()

        if total % 100 == 0 and total > 0:
            facts.append((f"You just played the {total}th game in total.", 4))

        if year % 50 == 0 and year > 0:
            facts.append((f"You just played the {year}th game this year.", 4))

        if month % 25 == 0 and month > 0:
            facts.append((f"You just played the {month}th game this month.", 3))
        return facts

    @staticmethod
    def last_month_summary() -> list[RandomFact]:
        facts = []
        games_this_month: int = RandomFactQueries.game_amount_this_month()

        # Only show if less than 3 games have been played this month, and it's before the fifth of a month
        if 5 >= games_this_month > 0 and datetime.today().day < 5:
            last_month_str = (datetime.today().replace(day=1) - timedelta(days=1)).strftime("%m-%Y")
            month_game_count = RandomFactQueries.unique_months_game_count()

            # Works because month are sorted by game count
            rank = [months[0] for months in month_game_count].index(last_month_str)
            game_amount = [t for t in month_game_count if t[0] == last_month_str][0][1]
            facts.append(
                (f"Last month, you played {game_amount} games, which ranks at {rank} out of {len(month_game_count)}.", 5))
        return facts

    @staticmethod
    def result_facts() -> list[RandomFact]:  # Unusual result  # TODO: Slow, rework
        facts = []

        results = RandomFactQueries.results_table()
        if not results:  # No games played yet
            return []

        goals, against = RandomFactQueries.last_result()
        for single_result in results:
            if single_result[0] == goals and single_result[1] == against:
                total, percent = single_result[2], single_result[2] / GeneralQueries.total_games()
                if percent <= 0.0025:
                    facts.append((f"The result of last match only happened for the {total}. time! That is only "
                                  f"{round(percent * 100, 4)}%", 5))
                elif percent <= 0.01:
                    facts.append((
                        f"The result of last match was really rare, in total it happened {total} times ("
                        f"{round(percent * 100, 4)}%)", 4))
                elif percent <= 0.04:
                    facts.append((
                        f"The result of last match was rare, in total it happened {total} times ({round(percent * 100, 4)}%)", 3))
                elif percent < 0.0025:
                    facts.append(
                        (f"Last game was the first time that this result happened. {goals}:{against}, a real rarity.", 5))
        return facts

    @staticmethod
    def milestone_facts() -> list[RandomFact]:  # Player reaches milestone in stat y
        facts = []
        for stat in RandomFactQueries.POSSIBLE_STATS:
            for player_id in range(3):
                milestone_val = 50000 if stat == "score" else 500 if stat == "shots" else 250
                total = RandomFactQueries.player_total_of_stat(player_id, stat)
                overshoot = total % milestone_val
                if overshoot < RandomFactQueries.player_stat_of_last_game(player_id, stat):  # Milestone crossed
                    facts.append((f"{GeneralQueries.player_name(player_id)} just reached {total - overshoot} {stat}!", 4))
        return facts

    @staticmethod
    def close_to_record() -> list[RandomFact]:  # Came close to a record
        facts = []

        # Record games
        last_id = GeneralQueries.total_games()

        if last_id == 0:
            return 0

        limit = 100  # round(last_id / 100) # TODO: find better metric, some crash for total_games, rework slow mess
        record_data = [
            (RecordQueries.highest_stat_value_one_game("score", limit).data,
             "The score of {value} reached by {name} last game was in the Top 100 of all scores, ranking at "
             "spot number {rank}!"),
            (RecordQueries.highest_stat_value_one_game("goals", limit).data,
             "The goal amount of {value} reached by {name} last game was in the Top 100 of all games, "
             "ranking at spot number {rank}!"),
            (RecordQueries.highest_stat_value_one_game("assists", limit).data,
             "The assist amount of {value} reached by {name} last game was in the Top 100 of all games, "
             "ranking at spot number {rank}!"),
            (RecordQueries.highest_stat_value_one_game("saves", limit).data,
             "The save amount of {value} reached by {name} last game was in the Top 100 of all games, "
             "ranking at spot number {rank}!"),
            (RecordQueries.highest_stat_value_one_game("shots", limit).data,
             "The shot amount of {value} reached by {name} last game was in the Top 100 of all games, "
             "ranking at spot number {rank}!"),
            (RecordQueries.most_points_without_goal(limit).data,
             """A total amount of {value} points was reached by {name} last game, without scoring! 
                        It was in the Top 100 of score without a goal, ranking at spot number {rank}!"""),
            (RecordQueries.least_points_with_goals(limit).data,
             "{name} only reached a total amount of {value} score, even though he scored... he was in the "
             "Bottom 100 of score having scored at least one goal, ranking at spot number {rank}!"),
            (RecordQueries.most_against(limit).data,
             "Last game you conceded a Top 100 amount of goals... {value} in total. It ranks at number {rank} "
             "of all games"),
            (RecordQueries.most_against_and_won(limit).data,
             "Last game you conceded a total of {value} goals, but still won. The game ranks at number {rank} "
             "in that regard."),
            (RecordQueries.most_goals_and_lost(limit).data,
             "Last game you scored a total of {value} goals, but still lost. The game ranks at number {rank} "
             "in that regard."),
            (RecordQueries.most_total_goals(limit).data,
             "Last game, both teams scored a total of {value} goals. The game ranks at number {rank} in that "
             "regard."),
            (RecordQueries.highest_stat_team_one_game("score", limit).data,
             "Last game you scored a total of {value} points. The game ranks at number {rank} in that regard."),
            (RecordQueries.highest_stat_team_one_game("goals", limit).data,
             "Last game you scored a total of {value} goals. The game ranks at number {rank} in that regard."),
            (RecordQueries.highest_stat_team_one_game("assists", limit).data,
             "Last game you got a total of {value} assists. The game ranks at number {rank} in that regard."),
            (RecordQueries.highest_stat_team_one_game("saves", limit).data,
             "Last game you scored a total of {value} saves. The game ranks at number {rank} in that regard."),
            (RecordQueries.highest_stat_team_one_game("shots", limit).data,
             "Last game you scored a total of {value} shots. The game ranks at number {rank} in that regard."),
            (RecordQueries.diff_mvp_lvp("DESC", limit).data,
             "Last game the difference between the MVP and LVP was {value} points. That is the {rank}. highest "
             "difference."),
            (RecordQueries.diff_mvp_lvp("ASC", limit).data,
             "Last game the difference between the MVP and LVP was only {value} points. That is the {rank}. "
             "lowest difference."),
            (RecordQueries.most_solo_goals(limit).data,
             "Last game had with {value} goals an usual amount of solo goals. The game ranks at number {rank} "
             "in that regard."),
            (RecordQueries.performance_records("score", "MIN", limit).data,
             "The point trend of {name} reached a value of {value}, which is the {rank}. lowest value in "
             "total."),
            (RecordQueries.performance_records("score", "MAX", limit).data,
             "The point trend of {name} reached a value of {value}, which is the {rank}. highest value in "
             "total."),
            (RecordQueries.performance_records("goals", "MIN", limit).data,
             "The goal trend of {name} reached a value of {value}, which is the {rank}. lowest value in total."),
            (RecordQueries.performance_records("goals", "MAX", limit).data,
             "The goal trend of {name} reached a value of {value}, which is the {rank}. highest value in "
             "total."),
            (RecordQueries.performance_records("assists", "MIN", limit).data,
             "The assist trend of {name} reached a value of {value}, which is the {rank}. lowest value in "
             "total."),
            (RecordQueries.performance_records("assists", "MAX", limit).data,
             "The assist trend of {name} reached a value of {value}, which is the {rank}. highest value in "
             "total."),
            (RecordQueries.performance_records("saves", "MIN", limit).data,
             "The saves trend of {name} reached a value of {value}, which is the {rank}. lowest value in "
             "total."),
            (RecordQueries.performance_records("saves", "MAX", limit).data,
             "The saves trend of {name} reached a value of {value}, which is the {rank}. highest value in "
             "total."),
            (RecordQueries.performance_records("shots", "MIN", limit).data,
             "The shots trend of {name} reached a value of {value}, which is the {rank}. lowest value in "
             "total."),
            (RecordQueries.performance_records("shots", "MAX", limit).data,
             "The shots trend of {name} reached a value of {value}, which is the {rank}. highest value in "
             "total.")
        ]
        # Iterate through data and check if last gameID appears # TODO Check only threshold
        # This kills performance badly. Change asap
        for record in record_data:
            for index in range(0, limit):
                if record[0][index][2] == last_id:
                    facts.append((record[1].format(value=record[0][index][1],
                                 name=record[0][index][0], rank=index + 1), 4))

        return facts

    @staticmethod
    def record_session() -> list[RandomFact]:
        facts = []
        # TODO: Session is close to being a record session
        session_count = RLQueries.session_count()
        session_limit = math.ceil(session_count)  # top 2%

        data = RandomFactQueries.record_games_per_session(session_limit)
        next_milestone_rank = None
        next_milestone_value = None
        for rank in range(session_limit):
            if (rank + 1) % 5 == 0 and data[rank][0] != session_count:
                next_milestone_rank = rank + 1
                next_milestone_value = data[rank][1]
            if data[rank][0] == session_count and data[rank][1] > 10:
                facts.append((
                    f"You played {data[rank][1]} games this session. It ranks at spot number {rank + 1} in that regard.",
                    4))
                if next_milestone_value is not None and next_milestone_rank is not None:
                    games_to_reach_milestone = next_milestone_value - data[rank][1]
                    facts.append((
                        f"""To reach rank {next_milestone_rank} in games played this session, you need to 
                        play {1 if games_to_reach_milestone == 0 else games_to_reach_milestone} more games.""", 4))
        return facts

    # X has double the amount of Y, also session/season based
    @staticmethod
    def outclassed() -> list[RandomFact]:
        facts = []
        return facts

    # 'At least 1' streak in Goals/Assists/Saves
    @staticmethod
    def at_least_1_streak() -> list[RandomFact]:
        facts = []
        return facts

    # Streak of stats
    @staticmethod
    def streak() -> list[RandomFact]:
        # MVP/LVP streaks
        # x goals in succession
        facts = []
        return facts

    @staticmethod
    def game_amount_this_month() -> int:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) FROM games WHERE MONTH(date) = MONTH(CURDATE()) AND YEAR(date) = YEAR(CURDATE())")
                return cursor.fetchone()[0]

    @staticmethod
    def last_two_sessions_dates() -> tuple[str]:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT date FROM sessions ORDER BY SessionID DESC LIMIT 2")
                return cursor.fetchall()

    @staticmethod
    def game_amount_this_year() -> int:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM games WHERE YEAR(date) = YEAR(CURDATE())")
                return cursor.fetchone()[0]

    @staticmethod
    def unique_months_game_count() -> tuple[str, int]:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT DATE_FORMAT(date, '%m-%Y') as d, COUNT(*) c FROM games GROUP BY d ORDER BY c DESC")
                return cursor.fetchall()

    @staticmethod
    def results_table() -> tuple[int, int, int]:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT goals, against, COUNT(g.gameID) AS c FROM games g GROUP BY goals, against ORDER BY 1, 2")
                return cursor.fetchall()

    @staticmethod
    def last_result() -> tuple[int, int]:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT goals, against FROM games ORDER BY gameID DESC LIMIT 1")
                return cursor.fetchone()

    @staticmethod
    def player_total_of_stat(player_id: int, stat: str) -> int:
        if stat not in RandomFactQueries.POSSIBLE_STATS:
            raise ValueError(f"{stat} is not in possible stats.")
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT SUM({stat}) FROM scores WHERE playerID = %s", (player_id,))
                data = cursor.fetchone()[0]  # (None,) if no scores in db
                return data if data else 0

    @staticmethod
    def player_stat_of_last_game(player_id: int, stat: str) -> int:
        if stat not in RandomFactQueries.POSSIBLE_STATS:
            raise ValueError(f"{stat} is not in possible stats.")
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"SELECT {stat} FROM scores WHERE playerID = %s ORDER BY gameID DESC LIMIT 1", (player_id,))
                data = cursor.fetchone()
                if data and data[0]:
                    return data[0]
                else:
                    return 0

    @staticmethod
    def record_games_per_session(limit: int = 1) -> list[tuple[int, int]]:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT sessionID, wins+losses FROM sessions ORDER BY wins+losses DESC LIMIT %s", (limit,))
                return cursor.fetchall()

    @staticmethod
    def session_data_by_date(date: str):
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM sessions WHERE date=%s", (date,))
                return cursor.fetchone()
