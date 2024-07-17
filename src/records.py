from typing import Any

from connect import BackendConnection


class RecordQueries(BackendConnection):
    def record_highest_value_per_stat(self, stat: str, limit: int = 3) -> list[Any]:
        if stat not in ['score', 'goals', 'assists', 'saves', 'shots']:
            raise ValueError(f'{stat} is not in possible stats.')
        if stat == 'goals':
            stat = 'scores.goals'

        self.c.execute(f'''
                SELECT name, {stat}, games.gameID, date 
                FROM games JOIN scores ON games.gameID = scores.gameID NATURAL JOIN players
                ORDER BY {stat} DESC LIMIT %s''', (limit,))
        return self.c.fetchall()


    def most_points_without_goal(self, limit: int = 3) -> list[Any]:
        self.c.execute('''
            SELECT name, score, games.gameID, date 
            FROM games JOIN scores ON games.gameID = scores.gameID NATURAL JOIN players
            WHERE scores.goals = 0
            ORDER BY score DESC LIMIT %s''', (limit,))
        return self.c.fetchall()


    def least_points_with_goals(self, limit: int = 3) -> list[Any]:
        self.c.execute('''
            SELECT name, score, games.gameID, date 
            FROM games JOIN scores ON games.gameID = scores.gameID NATURAL JOIN players
            WHERE scores.goals > 0
            ORDER BY score ASC LIMIT %s''', (limit,))
        return self.c.fetchall()


    def most_against(self, limit: int = 3) -> list[Any]:
        self.c.execute('SELECT "CG", against, gameID, date FROM games ORDER BY against DESC LIMIT %s', (limit,))
        return self.c.fetchall()


    def most_against_and_won(self, limit: int = 3) -> list[Any]:
        self.c.execute(
            'SELECT "CG", against, gameID, date FROM games WHERE goals > against ORDER BY against DESC LIMIT %s',
            (limit,))
        return self.c.fetchall()


    def most_goals_and_lost(self, limit: int = 3) -> list[Any]:
        self.c.execute(
            'SELECT "CG", goals, gameID, date FROM games WHERE goals < against ORDER BY goals DESC LIMIT %s',
            (limit,))
        return self.c.fetchall()


    def most_total_goals(self, limit: int = 3) -> list[Any]:
        self.c.execute('SELECT "CG",goals+against, gameID, date FROM games ORDER BY goals + against DESC LIMIT %s',
                        (limit,))
        return self.c.fetchall()


    def highest_stat_sum_team(self, stat: str, limit: int = 3) -> list[Any]:
        if stat == 'goals':
            stat = 'scores.goals'
        self.c.execute(f'''
                SELECT "CG", SUM({stat}) AS stat, games.gameID, date 
                FROM games JOIN scores ON games.gameID = scores.gameID 
                GROUP BY games.gameID, date ORDER BY stat DESC LIMIT %s
            ''', (limit,))
        return self.c.fetchall()


    # Difference between MVP and LVP, DESC for most diff, ASC for least diff
    def diff_mvp_lvp(self, order: str, limit: int = 3) -> list[Any]:
        if order not in ['ASC', 'DESC']:
            raise ValueError('Order is not DESC or ASC.')
        self.c.execute(f'''
            SELECT p.name, msc.score - lsc.score AS diff, ml.gameID, g.date
            FROM mvplvp ml
            LEFT JOIN scores msc ON ml.gameID = msc.gameID AND ml.MVP = msc.playerID
            LEFT JOIN scores lsc ON ml.gameID = lsc.gameID AND ml.LVP = lsc.playerID
            LEFT JOIN players p ON msc.playerID = p.playerID
            LEFT JOIN games g ON ml.gameID = g.gameID
            ORDER BY msc.score-lsc.score {order} LIMIT %s ''', (limit,))
        return self.c.fetchall()


    def most_solo_goals(self, limit: int = 3) -> list[Any]:
        self.c.execute('''
                SELECT "CG", games.goals - SUM(assists) AS ja, games.gameID, date FROM games 
                JOIN scores ON games.gameID = scores.gameID
                GROUP BY games.gameID, games.goals, date ORDER BY ja DESC LIMIT %s''', (limit,))
        return self.c.fetchall()


    def trend(self, stat: str, minmax: str, limit: int = 3) -> list[Any]:
        if stat not in ['score', 'goals', 'assists', 'saves', 'shots'] or minmax not in ['MIN', 'MAX']:
            raise ValueError(f'{stat} is not in possible stats or {minmax} is not "MIN" or "MAX"')
        if stat == 'goals':
            stat = 'performance.goals'
        self.c.execute(f'''
            SELECT name, {minmax}({stat}) AS s, games.gameID, date 
            FROM performance JOIN games ON games.gameID = performance.gameID NATURAL JOIN players
            GROUP BY games.gameID, name, date ORDER BY s {('DESC' if minmax == 'MAX' else 'ASC')} LIMIT %s''', (limit,))
        return self.c.fetchall()


    def highest_points_nothing_else(self, limit: int = 3) -> list[Any]:
        self.c.execute('''
                SELECT players.name, MAX(scores.score) AS p, games.gameID, games.date     
                FROM scores JOIN games ON games.gameID = scores.gameID NATURAL JOIN players
                WHERE scores.goals = 0 AND scores.assists=0 AND scores.saves=0 AND scores.shots=0
                GROUP BY games.gameID, players.name, games.date ORDER BY p DESC LIMIT %s''', (limit,))
        return self.c.fetchall()


    def least_points_at_least_1(self, limit: int = 3) -> list[Any]:
        self.c.execute('''
                SELECT name, MIN(score) as p, games.gameID, date 
                FROM scores JOIN games ON games.gameID = scores.gameID NATURAL JOIN players
                WHERE scores.goals >= 1 AND assists>=1 AND saves>=1 AND shots>=1
                GROUP BY games.gameID, name, date ORDER BY p ASC LIMIT %s''', (limit,))
        return self.c.fetchall()


    def most_points_without_goal_or_assist(self, limit: int = 3) -> list[Any]:
        self.c.execute('''
                SELECT players.name, MAX(scores.score) as p, games.gameID, games.date 
                FROM scores JOIN games ON games.gameID = scores.gameID NATURAL JOIN players
                WHERE scores.goals = 0 AND scores.assists=0
                GROUP BY games.gameID, players.name, games.date ORDER BY p DESC LIMIT %s''', (limit,))
        return self.c.fetchall()


    def generate_record_games(self):
        game_amount = 16
        records = [
            {
                'Highest Score by player': self.record_highest_value_per_stat('score', game_amount),
                'Most goals by player': self.record_highest_value_per_stat('goals', game_amount),
                'Most assists by player': self.record_highest_value_per_stat('assists', game_amount),
                'Most saves by player': self.record_highest_value_per_stat('saves', game_amount),
                'Most shots by player': self.record_highest_value_per_stat('shots', game_amount)
            },
            {
                'Highest score performance': self.trend('score', 'MAX', game_amount),
                'Highest goals performance': self.trend('goals', 'MAX', game_amount),
                'Highest assists performance': self.trend('assists', 'MAX', game_amount),
                'Highest saves performance': self.trend('saves', 'MAX', game_amount),
                'Highest shots performance': self.trend('shots', 'MAX', game_amount)
            },
            {
                'Lowest score in Trend': self.trend('score', 'MIN', game_amount),
                'Lowest goals in Trend': self.trend('goals', 'MIN', game_amount),
                'Lowest assists in Trend': self.trend('assists', 'MIN', game_amount),
                'Lowest saves in Trend': self.trend('saves', 'MIN', game_amount),
                'Lowest shots in Trend': self.trend('shots', 'MIN', game_amount)
            },
            {
                'Most points by team': self.highest_stat_sum_team('score', game_amount),
                'Most goals by team': self.highest_stat_sum_team('goals', game_amount),
                'Most assists by team': self.highest_stat_sum_team('assists', game_amount),
                'Most saves by team': self.highest_stat_sum_team('saves', game_amount),
                'Most shots by team': self.highest_stat_sum_team('shots', game_amount)
            },
            {
                'Most goals conceded by team': self.most_against(game_amount),
                'Most goals conceded and still won': self.most_against_and_won(game_amount),
                'Most goals scored and still lost': self.most_goals_and_lost(game_amount),
                'Most total goals in one game': self.most_total_goals(game_amount),
            },
            {
                'Most points with all stats being 0': self.highest_points_nothing_else(game_amount),
                'Most points without scoring or assisting': self.most_points_without_goal_or_assist(game_amount),
                'Least points with all stats being at least 1': self.least_points_at_least_1(game_amount),
                'Least points with at least one goal': self.least_points_with_goals(game_amount)
            },
            {
                'Most points with no goal': self.most_points_without_goal(game_amount),
                'Highest score diff between MVP and LVP': self.diff_mvp_lvp('DESC', game_amount),
                'Lowest score diff between MVP and LVP': self.diff_mvp_lvp('ASC', game_amount),
                'Most solo goals by "team"': self.most_solo_goals(game_amount),
            }
        ]
        # Segmentation for two separate tables
        return [{k: v for k, v in sorted(x.items(), key=lambda item: item[1][0][2])} for x in records]
