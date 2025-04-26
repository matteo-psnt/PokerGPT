import pytest
import json
from unittest.mock import MagicMock, patch
from bot.gpt_player import GPTPlayer
from game.poker import PokerGameManager
from game.card import Card, Rank, Suit
from db.enums import ActionType, Round

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.record_gpt_action = MagicMock()
    return db

@pytest.fixture
def mock_chain():
    with patch('bot.gpt_player.ChatPromptTemplate'), \
         patch('bot.gpt_player.ChatOpenAI'), \
         patch('bot.gpt_player.StrOutputParser'):
        gpt_player = GPTPlayer(MagicMock())
        gpt_player.chain = MagicMock()
        return gpt_player

@pytest.fixture
def poker_game():
    game = PokerGameManager(buy_in=1000, small_blind=5, big_blind=10)
    # Set specific cards for testing
    game.players[1].card1 = Card(Rank.ACE, Suit.SPADES)
    game.players[1].card2 = Card(Rank.KING, Suit.HEARTS)
    return game

def test_extract_action_raise(mock_db, poker_game):
    gpt_player = GPTPlayer(mock_db)
    
    # Test normal raise
    json_string = json.dumps({
        "your_hand": "Ace of Spades, King of Hearts",
        "opponents_hand": "Possibly a medium pair",
        "thought_process": "I have a strong starting hand, I should raise",
        "action": "raise",
        "raise_amount": 30
    })
    
    action, amount = gpt_player._extract_action(json_string, poker_game)
    
    assert action == ActionType.RAISE
    assert amount == 30
    mock_db.record_gpt_action.assert_called_once_with(action, 30, json_string)

def test_extract_action_min_raise(mock_db, poker_game):
    gpt_player = GPTPlayer(mock_db)
    mock_db.reset_mock()
    
    # Set current bet to make min raise higher
    poker_game.current_bet = 40
    
    # Test raise below minimum (should be adjusted)
    json_string = json.dumps({
        "your_hand": "Ace of Spades, King of Hearts",
        "opponents_hand": "Possibly a medium pair",
        "thought_process": "I have a strong starting hand, I should raise",
        "action": "raise",
        "raise_amount": 50  # Min raise would be 80 (40 * 2)
    })
    
    action, amount = gpt_player._extract_action(json_string, poker_game)
    
    assert action == ActionType.RAISE
    assert amount == 80  # Should be adjusted to min raise
    mock_db.record_gpt_action.assert_called_once_with(action, 80, json_string)

def test_extract_action_all_in(mock_db, poker_game):
    gpt_player = GPTPlayer(mock_db)
    mock_db.reset_mock()
    
    # Test raise above maximum (should become all-in)
    json_string = json.dumps({
        "your_hand": "Ace of Spades, King of Hearts",
        "opponents_hand": "Possibly a medium pair",
        "thought_process": "I have a strong starting hand, I should raise big",
        "action": "raise",
        "raise_amount": 2000  # More than player's stack
    })
    
    action, amount = gpt_player._extract_action(json_string, poker_game)
    
    assert action == ActionType.ALL_IN
    assert amount == 1000  # Player's stack
    mock_db.record_gpt_action.assert_called_once_with(action, 1000, json_string)

def test_extract_action_no_raise(mock_db, poker_game):
    gpt_player = GPTPlayer(mock_db)
    mock_db.reset_mock()
    
    # Test action without raise amount
    json_string = json.dumps({
        "your_hand": "Ace of Spades, King of Hearts",
        "opponents_hand": "Possibly a strong hand",
        "thought_process": "I shouldn't risk too much here",
        "action": "call"
    })
    
    action, amount = gpt_player._extract_action(json_string, poker_game)
    
    assert action == ActionType.CALL
    assert amount is None
    mock_db.record_gpt_action.assert_called_once_with(action, None, json_string)

def test_extract_action_invalid_json(mock_db, poker_game):
    gpt_player = GPTPlayer(mock_db)
    mock_db.reset_mock()
    
    # Test invalid JSON
    json_string = "This is not valid JSON"
    
    action, amount = gpt_player._extract_action(json_string, poker_game)
    
    assert action == "Default"
    assert amount == 0
    mock_db.record_gpt_action.assert_not_called()

