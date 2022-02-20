import sqlite3

database_path = '../resources/test.db'
conn = sqlite3.connect(database_path)
c = conn.cursor()

possible_stats = ['goals', 'assists', 'saves', 'shots']
possible_game_stats = ['goals', 'against']
possible_modes = ['AVG', 'SUM', 'MAX', 'MIN']


def weekdays():
    # output:    Weekday, W/R, Amount, W, L
    raise NotImplementedError()


def months():
    # output:    Month, W/R, Amount, W, L
    raise NotImplementedError()


def years():
    # output:    Weekday, W/R, Amount, W, L
    raise NotImplementedError()


def dates():
    # output:    Weekday, W/R, Amount, W, L
    raise NotImplementedError()


def goals_without_assist(start=0, end=None):
    if end is None:
        end = total_games()
    # output: Count, Occurrence, Winrate
    raise NotImplementedError()


def days_since_inception():
    raise NotImplementedError()


def longest_winning_streak():
    # output: Streak, GameID von bis
    raise NotImplementedError()


def longest_losing_streak():
    # output: Streak, GameID von bis
    raise NotImplementedError()


def mvp_streak(player_id):
    c.execute("""
    WITH MVPs AS (SELECT row_number() OVER (Order BY gameID) as 'RowNr',
    gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID
    FROM (SELECT gameID, score, playerID
        FROM scores
        GROUP BY gameID
        HAVING MAX(score) AND playerID = """ + player_id + """) AS MVPTable
        )
        SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
        FROM MVPs
        GROUP BY grouper
        ORDER BY 1 DESC, 2 ASC
    """)
    return c.fetchall()


def not_mvp_streak(player):
    raise NotImplementedError()


def not_lvp_streak(player):
    raise NotImplementedError()


def lvp_streak(player):
    raise NotImplementedError()


def average_games_per_day(start=0, end=None):
    if end is None:
        end = max_id()
    return total_games(start, end) / days_since_inception()


def general_game_stats(games):
    c.execute("""
        WITH
            scores0 AS (SELECT * FROM scores WHERE playerID = 0 GROUP BY gameID),
            scores1 AS (SELECT * FROM scores WHERE playerID = 1 GROUP BY gameID),
            scores2 AS (SELECT * FROM scores WHERE playerID = 2 GROUP BY gameID)
            SELECT 
                games.gameID AS ID,    games.date AS 'Date', games.goals As CG, against AS Enemy,
                scores0.rank AS RankK, scores0.score AS ScoreK, scores0.goals AS GoalsK, scores0.assists AS AssistsK, scores0.saves AS SavesK, scores0.shots AS ShotsK,
                scores1.rank AS RankP, scores1.score AS ScoreP, scores1.goals AS GoalsP, scores1.assists AS AssistsP, scores1.saves AS SavesP, scores1.shots AS ShotsP,
                scores2.rank AS RankS, scores2.score AS 'ScoreS', scores2.goals AS GoalsS, scores2.assists AS AssistsS,    scores2.saves AS SavesS, scores2.shots AS ShotsS
            FROM games JOIN scores ON games.gameID = scores.gameID JOIN scores0 ON games.gameID = scores0.gameID JOIN scores1 ON games.gameID = scores1.gameID JOIN scores2 ON games.gameID = scores2.gameID
            GROUP BY ID ORDER BY ID DESC
    """)
    return c.fetchmany(games)


def over_time_box_query(stat, start=0, end=None):
    if start < 0 or end < 0 or end < start:
        raise ValueError(f"Illegal combination of start and end index. (s={start}, e={end})")
    if end is None:
        end = max_id()
    c.execute("""
    WITH knusTable AS (SELECT SUM(""" + stat + """) s1, AVG(""" + stat + """) a1 FROM scores WHERE playerID = 0 AND gameID <= ? AND gameID >= ?),
	puadTable AS (SELECT SUM(""" + stat + """) s2, AVG(""" + stat + """) a2 FROM scores WHERE playerID = 1 AND gameID <= ? AND gameID >= ?),
	stickerTable AS (SELECT SUM(""" + stat + """) s3, AVG(""" + stat + """) a3 FROM scores WHERE playerID = 2 AND gameID <= ? AND gameID >= ?)
    SELECT s1, a1, s2, a2, s3, a3
    FROM knusTable, puadTable, stickerTable
    """, (end, start, end, start, end, start))
    return c.fetchone()


