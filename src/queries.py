import datetime
from typing import Any

from structs import RandomValues, Session, TeamOverview, TeamOverviewRow


def total_games(conn) -> int:
    with conn.cursor() as cursor:
        cursor.execute("SELECT MAX(gameID) FROM games")
        """
        SELECT COUNT(*) AS total_games
        FROM (
            SELECT s.gameID
            FROM scores s
            JOIN players p ON s.playerID = p.playerID
            WHERE p.active = 1
            GROUP BY s.gameID
            HAVING COUNT(DISTINCT s.playerID) = (
                SELECT COUNT(*) 
                FROM players 
                WHERE active = 1
            )
        ) AS games_together;
        """
        data = cursor.fetchone()[0]
        return data if data else 0


def days_since_first_game(conn) -> int:
    with conn.cursor() as cursor:
        cursor.execute("SELECT DATEDIFF(CURDATE(), MIN(date)) FROM games")
        return cursor.fetchone()[0]


def player_name(conn, player_id: str) -> str:
    with conn.cursor() as cursor:
        cursor.execute("SELECT name FROM players WHERE playerID = %s", (player_id,))
        return cursor.fetchone()[0]


def player_color(conn, player_id: str) -> str:
    with conn.cursor() as cursor:
        cursor.execute("SELECT color FROM players WHERE playerID = %s", (player_id,))
        color: str = cursor.fetchone()[0]
    return color


def write_game_data_from_excel_rows(conn, game: list) -> bool:
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO games VALUES (%s,%s,%s,%s,NULL,NULL,NULL,0)",
            (game[0], game[1], game[3], game[4]),
        )
        cursor.execute(
            "INSERT INTO scores VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                game[0],
                "76561198057132199",
                game[5],
                game[6],
                game[7],
                game[8],
                game[9],
                game[10],
            ),
        )
        cursor.execute(
            "INSERT INTO scores VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                game[0],
                "76561198037207475",
                game[11],
                game[12],
                game[13],
                game[14],
                game[15],
                game[16],
            ),
        )
        cursor.execute(
            "INSERT INTO scores VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                game[0],
                "76561198057982808",
                game[17],
                game[18],
                game[19],
                game[20],
                game[21],
                game[22],
            ),
        )
        conn.commit()
    return True


