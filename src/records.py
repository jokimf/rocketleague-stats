from structs import Record, StatType


def highest_stat_value_one_game(conn, stat: StatType, limit: int = 3) -> Record:
    stat = StatType.validate(stat)
    with conn.cursor() as cursor:
        cursor.execute(
            f"""
                SELECT name, scores.{stat}, games.gameID, date 
                FROM games JOIN scores ON games.gameID = scores.gameID NATURAL JOIN players
                WHERE players.active = 1
                ORDER BY {stat} DESC, games.gameID DESC LIMIT %s""",
            (limit,),
        )
        data = cursor.fetchall()
    return Record(f"Most {stat} by player ", f"max{stat}player", data)


def highest_stat_team_one_game(conn, stat: str, limit: int = 3) -> Record:
    stat = StatType.validate(stat)
    with conn.cursor() as cursor:
        cursor.execute(
            f"""
                SELECT "CG", SUM(scores.{stat}) AS stat, games.gameID, date 
                FROM games JOIN scores ON games.gameID = scores.gameID NATURAL JOIN players
                WHERE players.active = 1
                GROUP BY games.gameID, date ORDER BY stat DESC, games.gameID DESC LIMIT %s
            """,
            (limit,),
        )
        data = cursor.fetchall()

    stat = "points" if stat == "score" else stat
    stat = "goals" if stat == "scores.goals" else stat
    return Record(f"Most {stat} by team", f"max{stat}team", data)


def performance_records(conn, stat: StatType, minmax: str, limit: int = 3) -> Record:
    stat = StatType.validate(stat)
    with conn.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT name, {minmax}(performance.{stat}) AS s, games.gameID, date 
            FROM performance JOIN games ON games.gameID = performance.gameID NATURAL JOIN players
            WHERE players.active = 1
            GROUP BY games.gameID, name, date ORDER BY s {("DESC" if minmax == "MAX" else "ASC")}, games.gameID DESC LIMIT %s""",
            (limit,),
        )
        data = cursor.fetchall()
    return Record(
        f"{'Highest' if minmax == 'MAX' else 'Lowest'} {stat} performance",
        f"performance{minmax}{stat}",
        data,
    )


def most_against(conn, limit: int = 3) -> Record:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT 'CG', against, gameID, date FROM games ORDER BY against DESC, gameID DESC LIMIT %s",
            (limit,),
        )
        return Record("Most goals conceded by team", "mostagainst", cursor.fetchall())


def most_against_and_won(conn, limit: int = 3) -> Record:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT 'CG', against, gameID, date FROM games WHERE goals > against ORDER BY against DESC, gameID DESC LIMIT %s",
            (limit,),
        )
        return Record("Most goals conceded but still won", "mostagainstwon", cursor.fetchall())


def most_goals_and_lost(conn, limit: int = 3) -> Record:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT 'CG', goals, gameID, date FROM games WHERE goals < against ORDER BY goals DESC, gameID DESC LIMIT %s",
            (limit,),
        )
        return Record("Most goals scored and still lost", "mostscoredlost", cursor.fetchall())


def most_total_goals(conn, limit: int = 3) -> Record:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT 'CG',goals+against, gameID, date FROM games ORDER BY goals + against DESC, gameID DESC LIMIT %s",
            (limit,),
        )
        return Record("Most total goals in one game", "mosttotalgoals", cursor.fetchall())


def highest_points_nothing_else(conn, limit: int = 3) -> Record:
    with conn.cursor() as cursor:
        cursor.execute(
            """SELECT players.name, MAX(scores.score) AS p, games.gameID, games.date     
                FROM scores JOIN games ON games.gameID = scores.gameID NATURAL JOIN players
                WHERE scores.goals = 0 AND scores.assists=0 AND scores.saves=0 AND scores.shots=0 AND players.active = 1
                GROUP BY games.gameID, players.name, games.date ORDER BY p DESC, games.gameID DESC LIMIT %s""",
            (limit,),
        )
        return Record(
            "Most points with all stats being 0",
            "highestnothing",
            cursor.fetchall(),
        )


def most_points_without_goal_or_assist(conn, limit: int = 3) -> Record:
    with conn.cursor() as cursor:
        cursor.execute(
            """SELECT players.name, MAX(scores.score) as p, games.gameID, games.date 
                FROM scores JOIN games ON games.gameID = scores.gameID NATURAL JOIN players
                WHERE scores.goals = 0 AND scores.assists=0 AND players.active = 1
                GROUP BY games.gameID, players.name, games.date ORDER BY p DESC, games.gameID DESC LIMIT %s""",
            (limit,),
        )
        return Record(
            "Most points without scoring or assisting",
            "mostpointsnogoalassist",
            cursor.fetchall(),
        )


def most_points_without_goal(conn, limit: int = 3) -> Record:
    with conn.cursor() as cursor:
        cursor.execute(
            """SELECT name, score, games.gameID, date FROM games JOIN scores ON games.gameID = scores.gameID NATURAL JOIN players
            WHERE scores.goals = 0 AND players.active = 1 ORDER BY score DESC, games.gameID DESC LIMIT %s""",
            (limit,),
        )
        return Record("Most points with no goal", "mostpointsnogoal", cursor.fetchall())


def least_points_at_least_1(conn, limit: int = 3) -> Record:
    with conn.cursor() as cursor:
        cursor.execute(
            """SELECT name, MIN(score) as p, games.gameID, date 
                FROM scores JOIN games ON games.gameID = scores.gameID NATURAL JOIN players
                WHERE scores.goals >= 1 AND assists >=1 AND saves >=1 AND shots >=1 AND players.active = 1
                GROUP BY games.gameID, name, date ORDER BY p ASC, games.gameID DESC LIMIT %s""",
            (limit,),
        )
        return Record(
            "Least points with all stats being at least 1",
            "leastwith1",
            cursor.fetchall(),
        )


def least_points_with_goals(conn, limit: int = 3) -> Record:
    with conn.cursor() as cursor:
        cursor.execute(
            """SELECT name, score, games.gameID, date FROM games JOIN scores ON games.gameID = scores.gameID NATURAL JOIN players
            WHERE scores.goals > 0 AND players.active = 1 ORDER BY score ASC, games.gameID DESC LIMIT %s""",
            (limit,),
        )
        return Record(
            "Least points with at least one goal",
            "leastwithgoal",
            cursor.fetchall(),
        )


# Difference between MVP and LVP, DESC for most diff, ASC for least diff
def diff_mvp_lvp(conn, order: str, limit: int = 3) -> Record:
    if order not in ["ASC", "DESC"]:
        raise ValueError("Order is not DESC or ASC.")
    with conn.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT p.name, msc.score - lsc.score AS diff, ml.gameID, g.date
            FROM mvplvp ml
            LEFT JOIN scores msc ON ml.gameID = msc.gameID AND ml.MVP = msc.playerID
            LEFT JOIN scores lsc ON ml.gameID = lsc.gameID AND ml.LVP = lsc.playerID
            LEFT JOIN players p ON msc.playerID = p.playerID 
            LEFT JOIN games g ON ml.gameID = g.gameID
            WHERE p.active = 1
            ORDER BY msc.score-lsc.score {order}, g.gameID DESC LIMIT %s""",
            (limit,),
        )
        return Record(
            f"{'Highest' if order == 'DESC' else 'Lowest'} score diff between MVP and LVP",
            f"diff{order}",
            cursor.fetchall(),
        )


