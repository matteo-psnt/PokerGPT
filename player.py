from typing import Any
from deck import *


class handRank(Enum):
    HIGH_CARD, PAIR, TWO_PAIR, THREE_OF_A_KIND, STRAIGHT, FLUSH, FULL_HOUSE, FOUR_OF_A_KIND, STRAIGHT_FLUSH, ROYAL_FLUSH = range(10)

    def __str__(self) -> str:
        return self.name.replace("_", " ").title()
    
    def __lt__(self, other):
        return self.value < other.value
    
    def __gt__(self, other):
        return self.value > other.value
    
    def __eq__(self, other):
        return self.value == other.value


class Player:
    def __init__(self, player_name: str, buy_in: int):
        self.player_name = player_name
        self.stack = buy_in
        self.round_pot_commitment = 0
        self.card1 = None
        self.card2 = None
        self.hand_rank = handRank.HIGH_CARD
        self.hand_played = []

    def print_hand(self):
        print(f"{self.card1}, {self.card2}")
    
    def return_hand(self):
        return f"{self.card1}, {self.card2}"
    
    def return_long_hand(self):
        if self.card1 is not None and self.card2 is not None:
            return f"{self.card1.long_str()}, {self.card2.long_str()}"

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
        self.hand_rank = handRank.HIGH_CARD
        self.hand_played = []