def test_pre_flop_small_blind(mock_chain, poker_game):
    mock_chain.chain.invoke.return_value = json.dumps({
        "your_hand": "Ace of Spades, King of Hearts",
        "opponents_hand": "Unknown",
        "thought_process": "Strong starting hand, should raise",
        "action": "raise",
        "raise_amount": 30
    })
    
    action, amount = mock_chain.pre_flop_small_blind(poker_game)
    
    assert action == ActionType.RAISE
    assert amount == 30
    mock_chain.chain.invoke.assert_called_once()

def test_pre_flop_big_blind(mock_chain, poker_game):
    mock_chain.chain.invoke.return_value = json.dumps({
        "your_hand": "Ace of Spades, King of Hearts",
        "opponents_hand": "Unknown",
        "thought_process": "Strong starting hand, should raise",
        "action": "raise",
        "raise_amount": 40
    })
    
    action, amount = mock_chain.pre_flop_big_blind(poker_game)
    
    assert action == ActionType.RAISE
    assert amount == 40
    mock_chain.chain.invoke.assert_called_once()

def test_first_to_act(mock_chain, poker_game):
    # Set up board
    poker_game.board = [
        Card(Rank.TEN, Suit.SPADES),
        Card(Rank.JACK, Suit.HEARTS),
        Card(Rank.QUEEN, Suit.DIAMONDS)
    ]
    poker_game.round = Round.FLOP
    
    mock_chain.chain.invoke.return_value = json.dumps({
        "your_hand": "Ace of Spades, King of Hearts",
        "opponents_hand": "Unknown",
        "thought_process": "I have a straight draw, should bet",
        "action": "raise",
        "raise_amount": 50
    })
    
    action, amount = mock_chain.first_to_act(poker_game)
    
    assert action == ActionType.RAISE
    assert amount == 50
    mock_chain.chain.invoke.assert_called_once()

def test_player_check(mock_chain, poker_game):
    # Set up board
    poker_game.board = [
        Card(Rank.TEN, Suit.SPADES),
        Card(Rank.JACK, Suit.HEARTS),
        Card(Rank.QUEEN, Suit.DIAMONDS)
    ]
    poker_game.round = Round.FLOP
    
    mock_chain.chain.invoke.return_value = json.dumps({
        "your_hand": "Ace of Spades, King of Hearts",
        "opponents_hand": "Unknown",
        "thought_process": "I have a strong draw, should check",
        "action": "check"
    })
    
    action, amount = mock_chain.player_check(poker_game)
    
    assert action == ActionType.CHECK
    assert amount is None
    mock_chain.chain.invoke.assert_called_once()

def test_player_raise(mock_chain, poker_game):
    # Set up board and raise
    poker_game.board = [
        Card(Rank.TEN, Suit.SPADES),
        Card(Rank.JACK, Suit.HEARTS),
        Card(Rank.QUEEN, Suit.DIAMONDS)
    ]
    poker_game.round = Round.FLOP
    poker_game.current_bet = 30
    
    mock_chain.chain.invoke.return_value = json.dumps({
        "your_hand": "Ace of Spades, King of Hearts",
        "opponents_hand": "Possibly a pair",
        "thought_process": "I have a straight, should call",
        "action": "call"
    })
    
    action, amount = mock_chain.player_raise(poker_game)
    
    assert action == ActionType.CALL
    assert amount is None
    mock_chain.chain.invoke.assert_called_once()

def test_player_all_in(mock_chain, poker_game):
    # Set up board and all-in
    poker_game.board = [
        Card(Rank.TEN, Suit.SPADES),
        Card(Rank.JACK, Suit.HEARTS),
        Card(Rank.QUEEN, Suit.DIAMONDS),
        Card(Rank.KING, Suit.CLUBS)
    ]
    poker_game.round = Round.TURN
    poker_game.current_bet = 1000
    
    mock_chain.chain.invoke.return_value = json.dumps({
        "your_hand": "Ace of Spades, King of Hearts",
        "opponents_hand": "Possibly a flush draw",
        "thought_process": "I have the nuts, should call",
        "action": "call"
    })
    
    action, amount = mock_chain.player_all_in(poker_game)
    
    assert action == ActionType.CALL
    assert amount is None
    mock_chain.chain.invoke.assert_called_once()