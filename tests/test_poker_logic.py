import pytest
from game.poker import Dealer, PokerGameManager
from game.card import Card, Rank, Suit

def test_deal_board():
    dealer = Dealer(2)
    
    # Deal 3 cards (flop)
    dealer.deal_board(3)
    assert len(dealer.board) == 3
    
    # Deal 1 more card (turn)
    dealer.deal_board(4)
    assert len(dealer.board) == 4
    
    # Deal 1 more card (river)
    dealer.deal_board(5)
    assert len(dealer.board) == 5
    
    # Check that the board cards are unique
    assert len(set(str(card) for card in dealer.board)) == 5

def test_return_community_cards():
    dealer = Dealer(2)
    
    # Set specific board cards
    dealer.board = [
        Card(Rank.ACE, Suit.SPADES),
        Card(Rank.KING, Suit.HEARTS),
        Card(Rank.QUEEN, Suit.DIAMONDS)
    ]
    
    # Get community cards as string
    community_str = dealer.return_community_cards()
    
    # Check that the string contains all cards
    assert "AS" in community_str
    assert "KH" in community_str
    assert "QD" in community_str

def test_return_player_hand_str():
    dealer = Dealer(1)
    
    # Set specific player cards
    dealer.players[0].card1 = Card(Rank.ACE, Suit.SPADES)
    dealer.players[0].card2 = Card(Rank.KING, Suit.HEARTS)
    
    # Get player hand as string
    hand_str = dealer.return_player_hand_str(0)
    
    # Check that the string contains both cards
    assert "AS" in hand_str
    assert "KH" in hand_str

def test_all_in_call():
    game = PokerGameManager(buy_in=100)
    
    # Setup scenario where player 0 has less chips than current bet
    game.current_bet = 75
    game.players[0].stack = 40
    game.players[0].round_pot_commitment = 10
    game.players[1].round_pot_commitment = 75
    game.current_pot = 85  # 10 + 75
    
    # Player goes all-in as a call
    game.player_all_in_call(0)
    
    # Player should commit all their chips
    assert game.players[0].stack == 0
    assert game.players[0].round_pot_commitment == 50  # 10 + 40
    
    # The bet should be adjusted to what the all-in player can afford
    assert game.current_bet == 50
    
    # Other player should get refunded the difference
    assert game.players[1].round_pot_commitment == 50
    assert game.players[1].stack == 125
    
    # Pot should reflect the changes
    assert game.current_pot == 100  # 50 + 50

def test_all_in_raise():
    game = PokerGameManager(buy_in=100)
    
    # Setup scenario
    game.current_bet = 20
    game.players[0].stack = 50
    game.players[0].round_pot_commitment = 10
    
    # Player goes all-in as a raise
    game.player_all_in_raise(0)
    
    # Check that player committed all chips
    assert game.players[0].stack == 0
    assert game.players[0].round_pot_commitment == 60  # 10 + 50
    
    # Current bet should be raised to the all-in amount
    assert game.current_bet == 60

@pytest.mark.parametrize("opp_stack,expected_max", [
    (1000, 1000),    # equal stacks
    (400,  400),     # opponent shorter
])
def test_return_min_max_raise(opp_stack, expected_max):
    game = PokerGameManager()
    game.current_bet = 50
    game.players[1].stack = opp_stack
    min_raise, max_raise = game.return_min_max_raise(0)
    assert min_raise == 100                       # 50 * 2
    assert max_raise == expected_max + game.players[1].round_pot_commitment

def test_player_all_in_call_refund():
    game = PokerGameManager()
    game.current_bet = 200
    # player 1 has bet 200 already
    game.players[1].round_pot_commitment = 200
    # player 0 is short – only 120 total left (20 already in pot)
    game.players[0].round_pot_commitment = 20
    game.players[0].stack = 100
    starting_stack_p1 = game.players[1].stack

    game.player_all_in_call(0)

    # bet should drop to 120, diff refunded to player 1
    assert game.current_bet == 120
    assert game.players[0].stack == 0
    assert game.players[0].round_pot_commitment == 120
    assert game.players[1].round_pot_commitment == 120
    assert game.players[1].stack == starting_stack_p1 + 80   # refund

def test_player_win_split_list():
    game = PokerGameManager()
    game.current_pot = 100
    p0, p1 = game.players
    stack0, stack1 = p0.stack, p1.stack

    game.player_win([p0, p1])      # split
    assert p0.stack == stack0 + 50
    assert p1.stack == stack1 + 50