def last_x_games_stats(conn, active_player_ids: list[str], limit: int, with_date: bool) -> list[Any]:
    with conn.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT 
                g.gameID AS ID, {"g.date," if with_date else ""} g.goals As CG, against AS Enemy,
                p1.rank, p1.score, p1.goals, p1.assists, p1.saves, p1.shots,
                p2.rank, p2.score, p2.goals, p2.assists, p2.saves, p2.shots,
                p3.rank, p3.score, p3.goals, p3.assists, p3.saves, p3.shots,
                replayAvailable
            FROM games g
            LEFT JOIN scores p1 ON g.gameID = p1.gameID AND p1.playerID = %s
            LEFT JOIN scores p2 ON g.gameID = p2.gameID AND p2.playerID = %s
            LEFT JOIN scores p3 ON g.gameID = p3.gameID AND p3.playerID = %s
            ORDER BY ID DESC LIMIT %s
        """,
            (
                *active_player_ids,
                limit,
            ),
        )
        return cursor.fetchall()


def wins_in_range(conn, start: int, end: int) -> int:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(gameID) FROM games WHERE goals > against AND gameID >= %s AND gameID <= %s",
            (start, end),
        )
        return cursor.fetchone()[0]


def calculate_tilt(conn) -> float:
    now = datetime.datetime.now()
    cutoff = now - datetime.timedelta(days=7)

    with conn.cursor() as cursor:
        cursor.execute("SELECT date, goals, against FROM games WHERE date > %s ORDER BY date ASC", (cutoff,))
        games = cursor.fetchall()

    if not games:
        return 0.0

    total_wins = sum(goals >= against for _, goals, against in games)
    total_losses = len(games) - total_wins

    win_loss_ratio = total_wins / max(1, total_losses)
    decay_rate = 0.25 * (1.5 if win_loss_ratio > 1.0 else 1.0)
    tilt = 0.0

    for game_date, goals, against in games:
        if isinstance(game_date, str):
            game_date = datetime.datetime.fromisoformat(game_date[:10])
        days_ago = max(0.0, (now - game_date).total_seconds() / 86400)

        if against <= goals:
            margin = goals - against
            recovery = 0.15

            if margin == 0:
                recovery = 0.05
            elif against >= 3:
                recovery = 0.10
            impact = -recovery
        else:
            goal_diff = against - goals
            if goal_diff == 1:
                impact = 0.40
            elif goals > 2:
                impact = 0.40 + goals * 0.05
            else:
                impact = 0.25
            impact += min(0.40, against * 0.08)
        decay = max(0.0, 1.0 - days_ago * decay_rate)
        tilt += impact * decay
    return round(max(0.0, min(tilt, 1.0)), 2)


def average_session_length(conn) -> int:
    with conn.cursor() as cursor:
        cursor.execute("SELECT AVG(wins+losses) FROM sessions")
        return cursor.fetchone()[0]


def latest_session_main_data(conn) -> Session:
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute("SELECT sessionID as session_id, date, wins, losses, goals, against FROM sessions ORDER BY sessionID desc LIMIT 1")
        return Session(**cursor.fetchone())


def games_from_session_date(conn, session_date: str | None = None) -> list[Any]:
    if session_date is None:
        session_date = latest_session_main_data(conn).date
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM games WHERE date = %s", (session_date,))
        return cursor.fetchall()


def current_season_start_id(conn) -> int:
    with conn.cursor() as cursor:
        cursor.execute("""SELECT g.gameID FROM games g JOIN (
                    SELECT se.seasonID, MIN(g2.gameID) AS min_gameID FROM games g2
                    LEFT JOIN seasons se ON g2.date BETWEEN se.start_date AND se.end_date
                    GROUP BY se.seasonID) min_games ON g.gameID = min_games.min_gameID ORDER BY g.gameID DESC LIMIT 1;""")
        return cursor.fetchone()[0]


def winrates(conn) -> list:
    latest_game_id = total_games(conn)
    season_start = current_season_start_id(conn)
    last_session = latest_session_main_data(conn)
    games_last_session = last_session.wins + last_session.losses

    winrates_list = [
        total_wins(conn) / latest_game_id * 100,
        wins_in_range(conn, season_start, latest_game_id) / (latest_game_id - season_start + 1) * 100,
        float(wins_in_range(conn, latest_game_id - 99, latest_game_id)),
        wins_in_range(conn, latest_game_id - 19, latest_game_id) / 20 * 100,
        last_session.wins / games_last_session * 100,
    ]
    return winrates_list


def total_wins(conn) -> int:
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(gameID) FROM games WHERE goals > against")
        return cursor.fetchone()[0]


# Session Details W/L
def session_details(conn):
    session = latest_session_main_data(conn)
    games = games_from_session_date(conn, session.date)
    return {
        "session_game_count": session.wins + session.losses,
        "latest_session_date": session.date,
        "w_and_l": ["W" if game[2] > game[3] else "L" for game in games],
    }


# Session rank is determined by the delta of wins and losses, goals and against, and finally sum of player scores.
def latest_session_rank(conn) -> dict:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT t1.session_rank 
            FROM (
                SELECT ROW_NUMBER() OVER (ORDER BY  s.wins - s.losses DESC, s.goals - s.against DESC, s.date ASC) AS session_rank, s.sessionID, s.date, s.wins - s.losses, goals - against
                FROM sessions s
                ORDER BY s.wins - s.losses DESC, s.goals - s.against DESC, s.date ASC 
            ) t1
            WHERE t1.sessionId = %s
        """,
            (latest_session_main_data(conn).session_id,),
        )
        session_ranking = cursor.fetchone()[0]
        cursor.execute(
            """
            SELECT * 
            FROM (
                SELECT ROW_NUMBER() OVER (ORDER BY  s.wins - s.losses DESC, s.goals - s.against DESC, s.date ASC) AS session_rank, s.sessionID, s.date, CONCAT(s.wins,"-",s.losses), CONCAT(s.goals,"-",s.against)
                FROM sessions s
                ORDER BY s.wins - s.losses DESC, s.goals - s.against DESC, s.date ASC
            ) t1
            WHERE t1.session_rank BETWEEN %s-3 AND %s+3 ORDER BY session_rank
        """,
            (session_ranking, session_ranking),
        )
        neighbours = cursor.fetchall()  # three sessions above and three sessions below
        return neighbours


