from __future__ import annotations  # for class type hints

import random
from enum import Enum

import simplejson as json

from connect import BackendConnection

class GraphBuilder:
    def __init__(self) -> None:
        self._graph: dict = {
            "type": 'bar',
            "data": {
                "labels": [],
                "datasets": [],
            },
            "options": {
                "plugins": {
                    "legend": dict(),
                    "title": dict()
                }
            }
        }

    def toJSON(self) -> dict:
        return json.dumps(self._graph)

    def withType(self, graphType: str) -> GraphBuilder:
        self._graph |= {"type": graphType}
        return self

    def withLabels(self, labels: list) -> GraphBuilder:
        data_attributes = self._graph.get("data")
        data_attributes |= {"labels": labels}
        return self
    
    def withTitle(self, text: str, align: str = "center", position: str = "top") -> GraphBuilder:
        title_attributes = {
            "text": text,
            "align": align,
            "position": position,
            "display": True
        }
        title_section = self._graph.get("options").get("plugins").get("title")
        title_section |= title_attributes
        return self
    
    def withLegend(self, show: bool):
        legend_section = self._graph.get("options").get("plugins").get("legend")
        legend_section |= {"display": show}
        return self
    
    def withDataset(self, data: list[int|float], label: str, color: DatasetColor|str, border_color, borderWidth: int = 1) -> GraphBuilder:
        if isinstance(color, DatasetColor):
            color = color.value
        if isinstance(border_color, DatasetColor):
            border_color = border_color.value

        dataset_attributes = {
            "data": data,
            "label": label,
            "borderWidth": borderWidth,
            "backgroundColor": color,
            "borderColor": border_color
        }
        data_section: list = self._graph.get("data").get("datasets")
        data_section.append(dataset_attributes)
        return self
    
    
    def withLimits(self, xmin: int|None = None, xmax: int|None = None, ymin: int|None = None, ymax: int|None = None) -> GraphBuilder:
        options_section = self._graph.get("options")
        attributes = {"x_min": xmin, "x_max": xmax, "y_min": ymin, "y_max": ymax}
        
        # Filter None
        attributes = {key: value for key, value in attributes.items() if value is not None}
        
        options_section |= attributes
        return self
    
class DatasetColor(Enum):
    def random_color() -> str:
        r, g, b = random.randrange(0, 256), random.randrange(0, 256), random.randrange(0, 256)
        return f'rgba({r},{g},{b},0.6)'

    KNUS = 'rgba(47,147,26,0.8)',
    PUAD = 'rgba(147,26,26,0.8)',  
    STICKER = 'rgba(26,115,147,0.8)', 
    CLOWN = 'rgba(40, 40, 40, 0.8)',
    WIN = 'rgba(3, 58, 3, 0.8)',  
    LOSS = 'rgba(58, 3, 3, 0.8)',  
    GAME ='rgba(17, 3, 58, 0.8)',
    NEUTRAL = 'rgba(128,128,128,0.6)'

class GraphQueries(BackendConnection):
    def dates_table(self) -> dict:
        self.c.execute("""
            SELECT DATE_FORMAT(date, '%d') AS day, 
                SUM(IF(goals > against,1,0)) AS Wins,
                SUM(IF(goals < against,1,0)) AS Losses 
            FROM games GROUP BY day ORDER BY day ASC
        """)
        raw = self.c.fetchall()
        labels, wins, losses = zip(*raw)
        graph = GraphBuilder() \
            .withDataset(wins, "Wins", DatasetColor.WIN, DatasetColor.CLOWN) \
            .withDataset(losses, "Losses", DatasetColor.LOSS, DatasetColor.CLOWN) \
            .withLabels(labels)
        return graph.toJSON()
 
    def performance_graph(self) -> dict:
        player_ids = [0, 1, 2]
        data_list = []

        for player_id in player_ids:
            self.c.execute(f"SELECT s.score FROM performance s WHERE s.playerID = {player_id} ORDER BY gameID DESC LIMIT 20")
            raw = self.c.fetchall()
            data_list.append(list(reversed([x[0] for x in raw])))
            average = [sum(group) / len(group) for group in zip(*data_list)]
        graph = GraphBuilder() \
            .withType("line") \
            .withDataset(data_list[0], "Knus", DatasetColor.KNUS, DatasetColor.NEUTRAL) \
            .withDataset(data_list[1], "Puad", DatasetColor.PUAD, DatasetColor.NEUTRAL) \
            .withDataset(data_list[2], "Sticker", DatasetColor.STICKER, DatasetColor.NEUTRAL) \
            .withDataset(average, "Average", DatasetColor.GAME, DatasetColor.NEUTRAL, 3) \
            .withLabels(list(range(1,21)))
        return graph.toJSON()
    
    def results_table(self):
        self.c.execute("""
            WITH cG AS (SELECT COUNT(*) allG FROM games)
            SELECT goals, against, COUNT(*) AS c, CAST(COUNT(*) AS FLOAT) / MAX(cG.allG) AS ch  
            FROM games, cG
            GROUP BY goals, against
            ORDER BY goals ASC;
        """)
        return [{"x": str(g), "y": str(a), "v": v} for g, a, v, _ in self.c.fetchall()]
 
