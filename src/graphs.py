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
    
    def withLegend(self, show: bool) -> GraphBuilder:
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
            "borderColor": border_color,
            #"fill": True
        }
        data_section: list = self._graph.get("data").get("datasets")
        data_section.append(dataset_attributes)
        return self
    
    
    def withLimits(self, xmin: int|None = None, xmax: int|None = None, ymin: int|None = None, ymax: int|None = None) -> GraphBuilder:
        options_section = self._graph.get("options")
        attributes = {"x_min": xmin, "x_max": xmax, "y_min": ymin, "y_max": ymax}
        
        # Filter parameters that are None
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
    NEUTRAL = 'rgba(128,128,128,0.6)',
    WHITE = 'rgba(255,255,255,0.6)'

class GraphQueries(BackendConnection):
    def days_graph(self) -> dict:
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
            .withLabels(labels) \
            .withLegend(False)
        return graph.toJSON()
    
    def weekdays_graph(self) -> dict:
        self.c.execute("""
            SELECT DATE_FORMAT(date,'%w') AS weekday, SUM(IF(goals > against, 1, 0)), SUM(IF(goals < against, 1, 0))
            FROM games GROUP BY weekday ORDER BY weekday ASC
        """)
        raw = self.c.fetchall()
        _, wins, losses = zip(*raw)
        wins = list(wins)
        losses = list(losses)

        # Since Sunday is dayID=0, put it at the back of the list
        wins.append(wins.pop(0))
        losses.append(losses.pop(0))
        graph = GraphBuilder() \
            .withDataset(wins, "Wins", DatasetColor.WIN, DatasetColor.CLOWN) \
            .withDataset(losses, "Losses", DatasetColor.LOSS, DatasetColor.CLOWN) \
            .withLabels(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]) \
            .withLegend(False)
        return graph.toJSON()
    
    def month_graph(self) -> dict:
        self.c.execute("""
            SELECT DATE_FORMAT(date,'%m') AS month, SUM(IF(goals > against, 1, 0)), SUM(IF(goals < against, 1, 0)) 
            FROM games GROUP BY month ORDER BY month ASC""")
        raw = self.c.fetchall()
        _, wins, losses = zip(*raw)

        graph = GraphBuilder() \
            .withDataset(wins, "Wins", DatasetColor.WIN, DatasetColor.CLOWN) \
            .withDataset(losses, "Losses", DatasetColor.LOSS, DatasetColor.CLOWN) \
            .withLabels(["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]) \
            .withLegend(False)
        return graph.toJSON()
    
    def year_graph(self) -> dict:
        self.c.execute("""
            SELECT DATE_FORMAT(date,'%Y') AS year, SUM(IF(goals > against, 1, 0)), SUM(IF(goals < against, 1,0)) 
            FROM games GROUP BY year""")
        raw = self.c.fetchall()
        labels, wins, losses = zip(*raw)

        graph = GraphBuilder() \
            .withDataset(wins, "Wins", DatasetColor.WIN, DatasetColor.CLOWN) \
            .withDataset(losses, "Losses", DatasetColor.LOSS, DatasetColor.CLOWN) \
            .withLabels(labels) \
            .withLegend(False)
        return graph.toJSON()

    def performance_graph(self) -> dict:
        data_list = []
        for player_id in [0, 1, 2]:
            self.c.execute(f"SELECT s.score FROM performance s WHERE s.playerID = {player_id} ORDER BY gameID DESC LIMIT 20")
            raw = self.c.fetchall()
            data_list.append(list(reversed([x[0] for x in raw])))
            average = [sum(group) / len(group) for group in zip(*data_list)]
        graph = GraphBuilder() \
            .withType("line") \
            .withDataset(data_list[0], "Knus", DatasetColor.KNUS, DatasetColor.NEUTRAL) \
            .withDataset(data_list[1], "Puad", DatasetColor.PUAD, DatasetColor.NEUTRAL) \
            .withDataset(data_list[2], "Sticker", DatasetColor.STICKER, DatasetColor.NEUTRAL) \
            .withDataset(average, "Average", DatasetColor.WHITE, DatasetColor.NEUTRAL, 3) \
            .withLabels(list(range(1,21)))
        return graph.toJSON()
    
    def results_table(self) -> GraphBuilder:
        self.c.execute("""
            WITH cG AS (SELECT COUNT(*) allG FROM games)
            SELECT goals, against, COUNT(*) AS c, CAST(COUNT(*) AS FLOAT) / MAX(cG.allG) AS ch  
            FROM games, cG
            GROUP BY goals, against
            ORDER BY goals ASC;
        """)
        return [{"x": str(g), "y": str(a), "v": v} for g, a, v, _ in self.c.fetchall()]
    
    def score_distribution_graph(self) -> GraphBuilder:
        datasets = []
        for player_id in [0, 1, 2]:
            self.c.execute("""
                SELECT t1.grouper * 25 AS lower_bound, (t1.grouper + 1) * 25 AS upper_bound, COUNT(t1.grouper) AS score_count
                FROM (
                    SELECT score, FLOOR(score/25) AS grouper
                    FROM scores
                    WHERE playerID = %s
                ) t1
                GROUP BY t1.grouper
                ORDER BY 1
            """, (player_id,))
            raw = self.c.fetchall()
            datasets.append([x[2] for x in raw])
            labels = [x[1] for x in raw]
        graph = GraphBuilder() \
            .withType("line") \
            .withDataset(datasets[0], "Knus", DatasetColor.KNUS, DatasetColor.NEUTRAL) \
            .withDataset(datasets[1], "Puad", DatasetColor.PUAD, DatasetColor.NEUTRAL) \
            .withDataset(datasets[2], "Sticker", DatasetColor.STICKER, DatasetColor.NEUTRAL) \
            .withLabels(labels)
        return graph.toJSON()
 
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
# SELECT 
#     k.gameID, 
#     (SELECT SUM(k1.saves) FROM knus k1 WHERE k1.gameID <= k.gameID) AS 'Knus', 
#     (SELECT SUM(p1.saves) FROM puad p1 WHERE p1.gameID <= k.gameID) AS 'Puad', 
#     (SELECT SUM(s1.saves) FROM sticker s1 WHERE s1.gameID <= k.gameID) AS 'Sticker' 
# FROM knus k;
