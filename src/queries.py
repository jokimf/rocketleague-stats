import datetime
import sqlite3
from typing import Any

import database

database_path = 'resources/test.db'
conn = database.connect_to_database()
c = conn.cursor()

possible_stats = ['score', 'goals', 'assists', 'saves', 'shots']


def last_reload():
    return c.execute('SELECT last_reload FROM meta').fetchone()[0]


def set_last_reload(last_reload: int) -> None:
    c.execute('UPDATE meta SET last_reload = ?', (last_reload,))
    conn.commit()


def total_games() -> int:
    return c.execute("SELECT MAX(gameID) FROM games").fetchone()[0]


# Inserts game data fetched from Google Sheets API
def insert_game_data(d: list) -> bool:
    try:
        c.execute('INSERT INTO games VALUES (?,?,?,?)', (d[0], d[1], d[3], d[4]))
        c.execute('INSERT INTO scores VALUES (?,?,?,?,?,?,?,?)', (d[0], 0, d[5], d[6], d[7], d[8], d[9], d[10]))
        c.execute('INSERT INTO scores VALUES (?,?,?,?,?,?,?,?)', (d[0], 1, d[11], d[12], d[13], d[14], d[15], d[16]))
        c.execute('INSERT INTO scores VALUES (?,?,?,?,?,?,?,?)', (d[0], 2, d[17], d[18], d[19], d[20], d[21], d[22]))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(e)
        return False


def conditional_formatting(color: str, value: float, minimum: int, maximum: int) -> str:
    minimum = int(minimum)
    maximum = int(maximum)
    if color is None or (type(value) is not float and type(value) is not int):
        raise ValueError(f"Color can't be None and value needs to be int or float: color={color}, value={type(value)}")
    if maximum - minimum == 0:
        return f'{color[:-1]},0)'
    opacity = (value - minimum) / (maximum - minimum)
    rgb_code = f'{color[:-1]},{opacity})'
    return rgb_code


def fade_highlighting(game: int, game_range: int):
    return f'rgba(53, 159, 159,{(game_range - (total_games() - game)) / game_range})'


# Returns number of days since first game played
def days_since_first() -> int:
    return c.execute('SELECT julianday(DATE()) - julianday(MIN(date)) FROM games').fetchone()[0]


def last_x_games_stats(limit, with_date: bool) -> list[Any]:
    return c.execute(f"""
            SELECT 
                games.gameID AS ID, {'games.date,' if with_date else ''} games.goals As CG, against AS Enemy,
                k.rank, k.score, k.goals, k.assists, k.saves, k.shots,
                p.rank, p.score, p.goals, p.assists, p.saves, p.shots,
                s.rank, s.score, s.goals, s.assists, s.saves, s.shots
            FROM games JOIN scores ON games.gameID = scores.gameID JOIN knus k ON games.gameID = k.gameID 
                JOIN puad p ON games.gameID = p.gameID JOIN sticker s ON games.gameID = s.gameID
            GROUP BY ID ORDER BY ID DESC LIMIT ?
    """, (limit,)).fetchall()


def wins_in_range(start, end) -> int:
    return c.execute("SELECT COUNT(gameID) FROM games WHERE goals > against AND gameID >= ? AND gameID <= ?",
                     (start, end)).fetchone()[0]


def losses_in_range(start, end) -> int:
    return c.execute("SELECT COUNT(gameID) FROM games WHERE against > goals AND gameID >= ? AND gameID <= ?",
                     (start, end)).fetchone()[0]


