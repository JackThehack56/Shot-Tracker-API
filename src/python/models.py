import json
from src.python.schemas import (
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

    def __init__(self, hole: int, stroke: int, club: str, category: str, start: BallPosition, finish: BallPosition):
        self.hole = hole
        self.stroke = stroke
        self.club = club
        self.category = category
        self.start = start
        self.finish = finish

    @staticmethod
    def from_dict(data: ShotDict) -> Shot:
        return Shot(
            data["hole"],
            data["stroke"],
            data["club"],
            data["category"],
            BallPosition(lie=data["start"]["lie"], distance=data["start"]["distance"]),
            BallPosition(lie=data["finish"]["lie"], distance=data["finish"]["distance"])
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
            }
        }

        return shot

class Hole:
    hole: int
    shots: list[Shot]

    def __init__(self, hole: int, *shots: Shot):
        self.hole = hole
        self.shots = [*shots]

    def add_shot(self, shot: Shot):
        self.shots.append(shot)


    def to_dict(self) -> dict[str, int | list[Shot]]: 
        shots = [x.to_dict() for x in self.shots]

        Hole = {
            "hole": self.hole,
            "shots": shots
        }

        return Hole

    @staticmethod
    def from_dict(data: HoleDict) -> Hole:
        shots = [Shot.from_dict(x) for x in data["shots"]]
        return Hole(data["hole"], *shots)

    def save(self):
        data = self.to_dict()

        with open(f"Hole-{self.hole}.json", "w") as file:
            json.dump(data, file, indent=4)

class Round:
    round_id: int
    holes: list[Hole]
    is_finished: bool

    def __init__(self, round_id: int, *holes: Hole):
        self.round_id = round_id
        self.holes = [*holes]
        self.is_finished = len(self.holes)>=18

    def add_hole(self, hole: Hole):
        if not self.is_finished:
            self.holes.append(hole)
        self.is_finished = len(self.holes)>=18

    def to_dict(self) -> dict[str, int | list[Hole]]: 
        holes = [x.to_dict() for x in self.holes]

        Round = {
            "round_id": self.round_id,
            "holes": holes
        }

        return Round

    @staticmethod
    def from_dict(data: RoundDict) -> Round:
        holes = [Hole.from_dict(x) for x in data["holes"]]
        return Round(data["round_id"], *holes)

    def to_string(self) -> str:
        string = f"Round-{self.round_id}:\n    "
        for hole in self.holes:
            string += f"Hole-{hole.hole}:\n        "
            for idx, shot in enumerate(hole.shots):
                string += f"Shot{shot.stroke},\n        " if idx<(len(hole.shots)-1) else f"Shot{shot.stroke} \n    "

        return string

    def save(self):
        data = self.to_dict()

        with open(f"Round-{self.round_id}.json", "w") as file:
            json.dump(data, file, indent=4)