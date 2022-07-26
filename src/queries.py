import datetime
import sqlite3
from typing import Any

database_path = '../resources/test.db'
conn = sqlite3.connect(database_path)
c = conn.cursor()

possible_stats = ['score', 'goals', 'assists', 'saves', 'shots']
possible_game_stats = ['goals', 'against']
possible_modes = ['AVG', 'SUM', 'MAX', 'MIN']


def max_id() -> int:
    c.execute("SELECT MAX(gameID) FROM games")
    return c.fetchone()[0]


# Weekday table, [weekday, count, wins, losses]
def weekday_table() -> list[Any]:
    c.execute("""
        SELECT STRFTIME('%w', date) AS weekday, COUNT(date) AS dateCount, SUM(IIF(goals > against, 1, 0)) AS winCount, 
        SUM(IIF(goals < against, 1, 0)) AS loseCount FROM games GROUP BY weekday
    """)
    new = []

    # Calculate and insert winrate
    for x in c.fetchall():
        helper = list(x)
        helper.insert(2, x[2] / (x[2] + x[3]))
        new.append(helper)
    days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    # Substitute dayID with corresponding string
    for i in range(0, 7):
        new[i][0] = days[i]
    new = new[1:] + new[0]  # put Sunday at the back of the list
    return new


# Month table, [name, count, winrate, w, l]
def month_table() -> list[Any]:
    c.execute("""
        SELECT  STRFTIME('%m', date) AS month, COUNT(date) as monthCount, SUM(IIF(goals > against, 1, 0)) as winCount,
        SUM(IIF(goals < against, 1, 0)) as loseCount FROM games GROUP BY month""")
    values_done = []
    for x in c.fetchall():
        new_value = [x[0], x[1], x[2] / (x[2] + x[3]) * 100, x[2], x[3]]
        values_done.append(new_value)

    month = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
             "November", "December"]
    for i in range(0, 12):
        values_done[i][0] = month[i]
    return values_done


# Year table, [year, yearCount, winrate, w, l]
def year_table() -> list[Any]:
    c.execute("""
        SELECT  STRFTIME('%Y', date)AS year, COUNT(date) as yearCount, SUM(IIF(goals > against, 1, 0)) AS winCount,
        SUM(IIF(goals < against, 1,0)) AS lossCount FROM games GROUP BY year""")
    values_done = []
    for x in c.fetchall():
        wr = x[2] / (x[2] + x[3]) * 100
        new_value = [x[0], x[1], wr, x[2], x[3]]
        values_done.append(new_value)
    return values_done


# Date table, [day, count, winrate, w, l]
def dates_table() -> list[Any]:
    c.execute("""
        SELECT STRFTIME('%d', date) AS day, COUNT(date) as dayCount, SUM(IIF(goals > against,1,0)) AS winCount, 
        SUM(IIF(goals < against,1,0)) AS lossCount FROM games GROUP BY day
    """)
    raw_values = c.fetchall()
    values_done = []
    for x in raw_values:
        wr = x[2] / (x[2] + x[3]) * 100
        new_value = [x[0], x[1], wr, x[2], x[3]]
        values_done.append(new_value)
    return values_done


def goals_without_assist_between_games(start=1, end=None) -> int:
    if end is None:
        end = max_id()
    if start > end:
        raise ValueError(f'StartIndex was larger than EndIndex: {start} > {end}')
    c.execute("""
    SELECT SUM(goalsSum - assistsSum) AS diff FROM (
        SELECT SUM(assists) AS assistsSum, SUM(goals) AS goalsSum 
        FROM scores WHERE gameID >= ? AND gameID <= ? GROUP BY gameID
    )
    """, (start, end))
    return c.fetchone()[0]


# Returns number of days since first game played
def days_since_inception() -> int:
    return c.execute('SELECT julianday(DATE()) - julianday(MIN(date)) FROM games').fetchone()[0]


# Generates table of longest winning streaks [streak, gameStartID, gameEndID]
def longest_winning_streak() -> list[Any]:
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
    """).fetchone()[0]


# Generate table of longest losing streaks [steak, gameStartID, gameEndID]
def longest_losing_streak() -> list[Any]:
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
    """).fetchone()[0]


# Table of [streak, startGameID, endGameID]
def mvp_streak(player_id: int) -> list[Any]:
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
    """, (player_id,)).fetchall()


# Table of [streak, startGameID, endGameID]
def not_mvp_streak(player_id: int) -> list[Any]:
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
    """, (player_id,)).fetchall()


# Table of [streak, startGameID, endGameID]
def not_lvp_streak(player_id) -> list[Any]:
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
    """, (player_id,)).fetchall()


# Table of [streak, startGameID, endGameID]
def lvp_streak(player_id) -> list[Any]:
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
    """, (player_id,)).fetchall()


# Calculates average games per day based on start and end dates.
def average_games_per_day(start_date: str, end_date: str) -> float:
    if datetime.datetime.strptime(end_date, '%Y-%m-%d') < datetime.datetime.strptime(start_date, '%Y-%m-%d'):
        raise ValueError(f"start_date can't be before end_date {start_date} - {end_date}")
    return c.execute(
        """SELECT CAST(COUNT(gameID) AS FLOAT) / CAST(JULIANDAY(?) - JULIANDAY(?) AS FLOAT) 
           FROM games WHERE date BETWEEN ? AND ? """, (end_date, start_date, start_date, end_date)).fetchone()[0]