def general_game_stats_over_time_period(start=1, end=None):
    if end is None:
        end = max_id()
    if start > end:
        raise ValueError(f'StartIndex was larger than EndIndex: {start} > {end}')
    if start <= 0:
        raise ValueError("StartIndex can't be 0 or lower")

    wins = wins_in_range(start, end)
    losses = losses_in_range(start, end)
    games = end - start + 1
    goals = goals_in_range(start, end)
    against = against_in_range(start, end)
    data = {
        "General": [games, wins / games, goals, against, goals / games, against / games, wins, losses],
        "Score": over_time_box_query("score", start, end),
        "Goals": over_time_box_query("goals", start, end),
        "Assists": over_time_box_query("assists", start, end),
        "Saves": over_time_box_query("saves", start, end),
        "Shots": over_time_box_query("shots", start, end),
        "MVPs": mvp_helper_query(end, start)}
    return data


def mvp_helper_query(end_index, start_index):
    return c.execute("""
    WITH knusTable AS (SELECT 
	SUM(CASE playerID WHEN 0 THEN 1 ELSE 0 END), CAST(SUM(CASE playerID WHEN 0 THEN 1 ELSE 0 END) AS FLOAT) / CAST(COUNT(playerID) AS FLOAT) * 100
    FROM(SELECT playerID, gameID, score FROM scores GROUP BY scores.gameID HAVING MAX(score))WHERE gameID <= ? AND gameID >= ?),
	puadTable AS (SELECT 
	SUM(CASE playerID WHEN 1 THEN 1 ELSE 0 END), CAST(SUM(CASE playerID WHEN 1 THEN 1 ELSE 0 END) AS FLOAT) / CAST(COUNT(playerID) AS FLOAT) * 100
    FROM(SELECT playerID, gameID, score FROM scores GROUP BY scores.gameID HAVING MAX(score))WHERE gameID <= ? AND gameID >= ?),
	stickerTable AS (SELECT 
	SUM(CASE playerID WHEN 2 THEN 1 ELSE 0 END), CAST(SUM(CASE playerID WHEN 2 THEN 1 ELSE 0 END) AS FLOAT) / CAST(COUNT(playerID) AS FLOAT) * 100
    FROM(SELECT playerID, gameID, score FROM scores GROUP BY scores.gameID HAVING MAX(score))WHERE gameID <= ? AND gameID >= ?)
    SELECT * FROM knusTable, puadTable, stickerTable
    """, (end_index, start_index, end_index, start_index, end_index, start_index)).fetchone()


def goals_in_range(start_index, end_index):
    c.execute("SELECT SUM(goals) FROM games WHERE gameID >= ? AND gameID <= ?", (start_index, end_index))
    return c.fetchone()[0]


def against_in_range(start_index, end_index):
    c.execute("SELECT SUM(against) FROM games WHERE gameID >= ? AND gameID <= ?", (start_index, end_index))
    return c.fetchone()[0]


def wins_in_range(start_index, end_index):
    c.execute("SELECT COUNT(gameID) FROM games WHERE goals > against AND gameID >= ? AND gameID <= ?",
              (start_index, end_index))
    return c.fetchone()[0]


def losses_in_range(start_index, end_index):
    c.execute("SELECT COUNT(gameID) FROM games WHERE against > goals AND gameID >= ? AND gameID <= ?",
              (start_index, end_index))
    return c.fetchone()[0]


def build_fun_facts():
    data = []
    games = total_games()
    wins = total_wins()
    knus_mvp = mvp(0)
    # data.append(["Knus is MVP", knus_mvp / games, knus_mvp / wins])
    return 0


def sum_of_game_stat(stat):
    if stat not in possible_game_stats:
        raise ValueError('Stat: ' + stat + ' is not known for query.')
    c.execute("SELECT SUM(?) FROM games", stat)
    return c.fetchone()[0]


def mvp(player_id):
    c.execute("""
        SELECT COUNT(playerID) AS MVPs
        FROM (  SELECT gameID, playerID, score
                FROM scores
                GROUP BY scores.gameID
                HAVING MAX(score))
        WHERE playerID = """ + str(player_id) + """
    """)
    return c.fetchall()


def player_stats(stat, mode, player_id):
    if stat not in possible_stats or mode not in possible_modes:
        raise ValueError(f'Input: {stat}{mode} {str(player_id)}  is not known for query.')

    c.execute("""
        SELECT name AS 'Player', """ + mode + """(""" + stat + """)
        FROM scores JOIN players ON scores.playerID = players.playerID
        WHERE scores.playerID = """ + player_id + """
        GROUP BY scores.playerID
    """)
    return c.fetchall()


def solo_goals():
    c.execute("SELECT SUM(goals) - SUM(assists) FROM scores")
    return c.fetchone()[0]


