import datetime
import json
import os
import shutil
import subprocess
from typing import Optional

from queries import GeneralQueries, RLQueries
from structs import ReplayAnalysis, ReplayError, ReplayGoal, ReplayPlayer


def handle_upload(replay_file) -> int:

    # Validate file
    if not replay_file.filename.endswith(".replay"):
        raise ReplayError("Invalid file type.")
    # Save file to temp folder
    temp_file_path = f"./replays/temp/{datetime.datetime.now().timestamp()}_{replay_file.filename}"

    try:
        with open(temp_file_path, "wb+") as file_object:
            file_object.write(replay_file.file.read())
    except Exception:
        raise ReplayError("Error writing file to server.")
    # Analyze replay
    analysis: ReplayAnalysis = extract_replay_data(temp_file_path)
    # Determine game_id
    game_id: Optional[int] = determine_game_id(analysis)
    if not game_id:
        os.remove(temp_file_path)
        raise ReplayError("No database match found.")
    if GeneralQueries.game_id_has_replay(game_id):
        os.remove(temp_file_path)
        raise ReplayError(f"Replay {game_id} has already been uploaded.")
    # Persist file in replays folder
    try:
        shutil.move(temp_file_path, f"./replays/{game_id}.replay")
    except Exception as e:
        os.remove(temp_file_path)
        raise ReplayError(f"Error moving replay to persistent storage.")
    # Save statistics to db
    GeneralQueries.save_replay_stats(game_id, analysis)
    return game_id


def determine_game_id_old(analysis: ReplayAnalysis) -> Optional[int]:
    potential_games = RLQueries.games_by_date(analysis.date[:10])
    all_players = GeneralQueries.get_player_ids()
    print(f"Matching for {analysis}")
    for potential_game in potential_games:
        print(f"Checking {potential_game}")
        # Check each players stats
        matches = int(analysis.cg_score == potential_game["goals"]) + \
            int(analysis.enemy_score == potential_game["against"])
        for player_id in all_players:
            player_stats_db = RLQueries.player_stats_by_gameid(potential_game["gameID"], player_id)
            if not player_stats_db:
                continue
            player_stats_replay = [p for p in analysis.players if p.online_id == player_id]
            if not player_stats_replay:
                continue
            matches += amount_of_matching_stats(player_stats_db[0], player_stats_replay[0])
        if matches >= 15:  # 15 out of 17
            return potential_game["gameID"]


def determine_game_id(analysis: ReplayAnalysis) -> Optional[int]:
    potential_games = RLQueries.games_by_date(analysis.date[:10])
    for potential_game in potential_games:
        # Check each players stats
        matches = int(analysis.cg_score == potential_game["goals"]) + \
            int(analysis.enemy_score == potential_game["against"])
        for player_db in RLQueries.get_player_scores_by_gameid(potential_game["gameID"]):
            matching_players = [p for p in analysis.players if p.online_id == player_db["playerID"]]
            if player_analysis := matching_players[0] if matching_players else None:
                matches += amount_of_matching_stats(player_db, player_analysis)
        if matches >= 15:  # 15 out of 17
            return potential_game["gameID"]


def amount_of_matching_stats(player_stats_db, player_stats_replay) -> float:
    return sum(
        1 for attr in ("score", "goals", "assists", "saves", "shots")
        if player_stats_db.get(attr) == getattr(player_stats_replay, attr)
    )


def extract_replay_data(temp_file_path: str) -> ReplayAnalysis:
    try:
        rpy = json.loads(subprocess.check_output([".\\rrrocket-0.11.1.exe", f"{temp_file_path}"]))
    except subprocess.CalledProcessError:
        os.remove(temp_file_path)
        raise ReplayError("Encountered error while parsing.")
    except FileNotFoundError:
        raise ReplayError(f"Replay file {temp_file_path} not found.")

    cg_players_ids = GeneralQueries.get_team_player_ids()
    try:
        players = [
            ReplayPlayer(
                online_id=player.get("PlayerID").get("fields").get("EpicAccountId") if
                player.get("Platform").get("value") == "OnlinePlatform_Epic" else
                player.get("OnlineID"),
                name=player.get("Name"),
                team=player.get("Team"),
                score=player.get("Score"),
                goals=player.get("Goals"),
                assists=player.get("Assists"),
                saves=player.get("Saves"),
                shots=player.get("Shots")
            )
            for player in rpy.get("properties").get("PlayerStats")
        ]
        cg_id = 0 if any(p.online_id in cg_players_ids for p in players if p.team == 0) else 1
        analysis = ReplayAnalysis(
            match_id=rpy.get("properties").get("Id"),
            cg_score=rpy.get("properties").get("Team0Score", 0) if cg_id == 0 else rpy.get(
                "properties").get("Team1Score", 0),
            enemy_score=rpy.get("properties").get(
                "Team1Score", 0) if cg_id == 0 else rpy.get("properties").get("Team0Score", 0),
            total_seconds_played=rpy.get("properties").get("TotalSecondsPlayed"),
            num_frames=rpy.get("properties").get("NumFrames"),
            goals=[
                ReplayGoal(
                    goal.get("frame"),
                    goal.get("PlayerName"),
                    goal.get("PlayerTeam")
                )
                for goal in rpy.get("properties").get("Goals")
            ],
            players=players,
            map_name=rpy.get("properties").get("MapName"),
            date=rpy.get("properties").get("Date"),
            cg_id=cg_id
        )
    except Exception:
        os.remove(temp_file_path)
        raise ReplayError("Replay file too old to be supported.")
    return analysis