# Used for info table at top of the page
def last_x_games_stats(limit: int = 5) -> list[Any]:
    return c.execute("""
            SELECT 
                games.gameID AS ID, games.date, games.goals As CG, against AS Enemy,
                knus.rank, knus.score, knus.goals, knus.assists, knus.saves, knus.shots,
                puad.rank, puad.score, puad.goals, puad.assists, puad.saves, puad.shots,
                sticker.rank, sticker.score, sticker.goals, sticker.assists, sticker.saves, sticker.shots
            FROM games JOIN scores ON games.gameID = scores.gameID JOIN knus ON games.gameID = knus.gameID 
                JOIN puad ON games.gameID = puad.gameID JOIN sticker ON games.gameID = sticker.gameID
            GROUP BY ID ORDER BY ID DESC LIMIT ?
    """, (limit,)).fetchall()


def team_goals_in_range(start, end) -> int:
    return c.execute("SELECT SUM(goals) FROM games WHERE gameID >= ? AND gameID <= ?", (start, end)).fetchone()[0]


def team_against_in_range(start, end) -> int:
    return c.execute("SELECT SUM(against) FROM games WHERE gameID >= ? AND gameID <= ?", (start, end)).fetchone()[0]


def wins_in_range(start, end) -> int:
    return c.execute("SELECT COUNT(gameID) FROM games WHERE goals > against AND gameID >= ? AND gameID <= ?",
                     (start, end)).fetchone()[0]


def losses_in_range(start, end) -> int:
    return c.execute("SELECT COUNT(gameID) FROM games WHERE against > goals AND gameID >= ? AND gameID <= ?",
                     (start, end)).fetchone()[0]


# Used for general stat tables
def general_game_stats_over_time_period(start=1, end=None) -> list[Any]:
    # Input validation
    if end is None:
        end = max_id()
    if start > end:
        raise ValueError(f'StartIndex was larger than EndIndex: {start} > {end}')
    if start <= 0:
        raise ValueError("StartIndex can't be 0 or lower")
    wins = wins_in_range(start, end)
    losses = losses_in_range(start, end)
    games = end - start + 1
    goals = team_goals_in_range(start, end)
    against = team_against_in_range(start, end)

    def formatted_over_time_box_query(stat: str):
        if stat not in possible_stats:
            raise ValueError(f'{stat} not in possible stats.')

        return c.execute(f"""
            SELECT SUM(knus.{stat}), AVG(knus.{stat}), SUM(puad.{stat}), AVG(puad.{stat}), SUM(sticker.{stat}), AVG(sticker.{stat})
            FROM knus JOIN puad ON knus.gameID = puad.gameID JOIN sticker ON sticker.gameID = knus.gameID
            WHERE knus.gameID >= ? AND knus.gameID <= ?
        """, (start, end)).fetchone()

    def mvp_helper_query():
        query = c.execute(f"""
        SELECT COUNT(gameID), CAST(COUNT(gameID) AS FLOAT)/CAST({games} AS FLOAT) FROM mvplvp WHERE gameID >= ? AND gameID <= ? GROUP BY MVP
        """, (start, end)).fetchall()
        return [stats for tpl in query for stats in tpl]  # Convert three rows to one list

    data = {
        "General": [games, wins / games, goals, against, goals / games, against / games, wins, losses],
        "Score": formatted_over_time_box_query("score"),
        "Goals": formatted_over_time_box_query("goals"),
        "Assists": formatted_over_time_box_query("assists"),
        "Saves": formatted_over_time_box_query("saves"),
        "Shots": formatted_over_time_box_query("shots"),
        "MVPs": mvp_helper_query()}
    return data


# "FUN" FACTS # TODO: Also provide +/- if winrate changed from last game.

# p1 > p2+p3
def ff_solo_carry(player_id: int) -> tuple:
    if player_id < 0 or player_id > 2:
        raise ValueError('No player_id higher than 2 or less than 0 permitted.')
    return c.execute("""
        SELECT CAST(SUM(IIF(playerID = ? AND sc = 1, 1, 0)) AS FLOAT) / CAST(COUNT(gameID) AS FLOAT) AS oc, 
        CAST(SUM(IIF(playerID = ? AND sc = 1 AND w IS NOT NULL,1,0)) AS FLOAT) /
	    CAST(SUM(IIF(playerID = ? AND sc = 1 ,1,0)) AS FLOAT) AS wr
        FROM (SELECT s.gameID, s.playerID, MAX(s.score) > (SUM(s.score) - MAX(s.score)) AS sc, wins.gameID AS w
        FROM scores s LEFT JOIN wins ON s.gameID = wins.gameID GROUP BY s.gameID)
        --WHERE gameID <= ?
    """, (player_id, player_id, player_id)).fetchone()


