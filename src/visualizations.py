import random
from enum import Enum  # for class type hints

import simplejson as json  # To be able to serialize object of type Decimal
from typing import Self
from queries import GeneralQueries
from structs import Visualizations


def get_all_visualizations(conn, total_games_count, active_players) -> Visualizations:
    return Visualizations(
        days=_days(conn),
        months=_months(conn),
        years=_years(conn),
        weekdays=_weekdays(conn),
        seasons=_seasons(conn),
        performance=_performance(conn, total_games_count, active_players),
        score_distribution=_score_distribution(conn, active_players),
    )


class DatasetColor(Enum):
    @staticmethod
    def random_color() -> str:
        r, g, b = (
            random.randrange(0, 256),
            random.randrange(0, 256),
            random.randrange(0, 256),
        )
        return f"rgba({r},{g},{b},0.6)"

    TEAM = ("rgba(40, 40, 40, 0.8)",)
    WIN = ("rgba(13, 70, 13, 0.8)",)
    LOSS = ("rgba(135, 4, 4, 0.8)",)
    GAME = ("rgba(17, 3, 58, 0.8)",)
    NEUTRAL_GREY = ("rgba(128,128,128,0.6)",)
    WHITE = "rgba(255,255,255,0.6)"


class VisualizationBuilder:
    def __init__(self) -> None:
        self._vis: dict = {
            "type": "bar",
            "data": {
                "labels": [],
                "datasets": [],
            },
            "options": {
                "plugins": {"legend": dict(), "title": dict()},
                "scales": {
                    "x": dict(),
                    "y": dict(),
                },
            },
        }

    def to_str(self) -> str:
        return json.dumps(self._vis)

    def with_labels(self, labels: list) -> Self:
        self._vis["data"]["labels"] = labels
        return self

    def with_type(self, vis_type: str) -> Self:
        self._vis["type"] = vis_type
        return self

    def with_title(
        self, text: str, align: str = "center", position: str = "top"
    ) -> Self:
        title_attributes = {
            "text": text,
            "align": align,
            "position": position,
            "display": True,
        }
        title_section = self._vis["options"]["plugins"]["title"]
        title_section |= title_attributes
        return self

    def with_legend(self, show: bool) -> Self:
        legend_section = self._vis["options"]["plugins"]["legend"]
        legend_section |= {"display": show}
        return self

    def with_dataset(
        self,
        data: list[int | float],
        label: str,
        color: DatasetColor | str,
        border_color,
        border_width: int = 1,
    ) -> Self:
        if isinstance(color, DatasetColor):
            color = color.value
        if isinstance(border_color, DatasetColor):
            border_color = border_color.value

        dataset_attributes = {
            "data": data,
            "label": label,
            "borderWidth": border_width,
            "backgroundColor": color,
            "borderColor": border_color,
            # "fill": True
        }
        data_section: list = self._vis["data"]["datasets"]
        data_section.append(dataset_attributes)
        return self

    def with_limits(
        self,
        x_min: int | None = None,
        x_max: int | None = None,
        y_min: int | None = None,
        y_max: int | None = None,
    ) -> Self:
        scales = self._vis["options"]["scales"]

        if x_min is not None:
            scales["x"]["min"] = x_min
        if x_max is not None:
            scales["x"]["max"] = x_max
        if y_min is not None:
            scales["y"]["min"] = y_min
        if y_max is not None:
            scales["y"]["max"] = y_max
        return self

    def with_grid(
        self, x_color: DatasetColor | str = None, y_color: DatasetColor | str = None
    ) -> Self:
        def get_val(c):
            return c.value if isinstance(c, DatasetColor) else c

        scales = self._vis["options"]["scales"]

        if x_color is not None:
            scales["x"]["grid"] = {"color": get_val(x_color)}
        if y_color is not None:
            scales["y"]["grid"] = {"color": get_val(y_color)}
        return self

    def with_second_yaxis(self) -> Self:
        raise NotImplementedError
        y1_section = self._vis.get("options").get("scales").get("y1")
        y1_section |= {"display": True, "position": "right"}
        # TODO: Labels are unrelated
        return self


