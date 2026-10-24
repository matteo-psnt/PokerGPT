import random
from game.card import Card, Rank, Suit


class Deck:
    def __init__(self):
        self.cards = [Card(rank, suit) for suit in Suit for rank in Rank]
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal_card(self) -> Card:
        return self.cards.pop()