# OLD GRAPH QUERIES
# def graph_performance_team(stat: str) -> OldGraph:
#     if stat not in possible_stats:
#         raise ValueError(f'{stat} is not in possible stats.')
#     data = c.execute(f"SELECT gameID AS GameID, AVG({stat}) AS CG FROM performance GROUP BY gameID").fetchall()
#     return OldGraph(f"Team {stat} performance", "line", data, [x[0] for x in c.description], None, None, None, None, False)


# def graph_grief_value() -> OldGraph:
#     data = c.execute("""
#     WITH 	kT AS (SELECT gameID, score FROM performance WHERE playerID = 0),
#             pT AS (SELECT gameID, score FROM performance WHERE playerID = 1),
#             sT AS (SELECT gameID, score FROM performance WHERE playerID = 2),
#             gAvg AS (SELECT gameID, AVG(performance.score) AS gA FROM performance GROUP BY performance.gameID)
#             SELECT kT.gameID AS GameID, kT.score - gA AS Knus, pT.score - gA AS Puad, sT.score - gA AS Sticker FROM kT
#             LEFT JOIN pT ON kT.gameID = pT.gameID
#             LEFT JOIN sT ON kT.gameID = sT.gameID
#             LEFT JOIN gAvg ON kT.gameID = gAvg.gameID
#     """).fetchall()
#     return OldGraph(f"Grief Value", "line", data, [x[0] for x in c.description], None, None, None, None, False)


# def graph_winrate_last20() -> OldGraph:
#     data = c.execute("""
#         SELECT gameID as GameID, wr AS CG FROM(
#         SELECT gameID, 
#         CAST(SUM(w) OVER(ORDER BY gameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS FLOAT) / 20 AS wr 
#         FROM(SELECT gameID, IIF(goals > against,1,0) AS w FROM games)) WHERE gameID > 19
#     """).fetchall()
#     return OldGraph("Winrate Last20", "line", data, [x[0] for x in c.description], 20, None, 0.15, 0.8, False)


# def graph_winrate() -> OldGraph:
#     data = c.execute("""
#         SELECT gameID AS GameID, CAST(SUM(IIF(goals > against,1,0)) 
#         OVER(ORDER BY gameID) AS FLOAT) / gameID AS CG FROM games
#     """).fetchall()
#     return OldGraph("Winrate", "line", data, [x[0] for x in c.description], None, None, 0.5, 0.55, False)


# def graph_solo_goals() -> OldGraph:
#     data = c.execute("""
#         SELECT gameID AS GameID, SUM(SUM(goals) - SUM(assists)) OVER(ORDER BY gameID) AS CG FROM scores GROUP BY gameID
#     """).fetchall()
#     return OldGraph("Solo Goals", "line", data, [x[0] for x in c.description], None, None, None, None, False)


