import random
import sqlite3
from typing import List, Any
import queries as q

database_path = '../resources/test.db'
conn = sqlite3.connect(database_path)
c = conn.cursor()

possible_stats = ['score', 'goals', 'assists', 'saves', 'shots']
possible_game_stats = ['goals', 'against']
possible_modes = ['AVG', 'SUM', 'MAX', 'MIN']


def random_color():
    r, g, b = random.randrange(0, 256), random.randrange(0, 256), random.randrange(0, 256)
    return f'rgba({r},{g},{b},0.8)'


# GRAPH QUERIES
class Graph:
    def __init__(self, title: str, graph_type: str, data_type: str, data: List, datapoint_labels: List, x_min: float,
                 x_max: float, y_min: float, y_max: float, show_legend: bool):
        self.title = title
        self.graph_type = graph_type
        self.data_type = data_type
        self.data = data
        self.datapoint_labels = datapoint_labels
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.show_legend = show_legend

    def to_dict(self) -> dict:
        data: List = None
        if self.data_type == 'kps':  # TODO remove kps with help of c.description and SQL
            data = [{'label': 'Knus', 'data': [x[1] for x in self.data],
                     'borderColor': 'rgba(47,147,26,0.8)', 'borderWidth': 2},
                    {'label': 'Puad', 'data': [x[2] for x in self.data],
                     'borderColor': 'rgba(147,26,26,0.8)', 'borderWidth': 2},
                    {'label': 'Sticker', 'data': [x[3] for x in self.data],
                     'borderColor': 'rgba(26,115,147,0.8)', 'borderWidth': 2}]
        else:
            data = []
            length = len(self.data[0])
            for x in range(1, length):
                data.append({'data': [y[x] for y in self.data], 'borderColor': random_color(), 'borderWidth': 2,
                             'label': None if self.datapoint_labels is None else self.datapoint_labels[x]})
        graph_ctx = {'type': self.graph_type,
                     'data': {
                         'title': self.title,
                         'labels': [x[0] for x in self.data],
                         'datasets': data
                     },
                     'options': {
                         'x_min': self.x_min,
                         'x_max': self.x_max,
                         'y_min': self.y_min,
                         'y_max': self.y_max,
                         'show_legend': self.show_legend
                     }
                     }

        return graph_ctx


# TODO: Fix all Graph returns
def graph_performance(stat: str) -> Graph:
    if stat not in possible_stats:
        raise ValueError(f'{stat} is not in possible stats.')
    data = c.execute(f"""
        WITH kT AS (SELECT * FROM performance WHERE playerID = 0),
        pT AS (SELECT * FROM performance WHERE playerID = 1),
        sT AS (SELECT * FROM performance WHERE playerID = 2)
        SELECT kT.gameID, kT.{stat}, pT.{stat}, sT.{stat} FROM kT
        LEFT JOIN pT ON kT.gameID = pT.gameID
        LEFT JOIN sT ON kT.gameID = sT.gameID
    """).fetchall()
    return Graph(f'Player {stat} performance over time', 'line', 'kps', data, [x[0] for x in c.description], None, None,
                 None, None, False)


def graph_performance_team(stat: str) -> Graph:
    if stat not in possible_stats:
        raise ValueError(f'{stat} is not in possible stats.')
    data = c.execute(f"SELECT gameID, AVG({stat}) FROM performance GROUP BY gameID").fetchall()
    return Graph(f"Team {stat} performance", "line", "one", 1, q.max_id(), True, data)


def graph_grief_value() -> Graph:
    data = c.execute("""
    WITH 	kT AS (SELECT gameID, score FROM performance WHERE playerID = 0),
            pT AS (SELECT gameID, score FROM performance WHERE playerID = 1),
            sT AS (SELECT gameID, score FROM performance WHERE playerID = 2),
            gAvg AS (SELECT gameID, AVG(performance.score) AS gA FROM performance GROUP BY performance.gameID)
            SELECT kT.gameID, kT.score - gA, pT.score - gA, sT.score - gA FROM kT
            LEFT JOIN pT ON kT.gameID = pT.gameID
            LEFT JOIN sT ON kT.gameID = sT.gameID
            LEFT JOIN gAvg ON kT.gameID = gAvg.gameID
    """).fetchall()
    return Graph(f"Grief value", "line", "one", 20, q.max_id(), False, data)


