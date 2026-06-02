from dataclasses import dataclass


class ReplayError(Exception):
    """Custom exception for everything related to replays."""

    def __init__(self, reason: str) -> None:
        self.reason = reason


@dataclass
class ReplayPlayer:
    online_id: str
    name: str
    team: int
    score: int
    goals: int
    assists: int
    saves: int
    shots: int


@dataclass
class ReplayGoal:
    frame: int
    player_name: str
    player_team: int


@dataclass
class ReplayAnalysis:
    match_id: str
    cg_id: int
    cg_score: int
    enemy_score: int
    total_seconds_played: float
    num_frames: int
    goals: list[ReplayGoal]
    players: list[ReplayPlayer]
    map_name: str
    date: str


@dataclass
class RandomFact:
    fact: str
    rarity: int

@dataclass
class LatestSession:
    info_panels: dict
    table_data: list
    player_colors: list[str]


@dataclass(frozen=True)
class Visualizations:
    days: str
    months: str
    years: str
    weekdays: str
    seasons: str
    performance: str
    score_distribution: str