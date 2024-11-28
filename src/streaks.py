from typing import Any

from connect import BackendConnection
from records import Record


class StreakQueries(BackendConnection):

    # Generates table of the longest winning streaks [streak, gameStartID, gameEndID]
    def longest_winning_streak(self, limit: int = 16) -> Record:
        self.c.execute("""
            WITH Streaks AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
            gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID
            FROM (SELECT gameID FROM games WHERE goals > against)h)
                SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
                FROM Streaks GROUP BY grouper ORDER BY 1 DESC, 2 ASC LIMIT %s""", (limit,))
        return Record("Longest winning streak", "longestwin", self.c.fetchall())

    # Generate table of the longest losing streaks [steak, gameStartID, gameEndID]

    def longest_losing_streak(self, limit: int = 16) -> list[Any]:
        self.c.execute("""
            WITH Streaks AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
            gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID
            FROM (SELECT gameID FROM games WHERE goals < against)h)
                SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
                FROM Streaks GROUP BY grouper ORDER BY 1 DESC, 2 ASC LIMIT %s""", (limit,))
        return Record("Longest losing streak", "longestloss", self.c.fetchall())

    # Table of [streak, startGameID, endGameID]

    def mvp_streak(self, player_id: int, limit: int = 16) -> list[Any]:
        self.c.execute("""
            WITH MVPs AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
            gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID
            FROM (SELECT gameID FROM mvplvp WHERE MVP=%s) AS MVPTable)
                SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
                FROM MVPs GROUP BY grouper ORDER BY 1 DESC, 2 ASC LIMIT %s""", (player_id, limit),)
        return self.c.fetchall()

    # Table of [streak, startGameID, endGameID]

    def not_mvp_streak(self, player_id: int, limit: int = 16) -> list[Any]:
        self.c.execute("""
            WITH MVPs AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
            gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID
            FROM (SELECT gameID FROM mvplvp WHERE MVP!=%s) AS MVPTable)
                SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
                FROM MVPs GROUP BY grouper ORDER BY 1 DESC, 2 ASC LIMIT %s""", (player_id, limit))
        return self.c.fetchall()

    # Table of [streak, startGameID, endGameID]

    def not_lvp_streak(self, player_id: int, limit: int = 16) -> list[Any]:
        self.c.execute("""
            WITH MVPs AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
            gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID
            FROM (SELECT gameID FROM mvplvp WHERE LVP!=%s) AS MVPTable)
                SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
                FROM MVPs GROUP BY grouper ORDER BY 1 DESC, 2 ASC LIMIT %s""", (player_id, limit))
        return self.c.fetchall()

    # Table of [streak, startGameID, endGameID]

    def lvp_streak(self, player_id: int, limit: int = 16) -> list[Any]:
        self.c.execute("""
            WITH MVPs AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
            gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID
            FROM (SELECT gameID FROM mvplvp WHERE LVP=%s) AS MVPTable)
                SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
                FROM MVPs GROUP BY grouper ORDER BY 1 DESC, 2 ASC LIMIT %s""", (player_id, limit),)
        return self.c.fetchall()

    def streak_stat_is_zero(self, player_id: int, stat: str, comparison: str, value: int) -> list[Any]:
        if stat not in ["goals", "assists", "saves", "shots"]:
            return []
        if comparison not in [">", "<", "="]:
            return []
        if value < 0:
            return []
        self.c.execute(f"""
        WITH Streaks AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
                gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID
            FROM (SELECT gameID FROM scores WHERE playerID = %s AND {stat} {comparison} {value}))
            SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
            FROM Streaks GROUP BY grouper ORDER BY 1 DESC, 2 ASC""", (player_id,))
        return self.c.fetchall()

    def streak_win_or_loss_by_one(self, win: bool):  # todo unused?
        self.c.execute("""
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

    def generate_streaks_profile_page(self, user_id: int):
        pass  # tODO
        return []

    def generate_streaks_record_page(self):
        streaks = [
            self.longest_winning_streak(),
            self.longest_losing_streak(),
        ]
        # TODO: Win by one, lose by one
        return streaks

    def generate_profile_streaks(self, player_id: int):
        streaks = {
            "MVP Streak": self.mvp_streak(player_id),
            "LVP Streak": self.lvp_streak(player_id),
            "Not MVP Streak": self.not_mvp_streak(player_id),
            "Not LVP Streak": self.not_lvp_streak(player_id)
        }
        return streaks
