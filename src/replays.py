
import subprocess
import json


def deserialize_replay():
    pass


def process_replay(game_id: int):
    try:
        replay_json = json.loads(subprocess.check_output([".\\rrrocket.exe", f".\\replays\\{game_id}.replay"]))
    except subprocess.CalledProcessError:
        print("Encountered error while parsing.")
        return False
    print(replay_json)


process_replay(3956)
