from game.poker import Dealer
from game.player import handRank
from game.card import Card, Rank, Suit

def test_royal_flush():
    dealer = Dealer(1)
    player = dealer.players[0]
    
    # Set up royal flush in spades
    player.card1 = Card(Rank.ACE, Suit.SPADES)
    player.card2 = Card(Rank.KING, Suit.SPADES)
    dealer.board = [
        Card(Rank.QUEEN, Suit.SPADES),
        Card(Rank.JACK, Suit.SPADES),
        Card(Rank.TEN, Suit.SPADES),
        Card(Rank.TWO, Suit.HEARTS),  # Irrelevant cards
        Card(Rank.THREE, Suit.HEARTS)
    ]
    
    rank, hand = dealer.get_hand_rank(player)
    
    assert rank == handRank.ROYAL_FLUSH
    assert len(hand) == 5
    assert hand[0].rank == Rank.ACE
    assert all(card.suit == Suit.SPADES for card in hand)

def test_straight_flush():
    dealer = Dealer(1)
    player = dealer.players[0]
    
    # Set up 9-high straight flush in hearts
    player.card1 = Card(Rank.NINE, Suit.HEARTS)
    player.card2 = Card(Rank.EIGHT, Suit.HEARTS)
    dealer.board = [
        Card(Rank.SEVEN, Suit.HEARTS),
        Card(Rank.SIX, Suit.HEARTS),
        Card(Rank.FIVE, Suit.HEARTS),
        Card(Rank.TWO, Suit.DIAMONDS),  # Irrelevant cards
        Card(Rank.THREE, Suit.CLUBS)
    ]
    
    rank, hand = dealer.get_hand_rank(player)
    
    assert rank == handRank.STRAIGHT_FLUSH
    assert len(hand) == 5
    assert hand[0].rank == Rank.NINE
    assert all(card.suit == Suit.HEARTS for card in hand)

def test_four_of_a_kind():
    dealer = Dealer(1)
    player = dealer.players[0]
    
    # Set up four kings with ace kicker
    player.card1 = Card(Rank.KING, Suit.HEARTS)
    player.card2 = Card(Rank.KING, Suit.SPADES)
    dealer.board = [
        Card(Rank.KING, Suit.DIAMONDS),
        Card(Rank.KING, Suit.CLUBS),
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.TWO, Suit.DIAMONDS),
        Card(Rank.THREE, Suit.CLUBS)
    ]
    
    rank, hand = dealer.get_hand_rank(player)
    
    assert rank == handRank.FOUR_OF_A_KIND
    assert len(hand) == 5
    assert sum(1 for card in hand if card.rank == Rank.KING) == 4
    assert any(card.rank == Rank.ACE for card in hand)

def test_full_house():
    dealer = Dealer(1)
    player = dealer.players[0]
    
    # Set up full house: aces full of kings
    player.card1 = Card(Rank.ACE, Suit.HEARTS)
    player.card2 = Card(Rank.ACE, Suit.SPADES)
    dealer.board = [
        Card(Rank.ACE, Suit.DIAMONDS),
        Card(Rank.KING, Suit.CLUBS),
        Card(Rank.KING, Suit.HEARTS),
        Card(Rank.TWO, Suit.DIAMONDS),
        Card(Rank.THREE, Suit.CLUBS)
    ]
    
    rank, hand = dealer.get_hand_rank(player)
    
    assert rank == handRank.FULL_HOUSE
    assert len(hand) == 5
    assert sum(1 for card in hand if card.rank == Rank.ACE) == 3
    assert sum(1 for card in hand if card.rank == Rank.KING) == 2

def test_flush():
    dealer = Dealer(1)
    player = dealer.players[0]
    
    # Set up flush in diamonds
    player.card1 = Card(Rank.ACE, Suit.DIAMONDS)
    player.card2 = Card(Rank.KING, Suit.DIAMONDS)
    dealer.board = [
        Card(Rank.QUEEN, Suit.DIAMONDS),
        Card(Rank.NINE, Suit.DIAMONDS),
        Card(Rank.FIVE, Suit.DIAMONDS),
        Card(Rank.TWO, Suit.HEARTS),
        Card(Rank.THREE, Suit.CLUBS)
    ]
    
    rank, hand = dealer.get_hand_rank(player)
    
    assert rank == handRank.FLUSH
    assert len(hand) == 5
    assert all(card.suit == Suit.DIAMONDS for card in hand)

