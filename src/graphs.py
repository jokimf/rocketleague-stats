import random
import sqlite3
from typing import List, Optional, Tuple

database_path = '../resources/test.db'
conn = sqlite3.connect(database_path)
c = conn.cursor()
possible_stats = ['score', 'goals', 'assists', 'saves', 'shots']


def random_color() -> str:
    r, g, b = random.randrange(0, 256), random.randrange(0, 256), random.randrange(0, 256)
    return f'rgba({r},{g},{b},0.8)'


# GRAPH QUERIES
class Graph:
    def __init__(self, title: str, graph_type: str, data: List, datapoint_labels: List, x_min: Optional[float],
                 x_max: Optional[float], y_min: Optional[float], y_max: Optional[float], show_legend: bool):
        self.title = title
        self.graph_type = graph_type
        self.data = data
        self.datapoint_labels = datapoint_labels
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.show_legend = show_legend

    colors = {
        'K': 'rgba(47,147,26,0.8)',  # Knus
        'P': 'rgba(147,26,26,0.8)',  # Puad
        'S': 'rgba(26,115,147,0.8)',  # Sticker
        'C': 'rgba(40, 40, 40, 0.8)',  # CG
        'W': 'rgba(3, 58, 3, 0.8)',  # Wins
        'L': 'rgba(58, 3, 3, 0.8)',  # Losses
        'G': 'rgba(17, 3, 58, 0.8)'  # Games
    }

    def to_dict(self) -> dict:
        datasets = []
        length = len(self.data[0])
        for x in range(1, length):
            label: str = None if self.datapoint_labels is None else self.datapoint_labels[x]
            border_color: str = self.colors[label[0]] if label[0] in self.colors else random_color()
            data: List = [entry[x] for entry in self.data]
            datasets.append({'data': data, 'label': label, 'borderColor': border_color, 'borderWidth': 2})
        graph_ctx: dict = {'type': self.graph_type,
                           'data': {
                               'title': self.title,
                               'labels': [x[0] for x in self.data],
                               'datasets': datasets
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

    def symbiose(self, *others):
        data = [list(x) for x in self.data]
        for graph in others:
            for i, entry in enumerate(graph.data):
                data[i] = data[i] + list(entry[1:])

        labels = self.datapoint_labels
        for graph in others:
            labels = labels + graph.datapoint_labels[1:]

        return Graph(self.title, self.graph_type, data, labels, self.x_min, self.x_max, self.y_min, self.y_max,
                     self.show_legend)

    def __str__(self):
        return f'{self.title}+,{self.graph_type},{self.datapoint_labels},{self.data}'

    def change_y(self, new_min: Optional[float], new_max: Optional[float]):
        self.y_min = new_min
        self.y_max = new_max
        return self


def graph_performance(stat: str) -> Graph:
    if stat not in possible_stats:
        raise ValueError(f'{stat} is not in possible stats.')
    data = c.execute(f"""
        WITH kT AS (SELECT * FROM performance WHERE playerID = 0),
        pT AS (SELECT * FROM performance WHERE playerID = 1),
        sT AS (SELECT * FROM performance WHERE playerID = 2)
        SELECT kT.gameID AS GameID, kT.{stat} AS Knus, pT.{stat} AS Puad, sT.{stat} AS Sticker FROM kT
        LEFT JOIN pT ON kT.gameID = pT.gameID
        LEFT JOIN sT ON kT.gameID = sT.gameID
    """).fetchall()
    return Graph(f'{stat.capitalize()} performance', 'line', data,
                 [f'{x[0]}{stat.capitalize()}' for x in c.description], None, None,
                 None, None, False)


def graph_performance_team(stat: str) -> Graph:
    if stat not in possible_stats:
        raise ValueError(f'{stat} is not in possible stats.')
    data = c.execute(f"SELECT gameID AS GameID, AVG({stat}) AS CG FROM performance GROUP BY gameID").fetchall()
    return Graph(f"Team {stat} performance", "line", data, [x[0] for x in c.description], None, None, None, None, False)


def graph_grief_value() -> Graph:
    data = c.execute("""
    WITH 	kT AS (SELECT gameID, score FROM performance WHERE playerID = 0),
            pT AS (SELECT gameID, score FROM performance WHERE playerID = 1),
            sT AS (SELECT gameID, score FROM performance WHERE playerID = 2),
            gAvg AS (SELECT gameID, AVG(performance.score) AS gA FROM performance GROUP BY performance.gameID)
            SELECT kT.gameID AS GameID, kT.score - gA AS Knus, pT.score - gA AS Puad, sT.score - gA AS Sticker FROM kT
            LEFT JOIN pT ON kT.gameID = pT.gameID
            LEFT JOIN sT ON kT.gameID = sT.gameID
            LEFT JOIN gAvg ON kT.gameID = gAvg.gameID
    """).fetchall()
    return Graph(f"Grief Value", "line", data, [x[0] for x in c.description], None, None, None, None, False)


def graph_winrate_last20() -> Graph:
    data = c.execute("""
        SELECT gameID as GameID, wr AS CG FROM(
        SELECT gameID, 
        CAST(SUM(w) OVER(ORDER BY gameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS FLOAT) / 20 AS wr 
        FROM(SELECT gameID, IIF(goals > against,1,0) AS w FROM games)) WHERE gameID > 19
    """).fetchall()
    return Graph("Winrate Last20", "line", data, [x[0] for x in c.description], 20, None, 0.15, 0.8, False)


def graph_winrate() -> Graph:
    data = c.execute("""
        SELECT gameID AS GameID, CAST(SUM(IIF(goals > against,1,0)) 
        OVER(ORDER BY gameID) AS FLOAT) / gameID AS CG FROM games
    """).fetchall()
    return Graph("Winrate", "line", data, [x[0] for x in c.description], None, None, 0.5, 0.55, False)


def graph_solo_goals() -> Graph:
    data = c.execute("""
        SELECT gameID AS GameID, SUM(SUM(goals) - SUM(assists)) OVER(ORDER BY gameID) AS CG FROM scores GROUP BY gameID
    """).fetchall()
    return Graph("Solo Goals", "line", data, [x[0] for x in c.description], None, None, None, None, False)


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
    return Graph(f"{stat.capitalize()} Share", "line", data, [x[0] for x in c.description], None, None, None, None,
                 False)


def graph_performance_stat_share(stat: str) -> Graph:
    if stat not in possible_stats:
        raise ValueError(f'{stat} is not in possible stats.')
    data = c.execute(f"""
        SELECT k.gameID AS GameID, 
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
    print(data)
    return Graph(f"{stat.capitalize()} performance share", "line", data, [x[0] for x in c.description], None, None,
                 None, None,
                 False)


def graph_average_mvp_score_over_time() -> Graph:
    data = c.execute("""
        SELECT gameID, AVG(score) OVER (ORDER BY gameID) AS CG FROM scores GROUP BY gameID HAVING MAX(score)
    """).fetchall()  # Graph gets joined with LVP, so title is MVP/LVP here
    return Graph("Average MVP/LVP Score", "line", data, [x[0] for x in c.description], None, None, None, None, False)


def graph_average_lvp_score_over_time() -> Graph:
    data = c.execute("""
        SELECT gameID AS GameID, AVG(score) OVER (ORDER BY gameID) AS CG FROM scores GROUP BY gameID HAVING MIN(score)
    """).fetchall()
    return Graph("Average LVP Score", "line", data, [x[0] for x in c.description], None, None, 215, None, False)


def graph_cumulative_stat(stat: str) -> Graph:
    if stat not in possible_stats:
        raise ValueError(f'{stat} is not in possible stats.')
    data = c.execute(f"""
        SELECT k.gameID, SUM(k.{stat}) OVER (ORDER BY k.gameID) 'Knus', SUM(p.{stat}) OVER (ORDER BY k.gameID) 'Puad', 
        SUM(s.{stat}) OVER (ORDER BY k.gameID) 'Sticker' FROM knus k LEFT JOIN puad p ON k.gameID = p.gameID 
        LEFT JOIN sticker s ON k.gameID = s.gameID
    """).fetchall()
    return Graph(f"Cumulative {stat.capitalize()}", "line", data, [x[0] for x in c.description], None, None, None, None,
                 False)


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

    return Graph("Weekdays", "bar", data, [x[0] for x in c.description], None, None, None, None, False)


def month_table() -> Graph:
    c.execute("""
        SELECT  STRFTIME('%m', date) AS month, COUNT(date) AS Games, SUM(IIF(goals > against, 1, 0)) AS Wins,
        SUM(IIF(goals < against, 1, 0)) AS Losses FROM games GROUP BY month""")
    new = [list(x) for x in c.fetchall()]
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
              "November", "December"]

    for i in range(0, 12):
        new[i][0] = months[i]
    return Graph('Month', 'bar', new, [x[0] for x in c.description], None, None, None, None, False)


def year_table() -> Graph:
    c.execute("""
        SELECT STRFTIME('%Y', date) AS year, COUNT(date) AS Games, SUM(IIF(goals > against, 1, 0)) AS Wins,
        SUM(IIF(goals < against, 1,0)) AS Losses FROM games GROUP BY year""")
    new = [list(x) for x in c.fetchall()]
    return Graph('Years', 'bar', new, [x[0] for x in c.description], None, None, None, None, False)


def dates_table() -> Graph:
    c.execute("""
        SELECT STRFTIME('%d', date) AS day, COUNT(date) as Games, SUM(IIF(goals > against,1,0)) AS Wins, 
        SUM(IIF(goals < against,1,0)) AS Losses FROM games GROUP BY day
    """)
    new = [list(x) for x in c.fetchall()]
    return Graph('Dates', 'bar', new, [x[0] for x in c.description], None, None, None, None, True)


graphs = {
    'performance_score': graph_performance('score').symbiose(graph_performance_team('score')),
    'performance_goals': graph_performance('goals').symbiose(graph_performance_team('goals')),
    'performance_assists': graph_performance('assists').symbiose(graph_performance_team('assists')),
    'performance_saves': graph_performance('saves').symbiose(graph_performance_team('saves')),
    'performance_shots': graph_performance('shots').symbiose(graph_performance_team('shots')),
    'performance_share_score': graph_stat_share('score').change_y(0.3, 0.4),
    'performance_share_goals': graph_stat_share('goals').change_y(0.3, 0.375),
    'performance_share_assists': graph_stat_share('assists').change_y(0.3, 0.4),
    'performance_share_saves': graph_stat_share('saves').change_y(0.3, 0.375),
    'performance_share_shots': graph_stat_share('shots').change_y(0.285, 0.4),
    'cumulative_stats_score': graph_cumulative_stat('score'),
    'cumulative_stats_goals': graph_cumulative_stat('goals'),
    'cumulative_stats_assists': graph_cumulative_stat('assists'),
    'cumulative_stats_saves': graph_cumulative_stat('saves'),
    'cumulative_stats_shots': graph_cumulative_stat('shots'),
    'grief': graph_grief_value(),
    'wins_last_20': graph_winrate_last20(),
    'winrate': graph_winrate(),
    'solo_goals': graph_solo_goals(),
    'mvp_lvp_score': graph_average_mvp_score_over_time().symbiose(graph_average_lvp_score_over_time()),
    'datesChart': dates_table(),
    'monthChart': month_table(),
    'yearsChart': year_table(),
    'weekdChart': weekday_table()
}
