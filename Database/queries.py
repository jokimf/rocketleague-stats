from Database import data_csv_to_db

conn = None
c = None

possible_stats = ['score', 'goals', 'assists', 'saves', 'shots']
possible_modes = ['avg', 'sum', 'max', 'min']
possible_game_stats = ['goals', 'against']


# The (sum/avg/min/max) of the (goals/goals against) of all games OUTPUT: Single number
def game_stat(game_stat, mode):
    if game_stat.lower() not in possible_game_stats or mode.lower() not in possible_modes:
        raise ValueError(game_stat + ' ' + mode + ' is not a legal parameter set')
    c.execute("SELECT " + mode + "(" + game_stat + ") FROM games")
    return c.fetchone()[0]


# The (sum/avg/min/max) of the (goals/goals against) of the last (trend) games OUTPUT: List
def trend_game_stat(game_stat, mode, trend=20):
    if game_stat.lower() not in possible_game_stats or mode.lower() not in possible_modes or trend > game_amount() or trend < 1:
        raise ValueError(game_stat + ' ' + mode + ' ' + trend + ' is not a legal parameter set')
    raise NotImplementedError()


# The MVP count for player x OUTPUT: Number
def mvp_count(player_id):
    if player_id not in [0, 1, 2]:
        raise ValueError('player_id not legal (' + str(player_id) + ')')
    c.execute("""
        SELECT COUNT(playerID)
        FROM (  SELECT playerID FROM scores 
                GROUP BY scores.gameID
                HAVING MAX(score))
		WHERE playerID = """ + str(player_id) + """
    """)
    return c.fetchone()[0]


# The running MVP count for player for all games OUTPUT: List
def mvp_count_over_time(player_id):
    if player_id not in [0, 1, 2]:
        raise ValueError('player_id not legal (' + str(player_id) + ')')
    c.execute("""
        SELECT COUNT(score) FILTER (WHERE playerID = """ + str(player_id) + """) OVER (ORDER BY gameID)
            FROM (
                SELECT gameID, playerID, score
                FROM scores
                GROUP BY gameID
                HAVING MAX(score))
    """)
    return c.fetchall()


# The running MVP count for player for the last (trend) games OUTPUT: List
def trend_mvp_count(player_id, trend=20):
    if player_id not in [0, 1, 2]:
        raise ValueError('player_id not legal (' + str(player_id) + ')')
    if trend < 1 or trend > game_amount():
        raise ValueError('trend not legal (' + str(trend) + ')')
    c.execute("""
        SELECT COUNT(playerID) FILTER (WHERE playerID = """ + str(player_id) + """)
        OVER (ORDER BY gameID ROWS BETWEEN """ + str(trend - 1) + """ PRECEDING AND CURRENT ROW)
        FROM (
            SELECT gameID, playerID, score
            FROM scores
            GROUP BY gameID
            HAVING MAX(score))
    """)
    return c.fetchall()


# The LVP count for player x OUTPUT: Number
def lvp_count(player_id):
    if player_id not in [0, 1, 2]:
        raise ValueError('player_id not legal (' + str(player_id) + ')')
    c.execute("""
        SELECT COUNT(playerID)
        FROM (  SELECT playerID FROM scores 
                GROUP BY scores.gameID
                HAVING MIN(score))
		WHERE playerID = """ + str(player_id) + """
    """)
    return c.fetchone()[0]


# The running LVP count for player for all games OUTPUT: List
def lvp_count_over_time(player_id):
    if player_id not in [0, 1, 2]:
        raise ValueError('player_id not legal (' + str(player_id) + ')')
    c.execute("""
        SELECT COUNT(score) FILTER (WHERE playerID = """ + str(player_id) + """) OVER (ORDER BY gameID)
            FROM (
                SELECT gameID, playerID, score
                FROM scores
                GROUP BY gameID
                HAVING MIN(score))
    """)
    return c.fetchall()


