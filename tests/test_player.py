from game.player import Player, HandRank
from game.deck import Deck
from game.card import Card, Rank, Suit

def test_player_creation():
    player = Player("Test Player", 1000)
    assert player.name == "Test Player"
    assert player.stack == 1000
    assert player.round_pot_commitment == 0
    assert player.card1 is None
    assert player.card2 is None
    assert player.hand_rank == HandRank.HIGH_CARD
    assert player.hand_played == []

def test_deal_hand():
    player = Player("Test Player", 1000)
    deck = Deck()
    
    player.deal_hand(deck)
    
    assert player.card1 is not None
    assert player.card2 is not None
    assert isinstance(player.card1, Card)
    assert isinstance(player.card2, Card)
    assert player.card1 != player.card2
    assert len(deck.cards) == 50  # 52 - 2 cards dealt

def test_hand():
    player = Player("Test Player", 1000)
    player.card1 = Card(Rank.ACE, Suit.SPADES)
    player.card2 = Card(Rank.KING, Suit.HEARTS)
    
    hand = player.hand
    
    assert len(hand) == 2
    assert hand[0] == player.card1
    assert hand[1] == player.card2

def test_hand_long_str():
    player = Player("Test Player", 1000)
    player.card1 = Card(Rank.ACE, Suit.SPADES)
    player.card2 = Card(Rank.KING, Suit.HEARTS)
    
    long_hand = player.hand_long_str()
    
    assert long_hand == "Ace of Spades, King of Hearts"
    
    # Test with no cards
    player2 = Player("No Cards", 1000)
    assert player2.hand_long_str() is None

def test_bet():
    player = Player("Test Player", 1000)
    
    player.bet(100)
    
    assert player.stack == 900
    assert player.round_pot_commitment == 100
    
    player.bet(200)
    
    assert player.stack == 700
    assert player.round_pot_commitment == 300

def test_reset():
    player = Player("Test Player", 1000)
    player.card1 = Card(Rank.ACE, Suit.SPADES)
    player.card2 = Card(Rank.KING, Suit.HEARTS)
    player.round_pot_commitment = 100
    player.hand_rank = HandRank.PAIR
    player.hand_played = [player.card1, player.card2]
    
    player.reset()
    
    assert player.card1 is None
    assert player.card2 is None
    assert player.round_pot_commitment == 0
    assert player.hand_rank == HandRank.HIGH_CARD
    assert player.hand_played == []
    # Stack should remain unchanged
    assert player.stack == 1000