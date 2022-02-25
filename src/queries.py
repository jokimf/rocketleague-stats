import sqlite3

database_path = '../resources/test.db'
conn = sqlite3.connect(database_path)
c = conn.cursor()

possible_stats = ['score', 'goals', 'assists', 'saves', 'shots']
possible_game_stats = ['goals', 'against']
possible_modes = ['AVG', 'SUM', 'MAX', 'MIN']


def max_id():
    c.execute("SELECT MAX(gameID) FROM games")
    return c.fetchone()[0]


def weekdays():
    c.execute('''
    SELECT  STRFTIME('%w', '20' || substr(date, -2, 2) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2)) AS WD, 
            COUNT(date), SUM(CASE WHEN goals > against THEN 1 ELSE 0 END),
            SUM(CASE WHEN goals < against THEN 1 ELSE 0 END)
    FROM games GROUP BY WD''')
    new = []
    for x in c.fetchall():
        helper = list(x)
        helper.insert(2, x[2] / (x[2] + x[3]))
        new.append(helper)

    days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    for i in range(0, 7):
        new[i][0] = days[i]

    new = new[1:] + new[0]  # put Sunday at the back of the list
    return new


def months():
    c.execute("""
    SELECT  STRFTIME('%m', '20' || substr(date, -2, 2) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2)) AS m, 
            COUNT(date), SUM(CASE WHEN goals > against THEN 1 ELSE 0 END), 
            SUM(CASE WHEN goals < against THEN 1 ELSE 0 END)
    FROM games GROUP BY m""")
    values_done = []
    for x in c.fetchall():
        new_value = [x[0], x[1], x[2] / (x[2] + x[3]), x[2], x[3]]
        values_done.append(new_value)

    month = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
             "November", "December"]
    for i in range(0, 12):
        values_done[i][0] = month[i]
    return values_done


def years():
    c.execute("""
    SELECT  STRFTIME('%Y', '20' || substr(date, -2, 2) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2)) AS Y,
            COUNT(date), SUM(CASE WHEN goals > against THEN 1 ELSE 0 END),
            SUM(CASE WHEN goals < against THEN 1 ELSE 0 END)
    FROM games GROUP BY Y""")
    values_done = []
    for x in c.fetchall():
        wrate = x[2] / (x[2] + x[3])
        new_value = [x[0], x[1], wrate, x[2], x[3]]
        values_done.append(new_value)
    return values_done


def dates():
    c.execute("""
    SELECT  STRFTIME('%d', '20' || substr(date, -2, 2) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2)) AS d,
            COUNT(date), SUM(CASE WHEN goals > against THEN 1 ELSE 0 END), 
            SUM(CASE WHEN goals < against THEN 1 ELSE 0 END)
    FROM games GROUP BY d
    """)
    raw_values = c.fetchall()
    values_done = []
    for x in raw_values:
        wrate = x[2] / (x[2] + x[3])
        new_value = [x[0], x[1], wrate, x[2], x[3]]
        values_done.append(new_value)
    return values_done


def goals_without_assist(start=0, end=None):
    if end is None:
        end = max_id()
    c.execute("""
    SELECT SUM(goalsSum - assistsSum) AS diff FROM(
        SELECT SUM(assists) AS assistsSum, SUM(goals) AS goalsSum 
        FROM scores WHERE gameID >= ? AND gameID <= ? GROUP BY gameID)
    """, (start, end))
    return c.fetchone()[0]


def days_since_inception():
    c.execute("""
    SELECT julianday(MAX(dateF)) - julianday(MIN(dateF))
    FROM (
    SELECT STRFTIME('20' || substr(date, -2, 2) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2)) AS dateF
    FROM games)h
    """)
    return c.fetchone()[0]


def longest_winning_streak():
    c.execute("""
    WITH Streaks AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
    gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID
    FROM (SELECT gameID
        FROM games
        WHERE goals > against)h)
        SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
        FROM Streaks
        GROUP BY grouper
        ORDER BY 1 DESC, 2 ASC
    """)
    return c.fetchone()[0]


def longest_losing_streak():
    c.execute("""
    WITH Streaks AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
    gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID
    FROM (SELECT gameID
        FROM games
        WHERE goals < against)h)
        SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
        FROM Streaks
        GROUP BY grouper
        ORDER BY 1 DESC, 2 ASC
    """)
    return c.fetchone()[0]