# The running LVP count for player for the last (trend) games OUTPUT: List
def trend_lvp_count(player_id, trend=20):
    if player_id not in [0, 1, 2]:
        raise ValueError('player_id not legal (' + str(player_id) + ')')
    if trend < 1 or trend > game_amount():
        raise ValueError('trend not legal (' + str(trend) + ')')
    c.execute("""
        SELECT COUNT(playerID) FILTER (WHERE playerID = """ + str(player_id) + """)
        OVER (ORDER BY gameID ROWS BETWEEN """ + str(trend - 1) + """ PRECEDING AND CURRENT ROW)
        FROM (
            SELECT gameID, playerID, score
            FROM scores
            GROUP BY gameID
            HAVING MIN(score))
    """)
    return c.fetchall()


# Players (avg/sum/min/max) of (score/goals/...) of all games OUTPUT: Number
# TODO implement player_id
def player_stat(player_id, stat, mode):
    if stat not in possible_stats or mode not in possible_modes:
        raise ValueError('Input: ' + stat + ' ' + mode + ' is not known for query.')

    c.execute("""
        SELECT name AS 'Player', """ + mode + """(""" + stat + """)
        FROM scores JOIN players ON scores.playerID = players.playerID
        GROUP BY scores.playerID
    """)
    return c.fetchall()


# Players running (avg/sum/min/max) of (score/goals/...) of all games OUTPUT: List
def player_stat_over_time(player_id, stat, mode):
    if stat not in possible_stats or mode not in possible_modes:
        raise ValueError(stat + ' is not a possible stat or ' + mode + ' is not a possible mode')
    c.execute("""
    WITH 
    player AS(
    SELECT """ + mode + """(""" + stat + """) OVER (ORDER BY GameID) AS tilt1
    FROM (SELECT gameID, playerID, """ + stat + """
    FROM scores) WHERE playerID = """ + str(player_id) + """)
    SELECT ROUND(tilt1,3) AS 'Player'
    FROM player
    """)
    return c.fetchall()


# Players running (avg/sum/min/max) of (score/goals/...) of the last (trend) games OUTPUT: List
def player_stat_trend_over_time(player_id, stat, mode, trend=20):
    if stat not in possible_stats or mode not in possible_modes:
        raise ValueError(stat + ' is not a possible stat or ' + mode + ' is not a possible mode')
    if trend > game_amount() or trend < 1:
        raise ValueError('Trend number is not legal (' + trend + ')')
    c.execute("""
        SELECT ROUND(""" + mode + """(""" + stat + """) OVER (ORDER BY gameID ROWS BETWEEN """ + str(trend - 1) + """ PRECEDING AND CURRENT ROW), 3)
        FROM scores
        WHERE playerID = """ + str(player_id))
    return c.fetchall()


# Amount of solo goals OUTPUT: number
def solo_goals():
    c.execute("SELECT SUM(goals) - SUM(assists) FROM scores")
    return c.fetchone()[0]


# Amount of solo goals over time OUTPUT: List
def solo_goals_over_time():
    raise NotImplementedError()


# Amount of wins OUTPUT: number
def total_wins():
    c.execute("SELECT COUNT(gameID) FROM games WHERE goals > against")
    return c.fetchone()[0]


# Amount of wins over time OUTPUT: List
def total_wins_over_time():
    raise NotImplementedError()


# Amount of losses OUTPUT: number
def total_losses():
    c.execute("SELECT COUNT(gameID) FROM games WHERE goals < against")
    return c.fetchone()[0]


# Amount of losses over time OUTPUT: List
def total_losses_over_time():
    raise NotImplementedError()


# Amount of wins with one goal difference OUTPUT: number
def one_diff_win():
    c.execute("SELECT COUNT(gameID) FROM games WHERE goals - against = 1")
    return c.fetchone()[0]


# Amount of wins over time with one goal difference OUTPUT: List
def one_diff_win_over_time():
    raise NotImplementedError()


# Amount of losses with one goal difference OUTPUT: number
def one_diff_loss():
    c.execute("SELECT COUNT(gameID) FROM games WHERE against - goals = 1")
    return c.fetchall()


# Amount of losses over time with one goal difference OUTPUT: List
def one_diff_loss():
    raise NotImplementedError()