def graph_winrate_last20() -> Graph:
    data = c.execute("""
        SELECT gameID, wr FROM(
        SELECT gameID, 
		CAST(SUM(w) OVER(ORDER BY gameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS FLOAT) / 20 AS wr 
        FROM(SELECT gameID, IIF(goals > against,1,0) AS w FROM games)) WHERE gameID > 19
    """).fetchall()
    return Graph("Winrate last 20 games", "line", "one", 20, q.max_id(), False, data)


def graph_winrate() -> Graph:
    data = c.execute("""
        SELECT gameID, CAST(SUM(IIF(goals > against,1,0)) OVER(ORDER BY gameID) AS FLOAT) / gameID AS wr FROM games
    """).fetchall()
    return Graph("Winrate", "line", "ff", data, None, None, None, 0.48, 0.55, False)


def graph_solo_goals() -> Graph:
    data = c.execute("""
        SELECT gameID, SUM(SUM(goals) - SUM(assists)) OVER(ORDER BY gameID) as sumSG FROM scores GROUP BY gameID
    """).fetchall()
    return Graph("Total Solo Goals", "line", "one", 1, q.max_id(), True, data)


def graph_stat_share(stat: str) -> Graph:
    if stat not in possible_stats:
        raise ValueError(f'{stat} is not in possible stats.')
    data = c.execute(f"""
        SELECT k.gameID, 
        CAST(SUM(k.{stat}) OVER(ORDER BY k.gameID) AS FLOAT) / 
        (CAST(SUM(k.{stat}) OVER(ORDER BY k.gameID) AS FLOAT) + 
        CAST(SUM(p.{stat}) OVER(ORDER BY p.gameID) AS FLOAT) + 
        CAST(SUM(s.{stat}) OVER(ORDER BY s.gameID) AS FLOAT)) AS K,
        CAST(SUM(p.{stat}) OVER(ORDER BY p.gameID) AS FLOAT) / 
        (CAST(SUM(k.{stat}) OVER(ORDER BY k.gameID) AS FLOAT) + 
        CAST(SUM(p.{stat}) OVER(ORDER BY p.gameID) AS FLOAT) + 
        CAST(SUM(s.{stat}) OVER(ORDER BY s.gameID) AS FLOAT)) AS P,
        CAST(SUM(s.{stat}) OVER(ORDER BY s.gameID) AS FLOAT) / 
        (CAST(SUM(k.{stat}) OVER(ORDER BY k.gameID) AS FLOAT) + 
        CAST(SUM(p.{stat}) OVER(ORDER BY p.gameID) AS FLOAT) + 
        CAST(SUM(s.{stat}) OVER(ORDER BY s.gameID) AS FLOAT)) AS S
         FROM knus k JOIN puad p ON k.gameID = p.gameID JOIN sticker s ON k.gameID = s.gameID
    """).fetchall()
    return Graph(f"{stat} share", "line", "kps", 1, q.max_id(), False, data)