# player got more than 500 in one game #TODO: rewrite
def ff_more_than_500(player_id: int) -> tuple:
    return c.execute("""
        SELECT CAST(SUM(CASE WHEN playerID = ? AND sc = 1 THEN 1 ELSE 0 END) AS FLOAT) / 
        CAST(COUNT(gameID)/3 AS FLOAT) AS oc, 
        CAST(SUM(CASE WHEN playerID = ? AND sc = 1 AND w IS NOT NULL THEN 1 ELSE 0 END) AS FLOAT) / 
        CAST(SUM(CASE WHEN playerID = ? AND sc = 1 THEN 1 ELSE 0 END) AS FLOAT) AS wr
        FROM (SELECT s.gameID, s.playerID, CASE WHEN score >= 500 THEN 1 ELSE 0 END AS sc, wins.gameID AS w
        FROM scores s LEFT JOIN wins ON s.gameID = wins.gameID)
        --WHERE gameID >= ?
    """, (player_id, player_id, player_id)).fetchone()


def ff_everyone_scored() -> tuple:  # TODO: rewrite
    return c.execute("""
        SELECT CAST(SUM(CASE WHEN sc = 1 THEN 1 ELSE 0 END) AS FLOAT) / CAST(COUNT(gameID) AS FLOAT) AS oc, 
        CAST(SUM(CASE WHEN sc = 1 AND wi IS NOT NULL THEN 1 ELSE 0 END) AS FLOAT) / 
        CAST(SUM(CASE WHEN sc = 1 THEN 1 ELSE 0 END) AS FLOAT) AS wr
        FROM (SELECT s.gameID, CASE WHEN MIN(s.goals) > 0 THEN 1 ELSE 0 END AS sc, w.gameID AS wi FROM scores s 
        LEFT JOIN wins w ON s.gameID = w.gameID GROUP BY s.gameID)
        --WHERE gameID >= ? AND gameID <= ?
    """).fetchone()


def ff_did_not_score(player_id: int) -> tuple:  # TODO: rewrite
    return c.execute("""
        SELECT CAST(SUM(CASE WHEN sG = 0 THEN 1 ELSE 0 END) AS FLOAT) / CAST(COUNT(sID) AS FLOAT) AS oc,
        CAST(SUM(CASE WHEN sG = 0 AND wID IS NOT NULL THEN 1 ELSE 0 END) AS FLOAT) / 
        CAST(SUM(CASE WHEN sG = 0 THEN 1 ELSE 0 END) AS FLOAT) AS wr
        FROM (SELECT s.gameID AS sID, playerID, s.goals AS sG, w.gameID AS wID FROM scores s
        LEFT JOIN wins w ON s.gameID = w.gameID
        WHERE playerID = ?)
    """, (player_id,)).fetchone()


def ff_no_solo_goals() -> tuple:  # TODO: rewrite
    return c.execute("""
        SELECT CAST(SUM(CASE WHEN sG = sA AND sG > 0 THEN 1 ELSE 0 END) AS FLOAT) / CAST(COUNT(sID) AS FLOAT) AS oc,
        CAST(SUM(CASE WHEN sG = sA AND sG > 0 AND wID IS NOT NULL THEN 1 ELSE 0 END) AS FLOAT) / 
        CAST(SUM(CASE WHEN sG = sA AND sG > 0 THEN 1 ELSE 0 END) AS FLOAT) AS wr
        FROM(SELECT s.gameID AS sID, SUM(s.goals) AS sG, SUM(s.assists) AS sA, w.gameID AS wID FROM scores s 
        LEFT JOIN wins w ON s.gameID = w.gameID
        GROUP BY s.gameID)
        WHERE sID >= ? AND sID <= ?
    """).fetchone()


def ff_six_or_more_shots() -> tuple:
    return c.execute("""
        SELECT CAST(SUM(CASE WHEN sS >= 6 THEN 1 ELSE 0 END) AS FLOAT) / CAST(COUNT(sID) AS FLOAT) AS oc,
        CAST(SUM(CASE WHEN sS >= 6 AND wID IS NOT NULL THEN 1 ELSE 0 END) AS FLOAT) / 
        CAST(SUM(CASE WHEN sS >= 6 THEN 1 ELSE 0 END) AS FLOAT)
        FROM(SELECT s.gameID AS sID, SUM(s.shots) AS sS, w.gameID AS wID FROM scores s
        LEFT JOIN wins w ON s.gameID = w.gameID
        GROUP BY sID)
        WHERE sID >= ? AND sID <= ?
    """).fetchone()


def ff_at_least_one_assist(player_id: int) -> tuple:
    return c.execute("""
        SELECT CAST(SUM(CASE WHEN sA > 0 THEN 1 ELSE 0 END) AS FLOAT) / CAST(COUNT(sID) AS FLOAT) AS oc,
        CAST(SUM(CASE WHEN sA > 0 AND wID IS NOT NULL THEN 1 ELSE 0 END) AS FLOAT) / 
        CAST(SUM(CASE WHEN sA > 0 THEN 1 ELSE 0 END) AS FLOAT)
        FROM(SELECT s.gameID AS sID, s.assists AS sA, w.gameID AS wID FROM scores s
        LEFT JOIN wins w ON s.gameID = w.gameID
        WHERE playerID = ?
        GROUP BY sID)
        --WHERE sID >= ? AND sID <= ?
    """, (player_id,)).fetchone()


