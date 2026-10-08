import pytest
import typing
from pydantic import ValidationError
from unittest.mock import AsyncMock, MagicMock, patch
from bot.gpt_player import GPTPlayer, FacingBetDecision, CanCheckDecision, FacingAllInDecision
from db.enums import ActionType, Round
from game.card import Card, Rank, Suit
from game.poker import PokerGameManager

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.record_gpt_action = MagicMock()
    return db

@pytest.fixture
def mocked_player():
    with patch('bot.gpt_player.ChatPromptTemplate'), \
         patch('bot.gpt_player.ChatOpenAI'):
        gpt_player = GPTPlayer(MagicMock())
        gpt_player.chains = {schema: MagicMock(ainvoke=AsyncMock()) for schema in gpt_player.chains}
        return gpt_player

@pytest.fixture
def poker_game():
    game = PokerGameManager(buy_in=1000, small_blind=5, big_blind=10)
    # Set specific cards for testing
    game.players[1].card1 = Card(Rank.ACE, Suit.SPADES)
    game.players[1].card2 = Card(Rank.KING, Suit.HEARTS)
    return game

def decision(schema, action, **fields):
    return schema(
        your_hand="Ace of Spades, King of Hearts",
        opponents_hand="Unknown",
        thought_process="Test reasoning",
        action=action,
        **fields
    )

def test_resolve_action_raise(mock_db, poker_game):
    gpt_player = GPTPlayer(mock_db)

    # Test normal raise
    d = decision(FacingBetDecision, "raise", raise_amount=30)

    action, amount = gpt_player._resolve_action(d, poker_game)

    assert action == ActionType.RAISE
    assert amount == 30
    mock_db.record_gpt_action.assert_called_once_with(action, 30, d.model_dump_json())

def test_resolve_action_min_raise(mock_db, poker_game):
    gpt_player = GPTPlayer(mock_db)

    # Set current bet to make min raise higher
    poker_game.current_bet = 40

    # Test raise below minimum (should be adjusted)
    d = decision(FacingBetDecision, "raise", raise_amount=50)  # Min raise would be 80 (40 * 2)

    action, amount = gpt_player._resolve_action(d, poker_game)

    assert action == ActionType.RAISE
    assert amount == 80  # Should be adjusted to min raise
    mock_db.record_gpt_action.assert_called_once_with(action, 80, d.model_dump_json())

def test_resolve_action_raise_without_amount_uses_min_raise(mock_db, poker_game):
    gpt_player = GPTPlayer(mock_db)
    poker_game.current_bet = 40

    action, amount = gpt_player._resolve_action(decision(FacingBetDecision, "raise", raise_amount=None), poker_game)

    assert action == ActionType.RAISE
    assert amount == 80

def test_resolve_action_all_in(mock_db, poker_game):
    gpt_player = GPTPlayer(mock_db)

    # Test raise above maximum (should become all-in)
    d = decision(FacingBetDecision, "raise", raise_amount=2000)  # More than player's stack

    action, amount = gpt_player._resolve_action(d, poker_game)

    assert action == ActionType.ALL_IN
    assert amount == 1000  # Player's stack
    mock_db.record_gpt_action.assert_called_once_with(action, 1000, d.model_dump_json())

def test_resolve_action_no_raise(mock_db, poker_game):
    gpt_player = GPTPlayer(mock_db)

    # Test action without raise amount
    d = decision(FacingBetDecision, "call", raise_amount=None)

    action, amount = gpt_player._resolve_action(d, poker_game)

    assert action == ActionType.CALL
    assert amount is None
    mock_db.record_gpt_action.assert_called_once_with(action, None, d.model_dump_json())

def test_schema_actions_are_valid_action_types():
    for schema in (FacingBetDecision, CanCheckDecision, FacingAllInDecision):
        for action in typing.get_args(schema.model_fields["action"].annotation):
            ActionType(action)

def test_schemas_only_allow_legal_moves():
    with pytest.raises(ValidationError):
        decision(FacingAllInDecision, "raise")
    with pytest.raises(ValidationError):
        decision(CanCheckDecision, "fold", raise_amount=None)
    with pytest.raises(ValidationError):
        decision(FacingBetDecision, "check", raise_amount=None)