def total_wins():
    c.execute("SELECT COUNT(gameID) FROM games WHERE goals > against")
    return c.fetchone()[0]


def total_losses():
    c.execute("SELECT COUNT(gameID) FROM games WHERE goals < against")
    return c.fetchone()[0]


def one_diff_win():
    c.execute("SELECT COUNT(gameID) FROM games WHERE goals - against = 1")
    return c.fetchone()[0]


def one_diff_loss():
    c.execute("SELECT COUNT(gameID) FROM games WHERE against - goals = 1")
    return c.fetchall()


def most_one_day(stat):
    if stat not in possible_stats and not 'games':
        raise ValueError(f'Stat: {stat} is not known for most_one_day.')

    if stat == 'games':
        c.execute("SELECT date, MAX(Fisch) FROM(SELECT date, COUNT(date) AS Fisch FROM games GROUP BY date)")
    else:
        c.execute("SELECT date, MAX(Fisch) FROM(SELECT date, SUM(" + stat + ") AS Fisch FROM games GROUP BY date)")
    return c.fetchall()


def average_mvp_score():
    c.execute("""
        SELECT AVG(score)
        FROM (SELECT score FROM scores
        GROUP BY scores.gameID
        HAVING MAX(score))
    """)
    return c.fetchall()


def average_lvp_score():
    c.execute("""
        SELECT AVG(score)
        FROM (SELECT score FROM scores
        GROUP BY scores.gameID
        HAVING MIN(score))
    """)
    return c.fetchall()


def games_per_weekday():
    c.execute("""
        SELECT STRFTIME('%w', '20' || substr(date, -2, 2) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2)) AS WD, COUNT(date)
            FROM games
        GROUP BY WD
    """)
    return c.fetchall()


def wins_per_weekday():
    c.execute("""
        SELECT STRFTIME('%w', '20' || substr(date, -2, 2) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2)) AS WD, COUNT(date)
            FROM (SELECT gameID, date FROM games WHERE goals > against)
        GROUP BY WD
    """)
    return c.fetchall()


def latest_date():
    c.execute(
        "SELECT MAX(STRFTIME('20' || substr(date, -2, 2) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2))) FROM games")
    return c.fetchone()


def query_last_20(stat, mode, player):
    if stat not in possible_stats or mode not in possible_modes:
        raise ValueError(f'stat or mode invalid in query_last_20. stat={stat} mode={mode}')

    c.execute("""
        SELECT name, """ + mode + """(""" + stat + """)
        FROM(   SELECT scores.playerID, """ + stat + """, name
                FROM scores JOIN players ON scores.playerID = players.playerID
                ORDER BY scores.gameID DESC LIMIT 60)
        GROUP BY playerID
    """)
    return c.fetchall()


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


def total_games(start=1, end=None):
    if end is None:
        end = max_id()
    c.execute("SELECT COUNT(*) FROM games WHERE gameID >= ? AND gameID <= ?", (start, end))
    return c.fetchone()[0]


def max_id():
    c.execute("SELECT MAX(gameID) FROM games")
    return c.fetchone()


def stat_by_game_id(game_id):
    c.execute("""
    WITH
            scores0 AS (SELECT * FROM scores WHERE playerID = 0 GROUP BY gameID),
            scores1 AS (SELECT * FROM scores WHERE playerID = 1 GROUP BY gameID),
            scores2 AS (SELECT * FROM scores WHERE playerID = 2 GROUP BY gameID)
            SELECT 
                games.gameID AS ID,    games.date AS 'Date', games.goals As CG, against AS Enemy,
                scores0.rank AS RankK, scores0.score AS ScoreK, scores0.goals AS GoalsK, scores0.assists AS AssistsK, scores0.saves AS SavesK, scores0.shots AS ShotsK,
                scores1.rank AS RankP, scores1.score AS ScoreP, scores1.goals AS GoalsP, scores1.assists AS AssistsP, scores1.saves AS SavesP, scores1.shots AS ShotsP,
                scores2.rank AS RankS, scores2.score AS 'ScoreS', scores2.goals AS GoalsS, scores2.assists AS AssistsS,    scores2.saves AS SavesS, scores2.shots AS ShotsS
            FROM games JOIN scores ON games.gameID = scores.gameID JOIN scores0 ON games.gameID = scores0.gameID JOIN scores1 ON games.gameID = scores1.gameID JOIN scores2 ON games.gameID = scores2.gameID
            WHERE ID = """ + game_id + """
            GROUP BY ID ORDER BY ID DESC
    """)
    return c.fetchmany()