def two_or_more_saves(player_id, start=1, end=None):
    # Output: Occurrence, Winrate
    if end is None:
        end = max_id()
    c.execute("""
        SELECT CAST(SUM(CASE WHEN sS >= 2 THEN 1 ELSE 0 END) AS FLOAT) / CAST(COUNT(sID) AS FLOAT) AS oc,
        CAST(SUM(CASE WHEN sS >= 2 AND wID IS NOT NULL THEN 1 ELSE 0 END) AS FLOAT) / 
        CAST(SUM(CASE WHEN sS >= 2 THEN 1 ELSE 0 END) AS FLOAT)
        FROM(SELECT s.gameID AS sID, s.saves AS sS, w.gameID AS wID FROM scores s
        LEFT JOIN wins w ON s.gameID = w.gameID
        WHERE playerID = ?
        GROUP BY sID)
        WHERE sID >= ? AND sID <= ?
    """, (player_id, start, end))
    return c.fetchall()


def irrelevant(player_id, start=1, end=None):
    # Irrelevant: Sum of all averages / 7.5
    # Output: Occurrence, Winrate
    if end is None:
        end = max_id()
    c.execute("""
        WITH st AS (
        SELECT s.gameID AS sID, s.playerID, s.score AS stSc, w.gameID AS wID
        FROM scores s LEFT JOIN wins w ON s.gameID = w.gameID
        WHERE playerID = ?),
        at AS (SELECT AVG(score) * 3 / 7.5 AS avgS FROM scores)
        SELECT CAST(SUM(CASE WHEN st.stSc <= at.avgS THEN 1 ELSE 0 END) AS FLOAT) / 
        CAST(COUNT(st.sID) AS FLOAT) AS oc,
        CAST(SUM(CASE WHEN st.stSc <= at.avgS AND wID IS NOT NULL THEN 1 ELSE 0 END) AS FLOAT) / 
        CAST(SUM(CASE WHEN st.stSc <= at.avgS THEN 1 ELSE 0 END) AS FLOAT) AS wr
        FROM st, at
        WHERE sID >= ? AND sID <= ?
    """, (player_id, start, end))
    return c.fetchall()


def team_scores_x_times(x, start=1, end=None):  # pls test2
    # x = (1) bis (5 or more)
    # Output: Occurrence, Winrate
    if end is None:
        end = max_id()
    c.execute("""
        SELECT CAST(SUM(CASE WHEN gGoals = ? THEN 1 ELSE 0 END) AS FLOAT) / COUNT(gID) AS oc,
        CAST(SUM(CASE WHEN gGoals = ? AND wID IS NOT NULL THEN 1 ELSE 0 END) AS FLOAT) / 
        CAST(SUM(CASE WHEN gGoals = ? THEN 1 ELSE 0 END) AS FLOAT) AS wr
        FROM (SELECT g.gameID AS gID, g.goals AS gGoals, w.gameID AS wID FROM games g 
        LEFT JOIN wins w ON g.gameID = w.gameID)
        WHERE gID >= ? AND gID <= ?
    """, (x, x, x, start, end))
    return c.fetchall()


def team_concedes_x_times(x, start=1, end=None):
    # Output: Occurrence, Winrate
    if end is None:
        end = max_id()
    c.execute("""
        SELECT CAST(SUM(CASE WHEN gAgainst = ? THEN 1 ELSE 0 END) AS FLOAT) / COUNT(gID) AS oc,
        CAST(SUM(CASE WHEN gAgainst = ? AND wID IS NOT NULL THEN 1 ELSE 0 END) AS FLOAT) / 
        CAST(SUM(CASE WHEN gAgainst = ? THEN 1 ELSE 0 END) AS FLOAT) AS wr
        FROM (SELECT g.gameID AS gID, g.against AS gAgainst, w.gameID AS wID FROM games g 
        LEFT JOIN wins w ON g.gameID = w.gameID)
        WHERE gID >= ? AND gID <= ?
    """, (x, x, x, start, end))
    return c.fetchall()


def results_table():  # TODO: Rewrite to dict, {'2:1':[count,share%]}
    c.execute("""
        WITH cG AS (SELECT COUNT(*) allG FROM games)
        SELECT goals, against, COUNT(*) AS c, CAST(COUNT(*) AS FLOAT) / cG.allG AS ch  FROM games, cG
        GROUP BY goals, against
        ORDER BY c DESC
    """)
    return c.fetchall()


def results_table_ordered():
    data = c.execute("""
        WITH cG AS (SELECT COUNT(*) allG FROM games)
        SELECT goals, against, COUNT(*) AS c, CAST(COUNT(*) AS FLOAT) / cG.allG AS ch  FROM games, cG
        GROUP BY goals, against
        ORDER BY goals ASC
    """).fetchall()
    d = {}
    for x in data:
        key = x[0]
        if key in d:
            d[key].append(x)
        else:
            d[key] = [x]
    return d


def last_result() -> tuple:
    return c.execute('SELECT goals, against FROM games ORDER BY gameID DESC LIMIT 1').fetchone()


