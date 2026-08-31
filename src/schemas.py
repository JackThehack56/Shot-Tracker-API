from typing import TypedDict
from pydantic import BaseModel

class BallPosition(BaseModel):
    lie: str
    distance: int 


class ShotData(BaseModel):
    hole: int
    stroke: int
    club: str
    category: str
    start: BallPosition
    finish: BallPosition
    sg: float

class BallPositionDict(TypedDict):
    lie: str
    distance: int

class ShotDict(TypedDict):
    hole: int
    stroke: int
    club: str
    category: str
    start: BallPositionDict
    finish: BallPositionDict
    sg: float

class HoleDict(TypedDict):
    hole: int
    shots: list[ShotDict]

class RoundDict(TypedDict):
    round_id: int
    holes: list[HoleDict]