def get_game_stats(conn, active_players, fromID: int, toID: int):
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
                g.gameID AS ID, g.date, g.goals As CG, against AS Enemy,
                p1.rank, p1.score, p1.goals, p1.assists, p1.saves, p1.shots,
                p2.rank, p2.score, p2.goals, p2.assists, p2.saves, p2.shots,
                p3.rank, p3.score, p3.goals, p3.assists, p3.saves, p3.shots,
                replayAvailable
            FROM games g
            LEFT JOIN scores p1 ON g.gameID = p1.gameID AND p1.playerID = %s
            LEFT JOIN scores p2 ON g.gameID = p2.gameID AND p2.playerID = %s
            LEFT JOIN scores p3 ON g.gameID = p3.gameID AND p3.playerID = %s
            WHERE g.gameID BETWEEN %s AND %s
            ORDER BY ID DESC
        """,
            (*active_players, fromID, toID),
        )
        return cursor.fetchall()


def build_random_values(conn) -> RandomValues:
    return RandomValues(
        days_since_first=days_since_first_game(conn),
        total_games=total_games(conn),
        tilt=calculate_tilt(conn),
        average_session_length=average_session_length(conn),
    )


def build_team_overview(conn) -> TeamOverview:
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute("""
            WITH game_stats AS (
                SELECT g.gameID, g.date, g.goals, g.against, g.secondsPlayed,
                    COALESCE(SUM(s.score), 0) AS score,
                    COALESCE(SUM(s.assists), 0) AS assists,
                    COALESCE(SUM(s.saves), 0) AS saves,
                    COALESCE(SUM(s.shots), 0) AS shots
                FROM games g LEFT JOIN scores s  ON s.gameID = g.gameID
                GROUP BY g.gameID, g.date, g.goals, g.against, g.secondsPlayed
            ),
            ranked AS (
                SELECT *, ROW_NUMBER() OVER (
                        ORDER BY date DESC, gameID DESC
                    ) AS game_number
                FROM game_stats
            ),
            periods AS (
                SELECT 5 AS period, 'last_5' AS name
                UNION ALL SELECT 20, 'last_20'
                UNION ALL SELECT 100, 'last_100'
                UNION ALL SELECT 500, 'last_500'
                UNION ALL SELECT 1000, 'last_1000'
                UNION ALL SELECT 2147483647, 'lifetime'
            )
            SELECT COUNT(r.gameID) AS games,
                COALESCE(SUM(r.goals > r.against), 0) AS wins,
                COALESCE(SUM(r.goals < r.against), 0) AS losses,
                COALESCE(AVG(r.goals > r.against), 0) AS win_rate,
                COALESCE(AVG(r.goals), 0) AS avg_goals_per_game,
                COALESCE(AVG(r.against), 0) AS avg_against_per_game,
                COALESCE(AVG(r.goals - r.against), 0) AS avg_differential_per_game,
                COALESCE(AVG(r.score), 0) AS avg_score_per_game,
                COALESCE(AVG(r.assists), 0) AS avg_assists_per_game,
                COALESCE(AVG(r.saves), 0) AS avg_saves_per_game,
                COALESCE(AVG(r.shots), 0) AS avg_shots_per_game,
                COALESCE(AVG(r.secondsPlayed), 0) AS avg_game_duration_s,
                COALESCE(MAX(r.secondsPlayed), 0) AS longest_game_duration_s
            FROM periods p LEFT JOIN ranked r ON r.game_number <= p.period
            GROUP BY p.period, p.name ORDER BY p.period
        """)
        rows = (TeamOverviewRow(**row) for row in cursor.fetchall())
    return TeamOverview(*rows)


def goal_heatmap(conn):
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute(""" 
            SELECT CASE
                WHEN g.goals = 0 THEN '0'
                WHEN g.goals = 1 THEN '1'
                WHEN g.goals = 2 THEN '2'
                WHEN g.goals = 3 THEN '3'
                WHEN g.goals = 4 THEN '4'
                when g.goals = 5 then '5'
                ELSE '6+'
            END AS goals,

            SUM(CASE WHEN g.against = 0 THEN 1 ELSE 0 END) AS "against_0",
            SUM(CASE WHEN g.against = 1 THEN 1 ELSE 0 END) AS "against_1",
            SUM(CASE WHEN g.against = 2 THEN 1 ELSE 0 END) AS "against_2",
            SUM(CASE WHEN g.against = 3 THEN 1 ELSE 0 END) AS "against_3",
            SUM(CASE WHEN g.against = 4 THEN 1 ELSE 0 END) AS "against_4",
            sum(case when g.against = 5 then 1 else 0 end) as "against_5",
            SUM(CASE WHEN g.against >= 6 THEN 1 ELSE 0 END) AS "against_6+"
            FROM games g GROUP BY CASE
                WHEN g.goals = 0 THEN '0'
                WHEN g.goals = 1 THEN '1'
                WHEN g.goals = 2 THEN '2'
                WHEN g.goals = 3 THEN '3'
                WHEN g.goals = 4 THEN '4'
                when g.goals = 5 then '5'
                ELSE '6+' END,
            LEAST(g.goals, 6) ORDER BY LEAST(g.goals, 6)""")
        return cursor.fetchall()


# # Winrate of gameNr in session
# def winrate_game_in_session():
#     return self.c.execute("""
# SELECT gnis, CAST(SUM(IIF(goals>against,1,0)) AS FLOAT) / CAST(COUNT(gameID) AS FLOAT) AS wrm,
#     COUNT(gameID) AS gcount
# FROM (
#     SELECT row_number() OVER(PARTITION by date) AS gnis, gameID, goals, against
#     FROM games) p
# GROUP BY gnis
# """).fetchall()