# -- RECORD GAMES
def record_stat_per_session(stat: str, limit: int = 1) -> list[Any]:
    if stat not in possible_stats and not 'games':
        raise ValueError(f'Stat: {stat} is not known for most_one_day.')

    if stat == 'games':
        c.execute(
            "SELECT date, COUNT(date) AS counter FROM games GROUP BY date ORDER BY counter DESC, date ASC LIMIT ?",
            (limit,))
    else:
        c.execute("SELECT date, SUM(goals) AS counter FROM games GROUP BY date ORDER BY counter DESC, date ASC LIMIT ?",
                  (limit,))
    return c.fetchall()


def record_highest_value_per_stat(stat: str, limit: int = 3) -> list[Any]:
    if stat not in possible_stats:
        raise ValueError(f'{stat} not in possible stats.')
    if stat == 'goals':
        stat = 'scores.goals'

    return c.execute(f'''
            SELECT name, {stat}, games.gameID, date 
            FROM games JOIN scores ON games.gameID = scores.gameID NATURAL JOIN players
            ORDER BY {stat} DESC LIMIT ?''', (limit,)).fetchall()


def most_points_without_goal(limit: int = 3) -> list[Any]:
    return c.execute('''
        SELECT name, score, games.gameID, date 
        FROM games JOIN scores ON games.gameID = scores.gameID NATURAL JOIN players
        WHERE scores.goals = 0
        ORDER BY score DESC LIMIT ?''', (limit,)).fetchall()


def least_points_with_goals(limit: int = 3) -> list[Any]:
    return c.execute('''
        SELECT name, score, games.gameID, date 
        FROM games JOIN scores ON games.gameID = scores.gameID NATURAL JOIN players
        WHERE scores.goals > 0
        ORDER BY score ASC LIMIT ?''', (limit,)).fetchall()


def most_against(limit: int = 3) -> list[Any]:
    return c.execute('SELECT "CG", against, gameID, date FROM games ORDER BY against DESC LIMIT ?', (limit,)).fetchall()


def most_against_and_won(limit: int = 3) -> list[Any]:
    return c.execute(
        'SELECT "CG", against, gameID, date FROM games WHERE goals > against ORDER BY against DESC LIMIT ?',
        (limit,)).fetchall()


def most_goals_and_lost(limit: int = 3) -> list[Any]:
    return c.execute(
        'SELECT "CG", goals, gameID, date FROM games WHERE goals < against ORDER BY goals DESC LIMIT ?',
        (limit,)).fetchall()


def most_total_goals(limit: int = 3) -> list[Any]:
    return c.execute('SELECT "CG",goals+against, gameID, date FROM games ORDER BY goals + against DESC LIMIT ?',
                     (limit,)).fetchall()


def highest_team(stat: str, limit: int = 3):
    if stat == 'goals':
        stat = 'scores.goals'
    return c.execute(f'''
            SELECT "CG", SUM({stat}) AS stat, games.gameID, date 
            FROM games JOIN scores ON games.gameID = scores.gameID 
            GROUP BY games.gameID ORDER BY stat DESC LIMIT ?
        ''', (limit,)).fetchall()


def diff_mvp_lvp(order):
    if order not in ['ASC', 'DESC']:
        raise ValueError('Order is not DESC or ASC.')
    c.execute('''
        WITH
            mvp AS (SELECT gameID, playerID, score FROM scores GROUP BY scores.gameID HAVING MAX(score)),
            lvp AS (SELECT gameID, playerID, score FROM scores GROUP BY scores.gameID HAVING MIN(score))
            SELECT pm.name, mvp.score - lvp.score AS diff, mvp.gameID, games.date FROM mvp
            LEFT JOIN lvp ON mvp.gameID = lvp.gameID
            LEFT JOIN players AS pm ON mvp.playerID = pm.playerID
            LEFT JOIN games ON mvp.gameID = games.gameID
            ORDER BY diff ''' + order)
    return c.fetchmany(3)


def most_solo_goals():
    c.execute('''
            SELECT "", games.goals - SUM(assists) AS ja, games.gameID, date FROM games 
            JOIN scores ON games.gameID = scores.gameID
            GROUP BY games.gameID ORDER BY ja DESC''')
    return c.fetchmany(3)


def trend(stat, minmax):
    if stat not in possible_stats or minmax not in ['MIN', 'MAX']:
        raise ValueError('stat or MINMAX not known.')
    if stat == 'goals':
        stat = 'performance.goals'
    c.execute('''
        SELECT name, ''' + minmax + '''(''' + stat + ''') AS s, games.gameID, date 
        FROM performance JOIN games ON games.gameID = performance.gameID NATURAL JOIN players
        GROUP BY games.gameID ORDER BY s ''' + ('DESC' if minmax == 'MAX' else 'ASC'))
    return c.fetchmany(3)


def highest_points_nothing_else():
    c.execute('''
            SELECT name, MAX(score), games.gameID, date     
            FROM scores JOIN games ON games.gameID = scores.gameID NATURAL JOIN players
            WHERE scores.goals = 0 AND assists=0 AND saves=0 AND shots=0
            GROUP BY games.gameID ORDER BY score DESC''')
    return c.fetchmany(3)


