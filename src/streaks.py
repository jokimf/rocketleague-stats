import db
from records import Record


def longest_winning_streak(conn, limit: int = 16) -> Record:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            WITH Streaks AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
            gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID
            FROM (SELECT gameID FROM games WHERE goals > against)h)
                SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
                FROM Streaks GROUP BY grouper ORDER BY 1 DESC, 2 ASC LIMIT %s""",
            (limit,),
        )
        return Record("Longest winning streak", "longestwin", cursor.fetchall())


def longest_losing_streak(conn, limit: int = 16) -> Record:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            WITH Streaks AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
            gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID
            FROM (SELECT gameID FROM games WHERE goals < against)h)
                SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
                FROM Streaks GROUP BY grouper ORDER BY 1 DESC, 2 ASC LIMIT %s""",
            (limit,),
        )
        return Record("Longest losing streak", "longestloss", cursor.fetchall())


def mvp_streak(conn, player_id: str, limit: int = 16) -> Record:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            WITH MVPs AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
            gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID
            FROM (SELECT gameID FROM mvplvp WHERE MVP=%s) AS MVPTable)
                SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
                FROM MVPs GROUP BY grouper ORDER BY 1 DESC, 2 ASC LIMIT %s""",
            (player_id, limit),
        )
        return cursor.fetchall()


def not_mvp_streak(conn, player_id: str, limit: int = 16) -> Record:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            WITH MVPs AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
            gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID
            FROM (SELECT gameID FROM mvplvp WHERE MVP!=%s) AS MVPTable)
                SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
                FROM MVPs GROUP BY grouper ORDER BY 1 DESC, 2 ASC LIMIT %s""",
            (player_id, limit),
        )
        return cursor.fetchall()


def not_lvp_streak(conn, player_id: str, limit: int = 16) -> Record:
    with conn.cursor() as cursor:
        cursor.execute(
            """ 
            SELECT t2.name, COUNT(*) AS 'streak', MIN(gameID) AS 'start', MAX(gameID) AS 'end'
            FROM (
                SELECT t1.gameID, t1.score, t1.name, t1.gameID - ROW_NUMBER() OVER (PARTITION BY t1.name ORDER BY t1.gameID) AS 'marker'
                FROM (
                    SELECT s.gameID, ROW_NUMBER() OVER (PARTITION BY s.gameID ORDER BY s.score) AS rn, s.score, p.name
                    FROM scores s
                    LEFT JOIN players p ON s.playerID = p.playerID
                    WHERE p.playerID = %s
                ) t1
                WHERE t1.rn > 1
            ) t2
            GROUP BY t2.marker, t2.name
            ORDER BY 2 DESC, 3 DESC
            LIMIT %s
        """,
            (player_id, limit),
        )
        return cursor.fetchall()


def lvp_streak(conn, player_id: str, limit: int = 16) -> Record:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            WITH MVPs AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
            gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID
            FROM (SELECT gameID FROM mvplvp WHERE LVP=%s) AS MVPTable)
                SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
                FROM MVPs GROUP BY grouper ORDER BY 1 DESC, 2 ASC LIMIT %s""",
            (player_id, limit),
        )
        return cursor.fetchall()


def streak_stat_is_zero(player_id: str, stat: str, comparison: str, value: int) -> Record:  # TODO unused
    with db.get_db_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            f"""
            WITH Streaks AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
                    gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID
                FROM (SELECT gameID FROM scores WHERE playerID = %s AND {stat} {comparison} {value}))
                SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
                FROM Streaks GROUP BY grouper ORDER BY 1 DESC, 2 ASC""",
            (player_id,),
        )
        return cursor.fetchall()

    @staticmethod
    def streak_win_or_loss_by_one(win: bool):  # TODO unused
        with db.get_db_connection() as conn, conn.cursor() as cursor:
            cursor.execute(
                """
                    WITH Streaks AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
                        gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID
                    
                        FROM (SELECT gameID 
                        FROM games
                        WHERE goals - against = %s
                        )
                    )
                            
                    SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
                    FROM Streaks
                    GROUP BY grouper
                    ORDER BY 1 DESC, 2 ASC
                """,
                (1 if win else -1,),
            )


def generate_streaks_profile_page(user_id: int) -> Record:
    pass  # tODO
    return []


def generate_streaks_record_page(conn) -> list[Record]:
    streaks = [
        longest_winning_streak(conn),
        longest_losing_streak(conn),
    ]
    return streaks


def generate_profile_streaks(conn, player_id: str) -> dict[str, Record]:
    streaks = {
        "MVP Streak": mvp_streak(conn, player_id),
        "LVP Streak": lvp_streak(conn, player_id),
        "Not MVP Streak": not_mvp_streak(conn, player_id),
        "Not LVP Streak": not_lvp_streak(conn, player_id),
    }
    return streaks
