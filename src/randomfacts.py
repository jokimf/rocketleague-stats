import math
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

import queries
import records
from structs import RandomFact, StatType


def generate_random_facts(conn, active_player_ids: list[str]) -> list:
    all_facts: list[RandomFact] = (
        record_session(conn)
        + milestone_facts(conn, active_player_ids)
        + last_session_facts(conn)
        + last_month_summary(conn)
        + result_facts(conn)
        + game_count_facts(conn)
        + close_to_record(conn)
        + outclassed(conn)
        + at_least_1_streak(conn)
        + streak(conn)
    )
    return sorted(all_facts, key=lambda i: i[1], reverse=True)


# Last session was xy
def last_session_facts(conn) -> list[RandomFact]:
    facts = []
    session_id = queries.latest_session_main_data(conn).session_id

    # Session ID milestone
    if session_id % 50 == 0:
        facts.append((f"This session is the {session_id}th session!", 4))

    # Last session was x days ago
    today = datetime.today()
    day_difference = (today - datetime.strptime(last_two_sessions_dates()[0][0], "%Y-%m-%d")).days
    if day_difference >= 21:
        facts.append((f"The last session was as far back as {day_difference} days ago!", 4))
    elif day_difference >= 12:
        facts.append((f"The last session was {day_difference} days ago...", 3))
    elif day_difference >= 5:
        facts.append((f"The last session was {day_difference} days ago.", 2))

    # At the same date x years ago
    for years_ago in range(1, today.year - 2018):
        same_date = session_data_by_date(conn, (today - relativedelta(years=years_ago)).strftime("%Y-%m-%d"))
        if same_date:
            facts.append((f"On this day, {years_ago} years ago, you played a session with {same_date[2]} wins and {same_date[3]} losses!", 3))
    return facts


def game_count_facts(conn) -> list[RandomFact]:
    facts = []
    month = game_amount_this_month()
    year = game_amount_this_year()
    total = queries.total_games(conn)

    if total % 100 == 0 and total > 0:
        facts.append((f"You just played the {total}th game in total.", 4))

    if year % 50 == 0 and year > 0:
        facts.append((f"You just played the {year}th game this year.", 4))

    if month % 25 == 0 and month > 0:
        facts.append((f"You just played the {month}th game this month.", 3))
    return facts


def last_month_summary(conn) -> list[RandomFact]:
    today = datetime.today()

    if today.day >= 5:
        return []

    games_this_month = game_amount_this_month(conn)
    if not 0 < games_this_month <= 5:
        return []

    last_month = (today.replace(day=1) - timedelta(days=1)).strftime("%m-%Y")
    month_game_counts = unique_months_game_count(conn)
    for rank, (month, game_amount) in enumerate(month_game_counts):
        if month == last_month:
            return [RandomFact(f"Last month, you played {game_amount} games, which ranks at {rank} out of {len(month_game_counts)}.", 5)]

    return []


def result_facts(conn) -> list[RandomFact]:  # Unusual result  # TODO: Slow, rework
    facts = []

    results = results_table()
    if not results:  # No games played yet
        return []

    goals, against = last_result()
    for single_result in results:
        if single_result[0] == goals and single_result[1] == against:
            total, percent = single_result[2], single_result[2] / queries.total_games(conn)
            if percent <= 0.0025:
                facts.append((f"The result of last match only happened for the {total}. time! That is only {round(percent * 100, 4)}%", 5))
            elif percent <= 0.01:
                facts.append((f"The result of last match was really rare, in total it happened {total} times ({round(percent * 100, 4)}%)", 4))
            elif percent <= 0.04:
                facts.append((f"The result of last match was rare, in total it happened {total} times ({round(percent * 100, 4)}%)", 3))
            elif percent < 0.0025:
                facts.append((f"Last game was the first time that this result happened. {goals}:{against}, a real rarity.", 5))
    return facts


def milestone_facts(conn, active_player_ids: list[str]) -> list[RandomFact]:  # Player reaches milestone in stat y
    facts = []
    for stat in (stat_type.value for stat_type in StatType):
        for player_id in active_player_ids:
            milestone_val = 50000 if stat == "score" else 500 if stat == "shots" else 250
            total = player_total_of_stat(player_id, stat)
            overshoot = total % milestone_val
            if overshoot < player_stat_of_last_game(player_id, stat):  # Milestone crossed
                facts.append((f"{queries.player_name(conn, player_id)} just reached {total - overshoot} {stat}!", 4))
    return facts