# # Average winrate of sessions by number of games
# def average_winrate_of_sessions_by_game_count():
#     return self.c.execute("""
# SELECT games, AVG(wr) FROM(
#     SELECT wins + losses AS games, CAST(wins AS float) / CAST(wins + losses AS float) AS wr FROM sessions)p
# GROUP BY games
# """).fetchall()

# # UNUSED
# def seasons_dashboard():
#     return self.c.execute("""SELECT se.season_name,
#     SUM(IIF(g.goals > g.against,1,0)) 'wins',
#     SUM(IIF(g.goals < g.against,1,0)) 'losses',
#     CAST(SUM(IIF(g.goals > g.against,1,0)) AS FLOAT) / CAST(COUNT(g.gameID) AS FLOAT) 'wr',
#     AVG(k.score) 'k_score', AVG(k.goals) 'k_goals', AVG(k.assists) 'k_assists',
#     AVG(k.saves) 'k_saves', AVG(k.shots) 'k_shots',
#     AVG(p.score) 'p_score', AVG(p.goals) 'p_goals', AVG(p.assists) 'p_assists',
#     AVG(p.saves) 'p_saves', AVG(p.shots) 'p_shots',
#     AVG(s.score) 's_score', AVG(s.goals) 's_goals', AVG(s.assists) 's_assists',
#     AVG(s.saves) 's_saves', AVG(s.shots) 's_shots'
#     FROM games g
#     LEFT JOIN seasons se ON g.date BETWEEN se.start_date AND se.end_date
#     LEFT JOIN knus k ON g.gameID = k.gameID
#     LEFT JOIN puad p ON g.gameID = p.gameID
#     LEFT JOIN sticker s ON g.gameID = s.gameID
#     GROUP BY seasonID""").fetchall()

# def mvp_wins(player_id, start=1, end=None):
#     if end is None:
#         end = total_games()
#     self.c.execute("""
#     SELECT COUNT(playerID) AS MVPs FROM (
#         SELECT wins.gameID, playerID, score
#         FROM wins
#         LEFT JOIN scores ON scores.gameID = wins.gameID
#         WHERE wins.gameId >= %s AND wins.gameId <= %s
#         GROUP BY wins.gameID
#         HAVING MAX(score))
#     WHERE playerID = %s""", (start, end, player_id))
#     return self.c.fetchone()[0]

