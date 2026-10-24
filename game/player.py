from enum import IntEnum
from game.card import Card
from game.deck import Deck


class HandRank(IntEnum):
    HIGH_CARD, PAIR, TWO_PAIR, THREE_OF_A_KIND, STRAIGHT, FLUSH, FULL_HOUSE, FOUR_OF_A_KIND, STRAIGHT_FLUSH, ROYAL_FLUSH = range(10)

    def __str__(self) -> str:
        return self.name.replace("_", " ").title()


class Player:
    def __init__(self, name: str, buy_in: int):
        self.name = name
        self.stack = buy_in
        self.round_pot_commitment = 0
        self.card1: Card | None = None
        self.card2: Card | None = None
        self.hand_rank = HandRank.HIGH_CARD
        self.hand_played: list[Card] = []

    @property
    def hand(self) -> list[Card]:
        return [card for card in (self.card1, self.card2) if card is not None]

    # chips the player can still put into this betting round, counting what they've already bet
    @property
    def total_chips(self) -> int:
        return self.stack + self.round_pot_commitment

    def hand_str(self) -> str:
        return ", ".join(map(str, self.hand))

    def hand_long_str(self) -> str | None:
        if self.card1 is not None and self.card2 is not None:
            return f"{self.card1.long_str()}, {self.card2.long_str()}"
        return None

    def deal_hand(self, deck: Deck):
        self.card1 = deck.deal_card()
        self.card2 = deck.deal_card()

    def bet(self, amount: int):
        self.stack -= amount
        self.round_pot_commitment += amount

    def reset(self):
        self.card1 = None
        self.card2 = None
        self.round_pot_commitment = 0
        self.hand_rank = HandRank.HIGH_CARD
        self.hand_played = []
