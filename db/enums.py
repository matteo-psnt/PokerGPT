from enum import Enum

class GameResult(Enum):
    COMPLETE_WIN = "complete win"
    WIN = "win"
    COMPLETE_LOSS = "complete loss"
    LOSS = "loss"
    DRAW = "draw"
    IN_PROGRESS = "in progress"

class HandResult(Enum):
    WIN = "win"
    LOSS = "loss"
    SPLIT_POT = "split pot"
    IN_PROGRESS = "in progress"

class Round(Enum):
    PRE_FLOP = "pre-flop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"
    IN_PROGRESS = "in progress"

class ActionType(Enum):
    CALL = "call"
    CHECK = "check"
    FOLD = "fold"
    RAISE = "raise"
    ALL_IN = "all-in"