# def one_diff_wins() -> int:
#     return self.c.execute("SELECT COUNT(gameID) FROM games WHERE goals - against = 1").fetchone()[0]


# def one_diff_loss() -> int:
#     return self.c.execute("SELECT COUNT(gameID) FROM games WHERE against - goals = 1").fetchone()[0]

# def solo_goals_in_range(start=1, end=None) -> int:
#     if end is None:
#         end = total_games()
#     if start > end:
#         raise ValueError(f'StartIndex was larger than EndIndex: {start} > {end}')
#     self.c.execute("""
# SELECT SUM(goalsSum - assistsSum) AS diff FROM (
#     SELECT SUM(assists) AS assistsSum, SUM(goals) AS goalsSum
#     FROM scores WHERE gameID >= %s AND gameID <= %s GROUP BY gameID
# )
# """, (start, end))
#     return self.c.fetchone()[0]


# # Calculates average games per day based on start and end dates.
# def average_games_per_day(start_date: str, end_date: str) -> float:
#     if datetime.datetime.strptime(end_date, '%Y-%m-%d') < datetime.datetime.strptime(start_date, '%Y-%m-%d'):
#         raise ValueError(f"start_date can't be before end_date {start_date} - {end_date}")
#     return self.c.execute(
#         """SELECT CAST(COUNT(gameID) AS FLOAT) / CAST(JULIANDAY(%s) - JULIANDAY(%s) AS FLOAT)
#            FROM games WHERE date BETWEEN %s AND %s """, (end_date, start_date, start_date, end_date)).fetchone()[0]


# This is a clusterfuck and needs complete overhaul
# def generate_fun_facts(self) -> list:
# "FUN" FACTS # TODO: Also provide +/- if winrate changed from last game.
# p1 > p2+p3
#     def ff_solo_carry(player_id: int) -> tuple:
#         if player_id < 1 or player_id > 2:
#             raise ValueError('No player_id higher than 2 or less than 0 permitted.')
#         return self.c.execute("""
#         SELECT CAST(SUM(IIF(playerID = %s AND sc = 1, 1, 0)) AS FLOAT) / CAST(COUNT(gameID) AS FLOAT) AS oc,
#         CAST(SUM(IIF(playerID = %s AND sc = 1 AND w IS NOT NULL,1,0)) AS FLOAT) /
#         CAST(SUM(IIF(playerID = %s AND sc = 1 ,1,0)) AS FLOAT) AS wr
#         FROM (SELECT s.gameID, s.playerID, MAX(s.score) > (SUM(s.score) - MAX(s.score)) AS sc, wins.gameID AS w
#         FROM scores s LEFT JOIN wins ON s.gameID = wins.gameID GROUP BY s.gameID)
#     """, (player_id, player_id, player_id)).fetchone()

#     # player got more than 500 points in one game
#     def ff_more_than_500(player_id: int) -> tuple:
#         return self.c.execute("""
#         SELECT CAST(SUM(IIF(playerID = %s AND sc = 1,1,0)) AS FLOAT) /
#         CAST(COUNT(gameID)/3 AS FLOAT) AS oc,
#         CAST(SUM(IIF(playerID = %s AND sc = 1 AND w IS NOT NULL, 1, 0)) AS FLOAT) /
#         CAST(SUM(IIF(playerID = %s AND sc = 1,1,0)) AS FLOAT) AS wr
#         FROM (SELECT s.gameID, s.playerID, IIF(score >= 500,1,0) AS sc, wins.gameID AS w
#         FROM scores s LEFT JOIN wins ON s.gameID = wins.gameID)
#     """, (player_id, player_id, player_id)).fetchone()