def most_solo_goals(conn, limit: int = 3) -> Record:
    with conn.cursor() as cursor:
        cursor.execute(
            """
                SELECT "CG", games.goals - SUM(assists) AS ja, games.gameID, date FROM games 
                JOIN scores ON games.gameID = scores.gameID NATURAL JOIN players
                where players.active = 1
                GROUP BY games.gameID, games.goals, date ORDER BY ja DESC, games.gameID DESC LIMIT %s""",
            (limit,),
        )
        return Record("Most solo goals by 'team'", "MOST_SOLO", cursor.fetchall())


def generate_record_games(conn) -> tuple:
    game_amount = 16
    records = (
        (
            highest_stat_value_one_game(conn, StatType.SCORE, game_amount),
            highest_stat_value_one_game(conn, StatType.GOALS, game_amount),
            highest_stat_value_one_game(conn, StatType.ASSISTS, game_amount),
            highest_stat_value_one_game(conn, StatType.SAVES, game_amount),
            highest_stat_value_one_game(conn, StatType.SHOTS, game_amount),
        ),
        (
            highest_stat_team_one_game(conn, StatType.SCORE, game_amount),
            highest_stat_team_one_game(conn, StatType.GOALS, game_amount),
            highest_stat_team_one_game(conn, StatType.ASSISTS, game_amount),
            highest_stat_team_one_game(conn, StatType.SAVES, game_amount),
            highest_stat_team_one_game(conn, StatType.SHOTS, game_amount),
        ),
        (
            performance_records(conn, StatType.SCORE, "MAX", game_amount),
            performance_records(conn, StatType.GOALS, "MAX", game_amount),
            performance_records(conn, StatType.ASSISTS, "MAX", game_amount),
            performance_records(conn, StatType.SAVES, "MAX", game_amount),
            performance_records(conn, StatType.SHOTS, "MAX", game_amount),
        ),
        (
            performance_records(conn, StatType.SCORE, "MIN", game_amount),
            performance_records(conn, StatType.GOALS, "MIN", game_amount),
            performance_records(conn, StatType.ASSISTS, "MIN", game_amount),
            performance_records(conn, StatType.SAVES, "MIN", game_amount),
            performance_records(conn, StatType.SHOTS, "MIN", game_amount),
        ),
        (
            most_against(conn, game_amount),
            most_against_and_won(conn, game_amount),
            most_goals_and_lost(conn, game_amount),
            most_total_goals(conn, game_amount),
        ),
        (
            highest_points_nothing_else(conn, game_amount),
            most_points_without_goal_or_assist(conn, game_amount),
            most_points_without_goal(conn, game_amount),
            least_points_at_least_1(conn, game_amount),
            least_points_with_goals(conn, game_amount),
        ),
        (
            diff_mvp_lvp(conn, "DESC", game_amount),
            diff_mvp_lvp(conn, "ASC", game_amount),
            most_solo_goals(conn, game_amount),
        ),
    )
    return records
