import datetime
import json
import os
import shutil
import subprocess
from typing import Optional

import db
import utility
from structs import ReplayAnalysis, ReplayError, ReplayGoal, ReplayPlayer

RRROCKET_EXECUTABLE = utility.get_rrrocket_analyzer()


def handle_upload(conn, replay_file) -> int:
    if not replay_file.filename.endswith(".replay"):
        raise ReplayError("Invalid file type.")
    temp_file_path = f"./replays/temp/{datetime.datetime.now().timestamp()}_{replay_file.filename}"

    try:
        with open(temp_file_path, "wb+") as file_object:
            file_object.write(replay_file.file.read())
    except Exception:
        raise ReplayError("Error writing file to server.")

    analysis: ReplayAnalysis = extract_replay_data(conn, temp_file_path)
    game_id: Optional[int] = determine_game_id(conn, analysis)

    if not game_id:
        os.remove(temp_file_path)
        raise ReplayError("No database match found.")
    if game_id_has_replay(conn, game_id):
        os.remove(temp_file_path)
        raise ReplayError(f"Replay {game_id} has already been uploaded.")

    # Persist file in replays folder
    try:
        shutil.move(temp_file_path, f"./replays/{game_id}.replay")
    except Exception:
        os.remove(temp_file_path)
        raise ReplayError("Error moving replay to persistent storage.")

    # Save statistics to db
    write_replay_stats(conn, game_id, analysis)
    return game_id


def determine_game_id(conn, analysis: ReplayAnalysis) -> Optional[int]:
    potential_games = games_by_date(conn, analysis.date[:10])
    for potential_game in potential_games:
        # Check each players stats
        matches = int(analysis.cg_score == potential_game["goals"]) + int(analysis.enemy_score == potential_game["against"])
        for player_db in get_player_scores_by_gameid(conn, potential_game["gameID"]):
            matching_players = [p for p in analysis.players if p.online_id == player_db["playerID"]]
            if player_analysis := matching_players[0] if matching_players else None:
                matches += amount_of_matching_stats(player_db, player_analysis)
        if matches >= 15:  # 15 out of 17
            return potential_game["gameID"]


def amount_of_matching_stats(player_stats_db, player_stats_replay) -> float:
    return sum(1 for attr in ("score", "goals", "assists", "saves", "shots") if player_stats_db.get(attr) == getattr(player_stats_replay, attr))


def extract_replay_data(conn, temp_file_path: str) -> ReplayAnalysis:
    try:
        rpy = json.loads(subprocess.check_output([f"./{RRROCKET_EXECUTABLE}", f"{temp_file_path}"]))
    except subprocess.CalledProcessError:
        os.remove(temp_file_path)
        raise ReplayError(f"Encountered error while parsing file: {temp_file_path}")
    except FileNotFoundError:
        raise ReplayError(f"{RRROCKET_EXECUTABLE} not found.")

    # Check if replay is parse-worthy
    team_size = rpy.get("properties").get("TeamSize")
    if team_size != 3:
        raise ReplayError("Team size did not equal 3.")

    own_team_ids = get_team_player_ids(conn)
    try:
        players = [
            ReplayPlayer(
                online_id=player.get("PlayerID").get("fields").get("EpicAccountId")
                if player.get("Platform").get("value") == "OnlinePlatform_Epic"
                else player.get("OnlineID"),
                name=player.get("Name"),
                team=player.get("Team"),
                score=player.get("Score"),
                goals=player.get("Goals"),
                assists=player.get("Assists"),
                saves=player.get("Saves"),
                shots=player.get("Shots"),
            )
            for player in rpy.get("properties").get("PlayerStats")
        ]
        cg_id = 0 if any(p.online_id in own_team_ids for p in players if p.team == 0) else 1
        analysis = ReplayAnalysis(
            match_id=rpy.get("properties").get("Id"),
            cg_score=rpy.get("properties").get("Team0Score", 0) if cg_id == 0 else rpy.get("properties").get("Team1Score", 0),
            enemy_score=rpy.get("properties").get("Team1Score", 0) if cg_id == 0 else rpy.get("properties").get("Team0Score", 0),
            total_seconds_played=rpy.get("properties").get("TotalSecondsPlayed"),
            num_frames=rpy.get("properties").get("NumFrames"),
            goals=[ReplayGoal(goal.get("frame"), goal.get("PlayerName"), goal.get("PlayerTeam")) for goal in rpy.get("properties").get("Goals")],
            players=players,
            map_name=rpy.get("properties").get("MapName"),
            date=rpy.get("properties").get("Date"),
            cg_id=cg_id,
        )
    except Exception as e:
        os.remove(temp_file_path)
        raise ReplayError(f"Parser error: {e}")
    return analysis