# Max of (stat) achieved in one day OUTPUT: (Date, Count)
def most_one_day(stat):
    if stat not in possible_stats and not 'games':
        raise ValueError('Stat: ' + stat + ' is not known for most_one_day.')

    if stat == 'games':
        c.execute("SELECT date, MAX(Fisch) FROM(SELECT date, COUNT(date) AS Fisch FROM games GROUP BY date)")
    else:
        c.execute("SELECT date, MAX(Fisch) FROM(SELECT date, SUM(" + stat + ") AS Fisch FROM games GROUP BY date)")
    return c.fetchall()


# Average MVP Score OUTPUT: Number
def average_mvp_score():
    c.execute("""
        SELECT AVG(score)
        FROM (SELECT score FROM scores
        GROUP BY scores.gameID
        HAVING MAX(score))
    """)
    return c.fetchall()


# Average LVP Score OUTPUT: Number
def average_lvp_score():
    c.execute("""
        SELECT AVG(score)
        FROM (SELECT score FROM scores
        GROUP BY scores.gameID
        HAVING MIN(score))
    """)
    return c.fetchall()


# TODO: weekday as parameter, output as single number
# Amount of games per weekday OUTPUT: Number
def games_per_weekday():
    c.execute("""
        SELECT STRFTIME('%w', '20' || substr(date, -2, 2) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2)) AS WD, COUNT(date)
            FROM games
        GROUP BY WD
    """)
    return c.fetchall()


# TODO: weekday as parameter, output as single number
# Amount of wins per weekday OUTPUT: Number
def wins_per_weekday():
    c.execute("""
        SELECT STRFTIME('%w', '20' || substr(date, -2, 2) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2)) AS WD, COUNT(date)
            FROM (SELECT gameID, date FROM games WHERE goals > against)
        GROUP BY WD
    """)
    return c.fetchall()


# (AVG/SUM/MAX/MIN) of (stat) for every player OUTPUT: (Name, Value)
def query_last_20(stat, mode):
    if stat not in possible_stats or mode not in possible_modes:
        raise ValueError('stat or mode invalid in query_last_20. stat=' + stat + ' mode=' + mode)

    c.execute("""
        SELECT name, """ + mode + """(""" + stat + """)
        FROM(   SELECT scores.playerID, """ + stat + """, name
                FROM scores JOIN players ON scores.playerID = players.playerID
                ORDER BY scores.gameID DESC LIMIT 60)
        GROUP BY playerID
    """)
    return c.fetchall()


# TODO random ass query, find out what it does
def performance_agg(stat, mode, starting_game_id=0, games_considered=20):
    c.execute("""
        SELECT name, """ + mode + """(""" + stat + """)
            FROM(   SELECT scores.playerID, """ + stat + """, name
                    FROM scores JOIN players 
                    ON scores.playerID = players.playerID WHERE scores.gameID > """ + str(starting_game_id) + """
                    ORDER BY scores.gameID ASC LIMIT """ + str(games_considered * 3) + """)
            GROUP BY playerID
    """)
    return c.fetchall()


# Game amount OUTPUT: Number
def game_amount():
    c.execute("SELECT COUNT(*) FROM games")
    return c.fetchone()[0]


# MVP Streaks for player, Ranking OUTPUT: (Streak, Start, End)
def mvp_streak(player_id):
    c.execute("""
    WITH MVPs AS (SELECT row_number() OVER (Order BY gameID) as 'RowNr',
    gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID
    FROM (SELECT gameID, score, playerID
        FROM scores
        GROUP BY gameID
        HAVING MAX(score) AND playerID = """ + str(player_id) + """) AS MVPTable
        )
        SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
        FROM MVPs
        GROUP BY grouper
        ORDER BY 1 DESC, 2 ASC
    """)
    return c.fetchall()


# Displays the last x games like the sheet does #OUTPUT: (ID, Date, G, GA, K, P, S)
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


# Returns stat by game_id OUTPUT: (GameID, Date, G, GA, K, P, S)
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
            WHERE ID = """ + str(game_id) + """
            GROUP BY ID ORDER BY ID DESC
    """)
    return c.fetchmany()


# Must be called to initialize Database connection
def init():
    global conn, c
    conn = data_csv_to_db.create_connection('test.db')
    c = conn.cursor()