def graph_performance_stat_share(stat: str) -> Graph:
    if stat not in possible_stats:
        raise ValueError(f'{stat} is not in possible stats.')
    data = c.execute(f"""
        SELECT k.gameID, 
        CAST(SUM(k.{stat}) OVER(ORDER BY k.gameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS FLOAT) / 
        (CAST(SUM(k.{stat}) OVER(ORDER BY k.gameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS FLOAT) + 
        CAST(SUM(p.{stat}) OVER(ORDER BY p.gameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS FLOAT) + 
        CAST(SUM(s.{stat}) OVER(ORDER BY s.gameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS FLOAT)) AS K,
        CAST(SUM(p.{stat}) OVER(ORDER BY p.gameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS FLOAT) / 
        (CAST(SUM(k.{stat}) OVER(ORDER BY k.gameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS FLOAT) + 
        CAST(SUM(p.{stat}) OVER(ORDER BY p.gameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS FLOAT) + 
        CAST(SUM(s.{stat}) OVER(ORDER BY s.gameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS FLOAT)) AS P,
        CAST(SUM(s.{stat}) OVER(ORDER BY s.gameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS FLOAT) / 
        (CAST(SUM(k.{stat}) OVER(ORDER BY k.gameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS FLOAT) + 
        CAST(SUM(p.{stat}) OVER(ORDER BY p.gameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS FLOAT) + 
        CAST(SUM(s.{stat}) OVER(ORDER BY s.gameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS FLOAT)) AS S
         FROM knus k JOIN puad p ON k.gameID = p.gameID JOIN sticker s ON k.gameID = s.gameID
    """).fetchall()
    return Graph(f"{stat} performance share", "line", "kps", 1, q.max_id(), False, data)


def graph_average_mvp_score_over_time() -> Graph:
    data = c.execute("""
        SELECT gameID, AVG(score) OVER (ORDER BY gameID) FROM scores GROUP BY gameID HAVING MAX(score)
    """).fetchall()
    return Graph("Average MVP score", "line", "one", 1, q.max_id(), False, data)


def graph_average_lvp_score_over_time() -> Graph:
    data = c.execute("""
        SELECT gameID, AVG(score) OVER (ORDER BY gameID) FROM scores GROUP BY gameID HAVING MIN(score)
    """).fetchall()
    return Graph("Average LVP score", "line", "one", 1, q.max_id(), False, data)


def graph_cumulative_stat(stat: str) -> Graph:
    if stat not in possible_stats:
        raise ValueError(f'{stat} is not in possible stats.')
    data = c.execute("""
        WITH k AS (SELECT gameID, SUM(?) OVER (ORDER BY gameID) AS sc FROM scores WHERE playerID = 0),
        p AS (SELECT gameID, SUM(?) OVER (ORDER BY gameID) AS sc FROM scores WHERE playerID = 1),
        s AS (SELECT gameID, SUM(?) OVER (ORDER BY gameID) AS sc FROM scores WHERE playerID = 2)
        SELECT k.gameID, k.sc, p.sc, s.sc FROM k LEFT JOIN p ON k.gameID = p.gameID LEFT JOIN s ON k.gameID = s.gameID
    """, (stat, stat, stat)).fetchall()
    return Graph(f"Cumulative {stat}", "line", "kps", 1, q.max_id(), True, data)


def weekday_table() -> Graph:
    c.execute("""
        SELECT STRFTIME('%w', date) AS weekday, COUNT(date) AS Games, SUM(IIF(goals > against, 1, 0)) AS Wins, 
        SUM(IIF(goals < against, 1, 0)) AS Losses FROM games GROUP BY weekday
    """)

    # Substitute dayID with corresponding string
    days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    new = [list(x) for x in c.fetchall()]
    for i in range(0, 7):
        new[i][0] = days[i]

    data = new[1:]  # put Sunday at the back of the list
    data.append(new[0])
    return Graph("Weekdays", "bar", "full", data, [x[0] for x in c.description], None, None, None, None, True)


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
def dates_table() -> Graph:  # TODO: Games, Wins, Losses
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
    return Graph('Dates', 'bar', '?', 1, 2300, False, values_done)


graphs = {
    'performance': graph_performance,
    'total_performance': graph_performance_team,
    'grief': graph_grief_value,
    'wins_last_20': graph_winrate_last20,
    'winrate': graph_winrate,
    'solo_goals': graph_solo_goals,
    'performance_share': graph_stat_share,
    'av_mvp_score': graph_average_mvp_score_over_time,
    'av_lvp_score': graph_average_lvp_score_over_time,
    'game_stats': graph_cumulative_stat,
}