def get_missing_recent_game_ids():
    with db.get_db_connection() as conn, conn.cursor() as c:
        c.execute("SELECT gameID FROM games WHERE replayAvailable = 0 order by gameID desc LIMIT 50;")
        return (x[0] for x in c.fetchall())


def get_team_player_ids(conn) -> list[str]:
    with conn.cursor() as cursor:
        cursor.execute("SELECT playerID FROM players WHERE team = 1 ORDER BY `order` ASC")
        player_ids = cursor.fetchall()
        if not player_ids:
            return []
        return [player_id[0] for player_id in player_ids]


def game_id_has_replay(conn, game_id: int) -> bool:
    with conn.cursor() as cursor:
        cursor.execute("SELECT replayAvailable FROM games WHERE gameID = %s", (game_id,))
        return bool(cursor.fetchone()[0])


def write_replay_stats(conn, game_id: int, analysis: ReplayAnalysis) -> None:
    with conn.cursor() as cursor:
        cursor.execute(
            "UPDATE games SET secondsPlayed = %s, mapName = %s, replayAvailable = TRUE WHERE gameID = %s",
            (analysis.total_seconds_played, analysis.map_name, game_id),
        )
        for player in analysis.players:
            cursor.execute(
                "INSERT IGNORE INTO players (playerID, name) VALUES (%s,%s)",
                (player.online_id, player.name),
            )
            cursor.execute(
                "INSERT IGNORE INTO scores VALUES (%s,%s,NULL,%s,%s,%s,%s,%s)",
                (
                    game_id,
                    player.online_id,
                    player.score,
                    player.goals,
                    player.assists,
                    player.saves,
                    player.shots,
                ),
            )
        for goal in analysis.goals:
            scorer = [p for p in analysis.players if p.name == goal.player_name]
            if scorer := scorer[0] if scorer else None:  # TODO: Sometimes, players are not part of players but scored...?
                cursor.execute(
                    "INSERT IGNORE INTO goals VALUES (NULL,%s,%s,%s)",
                    (game_id, scorer.online_id, goal.frame),
                )
            else:
                raise ReplayError("A Player not in players scored.")

    conn.commit()


def get_player_scores_by_gameid(conn, game_id: int):
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute(
            """
            SELECT p.playerID, s.score, s.goals, s.assists, s.saves, s.shots
            FROM games g JOIN scores s ON g.gameID = s.gameID JOIN players p on s.playerID = p.playerID 
            WHERE g.gameID = %s AND p.team = TRUE;
        """,
            (game_id,),
        )
        return cursor.fetchall()


def games_by_date(conn, date: str, adjancent_days: int = 1) -> list:
    yesterday = (datetime.date.fromisoformat(date) - datetime.timedelta(days=adjancent_days)).strftime("%Y-%m-%d")
    tomorrow = (datetime.date.fromisoformat(date) + datetime.timedelta(days=adjancent_days)).strftime("%Y-%m-%d")
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute(
            "SELECT * FROM games WHERE date >= %s AND date <= %s;",
            (yesterday, tomorrow),
        )
        games = cursor.fetchall()
    return games
