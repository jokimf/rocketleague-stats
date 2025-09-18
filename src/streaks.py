from typing import Any

from connect import Database
from records import Record


class StreakQueries:

    # Generates table of the longest winning streaks [streak, gameStartID, gameEndID]
    @staticmethod
    def longest_winning_streak(limit: int = 16) -> Record:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    WITH Streaks AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
                    gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID
                    FROM (SELECT gameID FROM games WHERE goals > against)h)
                        SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
                        FROM Streaks GROUP BY grouper ORDER BY 1 DESC, 2 ASC LIMIT %s""", (limit,))
                return Record("Longest winning streak", "longestwin", cursor.fetchall())

    # Generate table of the longest losing streaks [steak, gameStartID, gameEndID]
    @staticmethod
    def longest_losing_streak(limit: int = 16) -> list[Any]:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    WITH Streaks AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
                    gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID
                    FROM (SELECT gameID FROM games WHERE goals < against)h)
                        SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
                        FROM Streaks GROUP BY grouper ORDER BY 1 DESC, 2 ASC LIMIT %s""", (limit,))
                return Record("Longest losing streak", "longestloss", cursor.fetchall())

    # Table of [streak, startGameID, endGameID]
    @staticmethod
    def mvp_streak(player_id: int, limit: int = 16) -> list[Any]:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    WITH MVPs AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
                    gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID
                    FROM (SELECT gameID FROM mvplvp WHERE MVP=%s) AS MVPTable)
                        SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
                        FROM MVPs GROUP BY grouper ORDER BY 1 DESC, 2 ASC LIMIT %s""", (player_id, limit),)
                return cursor.fetchall()

    # Table of [streak, startGameID, endGameID]
    @staticmethod
    def not_mvp_streak(player_id: int, limit: int = 16) -> list[Any]:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    WITH MVPs AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
                    gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID
                    FROM (SELECT gameID FROM mvplvp WHERE MVP!=%s) AS MVPTable)
                        SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
                        FROM MVPs GROUP BY grouper ORDER BY 1 DESC, 2 ASC LIMIT %s""", (player_id, limit))
                return cursor.fetchall()

    # Table of [streak, startGameID, endGameID]
    @staticmethod
    def not_lvp_streak(player_id: int, limit: int = 16) -> list[Any]:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    WITH MVPs AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
                    gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID
                    FROM (SELECT gameID FROM mvplvp WHERE LVP!=%s) AS MVPTable)
                        SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
                        FROM MVPs GROUP BY grouper ORDER BY 1 DESC, 2 ASC LIMIT %s""", (player_id, limit))
                return cursor.fetchall()

    # Table of [streak, startGameID, endGameID]
    @staticmethod
    def lvp_streak(player_id: int, limit: int = 16) -> list[Any]:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    WITH MVPs AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
                    gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID
                    FROM (SELECT gameID FROM mvplvp WHERE LVP=%s) AS MVPTable)
                        SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
                        FROM MVPs GROUP BY grouper ORDER BY 1 DESC, 2 ASC LIMIT %s""", (player_id, limit),)
                return cursor.fetchall()

    @staticmethod
    def streak_stat_is_zero(player_id: int, stat: str, comparison: str, value: int) -> list[Any]:
        if stat not in ["goals", "assists", "saves", "shots"]:
            return []
        if comparison not in [">", "<", "="]:
            return []
        if value < 0:
            return []
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"""
                WITH Streaks AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
                        gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID
                    FROM (SELECT gameID FROM scores WHERE playerID = %s AND {stat} {comparison} {value}))
                    SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
                    FROM Streaks GROUP BY grouper ORDER BY 1 DESC, 2 ASC""", (player_id,))
                return cursor.fetchall()

    @staticmethod
    def streak_win_or_loss_by_one(win: bool):  # todo unused?
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
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
                """, (1 if win else -1,))

    @staticmethod
    def generate_streaks_profile_page(user_id: int):
        pass  # tODO
        return []

    @staticmethod
    def generate_streaks_record_page():
        streaks = [
            StreakQueries.longest_winning_streak(),
            StreakQueries.longest_losing_streak(),
        ]
        return streaks

    @staticmethod
    def generate_profile_streaks(player_id: int):
        streaks = {
            "MVP Streak": StreakQueries.mvp_streak(player_id),
            "LVP Streak": StreakQueries.lvp_streak(player_id),
            "Not MVP Streak": StreakQueries.not_mvp_streak(player_id),
            "Not LVP Streak": StreakQueries.not_lvp_streak(player_id)
        }
        return streaks
