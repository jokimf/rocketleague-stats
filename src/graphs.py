import random
import sqlite3
from typing import List, Any

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
    def __init__(self, title: str, graph_type: str, data_type: str, x_min: int, x_max: int, begin_at_zero: bool,
                 data: List):
        self.title = title
        self.graph_type = graph_type
        self.data_type = data_type
        self.x_min = x_min
        self.x_max = x_max
        self.begin_at_zero = begin_at_zero
        self.data = data

    def to_dict(self) -> dict:
        data = None
        if self.data_type == 'kps':
            data = [{'label': 'Knus', 'data': [x[1] for x in self.data],
                     'borderColor': 'rgba(47,147,26,0.8)', 'borderWidth': 2},
                    {'label': 'Puad', 'data': [x[2] for x in self.data],
                     'borderColor': 'rgba(147,26,26,0.8)', 'borderWidth': 2},
                    {'label': 'Sticker', 'data': [x[3] for x in self.data],
                     'borderColor': 'rgba(26,115,147,0.8)', 'borderWidth': 2}]
        elif self.data_type == 'full':
            pass
        elif self.data_type == 'one':
            data = [{'label': 'CG', 'data': self.data[0],
                     'borderColor': 'rgba(197, 114, 54, 0.84)', 'borderWidth': 2}]
        else:
            data = []
            length = len(self.data[0])
            for x in range(1, length):
                data.append({'data': [y[x] for y in self.data], 'borderColor': random_color(), 'borderWidth': 2})
        json = {'type': self.graph_type,
                'data': {
                    'title': self.title,
                    'labels': [x[0] for x in self.data],
                    'datasets': data
                },
                'options': {
                    'beginAtZero': self.begin_at_zero,
                    'x_min': self.x_min,
                    'x_max': self.x_max
                }
                }

        return json

    def __str__(self) -> str:
        return f'Graph(title={self.title}, graph_type={self.graph_type}, data_type={self.data_type}, ' \
               f'x=({self.x_min},{self.x_max}), beginAtZero={self.begin_at_zero}, data={self.data})'


def graph_performance(stat: str) -> Graph:  # TODO rework query
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
    return Graph(f'Player {stat} performance over time', 'line', 'kps', 0, max_id(), False, data)


def graph_total_performance(stat, start=1, end=None) -> Graph:
    if end is None:
        end = max_id()
    if stat not in possible_stats:
        raise ValueError(f'{stat} is not in possible stats.')
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
    """, (start, end))
    data = c.fetchall()
    return "Solo goals over time", start, end, data


def graph_solo_goals_over_time():
    c.execute("""
        WITH solos AS (SELECT gameID, SUM(goals) - SUM(assists) AS solo FROM scores GROUP BY gameID)
        SELECT gameID, SUM(solo) OVER (ORDER BY gameID) AS cumulativeSolos FROM solos
    """)
    data = c.fetchall()
    return "Cumulative solo goals", data


# % Share of stat in game range [all stats + mvp share (might need own query)]
# Output: [k%,p%,s%]
def graph_performance_share(stat, start=1, end=None):
    if end is None:
        end = max_id()
    if stat not in possible_stats or stat != 'mvp':
        raise ValueError(f'{stat} is not in possible stats.')
    c.execute("""
        WITH k AS(SELECT SUM(?) AS ks FROM scores WHERE playerID = 0 AND gameID > ? AND gameID < ?),
        p AS (SELECT SUM(?) AS ps FROM scores WHERE playerID = 1 AND gameID > ? AND gameID < ?),
        s AS (SELECT SUM(?) AS ss FROM scores WHERE playerID = 2 AND gameID > ? AND gameID < ?)
        SELECT CAST(ks AS FLOAT) / CAST((ks+ps+ss) AS FLOAT) AS kp, CAST(ps AS FLOAT) / CAST((ks+ps+ss) AS FLOAT) AS pp, CAST(ss AS FLOAT) / CAST((ks+ps+ss) AS FLOAT) AS sp
        FROM k, p, s
    """, (stat, start, end, stat, start, end, stat, start, end))
    data = c.fetchall()
    return stat + " performance share", start, end, data


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
        raise ValueError(f'{stat} is not in possible stats.')
    c.execute("""
        WITH k AS (SELECT gameID, SUM(?) OVER (ORDER BY gameID) AS sc FROM scores WHERE playerID = 0),
        p AS (SELECT gameID, SUM(?) OVER (ORDER BY gameID) AS sc FROM scores WHERE playerID = 1),
        s AS (SELECT gameID, SUM(?) OVER (ORDER BY gameID) AS sc FROM scores WHERE playerID = 2)
        SELECT k.gameID, k.sc, p.sc, s.sc FROM k LEFT JOIN p ON k.gameID = p.gameID LEFT JOIN s ON k.gameID = s.gameID
    """, (stat, stat, stat))
    data = c.fetchall()
    return "Cumulative value for " + stat, stat, data


# Weekday table, [weekday, count, wins, losses]
def weekday_table() -> List[Any]:
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
    'total_performance': graph_total_performance,
    'grief': graph_grief_value,
    'wins_last_20': graph_winrate_last20,
    'winrate': graph_winrate,
    'solo_goals': graph_solo_goals,
    'performance_share': graph_performance_share,
    'av_mvp_score': graph_average_mvp_score_over_time,
    'av_lvp_score': graph_average_lvp_score_over_time,
    'game_stats': graph_cumulative_stat_over_time,
}