def _days(conn) -> str:
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT DATE_FORMAT(date, '%d') AS day, SUM(IF(goals > against,1,0)) AS Wins, SUM(IF(goals < against,1,0)) AS Losses 
            FROM games GROUP BY day ORDER BY day ASC
        """)
        raw = cursor.fetchall()

    labels, wins, losses = zip(*raw)
    graph = (
        VisualizationBuilder()
        .with_dataset(wins, "Wins", DatasetColor.WIN, DatasetColor.TEAM)
        .with_dataset(losses, "Losses", DatasetColor.LOSS, DatasetColor.TEAM)
        .with_labels(labels)
        .with_legend(False)
    )
    return graph.to_str()


def _weekdays(conn) -> str:
    with conn.cursor() as cursor:
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

    graph = (
        VisualizationBuilder()
        .with_dataset(wins, "Wins", DatasetColor.WIN, DatasetColor.TEAM)
        .with_dataset(losses, "Losses", DatasetColor.LOSS, DatasetColor.TEAM)
        .with_labels(
            [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
        )
        .with_legend(False)
    )
    return graph.to_str()


def _months(conn) -> str:
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT DATE_FORMAT(date,'%m') AS month, SUM(IF(goals > against, 1, 0)), SUM(IF(goals < against, 1, 0)) 
            FROM games GROUP BY month ORDER BY month ASC""")
        raw = cursor.fetchall()
    _, wins, losses = zip(*raw)

    graph = (
        VisualizationBuilder()
        .with_dataset(wins, "Wins", DatasetColor.WIN, DatasetColor.TEAM)
        .with_dataset(losses, "Losses", DatasetColor.LOSS, DatasetColor.TEAM)
        .with_labels(
            [
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December",
            ]
        )
        .with_legend(False)
    )
    return graph.to_str()


def _years(conn) -> str:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT DATE_FORMAT(date,'%Y') AS year, SUM(IF(goals > against, 1, 0)), SUM(IF(goals < against, 1,0)) FROM games GROUP BY year"
        )
        raw = cursor.fetchall()
    labels, wins, losses = zip(*raw)

    graph = (
        VisualizationBuilder()
        .with_dataset(wins, "Wins", DatasetColor.WIN, DatasetColor.TEAM)
        .with_dataset(losses, "Losses", DatasetColor.LOSS, DatasetColor.TEAM)
        .with_labels(labels)
        .with_legend(False)
    )
    return graph.to_str()


def _performance(conn, total_games_count: int, active_players: list[str]) -> str:
    data_list = []
    with conn.cursor() as cursor:
        for player_id in active_players:
            cursor.execute(
                f"SELECT s.score FROM performance s WHERE s.playerID = {player_id} ORDER BY gameID DESC LIMIT 20"
            )
            data_list.append(list(reversed([x[0] for x in cursor.fetchall()])))
        average = [sum(group) / len(group) for group in zip(*data_list)]

    graph = (
        VisualizationBuilder()
        .with_type("line")
        .with_dataset(
            average, "Average", DatasetColor.WHITE, DatasetColor.NEUTRAL_GREY, 3
        )
        .with_labels(list(range(total_games_count - 19, total_games_count + 1)))
        .with_grid(y_color="rgba(209, 209, 209, 0.1)")
    )

    for i, player_id in enumerate(active_players):
        player_info = GeneralQueries.get_player_info(conn, player_id)
        graph = graph.with_dataset(
            data_list[i],
            player_info.get("name"),
            player_info.get("color"),
            DatasetColor.NEUTRAL_GREY,
        )
    return graph.to_str()


def _score_distribution(conn, active_players: list[str]) -> str:
    datasets = []
    with conn.cursor() as cursor:
        for player_id in active_players:
            cursor.execute(
                """
                SELECT t1.grouper * 25 AS lower_bound, (t1.grouper + 1) * 25 AS upper_bound, COUNT(t1.grouper) AS score_count
                FROM (
                    SELECT score, FLOOR(score/25) AS grouper
                    FROM scores
                    WHERE playerID = %s
                ) t1
                GROUP BY t1.grouper
                ORDER BY 1
            """,
                (player_id,),
            )
            raw = cursor.fetchall()
            datasets.append([x[2] for x in raw])
            labels = [x[1] for x in raw]

    graph = (
        VisualizationBuilder()
        .with_type("line")
        .with_labels(labels)
        .with_grid(y_color="rgba(209, 209, 209, 0.1)")
    )

    for i, player_id in enumerate(active_players):
        player_info = GeneralQueries.get_player_info(conn, player_id)
        graph = graph.with_dataset(
            datasets[i],
            player_info.get("name"),
            player_info.get("color"),
            DatasetColor.NEUTRAL_GREY,
        )
    return graph.to_str()


def _seasons(conn) -> str:
    with conn.cursor() as cursor:
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
    graph = (
        VisualizationBuilder()
        .with_dataset(wins, "Wins", DatasetColor.WIN, DatasetColor.TEAM)
        .with_dataset(losses, "Losses", DatasetColor.LOSS, DatasetColor.TEAM)
        .with_labels(labels)
        .with_legend(False)
    )
    return graph.to_str()
