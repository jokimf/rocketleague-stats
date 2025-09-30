import datetime
from typing import Any
from connect import Database

possible_stats = ["score", "goals", "assists", "saves", "shots"]


class GeneralQueries:
    @staticmethod
    def total_games() -> int:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT MAX(gameID) FROM games")
                data = cursor.fetchone()[0]
                return data if data else 0

    @staticmethod
    def days_since_first_game() -> int:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT DATEDIFF(CURDATE(), MIN(date)) FROM games")
                return cursor.fetchone()[0]

    @staticmethod
    def player_name(player_id: int) -> str:
        if player_id < 0:
            raise ValueError(f"PlayerID can not be {player_id}.")
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT name FROM players WHERE playerID = %s", (player_id,))
                return cursor.fetchone()[0]

    @staticmethod
    def player_color(player_id: int, transparency: float = 1) -> str:
        if player_id < 0:
            raise ValueError(f"PlayerID can not be {player_id}.")
        if transparency < 0 or transparency > 1:
            raise ValueError(f"Transparency must be between 0 and 1, not {transparency}.")

        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT color FROM players WHERE playerID = %s", (player_id,))
                rgba_color: str = cursor.fetchone()[0]
        return rgba_color[:-1] + "," + str(transparency) + rgba_color[-1]

    @staticmethod
    def player_rank(player_id: int) -> str:
        if player_id < 0:
            raise ValueError(f"PlayerID can not be {player_id}.")
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT r.abbr FROM scores s NATURAL JOIN ranks r WHERE playerID = %s ORDER BY gameID desc LIMIT 1", (player_id,))
                data = cursor.fetchone()
                return data[0] if data else "u"  # TODO find better way than hardcoding unranked

    @staticmethod
    def get_active_players() -> list[int]:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT playerID FROM players WHERE active = 1")
                player_ids = cursor.fetchall()
                if not player_ids:
                    return None
                return [player_id[0] for player_id in player_ids]