def mvp_streak(player_id):
    c.execute("""
    WITH MVPs AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
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


def not_mvp_streak(player_id):
    c.execute("""
    WITH helperTable AS(
        SELECT gameID AS helperID, score, playerID
        FROM scores GROUP BY helperID
        HAVING MAX(score) AND playerID = ?),
    NotMVPs AS (SELECT row_number() OVER (Order BY gameID) AS 'RowNr',
    gameID - row_number() OVER (ORDER BY gameID) AS grouper, gameID FROM (
    SELECT gameID FROM games,helperTable 
    GROUP BY gameID HAVING gameID NOT IN (SELECT helperID FROM helperTable)) AS NotMVPTable)
        SELECT COUNT(*) AS Streak, MIN(gameId) AS 'Start', MAX(gameId) AS 'End'
        FROM NotMVPs GROUP BY grouper ORDER BY 1 DESC, 2 ASC LIMIT 5
    """, (player_id,))
    return c.fetchall()


def not_lvp_streak(player_id):
    c.execute("""
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
    """, (player_id,))
    return c.fetchall()


def lvp_streak(player_id):
    c.execute("""
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
    """, (player_id,))
    return c.fetchall()


def average_games_per_day(start=0, end=None):
    if end is None:
        end = max_id()
    return total_games(start, end) / days_since_inception()


def last_x_games_stats(amount):
    c.execute("""
        WITH
            scores0 AS (SELECT * FROM scores WHERE playerID = 0 GROUP BY gameID),
            scores1 AS (SELECT * FROM scores WHERE playerID = 1 GROUP BY gameID),
            scores2 AS (SELECT * FROM scores WHERE playerID = 2 GROUP BY gameID)
            SELECT 
                games.gameID AS ID,    games.date AS 'Date', games.goals As CG, against AS Enemy,
                scores0.rank, scores0.score, scores0.goals, scores0.assists, scores0.saves, scores0.shots,
                scores1.rank, scores1.score, scores1.goals, scores1.assists, scores1.saves, scores1.shots,
                scores2.rank, scores2.score, scores2.goals, scores2.assists, scores2.saves, scores2.shots
            FROM games JOIN scores ON games.gameID = scores.gameID JOIN scores0 ON games.gameID = scores0.gameID 
                JOIN scores1 ON games.gameID = scores1.gameID JOIN scores2 ON games.gameID = scores2.gameID
            GROUP BY ID ORDER BY ID DESC
    """)
    return c.fetchmany(amount)


def general_game_stats_over_time_period(start=1, end=None):
    # Input validation
    if end is None:
        end = max_id()
    if start > end:
        raise ValueError(f'StartIndex was larger than EndIndex: {start} > {end}')
    if start <= 0:
        raise ValueError("StartIndex can't be 0 or lower")

    # Nested helper function
    def over_time_box_query(stat, start2, end2):
        c.execute("""
        WITH knusTable AS (SELECT SUM(""" + stat + """) s1, AVG(""" + stat + """) a1 
            FROM scores WHERE playerID = 0 AND gameID <= ? AND gameID >= ?),
        puadTable AS (SELECT SUM(""" + stat + """) s2, AVG(""" + stat + """) a2
            FROM scores WHERE playerID = 1 AND gameID <= ? AND gameID >= ?),
        stickerTable AS (SELECT SUM(""" + stat + """) s3, AVG(""" + stat + """) a3
            FROM scores WHERE playerID = 2 AND gameID <= ? AND gameID >= ?)
        SELECT s1, a1, s2, a2, s3, a3
        FROM knusTable, puadTable, stickerTable
        """, (end2, start2, end2, start2, end2, start2))
        return c.fetchone()

    def mvp_helper_query(end_index, start_index):
        c.execute("""
        WITH 
        knusTable AS (SELECT SUM(CASE playerID WHEN 0 THEN 1 ELSE 0 END), 
            CAST(SUM(CASE playerID WHEN 0 THEN 1 ELSE 0 END) AS FLOAT) / CAST(COUNT(playerID) AS FLOAT) * 100
        FROM(SELECT playerID, gameID, score FROM scores GROUP BY scores.gameID HAVING MAX(score)) 
        WHERE gameID <= ? AND gameID >= ?),
        puadTable AS (SELECT SUM(CASE playerID WHEN 1 THEN 1 ELSE 0 END),
            CAST(SUM(CASE playerID WHEN 1 THEN 1 ELSE 0 END) AS FLOAT) / CAST(COUNT(playerID) AS FLOAT) * 100
        FROM(SELECT playerID, gameID, score FROM scores GROUP BY scores.gameID HAVING MAX(score))
        WHERE gameID <= ? AND gameID >= ?),
        stickerTable AS (SELECT SUM(CASE playerID WHEN 2 THEN 1 ELSE 0 END),
            CAST(SUM(CASE playerID WHEN 2 THEN 1 ELSE 0 END) AS FLOAT) / CAST(COUNT(playerID) AS FLOAT) * 100
        FROM(SELECT playerID, gameID, score FROM scores GROUP BY scores.gameID HAVING MAX(score))
        WHERE gameID <= ? AND gameID >= ?)
        SELECT * FROM knusTable, puadTable, stickerTable
        """, (end_index, start_index, end_index, start_index, end_index, start_index))
        return c.fetchone()

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


# TODO: use start/end in query
def mvp(player_id, start=1, end=None):
    if end is None:
        end = max_id()
    c.execute("""
        SELECT COUNT(playerID) AS MVPs FROM (
            SELECT gameID, playerID, score
            FROM scores
            WHERE gameId >= ? AND gameId <= ?
            GROUP BY scores.gameID
            HAVING MAX(score))
        WHERE playerID = ?""", (start, end, player_id))
    return c.fetchone()[0]


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


# unused
def player_stats(stat, mode, player_id):
    if stat not in possible_stats or mode not in possible_modes:
        raise ValueError(f'Input: {stat}{mode} {str(player_id)}  is not known for query.')

    c.execute("""
        SELECT name AS 'Player', """ + mode + """(""" + stat + """)
        FROM scores JOIN players ON scores.playerID = players.playerID
        WHERE scores.playerID = """ + str(player_id) + """
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
        c.execute("SELECT date, MAX(counter) FROM(SELECT date, COUNT(date) AS counter FROM games GROUP BY date)")
    else:
        c.execute("SELECT date, MAX(counter) FROM(SELECT date, SUM(" + stat + ") AS counter FROM games GROUP BY date)")
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
        SELECT STRFTIME('%w', '20' || substr(date, -2, 2) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2)) 
            AS WD, COUNT(date)
        FROM games
        GROUP BY WD
    """)
    return c.fetchall()


def wins_per_weekday():
    c.execute("""
        SELECT STRFTIME('%w', '20' || substr(date, -2, 2) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2)) 
            AS WD, COUNT(date)
        FROM (SELECT gameID, date FROM games WHERE goals > against)
        GROUP BY WD
    """)
    return c.fetchall()


def latest_date():
    c.execute(
        """SELECT MAX(STRFTIME('20' || substr(date, -2, 2) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2)))
        FROM games""")
    return c.fetchone()[0]


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


def stat_by_game_id(game_id):
    c.execute("""
    WITH
            scores0 AS (SELECT * FROM scores WHERE playerID = 0 GROUP BY gameID),
            scores1 AS (SELECT * FROM scores WHERE playerID = 1 GROUP BY gameID),
            scores2 AS (SELECT * FROM scores WHERE playerID = 2 GROUP BY gameID)
            SELECT 
                games.gameID AS ID,    games.date AS 'Date', games.goals As CG, against AS Enemy,
                scores0.rank, scores0.score, scores0.goals, scores0.assists, scores0.saves, scores0.shots,
                scores1.rank, scores1.score, scores1.goals, scores1.assists, scores1.saves, scores1.shots,
                scores2.rank, scores2.score, scores2.goals, scores2.assists, scores2.saves, scores2.shots
            FROM games JOIN scores ON games.gameID = scores.gameID JOIN scores0 ON games.gameID = scores0.gameID 
                JOIN scores1 ON games.gameID = scores1.gameID JOIN scores2 ON games.gameID = scores2.gameID
            WHERE ID = """ + str(game_id) + """
            GROUP BY ID ORDER BY ID DESC
    """)
    return c.fetchmany()


def query_last_x(games, stat, mode):
    if stat not in possible_stats or mode not in possible_modes:
        raise ValueError(f'stat or mode invalid in query_last_20. stat={stat} mode={mode}')
    c.execute("""
        SELECT name, """ + mode + """(""" + stat + """)
        FROM(   SELECT scores.playerID, """ + stat + """, name
                FROM scores JOIN players ON scores.playerID = players.playerID
                ORDER BY scores.gameID DESC LIMIT ?*3)
        GROUP BY playerID
    """, (games,))
    return c.fetchall()


def build_fun_facts():
    data = []
    games = max_id()
    wins = total_wins()
    knus_mvp = mvp(0)


def score_performance(show=5, games_considered=20):
    # Output: GameID, K, P, S
    #           234, 233,231,123
    #           233, 212,123,123
    raise NotImplementedError()


# Ignored because graphs will display better data
def trend_box():
    trend = []
    for stat in possible_stats:
        c.execute("""
        SELECT AVG(""" + stat + """) FROM(   
            SELECT * FROM scores JOIN players ON scores.playerID = players.playerID
            ORDER BY scores.gameID DESC LIMIT 20*3
        )
        GROUP BY playerID
        """)
        trend.append([x[0] for x in c.fetchall()])
    return trend


def mvp_count(player_id, start=1, end=None):
    # Vielleicht mvp(player_id) so anpassen, dass man sie auf 'games' und 'wins' anwenden kann
    # Output: Occurrence, Winrate
    if end is None:
        end = max_id()
    raise NotImplementedError()


def solo_carry(player_id, start=1, end=None):
    # p1 > p2+p3
    # Output: Occurrence, Winrate
    if end is None:
        end = max_id()
    raise NotImplementedError()


def more_than_500(player_id, start=1, end=None):
    # player got more than 500 in one game
    # Output: Occurrence, Winrate
    if end is None:
        end = max_id()
    raise NotImplementedError()


def everyone_scored(start=1, end=None):
    # Output: Occurrence, Winrate
    if end is None:
        end = max_id()
    raise NotImplementedError()


def did_not_score(player_id, start=1, end=None):
    # Output: Occurrence, Winrate
    if end is None:
        end = max_id()
    raise NotImplementedError()


def no_solo_goals(start=1, end=None):
    # Output: Occurrence, Winrate
    if end is None:
        end = max_id()
    raise NotImplementedError()


def six_or_more_shots(start=1, end=None):
    # Output: Occurrence, Winrate
    if end is None:
        end = max_id()
    raise NotImplementedError()


def at_least_one_assist(player_id, start=1, end=None):
    # Output: Occurrence, Winrate
    if end is None:
        end = max_id()
    raise NotImplementedError()


def two_or_more_saves(player_id, start=1, end=None):
    # Output: Occurrence, Winrate
    if end is None:
        end = max_id()
    raise NotImplementedError()


def irrelevant(player_id, start=1, end=None):
    # Irrelevant: Sum of all averages / 7.5
    # Output: Occurrence, Winrate
    if end is None:
        end = max_id()
    raise NotImplementedError()


def team_scores_x_times(x, start=1, end=None):
    # x = (1) bis (5 or more)
    # Output: Occurrence, Winrate
    if end is None:
        end = max_id()
    raise NotImplementedError()


def team_concedes_x_times(x, start=1, end=None):
    # x = (1) bis (5 or more)
    # Output: Occurrence, Winrate
    if end is None:
        end = max_id()
    raise NotImplementedError()


def results():
    # Result, Amount, %
    raise NotImplementedError()


# RECORD GAMES

def build_record_games():
    def highest_player(stat):
        if stat == 'goals':
            stat = 'scores.goals'

        c.execute('''
            SELECT name, ''' + stat + ''', games.gameID, date 
            FROM games JOIN scores ON games.gameID = scores.gameID NATURAL JOIN players
            ORDER BY ''' + stat + ''' DESC''')
        return c.fetchmany(3)

    def most_points_without_goal():
        c.execute('''
        SELECT name, score, games.gameID, date 
        FROM games JOIN scores ON games.gameID = scores.gameID NATURAL JOIN players
        WHERE scores.goals = 0
        ORDER BY score DESC''')
        return c.fetchmany(3)

    def least_points_with_goals():
        c.execute('''
        SELECT name, score, games.gameID, date 
        FROM games JOIN scores ON games.gameID = scores.gameID NATURAL JOIN players
        WHERE scores.goals > 0
        ORDER BY score ASC''')
        return c.fetchmany(3)

    def most_against():
        c.execute('SELECT "", against, gameID, date FROM games ORDER BY against DESC')
        return c.fetchmany(3)

    def most_against_and_won():
        c.execute('SELECT "", against, gameID, date FROM games WHERE goals > against ORDER BY against DESC')
        return c.fetchmany(3)

    def most_goals_and_lost():
        c.execute('SELECT "", goals, gameID, date FROM games WHERE goals < against ORDER BY goals DESC')
        return c.fetchmany(3)

    def most_total_goals():
        c.execute('SELECT "",goals+against, gameID, date FROM games ORDER BY goals + against DESC')
        return c.fetchmany(3)

    def highest_team(stat):
        if stat == 'goals':
            stat = 'scores.goals'
        c.execute('''
            SELECT SUM(''' + stat + ''') AS stat, games.gameID, date 
            FROM games JOIN scores ON games.gameID = scores.gameID 
            GROUP BY games.gameID ORDER BY stat DESC
        ''')
        return c.fetchmany(3)

    data = {
        'Highest Score by player': highest_player('score'),
        'Most goals by player': highest_player('goals'),
        'Most assists by player': highest_player('assists'),
        'Most saves by player': highest_player('saves'),
        'Most shots by player': highest_player('shots'),
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
        'Most total goals': most_total_goals()
    }
    return data


print(x) for x in build_record_games()