@pytest.mark.asyncio
async def test_pre_flop_small_blind(mocked_player, poker_game):
    chain = mocked_player.chains[FacingBetDecision]
    chain.ainvoke.return_value = decision(FacingBetDecision, "raise", raise_amount=30)

    action, amount = await mocked_player.pre_flop_small_blind(poker_game)

    assert action == ActionType.RAISE
    assert amount == 30
    chain.ainvoke.assert_awaited_once()

@pytest.mark.asyncio
async def test_pre_flop_big_blind(mocked_player, poker_game):
    chain = mocked_player.chains[CanCheckDecision]
    chain.ainvoke.return_value = decision(CanCheckDecision, "raise", raise_amount=40)

    action, amount = await mocked_player.pre_flop_big_blind(poker_game)

    assert action == ActionType.RAISE
    assert amount == 40
    chain.ainvoke.assert_awaited_once()

@pytest.mark.asyncio
async def test_first_to_act(mocked_player, poker_game):
    # Set up board
    poker_game.board = [
        Card(Rank.TEN, Suit.SPADES),
        Card(Rank.JACK, Suit.HEARTS),
        Card(Rank.QUEEN, Suit.DIAMONDS)
    ]
    poker_game.round = Round.FLOP

    chain = mocked_player.chains[CanCheckDecision]
    chain.ainvoke.return_value = decision(CanCheckDecision, "raise", raise_amount=50)

    action, amount = await mocked_player.first_to_act(poker_game)

    assert action == ActionType.RAISE
    assert amount == 50
    chain.ainvoke.assert_awaited_once()

@pytest.mark.asyncio
async def test_player_check(mocked_player, poker_game):
    # Set up board
    poker_game.board = [
        Card(Rank.TEN, Suit.SPADES),
        Card(Rank.JACK, Suit.HEARTS),
        Card(Rank.QUEEN, Suit.DIAMONDS)
    ]
    poker_game.round = Round.FLOP

    chain = mocked_player.chains[CanCheckDecision]
    chain.ainvoke.return_value = decision(CanCheckDecision, "check", raise_amount=None)

    action, amount = await mocked_player.player_check(poker_game)

    assert action == ActionType.CHECK
    assert amount is None
    chain.ainvoke.assert_awaited_once()

@pytest.mark.asyncio
async def test_player_raise(mocked_player, poker_game):
    # Set up board and raise
    poker_game.board = [
        Card(Rank.TEN, Suit.SPADES),
        Card(Rank.JACK, Suit.HEARTS),
        Card(Rank.QUEEN, Suit.DIAMONDS)
    ]
    poker_game.round = Round.FLOP
    poker_game.current_bet = 30

    chain = mocked_player.chains[FacingBetDecision]
    chain.ainvoke.return_value = decision(FacingBetDecision, "call", raise_amount=None)

    action, amount = await mocked_player.player_raise(poker_game)

    assert action == ActionType.CALL
    assert amount is None
    chain.ainvoke.assert_awaited_once()

@pytest.mark.asyncio
async def test_player_all_in(mocked_player, poker_game):
    # Set up board and all-in
    poker_game.board = [
        Card(Rank.TEN, Suit.SPADES),
        Card(Rank.JACK, Suit.HEARTS),
        Card(Rank.QUEEN, Suit.DIAMONDS),
        Card(Rank.KING, Suit.CLUBS)
    ]
    poker_game.round = Round.TURN
    poker_game.current_bet = 1000

    chain = mocked_player.chains[FacingAllInDecision]
    chain.ainvoke.return_value = decision(FacingAllInDecision, "call")

    action, amount = await mocked_player.player_all_in(poker_game)

    assert action == ActionType.CALL
    assert amount is None
    chain.ainvoke.assert_awaited_once()

@pytest.mark.asyncio
async def test_api_error_falls_back_to_fold_when_facing_bet(mocked_player, poker_game):
    mocked_player.chains[FacingBetDecision].ainvoke.side_effect = Exception("invalid_prompt")

    action, amount = await mocked_player.player_raise(poker_game)

    assert action == ActionType.FOLD
    assert amount is None

@pytest.mark.asyncio
async def test_api_error_falls_back_to_check_when_free(mocked_player, poker_game):
    mocked_player.chains[CanCheckDecision].ainvoke.side_effect = Exception("invalid_prompt")

    action, amount = await mocked_player.player_check(poker_game)

    assert action == ActionType.CHECK
    assert amount is None