def close_to_record(conn) -> list[RandomFact]:  # Came close to a record
    facts = []

    # Record games
    last_id = queries.total_games(conn)

    if last_id == 0:
        return 0

    limit = 100  # round(last_id / 100) # TODO: find better metric, some crash for total_games, rework slow mess
    record_data = [
        (
            records.highest_stat_value_one_game(conn, StatType.SCORE, limit).data,
            "The score of {value} reached by {name} last game was in the Top 100 of all scores, ranking at spot number {rank}!",
        ),
        (
            records.highest_stat_value_one_game(conn, StatType.GOALS, limit).data,
            "The goal amount of {value} reached by {name} last game was in the Top 100 of all games, ranking at spot number {rank}!",
        ),
        (
            records.highest_stat_value_one_game(conn, StatType.ASSISTS, limit).data,
            "The assist amount of {value} reached by {name} last game was in the Top 100 of all games, ranking at spot number {rank}!",
        ),
        (
            records.highest_stat_value_one_game(conn, StatType.SAVES, limit).data,
            "The save amount of {value} reached by {name} last game was in the Top 100 of all games, ranking at spot number {rank}!",
        ),
        (
            records.highest_stat_value_one_game(conn, StatType.SHOTS, limit).data,
            "The shot amount of {value} reached by {name} last game was in the Top 100 of all games, ranking at spot number {rank}!",
        ),
        (
            records.most_points_without_goal(limit).data,
            """A total amount of {value} points was reached by {name} last game, without scoring! 
                    It was in the Top 100 of score without a goal, ranking at spot number {rank}!""",
        ),
        (
            records.least_points_with_goals(limit).data,
            "{name} only reached a total amount of {value} score, even though he scored... he was in the "
            "Bottom 100 of score having scored at least one goal, ranking at spot number {rank}!",
        ),
        (
            records.most_against(limit).data,
            "Last game you conceded a Top 100 amount of goals... {value} in total. It ranks at number {rank} of all games",
        ),
        (
            records.most_against_and_won(limit).data,
            "Last game you conceded a total of {value} goals, but still won. The game ranks at number {rank} in that regard.",
        ),
        (
            records.most_goals_and_lost(limit).data,
            "Last game you scored a total of {value} goals, but still lost. The game ranks at number {rank} in that regard.",
        ),
        (
            records.most_total_goals(limit).data,
            "Last game, both teams scored a total of {value} goals. The game ranks at number {rank} in that regard.",
        ),
        (
            records.highest_stat_team_one_game(conn, StatType.SCORE, limit).data,
            "Last game you scored a total of {value} points. The game ranks at number {rank} in that regard.",
        ),
        (
            records.highest_stat_team_one_game(conn, StatType.GOALS, limit).data,
            "Last game you scored a total of {value} goals. The game ranks at number {rank} in that regard.",
        ),
        (
            records.highest_stat_team_one_game(conn, StatType.ASSISTS, limit).data,
            "Last game you got a total of {value} assists. The game ranks at number {rank} in that regard.",
        ),
        (
            records.highest_stat_team_one_game(conn, StatType.SAVES, limit).data,
            "Last game you scored a total of {value} saves. The game ranks at number {rank} in that regard.",
        ),
        (
            records.highest_stat_team_one_game(conn, StatType.SHOTS, limit).data,
            "Last game you scored a total of {value} shots. The game ranks at number {rank} in that regard.",
        ),
        (
            records.diff_mvp_lvp(conn, "DESC", limit).data,
            "Last game the difference between the MVP and LVP was {value} points. That is the {rank}. highest difference.",
        ),
        (
            records.diff_mvp_lvp(conn, "ASC", limit).data,
            "Last game the difference between the MVP and LVP was only {value} points. That is the {rank}. lowest difference.",
        ),
        (
            records.most_solo_goals(limit).data,
            "Last game had with {value} goals an usual amount of solo goals. The game ranks at number {rank} in that regard.",
        ),
        (
            records.performance_records(conn, StatType.SCORE, "MIN", limit).data,
            "The point trend of {name} reached a value of {value}, which is the {rank}. lowest value in total.",
        ),
        (
            records.performance_records(conn, StatType.SCORE, "MAX", limit).data,
            "The point trend of {name} reached a value of {value}, which is the {rank}. highest value in total.",
        ),
        (
            records.performance_records(conn, StatType.GOALS, "MIN", limit).data,
            "The goal trend of {name} reached a value of {value}, which is the {rank}. lowest value in total.",
        ),
        (
            records.performance_records(conn, StatType.GOALS, "MAX", limit).data,
            "The goal trend of {name} reached a value of {value}, which is the {rank}. highest value in total.",
        ),
        (
            records.performance_records(conn, StatType.ASSISTS, "MIN", limit).data,
            "The assist trend of {name} reached a value of {value}, which is the {rank}. lowest value in total.",
        ),
        (
            records.performance_records(conn, StatType.ASSISTS, "MAX", limit).data,
            "The assist trend of {name} reached a value of {value}, which is the {rank}. highest value in total.",
        ),
        (
            records.performance_records(conn, StatType.SAVES, "MIN", limit).data,
            "The saves trend of {name} reached a value of {value}, which is the {rank}. lowest value in total.",
        ),
        (
            records.performance_records(conn, StatType.SAVES, "MAX", limit).data,
            "The saves trend of {name} reached a value of {value}, which is the {rank}. highest value in total.",
        ),
        (
            records.performance_records(conn, StatType.SHOTS, "MIN", limit).data,
            "The shots trend of {name} reached a value of {value}, which is the {rank}. lowest value in total.",
        ),
        (
            records.performance_records(conn, StatType.SHOTS, "MAX", limit).data,
            "The shots trend of {name} reached a value of {value}, which is the {rank}. highest value in total.",
        ),
    ]
    # Iterate through data and check if last gameID appears # TODO Check only threshold
    # This kills performance badly. Change asap
    for record in record_data:
        for index in range(limit):
            if record[0][index][2] == last_id:
                facts.append((record[1].format(value=record[0][index][1], name=record[0][index][0], rank=index + 1), 4))

    return facts


