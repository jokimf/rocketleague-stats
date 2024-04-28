from database import connect_to_database
from typing import Any

conn = connect_to_database()
c = conn.cursor()


def record_highest_value_per_stat(stat: str, limit: int = 3) -> list[Any]:
    if stat not in ['score', 'goals', 'assists', 'saves', 'shots']:
        raise ValueError(f'{stat} is not in possible stats.')
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


def highest_team(stat: str, limit: int = 3) -> list[Any]:
    if stat == 'goals':
        stat = 'scores.goals'
    return c.execute(f'''
            SELECT "CG", SUM({stat}) AS stat, games.gameID, date 
            FROM games JOIN scores ON games.gameID = scores.gameID 
            GROUP BY games.gameID ORDER BY stat DESC LIMIT ?
        ''', (limit,)).fetchall()


# Difference between MVP and LVP, DESC for most diff, ASC for least diff
def diff_mvp_lvp(order: str, limit: int = 3) -> list[Any]:
    if order not in ['ASC', 'DESC']:
        raise ValueError('Order is not DESC or ASC.')
    return c.execute(f'''
        SELECT p.name, msc.score - lsc.score AS diff, ml.gameID, g.date
        FROM mvplvp ml
        LEFT JOIN scores msc ON ml.gameID = msc.gameID AND ml.MVP = msc.playerID
        LEFT JOIN scores lsc ON ml.gameID = lsc.gameID AND ml.LVP = lsc.playerID
        LEFT JOIN players p ON msc.playerID = p.playerID
        LEFT JOIN games g ON ml.gameID = g.gameID
        ORDER BY msc.score-lsc.score {order} LIMIT ? ''', (limit,)).fetchall()


def most_solo_goals(limit: int = 3) -> list[Any]:
    return c.execute('''
            SELECT "CG", games.goals - SUM(assists) AS ja, games.gameID, date FROM games 
            JOIN scores ON games.gameID = scores.gameID
            GROUP BY games.gameID ORDER BY ja DESC LIMIT ?''', (limit,)).fetchall()


def trend(stat: str, minmax: str, limit: int = 3) -> list[Any]:
    if stat not in ['score', 'goals', 'assists', 'saves', 'shots'] or minmax not in ['MIN', 'MAX']:
        raise ValueError(f'{stat} is not in possible stats or {minmax} is not "MIN" or "MAX"')
    if stat == 'goals':
        stat = 'performance.goals'
    return c.execute(f'''
        SELECT name, {minmax}({stat}) AS s, games.gameID, date 
        FROM performance JOIN games ON games.gameID = performance.gameID NATURAL JOIN players
        GROUP BY games.gameID ORDER BY s {('DESC' if minmax == 'MAX' else 'ASC')} LIMIT ?''', (limit,)).fetchall()


def highest_points_nothing_else(limit: int = 3) -> list[Any]:
    return c.execute('''
            SELECT name, MAX(score), games.gameID, date     
            FROM scores JOIN games ON games.gameID = scores.gameID NATURAL JOIN players
            WHERE scores.goals = 0 AND assists=0 AND saves=0 AND shots=0
            GROUP BY games.gameID ORDER BY score DESC LIMIT ?''', (limit,)).fetchall()


def least_points_at_least_1(limit: int = 3) -> list[Any]:
    return c.execute('''
            SELECT name, MIN(score), games.gameID, date 
            FROM scores JOIN games ON games.gameID = scores.gameID NATURAL JOIN players
            WHERE scores.goals >= 1 AND assists>=1 AND saves>=1 AND shots>=1
            GROUP BY games.gameID ORDER BY score ASC LIMIT ?''', (limit,)).fetchall()


def most_points_without_goal_or_assist(limit: int = 3) -> list[Any]:
    return c.execute('''
            SELECT name, MAX(score), games.gameID, date 
            FROM scores JOIN games ON games.gameID = scores.gameID NATURAL JOIN players
            WHERE scores.goals = 0 AND assists=0
            GROUP BY games.gameID ORDER BY score DESC LIMIT ?''', (limit,)).fetchall()


def generate_record_games():
    game_amount = 16
    records = [
        {
            'Highest Score by player': record_highest_value_per_stat('score', game_amount),
            'Most goals by player': record_highest_value_per_stat('goals', game_amount),
            'Most assists by player': record_highest_value_per_stat('assists', game_amount),
            'Most saves by player': record_highest_value_per_stat('saves', game_amount),
            'Most shots by player': record_highest_value_per_stat('shots', game_amount)
        },
        {
            'Highest score performance': trend('score', 'MAX', game_amount),
            'Highest goals performance': trend('goals', 'MAX', game_amount),
            'Highest assists performance': trend('assists', 'MAX', game_amount),
            'Highest saves performance': trend('saves', 'MAX', game_amount),
            'Highest shots performance': trend('shots', 'MAX', game_amount)
        },
        {
            'Lowest score in Trend': trend('score', 'MIN', game_amount),
            'Lowest goals in Trend': trend('goals', 'MIN', game_amount),
            'Lowest assists in Trend': trend('assists', 'MIN', game_amount),
            'Lowest saves in Trend': trend('saves', 'MIN', game_amount),
            'Lowest shots in Trend': trend('shots', 'MIN', game_amount)
        },
        {
            'Most points by team': highest_team('score', game_amount),
            'Most goals by team': highest_team('goals', game_amount),
            'Most assists by team': highest_team('assists', game_amount),
            'Most saves by team': highest_team('saves', game_amount),
            'Most shots by team': highest_team('shots', game_amount)
        },
        {
            'Most goals conceded by team': most_against(game_amount),
            'Most goals conceded and still won': most_against_and_won(game_amount),
            'Most goals scored and still lost': most_goals_and_lost(game_amount),
            'Most total goals in one game': most_total_goals(game_amount),
        },
        {
            'Most points with all stats being 0': highest_points_nothing_else(game_amount),
            'Most points without scoring or assisting': most_points_without_goal_or_assist(game_amount),
            'Least points with all stats being at least 1': least_points_at_least_1(game_amount),
            'Least points with at least one goal': least_points_with_goals(game_amount)
        },
        {
            'Most points with no goal': most_points_without_goal(game_amount),
            'Highest score diff between MVP and LVP': diff_mvp_lvp('DESC', game_amount),
            'Lowest score diff between MVP and LVP': diff_mvp_lvp('ASC', game_amount),
            'Most solo goals by "team"': most_solo_goals(game_amount),
        }
    ]
    # Segmentation for two separate tables
    return [{k: v for k, v in sorted(x.items(), key=lambda item: item[1][0][2])} for x in records]
