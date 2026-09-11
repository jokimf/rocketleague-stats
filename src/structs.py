from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum, StrEnum
from typing import Any, Self


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


@dataclass(frozen=True)
class Session:
    session_id: str
    date: str
    wins: int
    losses: int
    goals: int
    against: int


@dataclass
class LatestSessionPanel:
    session: Session
    table_data: list
    highlighting: list


@dataclass(frozen=True)
class Visualizations:
    days: str
    months: str
    years: str
    weekdays: str
    seasons: str
    performance: str
    score_distribution: str


@dataclass(frozen=True)
class Record:
    title: str
    id: str
    data: list[Any]


class StatType(StrEnum):
    SCORE = "score"
    GOALS = "goals"
    ASSISTS = "assists"
    SAVES = "saves"
    SHOTS = "shots"

    @classmethod
    def validate(cls, stat: Self | str) -> Self:
        try:
            return cls(stat)
        except ValueError:
            raise ValueError(f"'{stat}' is not a valid stat. Allowed stats: {', '.join([s.value for s in cls])}")


@dataclass(frozen=True)
class Player:
    playerID: str
    name: str
    color: str | None
    team: bool
    active: bool
    order: bool


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


@dataclass(frozen=True)
class RandomValues:
    days_since_first: int
    total_games: int
    tilt: float
    average_session_length: float


## Starting 3.0 ##


@dataclass(frozen=True)
class TeamOverviewRow:
    games: int
    wins: int
    losses: int
    win_rate: float
    avg_goals_per_game: float
    avg_against_per_game: float
    avg_differential_per_game: float
    avg_score_per_game: float
    avg_assists_per_game: float
    avg_saves_per_game: float
    avg_shots_per_game: float
    avg_game_duration_s: float
    longest_game_duration_s: float


@dataclass(frozen=True)
class TeamOverview:
    last_5: TeamOverviewRow
    last_20: TeamOverviewRow
    last_100: TeamOverviewRow
    last_500: TeamOverviewRow
    last_1000: TeamOverviewRow
    lifetime: TeamOverviewRow


@dataclass(frozen=True)
class TeamStreaks:
    current_win: int
    current_loss: int
    score: int
    not_score: int


# @dataclass(frozen=True)
# class GoalMargins:
