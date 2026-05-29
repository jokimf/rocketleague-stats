from queries import GeneralQueries, RLQueries
import db

class ProfileQueries:
    @staticmethod
    def build_player_profiles(conn, active_player_ids: list[str]) -> list[dict]:
        return [
            {
                "player_id": player_id,
                "name": GeneralQueries.player_name(conn, player_id),
                "rank": GeneralQueries.player_rank(conn, player_id),
                "color": GeneralQueries.player_color(conn, player_id),
                "stats": ProfileQueries.profile_averages(conn, player_id),
                "top": ProfileQueries.performance_profile_view(conn, player_id),
                "griefing": ProfileQueries.player_average_deviation(conn, player_id),
                "justout": ProfileQueries.just_out(conn, player_id),
                "tobeatnext": ProfileQueries.to_beat_next(conn, player_id)
            } for player_id in active_player_ids
        ]

    @staticmethod
    def profile_averages(conn, player_id: str):
        def _profile_average_stats(conn, past_games_amount: int) -> list:
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

        game_counts = [RLQueries.current_session_games_played(conn), 20, RLQueries.current_season_games_played(conn),
                       500, GeneralQueries.total_games(conn)]
        return list(zip(*[_profile_average_stats(conn, amount)[0] for amount in game_counts]))  # Transpose results

    @staticmethod
    def performance_profile_view(conn, player_id: str):
        def _performance_rank(conn, stat: str, player_id: str) -> int:
            with conn.cursor() as cursor:
                cursor.execute(f"""
                        SELECT n FROM 
                            (SELECT row_number() OVER (ORDER BY {stat} DESC) AS n, gameID, %s 
                            FROM performance WHERE playerID = %s) AS why 
                            WHERE gameID = %s
                        """, (stat, player_id, GeneralQueries.total_games(conn)))
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

        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM performance WHERE playerID = %s AND gameID = %s",
                            (player_id, GeneralQueries.total_games(conn)))
            data = cursor.fetchone()
            if data is None:
                return []
            values = data[2:]
        top = (
            round(_performance_rank(conn, "score", player_id) / GeneralQueries.total_games(conn) * 100, 1),
            round(_performance_rank(conn, "goals", player_id) / GeneralQueries.total_games(conn) * 100, 1),
            round(_performance_rank(conn, "assists", player_id) / GeneralQueries.total_games(conn) * 100, 1),
            round(_performance_rank(conn, "saves", player_id) / GeneralQueries.total_games(conn) * 100, 1),
            round(_performance_rank(conn, "shots", player_id) / GeneralQueries.total_games(conn) * 100, 1)
        )
        return list(zip(values, top, [_color(x) for x in top]))

    @staticmethod
    def player_average_deviation(conn, player_id: str) -> int:
        with conn.cursor() as cursor:
            cursor.execute(f"""WITH av AS (SELECT AVG(p2.score) a FROM (SELECT * FROM performance p ORDER BY p.gameID DESC LIMIT 3) p2)
                            SELECT p.score - av.a FROM performance p, av WHERE p.playerID = %s ORDER BY p.gameID DESC LIMIT 1""", (player_id,))
            data = cursor.fetchone()
            return data[0] if data else 0

    @staticmethod
    def just_out(conn, player_id: str) -> tuple[int]:
        max_id = GeneralQueries.total_games(conn)
        if max_id < 21:
            return (0, 0)
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
    def to_beat_next(conn, player_id: str) -> int:
        with conn.cursor() as cursor:
            cursor.execute("""WITH maxId AS (SELECT MAX(gameID) AS mId FROM scores)
                            SELECT scores.score FROM scores, maxId WHERE gameID = maxId.mId - 19 AND playerID = %s""", (player_id,))
            data = cursor.fetchone()
            return data[0] if data else 0