class RLQueries:
    @staticmethod
    def insert_game_data(game: list) -> bool:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO games VALUES (%s,%s,%s,%s,NULL)", (game[0], game[1], game[3], game[4]))
                cursor.execute("INSERT INTO scores VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                               (game[0], 0, game[5], game[6], game[7], game[8], game[9], game[10]))
                cursor.execute("INSERT INTO scores VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                               (game[0], 1, game[11], game[12], game[13], game[14], game[15], game[16]))
                cursor.execute("INSERT INTO scores VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                               (game[0], 2, game[17], game[18], game[19], game[20], game[21], game[22]))
                conn.commit()
        return True

    @staticmethod
    def get_last_reload() -> int:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT last_reload FROM meta")
                return cursor.fetchone()[0]

    @staticmethod
    def set_last_reload(last_reload: int) -> None:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE meta SET last_reload=%s", (last_reload,))
            conn.commit()

    @staticmethod
    def last_x_games_stats(limit: int, with_date: bool) -> list[Any]:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"""
                    SELECT 
                        g.gameID AS ID, {"g.date," if with_date else ""} g.goals As CG, against AS Enemy,
                        p1.rank, p1.score, p1.goals, p1.assists, p1.saves, p1.shots,
                        p2.rank, p2.score, p2.goals, p2.assists, p2.saves, p2.shots,
                        p3.rank, p3.score, p3.goals, p3.assists, p3.saves, p3.shots,
                        IF(replay IS NOT NULL, 1, 0)
                    FROM games g
                    LEFT JOIN scores p1 ON g.gameID = p1.gameID AND p1.playerID = 0
                    LEFT JOIN scores p2 ON g.gameID = p2.gameID AND p2.playerID = 1
                    LEFT JOIN scores p3 ON g.gameID = p3.gameID AND p3.playerID = 2
                    ORDER BY ID DESC LIMIT %s
                """, (limit,))
                return cursor.fetchall()

    @staticmethod
    def wins_in_range(start, end) -> int:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(gameID) FROM games WHERE goals > against AND gameID >= %s AND gameID <= %s",
                               (start, end))
                return cursor.fetchone()[0]

    @staticmethod
    def losses_in_range(start, end) -> int:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(gameID) FROM games WHERE against > goals AND gameID >= %s AND gameID <= %s", (start, end))
                return cursor.fetchone()[0]

    @staticmethod
    def current_session_games_played() -> int:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM games g GROUP BY g.`date` ORDER BY date DESC LIMIT 1")
                data = cursor.fetchone()
                return data[0] if data else 0

    @staticmethod
    def current_season_games_played() -> int:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM games g
                    LEFT JOIN seasons s ON g.date BETWEEN s.start_date AND s.end_date 
                    GROUP BY s.seasonID ORDER BY s.seasonID DESC LIMIT 1
                """)
                data = cursor.fetchone()
        return data[0] if data else 0

    @staticmethod
    def tilt() -> float:  # TODO: Write tilt-o-meter
        date14ago = (datetime.datetime.now() - datetime.timedelta(days=14)).strftime("%Y-%m-%d")
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT IFNULL(SUM(against),0) FROM games WHERE date > %s;", (date14ago,))
                enemy_goals = float(cursor.fetchone()[0])
                cursor.execute("SELECT COUNT(1) FROM losses WHERE date > %s;", (date14ago,))
                losses = cursor.fetchone()[0]
        return enemy_goals * 0.8 + losses * 0.2

    @staticmethod
    def average_session_length() -> int:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT AVG(wins+losses) FROM sessions")
                return cursor.fetchone()[0]

    @staticmethod
    def latest_session_main_data() -> list[Any]:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT sessionID, date, wins, losses, Goals, Against FROM sessions ORDER BY SessionID desc LIMIT 1")
                return cursor.fetchone()

    @staticmethod
    def games_from_session_date(session_date: str = None) -> list[Any]:  # TODO: rewrite
        if session_date is None:
            session_date = RLQueries.latest_session_main_data()[1]
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM games WHERE date >= %s", (session_date,))
                return cursor.fetchall()

    @staticmethod
    def session_count() -> int:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(1) FROM sessions")
                return cursor.fetchone()[0]

    @staticmethod
    def season_start_id() -> int:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""SELECT g.gameID FROM games g JOIN (
                            SELECT se.seasonID, MIN(g2.gameID) AS min_gameID FROM games g2
                            LEFT JOIN seasons se ON g2.date BETWEEN se.start_date AND se.end_date
                            GROUP BY se.seasonID) min_games ON g.gameID = min_games.min_gameID ORDER BY g.gameID DESC LIMIT 1;""")
                return cursor.fetchone()[0]

    @staticmethod
    def session_start_id() -> int:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT MIN(gameID) from games GROUP BY date ORDER BY date DESC LIMIT 1")
                return cursor.fetchone()[0]

    @staticmethod
    def winrates() -> list:
        latest_game_id = GeneralQueries.total_games()
        season_start = RLQueries.season_start_id()
        last_session = RLQueries.latest_session_main_data()
        games_last_session = last_session[2] + last_session[3]

        winrates_list = [
            RLQueries.total_wins() / latest_game_id * 100,
            RLQueries.wins_in_range(season_start, latest_game_id) / (latest_game_id - season_start + 1) * 100,
            float(RLQueries.wins_in_range(latest_game_id - 99, latest_game_id)),
            RLQueries.wins_in_range(latest_game_id - 19, latest_game_id) / 20 * 100,
            last_session[2] / games_last_session * 100
        ]
        return winrates_list

    @staticmethod
    def seasons_dashboard_short():
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""SELECT se.season_name,
                SUM(IF(g.goals > g.against,1,0)) 'wins',
                SUM(IF(g.goals < g.against,1,0)) 'losses',
                ROUND(CAST(SUM(IF(g.goals > g.against,1,0)) AS FLOAT) / CAST(COUNT(g.gameID) AS FLOAT)*100,2) 'wr'
                FROM games g
                LEFT JOIN seasons se ON g.date BETWEEN se.start_date AND se.end_date
                GROUP BY seasonID""")
                return cursor.fetchall()

    @staticmethod
    def total_wins() -> int:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(gameID) FROM games WHERE goals > against")
                return cursor.fetchone()[0]

    @staticmethod
    def total_losses() -> int:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(gameID) FROM games WHERE goals < against")
                return cursor.fetchone()[0]

    # Session Details W/L
    @staticmethod
    def session_details():
        details = dict()
        latest_session_details = RLQueries.latest_session_main_data()
        if not latest_session_details:
            return {}
        _, s_date, s_wins, s_losses, _, _ = latest_session_details  # TODO: rewrite
        s_games = s_wins + s_losses
        details["session_game_count"] = s_games
        details["latest_session_date"] = s_date
        details["w_and_l"] = ["W" if game[2] > game[3] else "L" for game in RLQueries.games_from_session_date(s_date)]
        return details

    # Session rank is determined by the delta of wins and losses, goals and against, and finally sum of player scores.
    @staticmethod
    def session_rank(session_id: int = None) -> dict:
        latest_session_details = RLQueries.latest_session_main_data()
        if session_id is None:
            if not latest_session_details:
                return 0
            session_id = latest_session_details[0]  # TODO: rewrite

        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT t1.session_rank 
                    FROM (
                        SELECT ROW_NUMBER() OVER (ORDER BY  s.wins - s.losses DESC, s.goals - s.against DESC, s.date ASC) AS session_rank, s.sessionID, s.date, s.wins - s.losses, goals - against
                        FROM sessions s
                        ORDER BY s.wins - s.losses DESC, s.goals - s.against DESC, s.date ASC 
                    ) t1
                    WHERE t1.sessionId = %s
                """, (session_id,))
                session_ranking = cursor.fetchone()[0]
                cursor.execute("""
                    SELECT * 
                    FROM (
                        SELECT ROW_NUMBER() OVER (ORDER BY  s.wins - s.losses DESC, s.goals - s.against DESC, s.date DESC) AS session_rank, s.sessionID, s.date, CONCAT(s.wins,"-",s.losses), CONCAT(s.goals,"-",s.against)
                        FROM sessions s
                        ORDER BY s.wins - s.losses DESC, s.goals - s.against DESC, s.date ASC
                    ) t1
                    WHERE t1.session_rank BETWEEN %s-3 AND %s+3
                """, (session_ranking, session_ranking))
                neighbours = cursor.fetchall()  # three sessions above and three sessions below
                return neighbours


# TODO: Use unused queries
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

#     # TODO: rework next to queries into own table
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
