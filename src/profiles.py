from connect import Database
from queries import GeneralQueries, RLQueries


class ProfileQueries:
    @staticmethod
    def build_player_profiles() -> list[dict]:
        return [
            {
                "name": GeneralQueries.player_name(player_id),
                "rank": GeneralQueries.player_rank(player_id),
                "color": GeneralQueries.player_color(player_id),
                "stats": ProfileQueries.profile_averages(player_id),
                "top": ProfileQueries.performance_profile_view(player_id),
                "griefing": ProfileQueries.player_average_deviation(player_id),
                "justout": ProfileQueries.just_out(player_id),
                "tobeatnext": ProfileQueries.to_beat_next(player_id)
            } for player_id in GeneralQueries.get_active_players()
        ]

    @staticmethod
    def profile_averages(player_id: int):
        def _profile_average_stats(past_games_amount: int) -> list:
            with Database.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT AVG(h.score), AVG(h.goals), AVG(h.assists), AVG(h.saves), AVG(h.shots)
                        FROM (
                            SELECT s.score, s.goals, s.assists, s.saves, s.shots
                            FROM scores s
                            WHERE s.playerID = %s
                            ORDER BY s.gameID DESC 
                            LIMIT %s
                        ) h
                    """, (player_id, past_games_amount))
                    return cursor.fetchall()

        game_counts = [RLQueries.current_session_games_played(), 20, RLQueries.current_season_games_played(),
                       500, GeneralQueries.total_games()]
        return list(zip(*[_profile_average_stats(amount)[0] for amount in game_counts]))  # Transpose results

    @staticmethod
    def performance_profile_view(p_id: int):
        def _performance_rank(stat: str, player_id: int) -> int:
            with Database.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(f"""
                            SELECT n FROM 
                                (SELECT row_number() OVER (ORDER BY {stat} DESC) AS n, gameID, %s 
                                FROM performance WHERE playerID = %s) AS why 
                                WHERE gameID = %s
                            """, (stat, player_id, GeneralQueries.total_games()))
                    return cursor.fetchone()[0]

        def _color(value: float) -> str:
            if value <= 2:
                return "Orange;font-weight:bolder"
            elif value <= 10:
                return "SteelBlue;font-weight:bolder"
            elif value <= 25:
                return "ForestGreen"
            elif value <= 50:
                return "LightSlateGrey"
            elif value <= 75:
                return "#B6B6B4"
            else:
                return "IndianRed"

        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM performance WHERE playerID = %s AND gameID = %s",
                               (p_id, GeneralQueries.total_games()))
                data = cursor.fetchone()
                if data is None:
                    return []
                values = data[2:]
        top = (
            round(_performance_rank("score", p_id) / GeneralQueries.total_games() * 100, 1),
            round(_performance_rank("goals", p_id) / GeneralQueries.total_games() * 100, 1),
            round(_performance_rank("assists", p_id) / GeneralQueries.total_games() * 100, 1),
            round(_performance_rank("saves", p_id) / GeneralQueries.total_games() * 100, 1),
            round(_performance_rank("shots", p_id) / GeneralQueries.total_games() * 100, 1)
        )
        return list(zip(values, top, [_color(x) for x in top]))

    @staticmethod
    def player_average_deviation(player_id: int) -> int:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"""WITH av AS (SELECT AVG(p2.score) a FROM (SELECT * FROM performance p ORDER BY p.gameID DESC LIMIT 3) p2)
                                SELECT p.score - av.a FROM performance p, av WHERE p.playerID = %s ORDER BY p.gameID DESC LIMIT 1""", (player_id,))
                data = cursor.fetchone()
                return data[0] if data else 0

    @staticmethod
    def just_out(player_id: int) -> tuple[int]:
        max_id = GeneralQueries.total_games()
        if max_id < 21:
            return (0, 0)
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT scores.score 
                    FROM scores
                    WHERE (gameID = %s - 20 OR gameID = %s) AND playerID = %s
                    ORDER BY playerID
                    """, (max_id, max_id, player_id))
                data = cursor.fetchall()
                if not data:
                    return (0, 0)
                return data[0][0], data[1][0]

    @staticmethod
    def to_beat_next(player_id: int) -> int:
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""WITH maxId AS (SELECT MAX(gameID) AS mId FROM scores)
                                SELECT scores.score FROM scores, maxId WHERE gameID = maxId.mId - 19 AND playerID = %s""", (player_id,))
                data = cursor.fetchone()
                return data[0] if data else 0
