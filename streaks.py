import database
from typing import Any

conn = database.connect_to_database()
c = conn.cursor()


# Generates table of the longest winning streaks [streak, gameStartID, gameEndID]
def longest_winning_streak(limit: int = 16) -> list[Any]:
    return c.execute("""
WITH Streaks AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID
FROM (SELECT gameID
    FROM games
    WHERE goals > against)h)
    SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
    FROM Streaks
    GROUP BY grouper
    ORDER BY 1 DESC, 2 ASC
    LIMIT ?
""", (limit,)).fetchall()


# Generate table of the longest losing streaks [steak, gameStartID, gameEndID]
def longest_losing_streak(limit: int = 16) -> list[Any]:
    return c.execute("""
WITH Streaks AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID
FROM (SELECT gameID
    FROM games
    WHERE goals < against)h)
    SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
    FROM Streaks
    GROUP BY grouper
    ORDER BY 1 DESC, 2 ASC
    LIMIT ?
""", (limit,)).fetchall()


# Table of [streak, startGameID, endGameID]
def mvp_streak(player_id: int, limit: int = 16) -> list[Any]:
    return c.execute("""
WITH MVPs AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID
FROM (SELECT gameID, score, playerID
    FROM scores
    GROUP BY gameID
    HAVING MAX(score) AND playerID = ?) AS MVPTable
    )
    SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
    FROM MVPs
    GROUP BY grouper
    ORDER BY 1 DESC, 2 ASC
    LIMIT ?
""", (player_id, limit), ).fetchall()


# Table of [streak, startGameID, endGameID]
def not_mvp_streak(player_id: int, limit: int = 16) -> list[Any]:
    return c.execute("""
WITH helperTable AS(
    SELECT gameID AS helperID, score, playerID
    FROM scores GROUP BY helperID
    HAVING MAX(score) AND playerID = ?),
NotMVPs AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID FROM (
SELECT gameID FROM games,helperTable 
GROUP BY gameID HAVING gameID NOT IN (SELECT helperID FROM helperTable)) AS NotMVPTable)
    SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
    FROM NotMVPs GROUP BY grouper ORDER BY 1 DESC, 2 ASC
    LIMIT ?
""", (player_id, limit)).fetchall()


# Table of [streak, startGameID, endGameID]
def not_lvp_streak(player_id: int, limit: int = 16) -> list[Any]:
    return c.execute("""
WITH helperTable AS(
    SELECT gameID AS helperID, score, playerID
    FROM scores GROUP BY helperID
    HAVING MIN(score) AND playerID = ?),
NotMVPs AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID FROM (
SELECT gameID FROM games,helperTable
GROUP BY gameID HAVING gameID NOT IN (SELECT helperID FROM helperTable)) AS NotMVPTable)
    SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
    FROM NotMVPs GROUP BY grouper ORDER BY 1 DESC, 2 ASC
    LIMIT ?
""", (player_id, limit)).fetchall()


# Table of [streak, startGameID, endGameID]
def lvp_streak(player_id: int, limit: int = 16) -> list[Any]:
    return c.execute("""
WITH MVPs AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID
FROM (SELECT gameID, score, playerID
    FROM scores
    GROUP BY gameID
    HAVING MIN(score) AND playerID = ?) AS MVPTable
    )
    SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
    FROM MVPs
    GROUP BY grouper
    ORDER BY 1 DESC, 2 ASC
    LIMIT ?
""", (player_id, limit)).fetchall()


def generate_streaks_record_page():
    streaks = {
        'Longest Winning Streak': longest_winning_streak(),
        'Longest Losing Streak': longest_losing_streak(),
    }
    # TODO: Win by one, lose by one
    return streaks


def generate_profile_streaks(player_id: int):
    streaks = {
        'MVP Streak': mvp_streak(player_id),
        'LVP Streak': lvp_streak(player_id),
        'Not MVP Streak': not_mvp_streak(player_id),
        'Not LVP Streak': not_lvp_streak(player_id)
    }
    return streaks
