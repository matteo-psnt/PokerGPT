from enum import Enum

class Rank(Enum):
    ACE, TWO, THREE, FOUR, FIVE, SIX, SEVEN, EIGHT, NINE, TEN, JACK, QUEEN, KING = range(13)

class Suit(Enum):
    SPADES, HEARTS, DIAMONDS, CLUBS = range(4)

class Card:
    def __init__(self, rank: Rank, suit: Suit):
        self.rank = rank
        self.suit = suit

    def __eq__(self, other):
        if type(other) == int:
            return self.rank.value == other
        elif type(other) == Rank:
            return self.rank == other
        elif type(other) == Card:
            return self.rank == other.rank
        else:
            raise TypeError("Cannot compare Card and " + str(type(other)))

    def __ne__(self, other):
        return self.rank != other.rank

    def __lt__(self, other):
        if self.rank == Rank.ACE and other.rank != Rank.ACE:
            return False
        elif self.rank != Rank.ACE and other.rank == Rank.ACE:
            return True
        return self.rank.value < other.rank.value
    
    def __gt__(self, other):
        if self.rank == Rank.ACE and other.rank != Rank.ACE:
            return True
        elif self.rank != Rank.ACE and other.rank == Rank.ACE:
            return False
        return self.rank.value > other.rank.value
    
    # A bit dubious to use this method, but it works
    def __add__(self, other):
        if type(other) == int:
            new_rank = self.rank.value + other
        elif type(other) == Rank:
            new_rank = self.rank.value + other.value
        elif type(other) == Card:
            new_rank = self.rank.value + other.rank.value
        else:
            raise TypeError("Cannot add Card and " + str(type(other)))
        
        if new_rank > 12:
            new_rank -= 13
        return Rank(new_rank)

    def __str__(self):
        suits = ["S", "H", "D", "C"]
        ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        return f"{ranks[self.rank.value]}{suits[self.suit.value]}"

    def __repr__(self):
        return self.__str__()