# Used for general stat tables
def general_game_stats_over_time_period(start=1, end=None) -> dict[Any]:
    def team_goals_in_range() -> int:
        return c.execute("SELECT SUM(goals) FROM games WHERE gameID >= ? AND gameID <= ?", (start, end)).fetchone()[0]

    def team_against_in_range() -> int:
        return c.execute("SELECT SUM(against) FROM games WHERE gameID >= ? AND gameID <= ?", (start, end)).fetchone()[0]

    # Input validation
    if end is None:
        end = total_games()
    if start > end:
        raise ValueError(f'StartIndex was larger than EndIndex: {start} > {end}')
    if start <= 0:
        raise ValueError("StartIndex can't be 0 or lower")
    wins = wins_in_range(start, end)
    losses = losses_in_range(start, end)
    games = end - start + 1
    goals = team_goals_in_range()
    against = team_against_in_range()

    def formatted_over_time_box_query(stat: str) -> tuple:
        if stat not in possible_stats:
            raise ValueError(f'{stat} is not in possible stats.')

        return c.execute(f"""
            SELECT SUM(k.{stat}), AVG(k.{stat}), SUM(p.{stat}), 
            AVG(p.{stat}), SUM(s.{stat}), AVG(s.{stat})
            FROM knus k JOIN puad p ON k.gameID = p.gameID JOIN sticker s ON s.gameID = k.gameID
            WHERE k.gameID >= ? AND k.gameID <= ?
        """, (start, end)).fetchone()

    def mvp_helper_query() -> list[Any]:
        query = c.execute(f"""
        SELECT COUNT(gameID), CAST(COUNT(gameID) AS FLOAT)/CAST({games} AS FLOAT) 
        FROM mvplvp WHERE gameID >= ? AND gameID <= ? GROUP BY MVP
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


# - Random facts queries - #
def results_table() -> list[Any]:
    return c.execute("""
        SELECT goals, against, COUNT(g.gameID) AS c FROM games g
        GROUP BY goals, against ORDER BY 1, 2
    """).fetchall()


def session_data_by_date(date: str):
    return c.execute("SELECT * FROM sessions WHERE date=?", (date,)).fetchone()


def last_result() -> tuple:
    return c.execute('SELECT goals, against FROM games ORDER BY gameID DESC LIMIT 1').fetchone()


def record_games_per_session(limit: int = 1) -> list[Any]:
    return c.execute('SELECT sessionID, wins+losses FROM sessions ORDER BY wins+losses DESC LIMIT ?',
                     (limit,)).fetchall()


# Frontpage QUERIES
def tilt() -> float:  # TODO: Write tilt-o-meter
    # Enemy goals last 14 days
    # Winrate
    date14ago = (datetime.datetime.now() - datetime.timedelta(days=14)).strftime('%Y-%m-%d')
    enemy_goals = c.execute("SELECT SUM(against) FROM games WHERE date > ?;", (date14ago,)).fetchone()[0]
    losses = c.execute("SELECT COUNT(1) FROM losses WHERE date > ?;", (date14ago,)).fetchone()[0]
    return enemy_goals * 0.8 + losses * 0.2


def average_session_length() -> int:
    return c.execute('SELECT AVG(wins+losses) FROM sessions').fetchone()[0]


# - RANDOM FACTS QUERIES - #
def player_total_of_stat(player_id: int, stat: str) -> int:
    if stat not in possible_stats:
        raise ValueError(f'{stat} is not in possible stats.')
    return c.execute(f'SELECT SUM({stat}) FROM scores WHERE playerID = ?', (player_id,)).fetchone()[0]


def player_stat_of_last_game(player_id: int, stat: str) -> int:
    if stat not in possible_stats:
        raise ValueError(f'{stat} is not in possible stats.')
    return c.execute(f'SELECT {stat} FROM scores WHERE playerID = ? ORDER BY gameID DESC LIMIT 1',
                     (player_id,)).fetchone()[0]


def performance_profile_view(p_id: int):
    def performance_rank(stat: str, player_id: int) -> int:  # ??? Bugged stat in first query
        return c.execute(f"""
        SELECT n 
        FROM 
            (SELECT row_number() OVER (ORDER BY {stat} DESC) AS n, gameID, ? 
            FROM performance WHERE playerID = ?) 
            WHERE gameID = ?
    """, (stat, player_id, total_games())).fetchone()[0]

    def color(value: float) -> str:
        if value <= 2:
            return "Orange;font-weight:bolder"
        elif value <= 10:
            return "SteelBlue;font-weight:bolder"
        elif value <= 25:
            return "ForestGreen"
        elif value <= 50:
            return "LightSlateGrey"
        elif value <= 75:
            return "#B6B6B4"
        else:
            return "IndianRed"

    values = c.execute('SELECT * FROM performance WHERE playerID = ? AND gameID = ?', (p_id, total_games())).fetchone()[
             2:]
    top = [round(performance_rank('score', p_id) / total_games() * 100, 1),
           round(performance_rank('goals', p_id) / total_games() * 100, 1),
           round(performance_rank('assists', p_id) / total_games() * 100, 1),
           round(performance_rank('saves', p_id) / total_games() * 100, 1),
           round(performance_rank('shots', p_id) / total_games() * 100, 1)]
    return list(zip(values, top, [color(x) for x in top]))


def player_name(player_id: int) -> str:
    return c.execute('SELECT name FROM players WHERE playerID = ?', (player_id,)).fetchone()[0]


def latest_session_main_data() -> list[Any]:
    return c.execute(
        '''SELECT sessionID, date, wins, losses, Goals, Against, quality
           FROM sessions ORDER BY SessionID desc LIMIT 1''').fetchone()


def games_from_session_date(session_date: str = None) -> list[Any]:
    if session_date is None:
        session_date = latest_session_main_data()[1]
    return c.execute('SELECT * FROM games WHERE date >= ?', (session_date,)).fetchall()


def last_two_sessions_dates() -> list[Any]:
    return c.execute('SELECT date FROM sessions ORDER BY SessionID DESC LIMIT 2').fetchall()


def game_amount_this_month() -> int:
    return c.execute(
        """SELECT COUNT(*) FROM games 
           WHERE strftime('%m', date) = strftime('%m',DATE()) AND 
           strftime('%Y',date) = strftime('%Y',DATE())""").fetchone()[0]


def game_amount_this_year() -> int:
    return c.execute("SELECT COUNT(*) FROM games WHERE strftime('%Y',date) = strftime('%Y',DATE())").fetchone()[0]


def unique_months_game_count() -> list[Any]:
    return c.execute(
        "SELECT strftime('%m-%Y',date) as d, COUNT(*) c FROM games GROUP BY d ORDER BY c DESC").fetchall()


def session_count() -> int:
    return c.execute("SELECT COUNT(1) FROM sessions").fetchone()[0]


def ranks() -> list[str]:
    ranks_list = []
    for i in range(0, 3):
        ranks_list.append(c.execute(
            "SELECT rank FROM scores WHERE playerID = ? ORDER BY gameID desc LIMIT 1", (i,)).fetchone()[0].lower())
    return ranks_list


def performance_score():
    def performance(stat, player_id):
        if stat not in ['score', 'goals', 'assists', 'saves', 'shots']:
            raise ValueError(f'{stat} not valid.')
        if player_id >= 3 or player_id < 0:
            raise ValueError(f'{player_id} not valid.')
        return c.execute(f'SELECT {stat} FROM performance WHERE playerID = ? ORDER BY gameID DESC LIMIT 1;',
                         (player_id,)).fetchone()[0]

    player_average = sum(players := [performance('score', x) for x in range(0, 3)]) / 3
    return [round(p - player_average, 2) for p in players]


def season_start_id() -> int:
    return c.execute("""SELECT g.gameID
    FROM games g 
    LEFT JOIN seasons se ON g.date BETWEEN se.start_date AND se.end_date 
    GROUP BY se.seasonID
    HAVING MIN(g.gameID)
    ORDER BY g.gameID DESC
    LIMIT 1""").fetchone()[0]


def session_start_id() -> int:
    return c.execute("SELECT MIN(gameID) from games GROUP BY date ORDER BY date DESC LIMIT 1").fetchone()[0]


def generate_fun_facts() -> list:
    # "FUN" FACTS # TODO: Also provide +/- if winrate changed from last game.
    # p1 > p2+p3
    def ff_solo_carry(player_id: int) -> tuple:  # TODO: unused
        if player_id < 0 or player_id > 2:
            raise ValueError('No player_id higher than 2 or less than 0 permitted.')
        return c.execute("""
        SELECT CAST(SUM(IIF(playerID = ? AND sc = 1, 1, 0)) AS FLOAT) / CAST(COUNT(gameID) AS FLOAT) AS oc, 
        CAST(SUM(IIF(playerID = ? AND sc = 1 AND w IS NOT NULL,1,0)) AS FLOAT) /
        CAST(SUM(IIF(playerID = ? AND sc = 1 ,1,0)) AS FLOAT) AS wr
        FROM (SELECT s.gameID, s.playerID, MAX(s.score) > (SUM(s.score) - MAX(s.score)) AS sc, wins.gameID AS w
        FROM scores s LEFT JOIN wins ON s.gameID = wins.gameID GROUP BY s.gameID)
    """, (player_id, player_id, player_id)).fetchone()

    # player got more than 500 points in one game
    def ff_more_than_500(player_id: int) -> tuple:
        return c.execute("""
        SELECT CAST(SUM(IIF(playerID = ? AND sc = 1,1,0)) AS FLOAT) / 
        CAST(COUNT(gameID)/3 AS FLOAT) AS oc, 
        CAST(SUM(IIF(playerID = ? AND sc = 1 AND w IS NOT NULL, 1, 0)) AS FLOAT) / 
        CAST(SUM(IIF(playerID = ? AND sc = 1,1,0)) AS FLOAT) AS wr
        FROM (SELECT s.gameID, s.playerID, IIF(score >= 500,1,0) AS sc, wins.gameID AS w
        FROM scores s LEFT JOIN wins ON s.gameID = wins.gameID)
    """, (player_id, player_id, player_id)).fetchone()

    def ff_everyone_scored() -> tuple:
        return c.execute("""
        SELECT CAST(SUM(IIF(sc = 1,1,0)) AS FLOAT) / CAST(COUNT(gameID) AS FLOAT) AS oc, 
        CAST(SUM(IIF(sc = 1 AND wi IS NOT NULL,1,0)) AS FLOAT) / CAST(SUM(IIF(sc = 1,1,0)) AS FLOAT) AS wr
        FROM (SELECT s.gameID, IIF(MIN(s.goals) > 0,1,0) AS sc, w.gameID AS wi FROM scores s 
        LEFT JOIN wins w ON s.gameID = w.gameID GROUP BY s.gameID)
    """).fetchone()

    def ff_did_not_score(player_id: int) -> tuple:
        return c.execute("""
        SELECT CAST(SUM(IIF(sG = 0,1,0)) AS FLOAT) / CAST(COUNT(sID) AS FLOAT) AS oc,
        CAST(SUM(IIF(sG = 0 AND wID IS NOT NULL,1,0)) AS FLOAT) / 
        CAST(SUM(IIF(sG = 0,1,0)) AS FLOAT) AS wr
        FROM (SELECT s.gameID AS sID, playerID, s.goals AS sG, w.gameID AS wID FROM scores s
        LEFT JOIN wins w ON s.gameID = w.gameID WHERE playerID = ?)
    """, (player_id,)).fetchone()

    def ff_no_solo_goals() -> tuple:
        return c.execute("""
        SELECT CAST(SUM(IIF(sG = sA AND sG > 0,1,0)) AS FLOAT) / CAST(COUNT(sID) AS FLOAT) AS oc,
        CAST(SUM(IIF(sG = sA AND sG > 0 AND wID IS NOT NULL,1,0)) AS FLOAT) / 
        CAST(SUM(IIF(sG = sA AND sG > 0,1,0)) AS FLOAT) AS wr
        FROM(SELECT s.gameID AS sID, SUM(s.goals) AS sG, SUM(s.assists) AS sA, w.gameID AS wID FROM scores s 
        LEFT JOIN wins w ON s.gameID = w.gameID GROUP BY s.gameID)
    """).fetchone()

    def ff_six_or_more_shots() -> tuple:
        return c.execute("""
        SELECT CAST(SUM(IIF(sS >= 6,1,0)) AS FLOAT) / CAST(COUNT(sID) AS FLOAT) AS oc,
        CAST(SUM(IIF(sS >= 6 AND wID IS NOT NULL,1,0)) AS FLOAT) / 
        CAST(SUM(IIF(sS >= 6,1,0)) AS FLOAT) AS wr
        FROM(SELECT s.gameID AS sID, SUM(s.shots) AS sS, w.gameID AS wID FROM scores s
        LEFT JOIN wins w ON s.gameID = w.gameID GROUP BY sID)
    """).fetchone()

    def ff_at_least_one_assist(player_id: int) -> tuple:
        return c.execute("""
        SELECT CAST(SUM(IIF(sA > 0,1,0)) AS FLOAT) / CAST(COUNT(sID) AS FLOAT) AS oc,
        CAST(SUM(IIF(sA > 0 AND wID IS NOT NULL,1,0)) AS FLOAT) / CAST(SUM(IIF(sA > 0,1,0)) AS FLOAT) AS wr
        FROM(SELECT s.gameID AS sID, s.assists AS sA, w.gameID AS wID FROM scores s
        LEFT JOIN wins w ON s.gameID = w.gameID WHERE playerID = ? GROUP BY sID)
    """, (player_id,)).fetchone()

    def ff_two_or_more_saves(player_id: int) -> tuple:
        return c.execute("""
        SELECT CAST(SUM(IIF(sS >= 2,1,0)) AS FLOAT) / CAST(COUNT(sID) AS FLOAT) AS oc,
        CAST(SUM(IIF(sS >= 2 AND wID IS NOT NULL,1,0)) AS FLOAT) / CAST(SUM(IIF(sS >= 2,1,0)) AS FLOAT) AS wr
        FROM(SELECT s.gameID AS sID, s.saves AS sS, w.gameID AS wID FROM scores s
        LEFT JOIN wins w ON s.gameID = w.gameID WHERE playerID = ? GROUP BY sID)
    """, (player_id,)).fetchone()

    # Irrelevant: Sum of all averages / 7.5
    def ff_irrelevant(player_id: int) -> tuple:
        return c.execute("""
        WITH st AS (
        SELECT s.gameID AS sID, s.playerID, s.score AS stSc, w.gameID AS wID
        FROM scores s LEFT JOIN wins w ON s.gameID = w.gameID
        WHERE playerID = ?),
        at AS (SELECT AVG(score) * 3 / 7.5 AS avgS FROM scores)
        SELECT CAST(SUM(IIF(st.stSc <= at.avgS,1,0)) AS FLOAT) / 
        CAST(COUNT(st.sID) AS FLOAT) AS oc,
        CAST(SUM(IIF(st.stSc <= at.avgS AND wID IS NOT NULL,1,0)) AS FLOAT) / 
        CAST(SUM(IIF(st.stSc <= at.avgS,1,0)) AS FLOAT) AS wr FROM st, at
    """, (player_id,)).fetchone()

    # TODO: rework next to queries into own table
    def ff_team_scores_x_times(x: int) -> tuple:
        return c.execute("""
    SELECT CAST(SUM(IIF(gGoals = ?,1,0)) AS FLOAT) / COUNT(gID) AS oc,
        CAST(SUM(IIF(gGoals = ? AND wID IS NOT NULL,1,0)) AS FLOAT) / 
        CAST(SUM(IIF(gGoals = ?,1,0)) AS FLOAT) AS wr
        FROM (SELECT g.gameID AS gID, g.goals AS gGoals, w.gameID AS wID FROM games g 
        LEFT JOIN wins w ON g.gameID = w.gameID)
    """, (x, x, x)).fetchone()

    def ff_team_concedes_x_times(x: int) -> tuple:
        return c.execute("""
    SELECT CAST(SUM(IIF(g.against = ?,1,0)) AS FLOAT) / COUNT(g.gameID) AS oc,
        CAST(SUM(IIF(g.against = ? AND w.gameID IS NOT NULL,1,0)) AS FLOAT) / 
        CAST(SUM(IIF(g.against = ?,1,0)) AS FLOAT) AS wr
        FROM games g LEFT JOIN wins w ON g.gameID = w.gameID
    """, (x, x, x)).fetchone()

    def format_fun_facts(title: str, function):
        return [title] + list(function)

    return [[format_fun_facts("CG shot six or more times", ff_six_or_more_shots()),
             format_fun_facts("Everyone scored", ff_everyone_scored()),
             format_fun_facts("No solo goals were scored", ff_no_solo_goals()),
             format_fun_facts("CG concedes zero goals", ff_team_concedes_x_times(0)),
             format_fun_facts("CG concedes one goal", ff_team_concedes_x_times(1)),
             format_fun_facts("CG concedes two goals", ff_team_concedes_x_times(2)),
             format_fun_facts("CG concedes three goals", ff_team_concedes_x_times(3)),
             format_fun_facts("CG concedes four goals", ff_team_concedes_x_times(4)),
             format_fun_facts("CG concedes five goals", ff_team_concedes_x_times(5)),
             format_fun_facts("CG scored zero goals", ff_team_scores_x_times(0)),
             format_fun_facts("CG scored one goal", ff_team_scores_x_times(1)),
             format_fun_facts("CG scored two goals", ff_team_scores_x_times(2)),
             format_fun_facts("CG scored three goals", ff_team_scores_x_times(3)),
             format_fun_facts("CG scored four goals", ff_team_scores_x_times(4)),
             format_fun_facts("CG scored five goals", ff_team_scores_x_times(5))],
            [format_fun_facts("Knus is irrelevant", ff_irrelevant(0)),
             format_fun_facts("Puad is irrelevant", ff_irrelevant(1)),
             format_fun_facts("Sticker is irrelevant", ff_irrelevant(2)),
             format_fun_facts("Knus has at least one assist", ff_at_least_one_assist(0)),
             format_fun_facts("Puad has at least one assist", ff_at_least_one_assist(1)),
             format_fun_facts("Sticker has at least one assist", ff_at_least_one_assist(2)),
             format_fun_facts("Knus did not score", ff_did_not_score(0)),
             format_fun_facts("Puad did not score", ff_did_not_score(1)),
             format_fun_facts("Sticker did not score", ff_did_not_score(2)),
             format_fun_facts("Knus scored more than 500 points", ff_more_than_500(0)),
             format_fun_facts("Puad scored more than 500 points", ff_more_than_500(1)),
             format_fun_facts("Sticker scored more than 500 points", ff_more_than_500(2)),
             format_fun_facts("Knus has two or more saves", ff_two_or_more_saves(0)),
             format_fun_facts("Puad has two or more saves", ff_two_or_more_saves(1)),
             format_fun_facts("Sticker has two or more saves", ff_two_or_more_saves(2)),
             ]]


def winrates() -> list:
    latest_game_id = total_games()
    season_start = season_start_id()
    last_session = latest_session_main_data()
    games_last_session = last_session[2] + last_session[3]
    winrates_list = [total_wins() / latest_game_id * 100,
                     wins_in_range(season_start, latest_game_id) / (latest_game_id - season_start + 1) * 100,
                     float(wins_in_range(latest_game_id - 99, latest_game_id)),
                     wins_in_range(latest_game_id - 19, latest_game_id) / 20 * 100,
                     last_session[2] / games_last_session * 100
                     ]

    return winrates_list


# 6 hours behind real time to account for after midnight gaming
def website_date() -> str:
    return (datetime.datetime.now() - datetime.timedelta(hours=6)).strftime('%Y-%m-%d')


# UNUSED
# TODO: player details page
# TODO: use all these queries
def seasons_dashboard():
    return c.execute("""SELECT se.season_name, 
    SUM(IIF(g.goals > g.against,1,0)) 'wins', 
    SUM(IIF(g.goals < g.against,1,0)) 'losses', 
    CAST(SUM(IIF(g.goals > g.against,1,0)) AS FLOAT) / CAST(COUNT(g.gameID) AS FLOAT) 'wr', 
    AVG(k.score) 'k_score', AVG(k.goals) 'k_goals', AVG(k.assists) 'k_assists', 
    AVG(k.saves) 'k_saves', AVG(k.shots) 'k_shots',
    AVG(p.score) 'p_score', AVG(p.goals) 'p_goals', AVG(p.assists) 'p_assists', 
    AVG(p.saves) 'p_saves', AVG(p.shots) 'p_shots',
    AVG(s.score) 's_score', AVG(s.goals) 's_goals', AVG(s.assists) 's_assists', 
    AVG(s.saves) 's_saves', AVG(s.shots) 's_shots'
    FROM games g 
    LEFT JOIN seasons se ON g.date BETWEEN se.start_date AND se.end_date 
    LEFT JOIN knus k ON g.gameID = k.gameID
    LEFT JOIN puad p ON g.gameID = p.gameID
    LEFT JOIN sticker s ON g.gameID = s.gameID
    GROUP BY seasonID""").fetchall()


def seasons_dashboard_short():
    return c.execute("""SELECT se.season_name,
    SUM(IIF(g.goals > g.against,1,0)) 'wins',
    SUM(IIF(g.goals < g.against,1,0)) 'losses',
    ROUND(CAST(SUM(IIF(g.goals > g.against,1,0)) AS FLOAT) / CAST(COUNT(g.gameID) AS FLOAT)*100,2) 'wr'
    FROM games g
    LEFT JOIN seasons se ON g.date BETWEEN se.start_date AND se.end_date
    GROUP BY seasonID""").fetchall()


def mvp_wins(player_id, start=1, end=None):
    if end is None:
        end = total_games()
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


def total_wins() -> int:
    return c.execute("SELECT COUNT(gameID) FROM games WHERE goals > against").fetchone()[0]


def total_losses() -> int:
    return c.execute("SELECT COUNT(gameID) FROM games WHERE goals < against").fetchone()[0]


def one_diff_wins() -> int:
    return c.execute("SELECT COUNT(gameID) FROM games WHERE goals - against = 1").fetchone()[0]


def one_diff_loss() -> int:
    return c.execute("SELECT COUNT(gameID) FROM games WHERE against - goals = 1").fetchone()[0]


# Session Details W/L
def session_details():
    details = dict()
    s_id, s_date, s_wins, s_losses, s_goals, s_against, s_quality = latest_session_main_data()
    s_games = s_wins + s_losses
    details['session_game_count'] = s_games
    details['latest_session_date'] = s_date
    details['w_and_l'] = ["W" if game[2] > game[3] else "L" for game in games_from_session_date(s_date)]
    return details


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


def solo_goals_in_range(start=1, end=None) -> int:
    if end is None:
        end = total_games()
    if start > end:
        raise ValueError(f'StartIndex was larger than EndIndex: {start} > {end}')
    c.execute("""
SELECT SUM(goalsSum - assistsSum) AS diff FROM (
    SELECT SUM(assists) AS assistsSum, SUM(goals) AS goalsSum 
    FROM scores WHERE gameID >= ? AND gameID <= ? GROUP BY gameID
)
""", (start, end))
    return c.fetchone()[0]


# Calculates average games per day based on start and end dates.
def average_games_per_day(start_date: str, end_date: str) -> float:
    if datetime.datetime.strptime(end_date, '%Y-%m-%d') < datetime.datetime.strptime(start_date, '%Y-%m-%d'):
        raise ValueError(f"start_date can't be before end_date {start_date} - {end_date}")
    return c.execute(
        """SELECT CAST(COUNT(gameID) AS FLOAT) / CAST(JULIANDAY(?) - JULIANDAY(?) AS FLOAT) 
           FROM games WHERE date BETWEEN ? AND ? """, (end_date, start_date, start_date, end_date)).fetchone()[0]


# Winrate of gameNr in session
def winrate_game_in_session():
    return c.execute("""
SELECT gnis, CAST(SUM(IIF(goals>against,1,0)) AS FLOAT) / CAST(COUNT(gameID) AS FLOAT) AS wrm, 
    COUNT(gameID) AS gcount
FROM (
    SELECT row_number() OVER(PARTITION by date) AS gnis, gameID, goals, against
    FROM games) p
GROUP BY gnis
""").fetchall()


# Average winrate of sessions by number of games
def average_winrate_of_sessions_by_game_count():
    return c.execute("""
SELECT games, AVG(wr) FROM(
    SELECT wins + losses AS games, CAST(wins AS float) / CAST(wins + losses AS float) AS wr FROM sessions)p
GROUP BY games
""").fetchall()


# "Just out" values -> [player0_just_out, player0_new_value, player1_just_out, etc.]
def just_out():
    return c.execute("""
WITH maxId AS (SELECT MAX(gameID) AS mId FROM scores)
SELECT scores.gameID, scores.playerID, scores.score FROM scores, maxId
WHERE gameID = maxId.mId - 20 OR gameID = maxId.mId
ORDER BY playerID
""").fetchall()


# "To beat next" values -> [player0_value, player1_value, player2_value]
def to_beat_next():
    return c.execute("""
WITH maxId AS (SELECT MAX(gameID) AS mId FROM scores)
SELECT scores.gameID, scores.playerID, scores.score FROM scores, maxId
WHERE gameID = maxId.mId - 19
ORDER BY playerID
""").fetchall()
