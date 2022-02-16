import sqlite3

database_path = '../resources/test.db'
conn = sqlite3.connect(database_path)
c = conn.cursor()

possible_stats = ['goals', 'assists', 'saves', 'shots']
possible_game_stats = ['goals', 'against']
possible_modes = ['AVG', 'SUM', 'MAX', 'MIN']


def allgemeine_game_stats(games):
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


def over_time_box_query(stat, start_index=0, end_index=20):
    c.execute("""
    WITH knusTable AS (SELECT SUM(""" + stat + """) s1, AVG(""" + stat + """) a1 FROM scores WHERE playerID = 0 AND gameID <= ? AND gameID >= ?),
	puadTable AS (SELECT SUM(""" + stat + """) s2, AVG(""" + stat + """) a2 FROM scores WHERE playerID = 1 AND gameID <= ? AND gameID >= ?),
	stickerTable AS (SELECT SUM(""" + stat + """) s3, AVG(""" + stat + """) a3 FROM scores WHERE playerID = 2 AND gameID <= ? AND gameID >= ?)
    SELECT s1, a1, s2, a2, s3, a3
    FROM knusTable, puadTable, stickerTable
    """, (end_index, start_index, end_index, start_index, end_index, start_index))
    return c.fetchone()


def general_game_stats_over_time_period(start_index=1, end_index=20):
    if start_index > end_index:
        raise ValueError(f'StartIndex was larger than EndIndex: {start_index} > {end_index}')
    elif start_index <= 0:
        raise ValueError("StartIndex can't be 0 or lower")

    data = {}
    wins = wins_in_range(start_index, end_index)
    losses = losses_in_range(start_index, end_index)
    games = end_index - start_index + 1
    goals = goals_in_range(start_index, end_index)
    against = against_in_range(start_index, end_index)
    data["General"] = [games, wins / games, goals, against, goals / games, against / games, wins, losses]
    data["Score"] = over_time_box_query("score", start_index, end_index)
    data["Goals"] = over_time_box_query("goals", start_index, end_index)
    data["Assists"] = over_time_box_query("assists", start_index, end_index)
    data["Saves"] = over_time_box_query("saves", start_index, end_index)
    data["Shots"] = over_time_box_query("shots", start_index, end_index)
    data["MVPs"] = mvp_helper_query(end_index, start_index)
    return data


def build_fun_facts():
    data = []
    games = total_games()
    wins = total_wins()
    knus_mvp = mvp(0)
    data.append(["Knus is MVP", knus_mvp / games, knus_mvp / wins])
    return 0


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
        WHERE playerID = """ + player_id + """
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


def total_games():
    c.execute("SELECT COUNT(*) FROM games")
    return c.fetchone()[0]


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