#     def ff_everyone_scored() -> tuple:
#         return self.c.execute("""
#         SELECT CAST(SUM(IIF(sc = 1,1,0)) AS FLOAT) / CAST(COUNT(gameID) AS FLOAT) AS oc,
#         CAST(SUM(IIF(sc = 1 AND wi IS NOT NULL,1,0)) AS FLOAT) / CAST(SUM(IIF(sc = 1,1,0)) AS FLOAT) AS wr
#         FROM (SELECT s.gameID, IIF(MIN(s.goals) > 0,1,0) AS sc, w.gameID AS wi FROM scores s
#         LEFT JOIN wins w ON s.gameID = w.gameID GROUP BY s.gameID)
#     """).fetchone()

#     def ff_did_not_score(player_id: int) -> tuple:
#         return self.c.execute("""
#         SELECT CAST(SUM(IIF(sG = 0,1,0)) AS FLOAT) / CAST(COUNT(sID) AS FLOAT) AS oc,
#         CAST(SUM(IIF(sG = 0 AND wID IS NOT NULL,1,0)) AS FLOAT) /
#         CAST(SUM(IIF(sG = 0,1,0)) AS FLOAT) AS wr
#         FROM (SELECT s.gameID AS sID, playerID, s.goals AS sG, w.gameID AS wID FROM scores s
#         LEFT JOIN wins w ON s.gameID = w.gameID WHERE playerID = %s)
#     """, (player_id,)).fetchone()

#     def ff_no_solo_goals() -> tuple:
#         return self.c.execute("""
#         SELECT CAST(SUM(IIF(sG = sA AND sG > 0,1,0)) AS FLOAT) / CAST(COUNT(sID) AS FLOAT) AS oc,
#         CAST(SUM(IIF(sG = sA AND sG > 0 AND wID IS NOT NULL,1,0)) AS FLOAT) /
#         CAST(SUM(IIF(sG = sA AND sG > 0,1,0)) AS FLOAT) AS wr
#         FROM(SELECT s.gameID AS sID, SUM(s.goals) AS sG, SUM(s.assists) AS sA, w.gameID AS wID FROM scores s
#         LEFT JOIN wins w ON s.gameID = w.gameID GROUP BY s.gameID)
#     """).fetchone()

#     def ff_six_or_more_shots() -> tuple:
#         return self.c.execute("""
#         SELECT CAST(SUM(IIF(sS >= 6,1,0)) AS FLOAT) / CAST(COUNT(sID) AS FLOAT) AS oc,
#         CAST(SUM(IIF(sS >= 6 AND wID IS NOT NULL,1,0)) AS FLOAT) /
#         CAST(SUM(IIF(sS >= 6,1,0)) AS FLOAT) AS wr
#         FROM(SELECT s.gameID AS sID, SUM(s.shots) AS sS, w.gameID AS wID FROM scores s
#         LEFT JOIN wins w ON s.gameID = w.gameID GROUP BY sID)
#     """).fetchone()

#     def ff_at_least_one_assist(player_id: int) -> tuple:
#         return self.c.execute("""
#         SELECT CAST(SUM(IIF(sA > 0,1,0)) AS FLOAT) / CAST(COUNT(sID) AS FLOAT) AS oc,
#         CAST(SUM(IIF(sA > 0 AND wID IS NOT NULL,1,0)) AS FLOAT) / CAST(SUM(IIF(sA > 0,1,0)) AS FLOAT) AS wr
#         FROM(SELECT s.gameID AS sID, s.assists AS sA, w.gameID AS wID FROM scores s
#         LEFT JOIN wins w ON s.gameID = w.gameID WHERE playerID = %s GROUP BY sID)
#     """, (player_id,)).fetchone()

#     def ff_two_or_more_saves(player_id: int) -> tuple:
#         return self.c.execute("""
#         SELECT CAST(SUM(IIF(sS >= 2,1,0)) AS FLOAT) / CAST(COUNT(sID) AS FLOAT) AS oc,
#         CAST(SUM(IIF(sS >= 2 AND wID IS NOT NULL,1,0)) AS FLOAT) / CAST(SUM(IIF(sS >= 2,1,0)) AS FLOAT) AS wr
#         FROM(SELECT s.gameID AS sID, s.saves AS sS, w.gameID AS wID FROM scores s
#         LEFT JOIN wins w ON s.gameID = w.gameID WHERE playerID = %s GROUP BY sID)
#     """, (player_id,)).fetchone()

