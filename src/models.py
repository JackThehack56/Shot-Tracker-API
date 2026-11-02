from __future__ import annotations
import json
from src.schemas import (
    BallPosition, 
    ShotDict, 
    HoleDict, 
    RoundDict
)


class Shot:
    hole: int
    stroke: int
    club: str
    category: str
    start: BallPosition
    finish: BallPosition
    sg: float

    def __init__(
        self, hole: int, 
        stroke: int, 
        club: str, 
        category: str, 
        start: BallPosition, 
        finish: BallPosition,
        sg: float
    ):
        self.hole = hole
        self.stroke = stroke
        self.club = club
        self.category = category
        self.start = start
        self.finish = finish
        self.sg = sg

    @staticmethod
    def from_dict(data: ShotDict) -> "Shot":
        return Shot(
            data["hole"],
            data["stroke"],
            data["club"],
            data["category"],
            BallPosition(lie=data["start"]["lie"], distance=data["start"]["distance"]),
            BallPosition(lie=data["finish"]["lie"], distance=data["finish"]["distance"]),
            data["sg"]
        )

    def to_dict(self):

        shot = {
            "hole": self.hole,
            "stroke": self.stroke,
            "club": self.club,
            "category": self.category,
            "start": {
                "lie": self.start.lie, 
                "distance": self.start.distance
            },
            "finish": {
                "lie": self.finish.lie,
                "distance": self.finish.distance
            },
            "sg": self.sg
        }

        return shot

class Hole:
    hole: int
    shots: list[Shot]
    is_finished: bool = False

    def __init__(self, hole: int, *shots: Shot):
        self.hole = hole
        self.shots = [*shots]

    def add_shot(self, shot: Shot):
        if not self.is_finished:
            self.shots.append(shot)
        self._is_finished()

    def _is_finished(self) -> bool:
        self.is_finished = self.shots and self.shots[-1].finish.distance == 0 
        return self.is_finished

    def to_dict(self) -> dict[str, int | list[Shot]]: 
        shots = [x.to_dict() for x in self.shots] if self.shots else []
        
        Hole = {
            "hole": self.hole,
            "shots": shots
        }

        return Hole

    @staticmethod
    def from_dict(data: HoleDict) -> "Hole":
        shots = [Shot.from_dict(x) for x in data["shots"]]
        return Hole(data["hole"], *shots)

    def delete_last_shot(self):
        self.shots = self.shots[:-1]

    def get_last_shot(self) -> Shot:
        return self.shots[-1] if self.shots else None

    def save(self):
        data = self.to_dict()

        with open(f"Hole-{self.hole}.json", "w") as file:
            json.dump(data, file, indent=4)

class Round:
    course: str
    holes: list[Hole]
    is_finished: bool = False

    def __init__(self, course: str, *holes: Hole):
        self.course = course
        self.holes = [*holes]
        self._is_finished()

    def add_hole(self, hole: Hole):
        if not self.is_finished:
            self.holes.append(hole)
        self._is_finished()

    def _is_finished(self):
        for hole in self.holes:
            # Check if all the holes are finished up to the current one 
            self.is_finished = hole._is_finished() and (self.is_finished or hole.hole==1)
        self.is_finished = len(self.holes)>=18 and self.is_finished
        return self.is_finished

    def get_last_shot(self) -> Shot:
        return self.holes[-1].get_last_shot()

    def to_dict(self) -> dict[str, int | list[Hole]]: 
        holes = [x.to_dict() for x in self.holes]

        Round = {
            "course": self.course ,
            "holes": holes
        }

        return Round

    @staticmethod
    def from_dict(data: RoundDict) -> "Round":
        holes = [Hole.from_dict(x) for x in data["holes"]]
        return Round(data["course"], *holes)

    def to_string(self) -> str:
        string = f"{self.course}:\n    "
        for hole in self.holes:
            string += f"Hole-{hole.hole}:\n        "
            for idx, shot in enumerate(hole.shots):
                string += f"Shot{shot.stroke},\n        " if idx<(len(hole.shots)-1) else f"Shot{shot.stroke} \n    "

        return string

#holes: list[Hole] = []
#for h in range(1, 19):
#    hole = Hole(h)
#    for shot in range(1, 5):
#        if h != 1 and shot == 4:
#            hole.add_shot(Shot(hole, shot, "club", "category", BallPosition(lie="lie", distance=10), 
#                               BallPosition(lie="lie", distance=0), 0.0194))
#            continue
#        hole.add_shot(Shot(hole, shot, "club", "category", BallPosition(lie="lie", distance=10), 
#                           BallPosition(lie="lie", distance=7), 0.0194))
#    holes.append(hole)
#
#for hole in holes:
#    print(hole.is_finished)
#
#round = Round("Dufferin Glen Golf Club", *holes)
#
#print(round.is_finished)