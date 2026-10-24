from dataclasses import dataclass
from enum import Enum, IntEnum


class Rank(IntEnum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

    @property
    def symbol(self) -> str:
        return self.name[0] if self > Rank.TEN else str(self.value)

    @property
    def long_name(self) -> str:
        return self.name.title() if self > Rank.TEN else str(self.value)


class Suit(Enum):
    SPADES = "S"
    HEARTS = "H"
    DIAMONDS = "D"
    CLUBS = "C"


@dataclass(frozen=True)
class Card:
    rank: Rank
    suit: Suit

    def __str__(self):
        return f"{self.rank.symbol}{self.suit.value}"

    def __repr__(self):
        return str(self)

    def long_str(self):
        return f"{self.rank.long_name} of {self.suit.name.title()}"
