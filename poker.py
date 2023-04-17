from enum import Enum
from typing import List, Tuple
import random


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
        suits = ["♠️", "♥️", "♦️", "♣️"]
        ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        colors = ['\033[30m', '\033[31m', '\033[34m','\033[32m', '\033[0m']
        
        # returns colored card based on suit (black for spades and clubs, red for hearts and diamonds)
        return f"{colors[self.suit.value]}{ranks[self.rank.value]}{suits[self.suit.value]}{colors[4]}"

    def __repr__(self):
        return self.__str__()


class Deck:
    def __init__(self):
        self.cards = [Card(rank, suit) for suit in Suit for rank in Rank]
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal_card(self):
        return self.cards.pop()

    def __str__(self):
        return ", ".join(map(str, self.cards))


class Player:
    def __init__(self, deck: Deck):
        self.card1 = deck.deal_card()
        self.card2 = deck.deal_card()

    def print_hand(self):
        print(f"{self.card1}, {self.card2}")
    
    def set_hand(self, card1: Card, card2: Card):
        self.card1 = card1
        self.card2 = card2


class PokerGame:
    def __init__(self, num_players: int):
        self.deck = Deck()
        self.players = [Player(self.deck) for _ in range(num_players)]
        self.board = []

    def deal_board(self, num_cards: int = 1):
        for _ in range(num_cards):
            self.board.append(self.deck.deal_card())

    def print_player_hands(self):
        for i, player in enumerate(self.players):
            print(f"\nPlayer {i + 1}:")
            player.print_hand()

    def print_board(self):
        print("Board:")
        print(", ".join(map(str, self.board)))

    def set_board(self, new_board: List[Card]):
        self.board = new_board

    def get_hand_rank(self, player) -> Tuple[str, List[Card]]:
        hand_rank = ""
        hand_played = []
        all_cards = self.board.copy()
        all_cards.append(player.card1)
        all_cards.append(player.card2)

        # Sort cards by rank
        all_cards.sort(reverse=True)

        # Check for straight flush
        highest_straight_rank = -1
        
        for suit in Suit:
            # Get all cards of the same suit
            suit_cards = [card for card in all_cards if card.suit == suit]
            if len(suit_cards) >= 5:
                for i in range(len(suit_cards)):
                    for j in range(i + 1, len(suit_cards)):
                        for k in range(j + 1, len(suit_cards)):
                            for l in range(k + 1, len(suit_cards)):
                                for m in range(l + 1, len(suit_cards)):
                                    # checks for straight
                                    if (suit_cards[i] == suit_cards[j] + 1 and suit_cards[i] == suit_cards[k] + 2 and suit_cards[i] == suit_cards[l] + 3 and suit_cards[i] == suit_cards[m] + 4):
                                        
                                        # Check if the current straight is higher than the previous highest straight
                                        if suit_cards[i].rank.value > highest_straight_rank:
                                            hand_rank = "Straight Flush"
                                            highest_straight_rank = suit_cards[i].rank.value
                                            hand_played = [suit_cards[i], suit_cards[j], suit_cards[k], suit_cards[l], suit_cards[m]]
                                    
                                    # considers edge case of ace high straight
                                    elif (suit_cards[m] == Rank.ACE and suit_cards[i] == Rank.KING and suit_cards[j] == Rank.QUEEN and 
                                        suit_cards[k] == Rank.JACK and suit_cards[l] == Rank.TEN):
                                        hand_rank = "Straight Flush"
                                        hand_played = [suit_cards[m], suit_cards[i], suit_cards[j], suit_cards[k], suit_cards[l]]
                                        return hand_rank, hand_played
                                    # considers edge case of ace low straight
                                    elif (suit_cards[i] == Rank.ACE and suit_cards[j] == Rank.FIVE and suit_cards[k] == Rank.FOUR and 
                                        suit_cards[l] == Rank.THREE and suit_cards[m] == Rank.TWO):
                                        if Rank.FIVE.value > highest_straight_rank: # type: ignore
                                            highest_straight_rank = Rank.FIVE.value # type: ignore
                                            hand_rank = "Straight Flush"
                                            hand_played = [suit_cards[j], suit_cards[k], suit_cards[l], suit_cards[m], suit_cards[i]]
        if highest_straight_rank != -1:
            return hand_rank, hand_played


        # Check for four of a kind and return heightest kicker
        for i in range(len(all_cards) - 3):
            if all_cards[i] == all_cards[i + 3]:
                hand_rank = "Four of a Kind"
                hand_played = all_cards[i : i + 4]
                if (all_cards[0] != all_cards[i]):
                    hand_played.append(all_cards[0])
                else:
                    hand_played.append(all_cards[4])
                return hand_rank, hand_played
        

        # Check for full house
        for i in range(len(all_cards) - 2):
            for i in range(len(all_cards) - 2):
                if all_cards[i] == all_cards[i + 2]:
                    for j in range(len(all_cards) - 1):
                        if all_cards[j] == all_cards[j + 1] and all_cards[i] != all_cards[j]:
                            hand_rank = "Full House"
                            hand_played = all_cards[i : i + 3]
                            hand_played.append(all_cards[j])
                            hand_played.append(all_cards[j + 1])
                            return hand_rank, hand_played
        

        # Check for flush
        for suit in Suit:
            suit_cards = [card for card in all_cards if card.suit == suit]
            if len(suit_cards) >= 5:
                hand_rank = "Flush"
                hand_played = suit_cards[:5]
                return hand_rank, hand_played
        

        # Check for straight
        highest_straight_rank = -1
        
        for i in range(7):
            for j in range(i + 1, 7):
                for k in range(j + 1, 7):
                    for l in range(k + 1, 7):
                        for m in range(l + 1, 7):
                            # checks for straight
                            if (all_cards[i] == all_cards[j] + 1 and all_cards[i] == all_cards[k] + 2 and all_cards[i] == all_cards[l] + 3 and all_cards[i] == all_cards[m] + 4):
                                
                                # Check if the current straight is higher than the previous highest straight
                                if all_cards[i].rank.value > highest_straight_rank:
                                    hand_rank = "Straight"
                                    highest_straight_rank = all_cards[i].rank.value
                                    hand_played = [all_cards[i], all_cards[j], all_cards[k], all_cards[l], all_cards[m]]
                            
                            # considers edge case of ace high straight
                            elif (all_cards[m] == Rank.ACE and all_cards[i] == Rank.KING and all_cards[j] == Rank.QUEEN and 
                                all_cards[k] == Rank.JACK and all_cards[l] == Rank.TEN):
                                hand_rank = "Straight"
                                hand_played = [all_cards[m], all_cards[i], all_cards[j], all_cards[k], all_cards[l]]
                                return hand_rank, hand_played
                            # considers edge case of ace low straight
                            elif (all_cards[i] == Rank.ACE and all_cards[j] == Rank.FIVE and all_cards[k] == Rank.FOUR and 
                                all_cards[l] == Rank.THREE and all_cards[m] == Rank.TWO):
                                highest_straight_rank = Rank.FIVE.value # type: ignore
                                hand_rank = "Straight"
                                hand_played = [all_cards[j], all_cards[k], all_cards[l], all_cards[m], all_cards[i]]

        if highest_straight_rank != -1:
            return hand_rank, hand_played
        
            
        # Check for heightest three of a kind and return heightest kicker
        for i in range(len(all_cards) - 2):
            if all_cards[i] == all_cards[i + 2]:
                hand_rank = "Three of a Kind"
                hand_played = all_cards[i : i + 3]
                if (all_cards[0] != all_cards[i] and all_cards[1] != all_cards[i]):
                    hand_played.append(all_cards[0])
                    hand_played.append(all_cards[1])
                elif (all_cards[0] != all_cards[i] and all_cards[4] != all_cards[i]):
                    hand_played.append(all_cards[0])
                    hand_played.append(all_cards[4])
                else:
                    hand_played.append(all_cards[3])
                    hand_played.append(all_cards[4])

                return hand_rank, hand_played
        
        # Check for two pair and return heightest kicker
        for i in range(len(all_cards) - 1):
            if all_cards[i] == all_cards[i + 1]:
                for j in range(i + 2, len(all_cards) - 1):
                    if all_cards[j] == all_cards[j + 1]:
                        hand_rank = "Two Pair"
                        hand_played = all_cards[i : i + 2]
                        hand_played.append(all_cards[j])
                        hand_played.append(all_cards[j + 1])
                        if (all_cards[0] != all_cards[i] and all_cards[0] != all_cards[j]):
                            hand_played.append(all_cards[0])
                        elif (all_cards[2] != all_cards[i] and all_cards[2] != all_cards[j]):
                            hand_played.append(all_cards[2])
                        else:
                            hand_played.append(all_cards[4])
                        return hand_rank, hand_played
              
        # Check for pair and return heightest kicker
        for i in range(len(all_cards) - 1):
            if all_cards[i] == all_cards[i + 1]:
                hand_rank = "Pair"
                hand_played = all_cards[i : i + 2]
                if (all_cards[0] != all_cards[i] and all_cards[1] != all_cards[i] and all_cards[2] != all_cards[i]):
                    hand_played.append(all_cards[0])
                    hand_played.append(all_cards[1])
                    hand_played.append(all_cards[2])
                elif (all_cards[2] != all_cards[i] and all_cards[3] != all_cards[i] and all_cards[4] != all_cards[i]):
                    hand_played.append(all_cards[2])
                    hand_played.append(all_cards[3])
                    hand_played.append(all_cards[4])
                elif (all_cards[0] != all_cards[i] and all_cards[3] != all_cards[i] and all_cards[4] != all_cards[i]):
                    hand_played.append(all_cards[0])
                    hand_played.append(all_cards[3])
                    hand_played.append(all_cards[4])
                else:
                    hand_played.append(all_cards[0])
                    hand_played.append(all_cards[1])
                    hand_played.append(all_cards[4])
                return hand_rank, hand_played
        
        # Return highest card
        hand_rank = "High Card"
        hand_played = all_cards[0:5]
        return hand_rank, hand_played

    # evaluate the hands of all players
    def evaluate_hands(self) -> None:
        for i, player in enumerate(self.players):
            hand = self.get_hand_rank(player)
            print(f"\nPlayer {i + 1} has {hand[0]}")
            print("Hand: ", end="")
            player.print_hand()

            for j, card in enumerate(hand[1]):
                print(card, end=", ")
    
    # return the winner of the hand
    def get_winner(self):




        
def main():
    game = PokerGame(2)
    game.
    game.evaluate_hands()

if __name__ == "__main__":
    main()