#     # Irrelevant: Sum of all averages / 7.5
#     def ff_irrelevant(player_id: int) -> tuple:
#         return self.c.execute("""
#         WITH st AS (
#         SELECT s.gameID AS sID, s.playerID, s.score AS stSc, w.gameID AS wID
#         FROM scores s LEFT JOIN wins w ON s.gameID = w.gameID
#         WHERE playerID = %s),
#         at AS (SELECT AVG(score) * 3 / 7.5 AS avgS FROM scores)
#         SELECT CAST(SUM(IIF(st.stSc <= at.avgS,1,0)) AS FLOAT) /
#         CAST(COUNT(st.sID) AS FLOAT) AS oc,
#         CAST(SUM(IIF(st.stSc <= at.avgS AND wID IS NOT NULL,1,0)) AS FLOAT) /
#         CAST(SUM(IIF(st.stSc <= at.avgS,1,0)) AS FLOAT) AS wr FROM st, at
#     """, (player_id,)).fetchone()

#     # TODO: rework next two queries into own table
#     def ff_team_scores_x_times(x: int) -> tuple:
#         return self.c.execute("""
#     SELECT CAST(SUM(IIF(gGoals = %s,1,0)) AS FLOAT) / COUNT(gID) AS oc,
#         CAST(SUM(IIF(gGoals = %s AND wID IS NOT NULL,1,0)) AS FLOAT) /
#         CAST(SUM(IIF(gGoals = %s,1,0)) AS FLOAT) AS wr
#         FROM (SELECT g.gameID AS gID, g.goals AS gGoals, w.gameID AS wID FROM games g
#         LEFT JOIN wins w ON g.gameID = w.gameID)
#     """, (x, x, x)).fetchone()

#     def ff_team_concedes_x_times(x: int) -> tuple:
#         return self.c.execute("""
#     SELECT CAST(SUM(IIF(g.against = %s,1,0)) AS FLOAT) / COUNT(g.gameID) AS oc,
#         CAST(SUM(IIF(g.against = %s AND w.gameID IS NOT NULL,1,0)) AS FLOAT) /
#         CAST(SUM(IIF(g.against = %s,1,0)) AS FLOAT) AS wr
#         FROM games g LEFT JOIN wins w ON g.gameID = w.gameID
#     """, (x, x, x)).fetchone()

#     def format_fun_facts(title: str, function):
#         return [title] + list(function)

#     return [[format_fun_facts("CG shot six or more times", ff_six_or_more_shots()),
#             format_fun_facts("Everyone scored", ff_everyone_scored()),
#             format_fun_facts("No solo goals were scored", ff_no_solo_goals()),
#             format_fun_facts("CG concedes zero goals", ff_team_concedes_x_times(0)),
#             format_fun_facts("CG concedes one goal", ff_team_concedes_x_times(1)),
#             format_fun_facts("CG concedes two goals", ff_team_concedes_x_times(2)),
#             format_fun_facts("CG concedes three goals", ff_team_concedes_x_times(3)),
#             format_fun_facts("CG concedes four goals", ff_team_concedes_x_times(4)),
#             format_fun_facts("CG concedes five goals", ff_team_concedes_x_times(5)),
#             format_fun_facts("CG scored zero goals", ff_team_scores_x_times(0)),
#             format_fun_facts("CG scored one goal", ff_team_scores_x_times(1)),
#             format_fun_facts("CG scored two goals", ff_team_scores_x_times(2)),
#             format_fun_facts("CG scored three goals", ff_team_scores_x_times(3)),
#             format_fun_facts("CG scored four goals", ff_team_scores_x_times(4)),
#             format_fun_facts("CG scored five goals", ff_team_scores_x_times(5))],
#             [format_fun_facts("Knus is irrelevant", ff_irrelevant(0)),
#             format_fun_facts("Puad is irrelevant", ff_irrelevant(1)),
#             format_fun_facts("Sticker is irrelevant", ff_irrelevant(2)),
#             format_fun_facts("Knus has at least one assist", ff_at_least_one_assist(0)),
#             format_fun_facts("Puad has at least one assist", ff_at_least_one_assist(1)),
#             format_fun_facts("Sticker has at least one assist", ff_at_least_one_assist(2)),
#             format_fun_facts("Knus did not score", ff_did_not_score(0)),
#             format_fun_facts("Puad did not score", ff_did_not_score(1)),
#             format_fun_facts("Sticker did not score", ff_did_not_score(2)),
#             format_fun_facts("Knus scored more than 500 points", ff_more_than_500(0)),
#             format_fun_facts("Puad scored more than 500 points", ff_more_than_500(1)),
#             format_fun_facts("Sticker scored more than 500 points", ff_more_than_500(2)),
#             format_fun_facts("Knus has two or more saves", ff_two_or_more_saves(0)),
#             format_fun_facts("Puad has two or more saves", ff_two_or_more_saves(1)),
#             format_fun_facts("Sticker has two or more saves", ff_two_or_more_saves(2)),
#             ]]
# 6 hours behind real time to account for after midnight gaming