def lowest_points_at_least_1():
    c.execute('''
            SELECT name, MIN(score), games.gameID, date 
            FROM scores JOIN games ON games.gameID = scores.gameID NATURAL JOIN players
            WHERE scores.goals >= 1 AND assists>=1 AND saves>=1 AND shots>=1
            GROUP BY games.gameID ORDER BY score ASC ''')
    return c.fetchmany(3)


def most_points_without_goal_or_assist():
    c.execute('''
            SELECT name, MAX(score), games.gameID, date 
            FROM scores JOIN games ON games.gameID = scores.gameID NATURAL JOIN players
            WHERE scores.goals = 0 AND assists=0
            GROUP BY games.gameID ORDER BY score DESC''')
    return c.fetchmany(3)


def build_record_games():
    data = {
        'Highest Score by player': record_highest_value_per_stat('score'),
        'Most goals by player': record_highest_value_per_stat('goals'),
        'Most assists by player': record_highest_value_per_stat('assists'),
        'Most saves by player': record_highest_value_per_stat('saves'),
        'Most shots by player': record_highest_value_per_stat('shots'),
        'Most points by team': highest_team('score'),
        'Most goals by team': highest_team('goals'),
        'Most assists by team': highest_team('assists'),
        'Most saves by team': highest_team('saves'),
        'Most shots by team': highest_team('shots'),
        'Most points with no goal': most_points_without_goal(),
        'Least points with at least one goal': least_points_with_goals(),
        'Most goals conceded by team': most_against(),
        'Most goals conceded and still won': most_against_and_won(),
        'Most goals scored and still lost': most_goals_and_lost(),
        'Most total goals in one game': most_total_goals(),
        'Highest score diff between MVP and LVP': diff_mvp_lvp('DESC'),
        'Lowest score diff between MVP and LVP': diff_mvp_lvp('ASC'),
        'Most solo goals by "team"': most_solo_goals(),
        'Highest score in Trend': trend('score', 'MAX'),
        'Highest goals in Trend': trend('goals', 'MAX'),
        'Highest assists in Trend': trend('assists', 'MAX'),
        'Highest saves in Trend': trend('saves', 'MAX'),
        'Highest shots in Trend': trend('shots', 'MAX'),
        'Lowest score in Trend': trend('score', 'MIN'),
        'Lowest goals in Trend': trend('goals', 'MIN'),
        'Lowest assists in Trend': trend('assists', 'MIN'),
        'Lowest saves in Trend': trend('saves', 'MIN'),
        'Lowest shots in Trend': trend('shots', 'MIN'),
        'Most points with all stats being 0': highest_points_nothing_else(),
        'Lowest points with all stats being at least 1': lowest_points_at_least_1(),
        'Most points without scoring or assisting': most_points_without_goal_or_assist()
    }
    return {k: v for k, v in sorted(data.items(), key=lambda item: item[1][0][2])}  # Sort by gameID


# GRAPH QUERIES
# TODO: OUTPUT: Graph queries as dictionary, keys: {title, x-axis-range; (k, p, s) OR (data)}

# title xmin xmax data

def graph_performance(stat, start=1, end=None):
    if end is None:
        end = max_id()
    if stat not in possible_stats:
        raise ValueError("Not valid stat.")
    c.execute("""
        WITH kT AS (SELECT * FROM performance WHERE playerID = 0),
        pT AS (SELECT * FROM performance WHERE playerID = 1),
        sT AS (SELECT * FROM performance WHERE playerID = 2)
        SELECT kT.gameID, kT.""" + stat + """, pT.""" + stat + """, sT.""" + stat + """ FROM kT
        LEFT JOIN pT ON kT.gameID = pT.gameID
        LEFT JOIN sT ON kT.gameID = sT.gameID
        WHERE kT.gameID >= ? AND kT.gameID <= ?
    """, (start, end))
    data = c.fetchall()
    return "Player performance over time", start, end, data


def graph_total_performance(stat, start=1, end=None):
    if end is None:
        end = max_id()
    if stat not in possible_stats:
        raise ValueError("Not valid stat.")
    c.execute("""
        SELECT gameID, AVG(""" + stat + """) FROM performance WHERE gameID >= ? AND gameID <= ? GROUP BY gameID
    """, (start, end))
    data = c.fetchall()
    return stat + " performance over time", start, end, data


def graph_grief_value(start=1, end=None):
    if end is None:
        end = max_id()
    c.execute("""
        WITH kT AS (SELECT * FROM performance WHERE playerID = 0),
        pT AS (SELECT * FROM performance WHERE playerID = 1),
        sT AS (SELECT * FROM performance WHERE playerID = 2),
        gAvg AS (SELECT gameID, AVG(performance.score) AS gA FROM performance GROUP BY performance.gameID)
        SELECT kT.gameID, kT.score - gA, pT.score - gA, sT.score - gA FROM kT
        LEFT JOIN pT ON kT.gameID = pT.gameID
        LEFT JOIN sT ON kT.gameID = sT.gameID
        LEFT JOIN gAvg ON kT.gameID = gAvg.gameID
        WHERE kT.gameID >= ? AND kT.gameID <= ?
    """, (start, end))
    data = c.fetchall()
    return "Grief value over time", start, end, data


