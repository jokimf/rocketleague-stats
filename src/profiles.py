import queries


def build_player_profiles(conn, active_player_ids: list[str]) -> list[dict]:
    return [
        {
            "player_id": player_id,
            "name": queries.player_name(conn, player_id),
            "rank": player_rank(conn, player_id),
            "color": queries.player_color(conn, player_id),
            "stats": profile_averages(conn, player_id),
            "top": performance_profile_view(conn, player_id),
            "griefing": player_average_deviation(conn, player_id),
            "justout": just_out(conn, player_id),
            "tobeatnext": to_beat_next(conn, player_id),
        }
        for player_id in active_player_ids
    ]


def get_current_session_games(conn) -> int:
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM games g GROUP BY g.`date` ORDER BY date DESC LIMIT 1")
        data = cursor.fetchone()
        return data[0] if data else 0


def get_current_season_games(conn) -> int:
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) FROM games g
            LEFT JOIN seasons s ON g.date BETWEEN s.start_date AND s.end_date 
            GROUP BY s.seasonID 
            ORDER BY s.seasonID DESC 
            LIMIT 1
        """)
        data = cursor.fetchone()
        return data[0] if data else 0


def get_player_stat_averages(conn, player_id: str, limit: int) -> tuple:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT AVG(h.score), AVG(h.goals), AVG(h.assists), AVG(h.saves), AVG(h.shots)
            FROM (
                SELECT s.score, s.goals, s.assists, s.saves, s.shots
                FROM scores s
                WHERE s.playerID = %s
                ORDER BY s.gameID DESC 
                LIMIT %s
            ) h
        """,
            (player_id, limit),
        )
        result = cursor.fetchone()
        return result if result else (0, 0, 0, 0, 0)


def profile_averages(conn, player_id: str) -> list:
    """Calculates aggregated player stat averages across multiple game thresholds."""
    game_thresholds = [
        get_current_session_games(conn),
        20,
        get_current_season_games(conn),
        500,
        queries.total_games(conn),
    ]

    # Fetch stats for each threshold and transpose the results
    stats_matrix = [get_player_stat_averages(conn, player_id, limit) for limit in game_thresholds]
    return list(zip(*stats_matrix))


def performance_profile_view(conn, player_id: str):
    def _performance_rank(conn, stat: str, player_id: str) -> int:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                    SELECT n FROM 
                        (SELECT row_number() OVER (ORDER BY {stat} DESC) AS n, gameID, %s 
                        FROM performance WHERE playerID = %s) AS why 
                        WHERE gameID = %s
                    """,
                (stat, player_id, queries.total_games(conn)),
            )
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
        cursor.execute("SELECT * FROM performance WHERE playerID = %s AND gameID = %s", (player_id, queries.total_games(conn)))
        data = cursor.fetchone()
        if data is None:
            return []
        values = data[2:]
    top = (
        round(_performance_rank(conn, "score", player_id) / queries.total_games(conn) * 100, 1),
        round(_performance_rank(conn, "goals", player_id) / queries.total_games(conn) * 100, 1),
        round(_performance_rank(conn, "assists", player_id) / queries.total_games(conn) * 100, 1),
        round(_performance_rank(conn, "saves", player_id) / queries.total_games(conn) * 100, 1),
        round(_performance_rank(conn, "shots", player_id) / queries.total_games(conn) * 100, 1),
    )
    return list(zip(values, top, [_color(x) for x in top]))


def player_average_deviation(conn, player_id: str) -> int:
    with conn.cursor() as cursor:
        cursor.execute(
            """WITH av AS (
                            SELECT AVG(p2.score) AS a FROM (
                                SELECT p.score FROM performance p JOIN players z ON p.playerID = z.playerID
                                WHERE z.active = 1 ORDER BY p.gameID DESC LIMIT 3
                            ) p2
                        )
                        SELECT p.score - av.a FROM performance p, av
                        WHERE p.playerID = %s
                        ORDER BY p.gameID DESC LIMIT 1;""",
            (player_id,),
        )
        data = cursor.fetchone()
        return data[0] if data else 0


def just_out(conn, player_id: str) -> tuple[int, int]:
    max_id = queries.total_games(conn)
    if max_id < 21:
        return (0, 0)
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT scores.score 
            FROM scores
            WHERE (gameID = %s - 20 OR gameID = %s) AND playerID = %s
            ORDER BY playerID
            """,
            (max_id, max_id, player_id),
        )
        data = cursor.fetchall()
        if not data:
            return (0, 0)
        return data[0][0], data[1][0]


def to_beat_next(conn, player_id: str) -> int:
    with conn.cursor() as cursor:
        cursor.execute(
            """WITH maxId AS (SELECT MAX(gameID) AS mId FROM scores)
                        SELECT scores.score FROM scores, maxId WHERE gameID = maxId.mId - 19 AND playerID = %s""",
            (player_id,),
        )
        data = cursor.fetchone()
        return data[0] if data else 0


def player_rank(conn, player_id: str) -> str:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT r.abbr FROM scores s JOIN ranks r ON s.rank = r.abbr WHERE playerID = %s ORDER BY gameID desc LIMIT 1",
            (player_id,),
        )
        data = cursor.fetchone()
        return data[0] if data else "u"  # TODO find better way than hardcoding unranked
