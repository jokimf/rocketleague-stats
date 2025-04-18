from __future__ import annotations  # for class type hints

import random
from enum import Enum

import simplejson as json  # To be able to serialize object of type Decimal
from mysql.connector import MySQLConnection

from connect import DatabaseConnection


class GraphBuilder:
    def __init__(self) -> None:
        self._graph: dict = {
            "type": "bar",
            "data": {
                "labels": [],
                "datasets": [],
            },
            "options": {
                "plugins": {
                    "legend": dict(),
                    "title": dict()
                },
                "scales": {
                    "x": dict(),
                    "y": dict(),
                    # "y1":
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

    def withDataset(self, data: list[int | float], label: str, color: DatasetColor | str, border_color, borderWidth: int = 1) -> GraphBuilder:
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
            # "fill": True
        }
        data_section: list = self._graph.get("data").get("datasets")
        data_section.append(dataset_attributes)
        return self

    def withLimits(self, xmin: int | None = None, xmax: int | None = None, ymin: int | None = None, ymax: int | None = None) -> GraphBuilder:
        options_section = self._graph.get("options")
        attributes = {"x_min": xmin, "x_max": xmax, "y_min": ymin, "y_max": ymax}

        # Filter parameters that are None
        attributes = {key: value for key, value in attributes.items() if value is not None}

        options_section |= attributes
        return self

    def withGrid(self, x_color: DatasetColor | str = None, y_color: DatasetColor | str = None) -> GraphBuilder:
        if x_color is not None:
            if isinstance(x_color, DatasetColor):
                x_color = x_color.value
            x_section = self._graph.get("options").get("scales").get("x")
            x_section |= {"x": {"grid": {"color": x_color}}}

        if y_color is not None:
            if isinstance(y_color, DatasetColor):
                y_color = y_color.value
            y_section = self._graph.get("options").get("scales").get("y")
            y_section |= {"y": {"grid": {"color": y_color}}}
        return self

    def withSecondYAxis(self) -> GraphBuilder:
        raise NotImplementedError
        y1_section = self._graph.get("options").get("scales").get("y1")
        y1_section |= {"display": True, "position": "right"}
        # TODO: Labels are unrelated to graph
        return self


class DatasetColor(Enum):
    def random_color() -> str:
        r, g, b = random.randrange(0, 256), random.randrange(0, 256), random.randrange(0, 256)
        return f"rgba({r},{g},{b},0.6)"

    KNUS = "rgba(47,147,26,0.8)",
    PUAD = "rgba(147,26,26,0.8)",
    STICKER = "rgba(26,115,147,0.8)",
    CLOWN = "rgba(40, 40, 40, 0.8)",
    WIN = "rgba(3, 58, 3, 0.8)",
    LOSS = "rgba(58, 3, 3, 0.8)",
    GAME = "rgba(17, 3, 58, 0.8)",
    NEUTRAL = "rgba(128,128,128,0.6)",
    WHITE = "rgba(255,255,255,0.6)"


class GraphQueries:
    conn: MySQLConnection = DatabaseConnection().get()

    @staticmethod
    def days_graph() -> dict:
        with GraphQueries.conn.cursor() as cursor:
            cursor.execute("""
                SELECT DATE_FORMAT(date, '%d') AS day, SUM(IF(goals > against,1,0)) AS Wins, SUM(IF(goals < against,1,0)) AS Losses 
                FROM games GROUP BY day ORDER BY day ASC
            """)
            raw = cursor.fetchall()

        labels, wins, losses = zip(*raw)
        graph = GraphBuilder() \
            .withDataset(wins, "Wins", DatasetColor.WIN, DatasetColor.CLOWN) \
            .withDataset(losses, "Losses", DatasetColor.LOSS, DatasetColor.CLOWN) \
            .withLabels(labels) \
            .withLegend(False)
        return graph.toJSON()

    @staticmethod
    def weekdays_graph() -> dict:
        with GraphQueries.conn.cursor() as cursor:
            cursor.execute("""
                SELECT DATE_FORMAT(date,'%w') AS weekday, SUM(IF(goals > against, 1, 0)), SUM(IF(goals < against, 1, 0))
                FROM games GROUP BY weekday ORDER BY weekday ASC
            """)
            raw = cursor.fetchall()
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

    @staticmethod
    def month_graph() -> dict:
        with GraphQueries.conn.cursor() as cursor:
            cursor.execute("""
                SELECT DATE_FORMAT(date,'%m') AS month, SUM(IF(goals > against, 1, 0)), SUM(IF(goals < against, 1, 0)) 
                FROM games GROUP BY month ORDER BY month ASC""")
            raw = cursor.fetchall()
        _, wins, losses = zip(*raw)

        graph = GraphBuilder() \
            .withDataset(wins, "Wins", DatasetColor.WIN, DatasetColor.CLOWN) \
            .withDataset(losses, "Losses", DatasetColor.LOSS, DatasetColor.CLOWN) \
            .withLabels(["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]) \
            .withLegend(False)
        return graph.toJSON()

    @staticmethod
    def year_graph() -> dict:
        with GraphQueries.conn.cursor() as cursor:
            cursor.execute(
                "SELECT DATE_FORMAT(date,'%Y') AS year, SUM(IF(goals > against, 1, 0)), SUM(IF(goals < against, 1,0)) FROM games GROUP BY year")
            raw = cursor.fetchall()
        labels, wins, losses = zip(*raw)

        graph = GraphBuilder() \
            .withDataset(wins, "Wins", DatasetColor.WIN, DatasetColor.CLOWN) \
            .withDataset(losses, "Losses", DatasetColor.LOSS, DatasetColor.CLOWN) \
            .withLabels(labels) \
            .withLegend(False)
        return graph.toJSON()

    @staticmethod
    def performance_graph(total_games_count: int) -> dict:
        data_list = []
        with GraphQueries.conn.cursor() as cursor:
            for player_id in [0, 1, 2]:  # TODO: cleanup
                cursor.execute(
                    f"SELECT s.score FROM performance s WHERE s.playerID = {player_id} ORDER BY gameID DESC LIMIT 20")
                data_list.append(list(reversed([x[0] for x in cursor.fetchall()])))
            average = [sum(group) / len(group) for group in zip(*data_list)]

        graph = GraphBuilder() \
            .withType("line") \
            .withDataset(data_list[0], "Knus", DatasetColor.KNUS, DatasetColor.KNUS) \
            .withDataset(data_list[1], "Puad", DatasetColor.PUAD, DatasetColor.PUAD) \
            .withDataset(data_list[2], "Sticker", DatasetColor.STICKER, DatasetColor.STICKER) \
            .withDataset(average, "Average", DatasetColor.WHITE, DatasetColor.NEUTRAL, 3) \
            .withLabels(list(range(total_games_count - 20, total_games_count))) \
            .withGrid(y_color="rgba(209, 209, 209, 0.1)")  # TODO: label is one off
        return graph.toJSON()

    @staticmethod
    def results_table():
        with GraphQueries.conn.cursor() as cursor:
            cursor.execute("""
                WITH cG AS (SELECT COUNT(*) allG FROM games)
                SELECT goals, against, COUNT(*) AS c, CAST(COUNT(*) AS FLOAT) / MAX(cG.allG) AS ch  
                FROM games, cG
                GROUP BY goals, against
                ORDER BY goals ASC;
            """)
            graph_data = cursor.fetchall()
        return [{"x": str(goals), "y": str(against), "v": value} for goals, against, value, _ in graph_data]

    @staticmethod
    def score_distribution_graph() -> dict:
        datasets = []
        with GraphQueries.conn.cursor() as cursor:
            for player_id in [0, 1, 2]:  # TODO: cleanup
                cursor.execute("""
                    SELECT t1.grouper * 25 AS lower_bound, (t1.grouper + 1) * 25 AS upper_bound, COUNT(t1.grouper) AS score_count
                    FROM (
                        SELECT score, FLOOR(score/25) AS grouper
                        FROM scores
                        WHERE playerID = %s
                    ) t1
                    GROUP BY t1.grouper
                    ORDER BY 1
                """, (player_id,))
                raw = cursor.fetchall()
                datasets.append([x[2] for x in raw])
                labels = [x[1] for x in raw]

        graph = GraphBuilder() \
            .withType("line") \
            .withDataset(datasets[0], "Knus", DatasetColor.KNUS, DatasetColor.NEUTRAL) \
            .withDataset(datasets[1], "Puad", DatasetColor.PUAD, DatasetColor.NEUTRAL) \
            .withDataset(datasets[2], "Sticker", DatasetColor.STICKER, DatasetColor.NEUTRAL) \
            .withLabels(labels)
        return graph.toJSON()

    @staticmethod
    def seasons_graph() -> dict:
        with GraphQueries.conn.cursor() as cursor:
            cursor.execute(""" 
                SELECT se.season_name,
                SUM(IF(g.goals > g.against,1,0)) 'wins',
                SUM(IF(g.goals < g.against,1,0)) 'losses',
                ROUND(CAST(SUM(IF(g.goals > g.against,1,0)) AS FLOAT) / CAST(COUNT(g.gameID) AS FLOAT)*100,2) 'wr'
                FROM games g
                LEFT JOIN seasons se ON g.date BETWEEN se.start_date AND se.end_date
                GROUP BY seasonID
            """)
            dataset = cursor.fetchall()

        labels, wins, losses, _ = zip(*dataset)
        graph = GraphBuilder() \
            .withDataset(wins, "Wins", DatasetColor.WIN, DatasetColor.CLOWN) \
            .withDataset(losses, "Losses", DatasetColor.LOSS, DatasetColor.CLOWN) \
            .withLabels(labels) \
            .withLegend(False)
        return graph.toJSON()