def graph_winrate_last20(start=20, end=None):
    if end is None:
        end = max_id()
    if start < 20:
        raise ValueError("No values for gameID < 20")
    c.execute("""
        SELECT gameID, wr FROM(
        SELECT gameID, CAST(SUM(w) OVER(ORDER BY gameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS FLOAT) / 20 AS wr 
        FROM(  
        SELECT gameID, CASE WHEN goals > against THEN 1 ELSE 0 END AS w FROM games))
        WHERE gameID >= ? AND gameID <= ?
    """, (start, end))
    data = c.fetchall()
    return "Winrate last 20 over time", start, end, data


def graph_winrate(start=1, end=None):
    if end is None:
        end = max_id()
    c.execute("""
        SELECT gameID, 
        CAST(SUM(CASE WHEN goals > against THEN 1 ELSE 0 END) OVER(ORDER BY gameID) AS FLOAT) / gameID AS wr FROM games
        WHERE gameID >= ? AND gameID <= ?
    """, (start, end))
    data = c.fetchall()
    return "Winrate over time", start, end, data


def graph_solo_goals(start=1, end=None):
    if end is None:
        end = max_id()
    c.execute("""
        SELECT gameID, SUM(SUM(goals) - SUM(assists)) OVER(ORDER BY gameID) as sumSG FROM scores GROUP BY gameID
        WHERE gameID >= = AND gameID <= ?
    """, (start, end))
    data = c.fetchall()
    return "Solo goals over time", start, end, data


# % Share of stat in game range [all stats + mvp share (might need own query)]
# Output: [k%,p%,s%]
def graph_performance_share(stat, start=1, end=None):
    if end is None:
        end = max_id()
    if stat not in possible_stats or stat != 'mvp':
        raise ValueError('Stat not legal')
    c.execute("""
        WITH k AS(SELECT SUM(?) AS ks FROM scores WHERE playerID = 0 AND gameID > ? AND gameID < ?),
        p AS (SELECT SUM(?) AS ps FROM scores WHERE playerID = 1 AND gameID > ? AND gameID < ?),
        s AS (SELECT SUM(?) AS ss FROM scores WHERE playerID = 2 AND gameID > ? AND gameID < ?)
        SELECT CAST(ks AS FLOAT) / CAST((ks+ps+ss) AS FLOAT) AS kp, CAST(ps AS FLOAT) / CAST((ks+ps+ss) AS FLOAT) AS pp, CAST(ss AS FLOAT) / CAST((ks+ps+ss) AS FLOAT) AS sp
        FROM k, p, s
    """, (stat, start, end, stat, start, end, stat, start, end))
    data = c.fetchall()
    return stat + " performance share", start, end, data


# Output: Three dictionaries for K,P,S; {200:v, 250: w, 300: x, 350:y, ..., 500:z}
# Score is capped, rounded down, 275 -> 250, 301 -> 300, 499 -> 450 (maybe use modulo 50?)
# Fragen: Was sind v,w,x,y,z? Count? Momentaner Wert?
def graph_score_performance_pointer(start=1, end=None):
    if end is None:
        end = max_id()
    raise NotImplementedError()


# Average MVP score over time
# Fragen: Neue Berechnung für jeden Rahmen oder eine Liste wo nur der Rahmen angezeigt wird? + Score oder Performance? Score ist etwas Aussageschwach
def graph_average_mvp_score_over_time(start=1, end=None):
    if end is None:
        end = max_id()
    c.execute("""
        SELECT gameID, AVG(score) OVER (ORDER BY gameID) FROM scores
        WHERE gameID > ? AND gameID < ?
        GROUP BY gameID HAVING MAX(score)
    """, (start, end))
    data = c.fetchall()
    return "Average mvp score over time", start, end, data


# Average LVP score over time
def graph_average_lvp_score_over_time(start=1, end=None):
    if end is None:
        end = max_id()
    raise NotImplementedError()


# SUM of all stat over time, also for MVPs
# Fragen: Was ist mit also for MVPs gemeint? Eigene Query?
def graph_cumulative_stat_over_time(stat):
    if stat not in possible_stats or stat != 'mvp':
        raise ValueError('Illegal stat')
    c.execute("""
        WITH k AS (SELECT gameID, SUM(?) OVER (ORDER BY gameID) AS sc FROM scores WHERE playerID = 0),
        p AS (SELECT gameID, SUM(?) OVER (ORDER BY gameID) AS sc FROM scores WHERE playerID = 1),
        s AS (SELECT gameID, SUM(?) OVER (ORDER BY gameID) AS sc FROM scores WHERE playerID = 2)
        SELECT k.gameID, k.sc, p.sc, s.sc FROM k LEFT JOIN p ON k.gameID = p.gameID LEFT JOIN s ON k.gameID = s.gameID
    """, (stat, stat, stat))
    data = c.fetchall()
    return "Cumulative value for " + stat, stat, data


# ja
def graph_solo_goals_over_time():
    c.execute("""
        WITH solos AS (SELECT gameID, SUM(goals) - SUM(assists) AS solo FROM scores GROUP BY gameID)
        SELECT gameID, SUM(solo) OVER (ORDER BY gameID) AS cumulativeSolos FROM solos
    """)
    data = c.fetchall()
    return "Cumulative solo goals", data