def test_straight():
    dealer = Dealer(1)
    player = dealer.players[0]
    
    # Set up 8-high straight with mixed suits
    player.card1 = Card(Rank.EIGHT, Suit.HEARTS)
    player.card2 = Card(Rank.SEVEN, Suit.SPADES)
    dealer.board = [
        Card(Rank.SIX, Suit.DIAMONDS),
        Card(Rank.FIVE, Suit.CLUBS),
        Card(Rank.FOUR, Suit.HEARTS),
        Card(Rank.TWO, Suit.HEARTS),
        Card(Rank.THREE, Suit.CLUBS)
    ]
    
    rank, hand = dealer.get_hand_rank(player)
    
    assert rank == handRank.STRAIGHT
    assert len(hand) == 5
    assert hand[0].rank == Rank.EIGHT

def test_three_of_a_kind():
    dealer = Dealer(1)
    player = dealer.players[0]
    
    # Set up three queens with ace-king kickers
    player.card1 = Card(Rank.QUEEN, Suit.HEARTS)
    player.card2 = Card(Rank.QUEEN, Suit.SPADES)
    dealer.board = [
        Card(Rank.QUEEN, Suit.DIAMONDS),
        Card(Rank.ACE, Suit.CLUBS),
        Card(Rank.KING, Suit.HEARTS),
        Card(Rank.TWO, Suit.DIAMONDS),
        Card(Rank.THREE, Suit.CLUBS)
    ]
    
    rank, hand = dealer.get_hand_rank(player)
    
    assert rank == handRank.THREE_OF_A_KIND
    assert len(hand) == 5
    assert sum(1 for card in hand if card.rank == Rank.QUEEN) == 3
    assert any(card.rank == Rank.ACE for card in hand)
    assert any(card.rank == Rank.KING for card in hand)

def test_two_pair():
    dealer = Dealer(1)
    player = dealer.players[0]
    
    # Set up two pair: aces and kings with queen kicker
    player.card1 = Card(Rank.ACE, Suit.HEARTS)
    player.card2 = Card(Rank.ACE, Suit.SPADES)
    dealer.board = [
        Card(Rank.KING, Suit.DIAMONDS),
        Card(Rank.KING, Suit.CLUBS),
        Card(Rank.QUEEN, Suit.HEARTS),
        Card(Rank.TWO, Suit.DIAMONDS),
        Card(Rank.THREE, Suit.CLUBS)
    ]
    
    rank, hand = dealer.get_hand_rank(player)
    
    assert rank == handRank.TWO_PAIR
    assert len(hand) == 5
    assert sum(1 for card in hand if card.rank == Rank.ACE) == 2
    assert sum(1 for card in hand if card.rank == Rank.KING) == 2
    assert any(card.rank == Rank.QUEEN for card in hand)

def test_pair():
    dealer = Dealer(1)
    player = dealer.players[0]
    
    # Set up pair of jacks with ace-king-queen kickers
    player.card1 = Card(Rank.JACK, Suit.HEARTS)
    player.card2 = Card(Rank.JACK, Suit.SPADES)
    dealer.board = [
        Card(Rank.ACE, Suit.DIAMONDS),
        Card(Rank.KING, Suit.CLUBS),
        Card(Rank.QUEEN, Suit.HEARTS),
        Card(Rank.TWO, Suit.DIAMONDS),
        Card(Rank.THREE, Suit.CLUBS)
    ]
    
    rank, hand = dealer.get_hand_rank(player)
    
    assert rank == handRank.PAIR
    assert len(hand) == 5
    assert sum(1 for card in hand if card.rank == Rank.JACK) == 2
    assert any(card.rank == Rank.ACE for card in hand)
    assert any(card.rank == Rank.KING for card in hand)
    assert any(card.rank == Rank.QUEEN for card in hand)

def test_high_card():
    dealer = Dealer(1)
    player = dealer.players[0]
    
    # Set up ace-high with king, queen, jack, nine
    player.card1 = Card(Rank.ACE, Suit.HEARTS)
    player.card2 = Card(Rank.KING, Suit.SPADES)
    dealer.board = [
        Card(Rank.QUEEN, Suit.DIAMONDS),
        Card(Rank.JACK, Suit.CLUBS),
        Card(Rank.NINE, Suit.HEARTS),
        Card(Rank.TWO, Suit.DIAMONDS),
        Card(Rank.THREE, Suit.CLUBS)
    ]
    
    rank, hand = dealer.get_hand_rank(player)
    
    assert rank == handRank.HIGH_CARD
    assert len(hand) == 5
    assert hand[0].rank == Rank.ACE
    assert hand[1].rank == Rank.KING
    assert hand[2].rank == Rank.QUEEN
    assert hand[3].rank == Rank.JACK
    assert hand[4].rank == Rank.NINE