from dataclasses import dataclass
from typing import Optional

from fastapi import Header, HTTPException, status
from fastapi.requests import Request

import db
from queries import GeneralQueries

import os


def conditional_formatting(color: str, value: float, minimum: int, maximum: int) -> str:
    minimum = int(minimum)
    maximum = int(maximum)
    if color is None or (type(value) is not float and type(value) is not int):
        raise ValueError(
            f"Color can not be None and value needs to be int or float: color={color}, value={type(value)}")
    if maximum - minimum == 0:
        return f"{color[:-1]},0)"
    opacity = (value - minimum) / (maximum - minimum)
    rgb_code = f"{color[:-1]},{opacity})"
    return rgb_code


def fade_highlighting(game: int, game_range: int):
    return f"rgba(53, 159, 159,{(game_range - (GeneralQueries.total_games() - game)) / game_range})"


@dataclass
class User:
    username: str
    identifier: str
    userid: int

    def has_valid_values(self) -> bool:
        return bool(self.username and self.identifier and self.userid)

    def is_premium(self, conn) -> bool:
        with conn.cursor() as cursor:
            cursor.execute("SELECT premium FROM users WHERE username=%s AND identifier=%s AND userID=%s",
                            (self.username, self.identifier, self.userid))
            premium = cursor.fetchone()[0]
            return bool(premium)

    def check_credentials(self, conn) -> bool:
        with conn.cursor() as cursor:
            if not self.has_valid_values():
                return False
            cursor.execute("SELECT 1 FROM users WHERE username=%s AND identifier=%s AND userid=%s",
                            (self.username, self.identifier, self.userid))
            user_found = cursor.fetchone()
        return user_found and bool(user_found[0])


def extract_user_info(request: Request) -> Optional[User]:
    username = request.cookies.get('username')
    identifier = request.cookies.get('identifier')
    userid = int(request.cookies.get('userid')) if request.cookies.get('userid') else 0
    user = User(username, identifier, int(userid))
    return user


MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def enforce_max_size(content_length: int = Header(None)):
    if content_length is None:
        raise HTTPException(
            status_code=411, detail="Missing Content-Length header"
        )
    if content_length > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large"
        )

def get_rrrocket_analyzer():
    match os.name:
        case "posix":
            return "rrrocket/rrrocket-0.11.1"
        case _:
            return "rrrocket/rrrocket-0.11.1.exe"