# def website_date(self) -> str:
#     return (datetime.datetime.now() - datetime.timedelta(hours=6)).strftime('%Y-%m-%d')

# def graph_stat_share(stat: str) -> OldGraph:
#     if stat not in possible_stats:
#         raise ValueError(f"{stat} is not in possible stats.")
#     data = c.execute(f"""
#         SELECT k.gameID,
#         CAST(SUM(k.{stat}) OVER(ORDER BY k.gameID) AS FLOAT) /
#         (CAST(SUM(k.{stat}) OVER(ORDER BY k.gameID) AS FLOAT) +
#         CAST(SUM(p.{stat}) OVER(ORDER BY p.gameID) AS FLOAT) +
#         CAST(SUM(s.{stat}) OVER(ORDER BY s.gameID) AS FLOAT)) AS K,
#         CAST(SUM(p.{stat}) OVER(ORDER BY p.gameID) AS FLOAT) /
#         (CAST(SUM(k.{stat}) OVER(ORDER BY k.gameID) AS FLOAT) +
#         CAST(SUM(p.{stat}) OVER(ORDER BY p.gameID) AS FLOAT) +
#         CAST(SUM(s.{stat}) OVER(ORDER BY s.gameID) AS FLOAT)) AS P,
#         CAST(SUM(s.{stat}) OVER(ORDER BY s.gameID) AS FLOAT) /
#         (CAST(SUM(k.{stat}) OVER(ORDER BY k.gameID) AS FLOAT) +
#         CAST(SUM(p.{stat}) OVER(ORDER BY p.gameID) AS FLOAT) +
#         CAST(SUM(s.{stat}) OVER(ORDER BY s.gameID) AS FLOAT)) AS S
#         FROM knus k JOIN puad p ON k.gameID = p.gameID JOIN sticker s ON k.gameID = s.gameID
#     """).fetchall()
#     return OldGraph(f"{stat.capitalize()} Share", "line", data, [x[0] for x in c.description], None, None, None, None,
#                  False)
# def graph_cumulative_stat(stat: str) -> OldGraph:
#     if stat not in possible_stats:
#         raise ValueError(f"{stat} is not in possible stats.")
#     data = c.execute(f"""
#         SELECT k.gameID, SUM(k.{stat}) OVER (ORDER BY k.gameID) 'Knus', SUM(p.{stat}) OVER (ORDER BY k.gameID) 'Puad',
#         SUM(s.{stat}) OVER (ORDER BY k.gameID) 'Sticker' FROM knus k LEFT JOIN puad p ON k.gameID = p.gameID
#         LEFT JOIN sticker s ON k.gameID = s.gameID
#     """).fetchall()
#     return OldGraph(f"Cumulative {stat.capitalize()}", "line", data, [x[0] for x in c.description], None, None, None, None,
#                  False)
# SELECT
#     k.gameID,
#     (SELECT SUM(k1.saves) FROM knus k1 WHERE k1.gameID <= k.gameID) AS 'Knus',
#     (SELECT SUM(p1.saves) FROM puad p1 WHERE p1.gameID <= k.gameID) AS 'Puad',
#     (SELECT SUM(s1.saves) FROM sticker s1 WHERE s1.gameID <= k.gameID) AS 'Sticker'
# FROM knus k;