def record_session(conn) -> list[RandomFact]:
    facts = []
    # TODO: Session is close to being a record session
    session_count = session_game_count(conn)
    session_limit = math.ceil(session_count)  # top 2%

    data = record_games_per_session(conn, session_limit)
    next_milestone_rank = None
    next_milestone_value = None
    for rank in range(session_limit):
        if (rank + 1) % 5 == 0 and data[rank][0] != session_game_count:
            next_milestone_rank = rank + 1
            next_milestone_value = data[rank][1]
        if data[rank][0] == session_game_count and data[rank][1] > 10:
            facts.append((f"You played {data[rank][1]} games this session. It ranks at spot number {rank + 1} in that regard.", 4))
            if next_milestone_value is not None and next_milestone_rank is not None:
                games_to_reach_milestone = next_milestone_value - data[rank][1]
                facts.append(
                    (
                        f"""To reach rank {next_milestone_rank} in games played this session, you need to 
                    play {1 if games_to_reach_milestone == 0 else games_to_reach_milestone} more games.""",
                        4,
                    )
                )
    return facts


# X has double the amount of Y, also session/season based
def outclassed(conn) -> list[RandomFact]:
    facts = []
    return facts


# 'At least 1' streak in Goals/Assists/Saves
def at_least_1_streak(conn) -> list[RandomFact]:
    facts = []
    return facts


# Streak of stats
def streak(conn) -> list[RandomFact]:
    # MVP/LVP streaks
    # x goals in succession
    facts = []
    return facts


def game_amount_this_month(conn) -> int:
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM games WHERE MONTH(date) = MONTH(CURDATE()) AND YEAR(date) = YEAR(CURDATE())")
        return cursor.fetchone()[0]


def last_two_sessions_dates(conn) -> tuple[str]:
    with conn.cursor() as cursor:
        cursor.execute("SELECT date FROM sessions ORDER BY SessionID DESC LIMIT 2")
        return cursor.fetchall()


def game_amount_this_year(conn) -> int:
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM games WHERE YEAR(date) = YEAR(CURDATE())")
        return cursor.fetchone()[0]


def unique_months_game_count(conn) -> tuple[str, int]:
    with conn.cursor() as cursor:
        cursor.execute("SELECT DATE_FORMAT(date, '%m-%Y') as d, COUNT(*) c FROM games GROUP BY d ORDER BY c DESC")
        return cursor.fetchall()


def results_table(conn) -> tuple[int, int, int]:
    with conn.cursor() as cursor:
        cursor.execute("SELECT goals, against, COUNT(g.gameID) AS c FROM games g GROUP BY goals, against ORDER BY 1, 2")
        return cursor.fetchall()


def last_result(conn) -> tuple[int, int]:
    with conn.cursor() as cursor:
        cursor.execute("SELECT goals, against FROM games ORDER BY gameID DESC LIMIT 1")
        return cursor.fetchone()


def player_total_of_stat(conn, player_id: str, stat: str) -> int:
    if stat not in (stat_type.value for stat_type in StatType):
        raise ValueError(f"{stat} is not in possible stats.")
    with conn.cursor() as cursor:
        cursor.execute(f"SELECT SUM({stat}) FROM scores WHERE playerID = %s", (player_id,))
        data = cursor.fetchone()[0]  # (None,) if no scores in db
        return data if data else 0


def player_stat_of_last_game(conn, player_id: str, stat: str) -> int:
    if stat not in (stat_type.value for stat_type in StatType):
        raise ValueError(f"{stat} is not in possible stats.")
    with conn.cursor() as cursor:
        cursor.execute(f"SELECT {stat} FROM scores WHERE playerID = %s ORDER BY gameID DESC LIMIT 1", (player_id,))
        data = cursor.fetchone()
        if data and data[0]:
            return data[0]
        else:
            return 0


def record_games_per_session(conn, limit: int = 1) -> list[tuple[int, int]]:
    with conn.cursor() as cursor:
        cursor.execute("SELECT sessionID, wins+losses FROM sessions ORDER BY wins+losses DESC LIMIT %s", (limit,))
        return cursor.fetchall()


def session_data_by_date(conn, date: str):
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM sessions WHERE date=%s LIMIT 1", (date,))
        return cursor.fetchone()


def session_game_count(conn) -> int:
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(1) FROM sessions")
        return cursor.fetchone()[0]
