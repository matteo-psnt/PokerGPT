import pytest
from game.poker import PokerGameManager
from game.player import Player, handRank
from game.card import Card, Rank, Suit
from db.enums import Round

class TestPokerGameManager:
    def test_initialization(self):
        game = PokerGameManager(buy_in=1500, small_blind=10, big_blind=20)
        
        assert game.starting_stack == 1500
        assert game.small_blind == 10
        assert game.big_blind == 20
        assert game.button == 0
        assert game.current_action == 0
        assert game.round == Round.PRE_FLOP
        assert game.current_pot == 0
        assert game.current_bet == 0
        assert len(game.players) == 2
        assert all(player.stack == 1500 for player in game.players)
        
    def test_new_round(self):
        game = PokerGameManager()
        
        # Simulate some betting activity
        game.current_pot = 100
        game.current_bet = 50
        game.button = 0
        game.round = Round.RIVER
        
        # Player bets to change stack and round_pot_commitment
        game.players[0].bet(30)
        game.players[1].bet(20)
        
        # Start new round
        game.new_round()
        
        # Check reset state
        assert game.current_pot == 0
        assert game.current_bet == 0
        assert game.button == 1  # Button should move to next player
        assert game.current_action == 1
        assert game.round == Round.PRE_FLOP
        
        # Players' hands should be reset
        assert all(player.card1 is not None for player in game.players)
        assert all(player.card2 is not None for player in game.players)
        
        assert game.players[0].stack == 970
        assert game.players[1].stack == 980
        
    def test_reset_betting(self):
        game = PokerGameManager()
        
        # Set up betting state
        game.current_bet = 50
        game.players[0].round_pot_commitment = 50
        game.players[1].round_pot_commitment = 25
        
        # Reset betting
        game.reset_betting()
        
        # Bet should be reset
        assert game.current_bet == 0
        
        # Players' round_pot_commitment should be reset
        assert game.players[0].round_pot_commitment == 0
        assert game.players[1].round_pot_commitment == 0
    
    def test_player_call(self):
        game = PokerGameManager()
        
        # Set up initial state
        game.current_bet = 50
        game.players[0].round_pot_commitment = 20
        game.players[0].stack = 100
        
        # Player calls
        game.player_call(0)
        
        # Check that correct amount was called
        assert game.players[0].round_pot_commitment == 50
        assert game.players[0].stack == 70  # 100 - (50 - 20)
        assert game.current_pot == 30  # The call amount
    
    def test_player_raise(self):
        game = PokerGameManager()
        
        # Set up initial state
        game.current_bet = 20
        game.players[0].round_pot_commitment = 20
        game.players[0].stack = 100
        
        # Player raises to 60
        game.player_raise(0, 60)
        
        # Check that bet was raised correctly
        assert game.current_bet == 60
        assert game.players[0].round_pot_commitment == 60
        assert game.players[0].stack == 60  # 100 - (60 - 20)
        assert game.current_pot == 40  # The raise amount
    
    def test_player_win(self):
        game = PokerGameManager()
        
        # Set up pot and player stacks
        game.current_pot = 100
        game.players[0].stack = 900
        game.players[1].stack = 1000
        
        # Player 0 wins
        game.player_win(0)
        
        # Check that pot was awarded correctly
        assert game.players[0].stack == 1000  # 900 + 100
        assert game.players[1].stack == 1000  # Unchanged
    
    def test_determine_winner(self):
        game = PokerGameManager()
        
        # Set up player hands
        game.players[0].hand_rank = handRank.FLUSH
        game.players[1].hand_rank = handRank.STRAIGHT
        
        # Set hand_played for tiebreaking
        game.players[0].hand_played = [
            Card(Rank.ACE, Suit.HEARTS),
            Card(Rank.KING, Suit.HEARTS),
            Card(Rank.QUEEN, Suit.HEARTS),
            Card(Rank.JACK, Suit.HEARTS),
            Card(Rank.NINE, Suit.HEARTS)
        ]
        
        game.players[1].hand_played = [
            Card(Rank.KING, Suit.CLUBS),
            Card(Rank.QUEEN, Suit.DIAMONDS),
            Card(Rank.JACK, Suit.HEARTS),
            Card(Rank.TEN, Suit.SPADES),
            Card(Rank.NINE, Suit.CLUBS)
        ]
        
        # Determine winner
        winner = game.determine_winner()
        
        # Player 0 should win with a flush
        assert winner == game.players[0]
        
        # Test tie
        game.players[1].hand_rank = handRank.FLUSH
        game.players[1].hand_played = game.players[0].hand_played.copy()
        
        # Determine winner again
        winners = game.determine_winner()
        
        # Both players should tie
        assert isinstance(winners, list)
        assert len(winners) == 2
        assert game.players[0] in winners
        assert game.players[1] in winners