# Random Facts
def total(player_id, stat):
    if stat not in possible_stats:
        raise ValueError()
    return c.execute('SELECT SUM(' + stat + ') FROM scores WHERE playerID = ?', (player_id,)).fetchone()[0]


def last(player_id, stat):
    if stat not in possible_stats:
        raise ValueError()
    return c.execute('SELECT ' + stat + '  FROM scores WHERE playerID = ? ORDER BY gameID DESC LIMIT 1',
                     (player_id,)).fetchone()[0]


def average(player_id, stat):
    if stat not in possible_stats:
        raise ValueError()
    return c.execute('SELECT AVG(' + stat + ') FROM scores WHERE playerID = ?', (player_id,)).fetchone()[0]


def average_all(player_id, stat):
    if stat not in possible_stats:
        raise ValueError()
    data = c.execute('SELECT ' + stat + ' FROM performance WHERE playerID = ?', (player_id,)).fetchall()
    return [x[0] for x in data]


def performance(player_id, stat):
    if stat not in possible_stats:
        raise ValueError()
    return c.execute('SELECT ' + stat + '  FROM performance WHERE playerID = ? ORDER BY gameID DESC LIMIT 1',
                     (player_id,)).fetchone()[0]


def performance100(player_id, stat):
    if stat not in possible_stats:
        raise ValueError()
    return c.execute('SELECT ' + stat + '  FROM performance100 WHERE playerID = ? ORDER BY gameID DESC LIMIT 1',
                     (player_id,)).fetchone()[0]


def performance250(player_id, stat):
    if stat not in possible_stats:
        raise ValueError()
    return c.execute('SELECT ' + stat + '  FROM performance250 WHERE playerID = ? ORDER BY gameID DESC LIMIT 1',
                     (player_id,)).fetchone()[0]


def player_name(player_id: int) -> str:
    return c.execute('SELECT name FROM players WHERE playerID = ?', (player_id,)).fetchone()[0]


def last_session_data():
    return c.execute('SELECT * FROM sessions ORDER BY SessionID desc LIMIT 1').fetchone()


def last_two_sessions_dates():
    return c.execute('SELECT date FROM sessions ORDER BY SessionID DESC LIMIT 2').fetchall()


def games_this_month() -> int:
    return c.execute(
        "SELECT COUNT(*) FROM games WHERE strftime('%m', date) = strftime('%m',DATE()) AND strftime('%Y',date) = strftime('%Y',DATE())").fetchone()[
        0]


def games_this_year() -> int:
    return c.execute("SELECT COUNT(*) FROM games WHERE strftime('%Y',date) = strftime('%Y',DATE())").fetchone()[0]


def month_game_counts():
    return c.execute("SELECT strftime('%m-%Y',date) as d, COUNT(*) c FROM games GROUP BY d ORDER BY c DESC").fetchall()


# UNUSED #
def build_fun_facts():
    raise NotImplementedError()


def mvp_wins(player_id, start=1, end=None):
    if end is None:
        end = max_id()
    c.execute("""
        SELECT COUNT(playerID) AS MVPs FROM (
            SELECT wins.gameID, playerID, score
            FROM wins
            LEFT JOIN scores ON scores.gameID = wins.gameID
            WHERE wins.gameId >= ? AND wins.gameId <= ?
            GROUP BY wins.gameID
            HAVING MAX(score))
        WHERE playerID = ?""", (start, end, player_id))
    return c.fetchone()[0]


def team_solo_goals() -> int:
    return c.execute("SELECT SUM(goals) - SUM(assists) FROM scores").fetchone()[0]


def total_wins() -> int:
    return c.execute("SELECT COUNT(gameID) FROM games WHERE goals > against").fetchone()[0]


def total_losses() -> int:
    return c.execute("SELECT COUNT(gameID) FROM games WHERE goals < against").fetchone()[0]


def one_diff_wins() -> int:
    return c.execute("SELECT COUNT(gameID) FROM games WHERE goals - against = 1").fetchone()[0]


def one_diff_loss() -> int:
    return c.execute("SELECT COUNT(gameID) FROM games WHERE against - goals = 1").fetchone()[0]


def average_mvp_score() -> int:
    return c.execute(
        """SELECT AVG(scores.score) 
        FROM mvplvp JOIN scores ON mvplvp.MVP = scores.playerID AND mvplvp.gameID = scores.gameID""").fetchone()[0]


def average_lvp_score() -> int:
    return c.execute(
        """SELECT AVG(scores.score) 
        FROM mvplvp JOIN scores ON mvplvp.LVP = scores.playerID AND mvplvp.gameID = scores.gameID""").fetchone()[0]


# ???
def performance_agg(stat, mode, starting_game_id=1, games_considered=20):
    c.execute("""
        SELECT name, """ + mode + """(""" + stat + """)
            FROM(   SELECT scores.playerID, """ + stat + """, name
                    FROM scores JOIN players 
                    ON scores.playerID = players.playerID WHERE scores.gameID > """ + str(starting_game_id) + """
                    ORDER BY scores.gameID ASC LIMIT """ + str(games_considered) + """)
            GROUP BY playerID
    """)
    return c.fetchall()
