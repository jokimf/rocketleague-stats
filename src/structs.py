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