# def graph_stat_share(stat: str) -> OldGraph:
#     if stat not in possible_stats:
#         raise ValueError(f'{stat} is not in possible stats.')
#     data = c.execute(f"""
#         SELECT k.gameID, 
#         CAST(SUM(k.{stat}) OVER(ORDER BY k.gameID) AS FLOAT) / 
#         (CAST(SUM(k.{stat}) OVER(ORDER BY k.gameID) AS FLOAT) + 
#         CAST(SUM(p.{stat}) OVER(ORDER BY p.gameID) AS FLOAT) + 
#         CAST(SUM(s.{stat}) OVER(ORDER BY s.gameID) AS FLOAT)) AS K,
#         CAST(SUM(p.{stat}) OVER(ORDER BY p.gameID) AS FLOAT) / 
#         (CAST(SUM(k.{stat}) OVER(ORDER BY k.gameID) AS FLOAT) + 
#         CAST(SUM(p.{stat}) OVER(ORDER BY p.gameID) AS FLOAT) + 
#         CAST(SUM(s.{stat}) OVER(ORDER BY s.gameID) AS FLOAT)) AS P,
#         CAST(SUM(s.{stat}) OVER(ORDER BY s.gameID) AS FLOAT) / 
#         (CAST(SUM(k.{stat}) OVER(ORDER BY k.gameID) AS FLOAT) + 
#         CAST(SUM(p.{stat}) OVER(ORDER BY p.gameID) AS FLOAT) + 
#         CAST(SUM(s.{stat}) OVER(ORDER BY s.gameID) AS FLOAT)) AS S
#         FROM knus k JOIN puad p ON k.gameID = p.gameID JOIN sticker s ON k.gameID = s.gameID
#     """).fetchall()
#     return OldGraph(f"{stat.capitalize()} Share", "line", data, [x[0] for x in c.description], None, None, None, None,
#                  False)


# def graph_performance_stat_share(stat: str) -> OldGraph:
#     if stat not in possible_stats:
#         raise ValueError(f'{stat} is not in possible stats.')
#     data = c.execute(f"""
#         SELECT k.gameID AS GameID, 
#         CAST(SUM(k.{stat}) OVER(ORDER BY k.gameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS FLOAT) / 
#         (CAST(SUM(k.{stat}) OVER(ORDER BY k.gameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS FLOAT) + 
#         CAST(SUM(p.{stat}) OVER(ORDER BY p.gameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS FLOAT) + 
#         CAST(SUM(s.{stat}) OVER(ORDER BY s.gameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS FLOAT)) AS K,
#         CAST(SUM(p.{stat}) OVER(ORDER BY p.gameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS FLOAT) / 
#         (CAST(SUM(k.{stat}) OVER(ORDER BY k.gameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS FLOAT) + 
#         CAST(SUM(p.{stat}) OVER(ORDER BY p.gameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS FLOAT) + 
#         CAST(SUM(s.{stat}) OVER(ORDER BY s.gameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS FLOAT)) AS P,
#         CAST(SUM(s.{stat}) OVER(ORDER BY s.gameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS FLOAT) / 
#         (CAST(SUM(k.{stat}) OVER(ORDER BY k.gameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS FLOAT) + 
#         CAST(SUM(p.{stat}) OVER(ORDER BY p.gameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS FLOAT) + 
#         CAST(SUM(s.{stat}) OVER(ORDER BY s.gameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS FLOAT)) AS S
#         FROM knus k JOIN puad p ON k.gameID = p.gameID JOIN sticker s ON k.gameID = s.gameID
#     """).fetchall()
#     return OldGraph(f"{stat.capitalize()} performance share", "line", data, [x[0] for x in c.description], None, None,
#                  None, None,
#                  False)


# def graph_average_mvp_score_over_time() -> OldGraph:
#     data = c.execute("""
#         SELECT gameID, AVG(score) OVER (ORDER BY gameID) AS CG FROM scores GROUP BY gameID HAVING MAX(score)
#     """).fetchall()  # Graph gets joined with LVP, so title is MVP/LVP here
#     return OldGraph("Average MVP/LVP Score", "line", data, [x[0] for x in c.description], None, None, None, None, False)


# def graph_average_lvp_score_over_time() -> OldGraph:
#     data = c.execute("""
#         SELECT gameID AS GameID, AVG(score) OVER (ORDER BY gameID) AS CG FROM scores GROUP BY gameID HAVING MIN(score)
#     """).fetchall()
#     return OldGraph("Average LVP Score", "line", data, [x[0] for x in c.description], None, None, 215, None, False)


# def graph_cumulative_stat(stat: str) -> OldGraph:
#     if stat not in possible_stats:
#         raise ValueError(f'{stat} is not in possible stats.')
#     data = c.execute(f"""
#         SELECT k.gameID, SUM(k.{stat}) OVER (ORDER BY k.gameID) 'Knus', SUM(p.{stat}) OVER (ORDER BY k.gameID) 'Puad', 
#         SUM(s.{stat}) OVER (ORDER BY k.gameID) 'Sticker' FROM knus k LEFT JOIN puad p ON k.gameID = p.gameID 
#         LEFT JOIN sticker s ON k.gameID = s.gameID
#     """).fetchall()
#     return OldGraph(f"Cumulative {stat.capitalize()}", "line", data, [x[0] for x in c.description], None, None, None, None,
#                  False)


# def weekday_table() -> OldGraph:
#     c.execute("""
#         SELECT STRFTIME('%w', date) AS weekday, COUNT(date) AS Games, SUM(IIF(goals > against, 1, 0)) AS Wins, 
#         SUM(IIF(goals < against, 1, 0)) AS Losses FROM games GROUP BY weekday
#     """)

#     # Substitute dayID with corresponding string
#     days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
#     new = [list(x) for x in c.fetchall()]
#     for i in range(0, 7):
#         new[i][0] = days[i]

#     data = new[1:]  # put Sunday at the back of the list
#     data.append(new[0])

#     return OldGraph("Weekdays", "bar", data, [x[0] for x in c.description], None, None, None, None, False)


# def month_table() -> OldGraph:
#     c.execute("""
#         SELECT  STRFTIME('%m', date) AS month, COUNT(date) AS Games, SUM(IIF(goals > against, 1, 0)) AS Wins,
#         SUM(IIF(goals < against, 1, 0)) AS Losses FROM games GROUP BY month""")
#     new = [list(x) for x in c.fetchall()]
#     months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
#               "November", "December"]

#     for i in range(0, 12):
#         new[i][0] = months[i]
#     return OldGraph('Month', 'bar', new, [x[0] for x in c.description], None, None, None, None, False)


# def year_table() -> OldGraph:
#     c.execute("""
#         SELECT STRFTIME('%Y', date) AS year, COUNT(date) AS Games, SUM(IIF(goals > against, 1, 0)) AS Wins,
#         SUM(IIF(goals < against, 1,0)) AS Losses FROM games GROUP BY year""")
#     new = [list(x) for x in c.fetchall()]
#     return OldGraph('Years', 'bar', new, [x[0] for x in c.description], None, None, None, None, False)
# graphs = {
#     'performance_score': graph_performance('score').symbiose(graph_performance_team('score')),
#     'performance_goals': graph_performance('goals').symbiose(graph_performance_team('goals')),
#     'performance_assists': graph_performance('assists').symbiose(graph_performance_team('assists')),
#     'performance_saves': graph_performance('saves').symbiose(graph_performance_team('saves')),
#     'performance_shots': graph_performance('shots').symbiose(graph_performance_team('shots')),
#     'performance_share_score': graph_stat_share('score').change_y(0.3, 0.4),
#     'performance_share_goals': graph_stat_share('goals').change_y(0.3, 0.375),
#     'performance_share_assists': graph_stat_share('assists').change_y(0.3, 0.4),
#     'performance_share_saves': graph_stat_share('saves').change_y(0.3, 0.375),
#     'performance_share_shots': graph_stat_share('shots').change_y(0.285, 0.4),
#     'cumulative_stats_score': graph_cumulative_stat('score'),
#     'cumulative_stats_goals': graph_cumulative_stat('goals'),
#     'cumulative_stats_assists': graph_cumulative_stat('assists'),
#     'cumulative_stats_saves': graph_cumulative_stat('saves'),
#     'cumulative_stats_shots': graph_cumulative_stat('shots'),
#     'grief': graph_grief_value(),
#     'wins_last_20': graph_winrate_last20(),
#     'winrate': graph_winrate(),
#     'solo_goals': graph_solo_goals(),
#     'mvp_lvp_score': graph_average_mvp_score_over_time().symbiose(graph_average_lvp_score_over_time()),
#     'datesChart': dates_table(),
#     'monthChart': month_table(),
#     'yearsChart': year_table(),
#     'weekdChart': weekday_table()
# }
