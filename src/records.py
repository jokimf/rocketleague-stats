from collections import namedtuple

from connect import BackendConnection

Record = namedtuple("Record", ["title", "id", "data"])


class RecordQueries(BackendConnection):
    def highest_stat_value_one_game(self, stat: str, limit: int = 3) -> Record:
        if stat not in ["score", "goals", "assists", "saves", "shots"]:
            raise ValueError(f"{stat} is not in possible stats.")
        if stat == "goals":
            stat = "scores.goals"

        self.c.execute(f"""
                SELECT name, {stat}, games.gameID, date 
                FROM games JOIN scores ON games.gameID = scores.gameID NATURAL JOIN players
                ORDER BY {stat} DESC, games.gameID ASC LIMIT %s""", (limit,))
        stat = "points" if stat == "score" else stat
        stat = "goals" if stat == "scores.goals" else stat
        return Record(f"Most {stat} by player ", f"max{stat}player", self.c.fetchall())

    def highest_stat_team_one_game(self, stat: str, limit: int = 3) -> Record:
        if stat not in ["score", "goals", "assists", "saves", "shots"]:
            raise ValueError(f"{stat} is not in possible stats.")
        if stat == "goals":
            stat = "scores.goals"
        self.c.execute(f"""
                SELECT "CG", SUM({stat}) AS stat, games.gameID, date 
                FROM games JOIN scores ON games.gameID = scores.gameID 
                GROUP BY games.gameID, date ORDER BY stat DESC, games.gameID ASC LIMIT %s
            """, (limit,))
        stat = "points" if stat == "score" else stat
        stat = "goals" if stat == "scores.goals" else stat
        return Record(f"Most {stat} by team", f"max{stat}team", self.c.fetchall())

    def performance_records(self, stat: str, minmax: str, limit: int = 3) -> Record:
        if stat not in ["score", "goals", "assists", "saves", "shots"] or minmax not in ["MIN", "MAX"]:
            raise ValueError(f"{stat} is not in possible stats or {minmax} is not MIN or MAX")
        if stat == "goals":
            stat = "performance.goals"
        self.c.execute(f"""
            SELECT name, {minmax}({stat}) AS s, games.gameID, date 
            FROM performance JOIN games ON games.gameID = performance.gameID NATURAL JOIN players
            GROUP BY games.gameID, name, date ORDER BY s {("DESC" if minmax == "MAX" else "ASC")}, games.gameID ASC LIMIT %s""", (limit,))
        stat = "points" if stat == "score" else stat
        stat = "goals" if stat == "performance.goals" else stat
        return Record(f"{"Highest" if minmax == "MAX" else "Lowest"} {stat} performance", f"performance{minmax}{stat}", self.c.fetchall())

    def most_against(self, limit: int = 3) -> Record:
        self.c.execute("SELECT 'CG', against, gameID, date FROM games ORDER BY against DESC, gameID ASC LIMIT %s", (limit,))
        return Record("Most goals conceded by team", "mostagainst", self.c.fetchall())

    def most_against_and_won(self, limit: int = 3) -> Record:
        self.c.execute(
            "SELECT 'CG', against, gameID, date FROM games WHERE goals > against ORDER BY against DESC, gameID ASC LIMIT %s", (limit,))
        return Record("Most goals conceded but still won", "mostagainstwon", self.c.fetchall())

    def most_goals_and_lost(self, limit: int = 3) -> Record:
        self.c.execute(
            "SELECT 'CG', goals, gameID, date FROM games WHERE goals < against ORDER BY goals DESC, gameID ASC LIMIT %s",
            (limit,))
        return Record("Most goals scored and still lost", "mostscoredlost", self.c.fetchall())

    def most_total_goals(self, limit: int = 3) -> Record:
        self.c.execute("SELECT 'CG',goals+against, gameID, date FROM games ORDER BY goals + against DESC, gameID ASC LIMIT %s",
                       (limit,))
        return Record(f"Most total goals in one game", "mosttotalgoals", self.c.fetchall())

    def highest_points_nothing_else(self, limit: int = 3) -> Record:
        self.c.execute("""SELECT players.name, MAX(scores.score) AS p, games.gameID, games.date     
                FROM scores JOIN games ON games.gameID = scores.gameID NATURAL JOIN players
                WHERE scores.goals = 0 AND scores.assists=0 AND scores.saves=0 AND scores.shots=0
                GROUP BY games.gameID, players.name, games.date ORDER BY p DESC, games.gameID ASC LIMIT %s""", (limit,))
        return Record("Most points with all stats being 0", "highestnothing", self.c.fetchall())

    def most_points_without_goal_or_assist(self, limit: int = 3) -> Record:
        self.c.execute("""SELECT players.name, MAX(scores.score) as p, games.gameID, games.date 
                FROM scores JOIN games ON games.gameID = scores.gameID NATURAL JOIN players
                WHERE scores.goals = 0 AND scores.assists=0
                GROUP BY games.gameID, players.name, games.date ORDER BY p DESC, games.gameID ASC LIMIT %s""", (limit,))
        return Record("Most points without scoring or assisting", "mostpointsnogoalassist", self.c.fetchall())

    def most_points_without_goal(self, limit: int = 3) -> Record:
        self.c.execute("""SELECT name, score, games.gameID, date FROM games JOIN scores ON games.gameID = scores.gameID NATURAL JOIN players
            WHERE scores.goals = 0 ORDER BY score DESC, games.gameID ASC LIMIT %s""", (limit,))
        return Record("Most points with no goal", "mostpointsnogoal", self.c.fetchall())

    def least_points_at_least_1(self, limit: int = 3) -> Record:
        self.c.execute("""SELECT name, MIN(score) as p, games.gameID, date 
                FROM scores JOIN games ON games.gameID = scores.gameID NATURAL JOIN players
                WHERE scores.goals >= 1 AND assists >=1 AND saves >=1 AND shots >=1
                GROUP BY games.gameID, name, date ORDER BY p ASC, games.gameID ASC LIMIT %s""", (limit,))
        return Record("Least points with all stats being at least 1", "leastwith1", self.c.fetchall())

    def least_points_with_goals(self, limit: int = 3) -> Record:
        self.c.execute("""SELECT name, score, games.gameID, date FROM games JOIN scores ON games.gameID = scores.gameID NATURAL JOIN players
            WHERE scores.goals > 0 ORDER BY score ASC, games.gameID ASC LIMIT %s""", (limit,))
        return Record("Least points with at least one goal", "leastwithgoal", self.c.fetchall())

    # Difference between MVP and LVP, DESC for most diff, ASC for least diff
    def diff_mvp_lvp(self, order: str, limit: int = 3) -> Record:
        if order not in ["ASC", "DESC"]:
            raise ValueError("Order is not DESC or ASC.")
        self.c.execute(f"""
            SELECT p.name, msc.score - lsc.score AS diff, ml.gameID, g.date
            FROM mvplvp ml
            LEFT JOIN scores msc ON ml.gameID = msc.gameID AND ml.MVP = msc.playerID
            LEFT JOIN scores lsc ON ml.gameID = lsc.gameID AND ml.LVP = lsc.playerID
            LEFT JOIN players p ON msc.playerID = p.playerID
            LEFT JOIN games g ON ml.gameID = g.gameID
            ORDER BY msc.score-lsc.score {order}, g.gameID ASC LIMIT %s""", (limit,))
        return Record(f"{"Highest" if order == "DESC" else "Lowest"} score diff between MVP and LVP", f"diff{order}", self.c.fetchall())

    def most_solo_goals(self, limit: int = 3) -> Record:
        self.c.execute("""
                SELECT "CG", games.goals - SUM(assists) AS ja, games.gameID, date FROM games 
                JOIN scores ON games.gameID = scores.gameID
                GROUP BY games.gameID, games.goals, date ORDER BY ja DESC, games.gameID ASC LIMIT %s""", (limit,))
        return Record("Most solo goals by 'team'", "MOST_SOLO", self.c.fetchall())

    def generate_record_games(self) -> list[tuple[Record]]:
        game_amount = 16
        records = [
            (self.highest_stat_value_one_game("score", game_amount),
             self.highest_stat_value_one_game("goals", game_amount),
             self.highest_stat_value_one_game("assists", game_amount),
             self.highest_stat_value_one_game("saves", game_amount),
             self.highest_stat_value_one_game("shots", game_amount)),
            (self.highest_stat_team_one_game("score", game_amount),
             self.highest_stat_team_one_game("goals", game_amount),
             self.highest_stat_team_one_game("assists", game_amount),
             self.highest_stat_team_one_game("saves", game_amount),
             self.highest_stat_team_one_game("shots", game_amount)),
            (self.performance_records("score", "MAX", game_amount),
             self.performance_records("goals", "MAX", game_amount),
             self.performance_records("assists", "MAX", game_amount),
             self.performance_records("saves", "MAX", game_amount),
             self.performance_records("shots", "MAX", game_amount)),
            (self.performance_records("score", "MIN", game_amount),
             self.performance_records("goals", "MIN", game_amount),
             self.performance_records("assists", "MIN", game_amount),
             self.performance_records("saves", "MIN", game_amount),
             self.performance_records("shots", "MIN", game_amount)),
            (self.most_against(game_amount),
             self.most_against_and_won(game_amount),
             self.most_goals_and_lost(game_amount),
             self.most_total_goals(game_amount)),
            (self.highest_points_nothing_else(game_amount),
             self.most_points_without_goal_or_assist(game_amount),
             self.most_points_without_goal(game_amount),
             self.least_points_at_least_1(game_amount),
             self.least_points_with_goals(game_amount)),
            (self.diff_mvp_lvp("DESC", game_amount),
             self.diff_mvp_lvp("ASC", game_amount),
             self.most_solo_goals(game_amount))
        ]
        return records
