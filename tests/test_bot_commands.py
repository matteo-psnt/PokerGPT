import discord
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bot.bot_poker_handler import DiscordPokerManager
from db.enums import Round
from game.card import Card, Rank, Suit
from game.poker import PokerGameManager

@pytest.fixture
def mock_ctx():
    ctx = MagicMock()
    ctx.send = AsyncMock()
    ctx.respond = AsyncMock()
    ctx.author = MagicMock()
    ctx.author.name = "TestUser"
    return ctx

@pytest.fixture
def mock_db_manager():
    return MagicMock()

@pytest.fixture
def poker_game():
    game = PokerGameManager(buy_in=1000, small_blind=5, big_blind=10)
    game.players[0].name = "TestUser"
    game.players[1].name = "PokerGPT"
    return game

def make_manager(ctx, game, db, **kwargs):
    with patch('bot.bot_poker_handler.GPTPlayer'):
        return DiscordPokerManager(ctx, game, db, small_cards=False, timeout=1.0, **kwargs)

def sent_messages(ctx):
    return [call.args[0] for call in ctx.send.call_args_list if call.args]

@pytest.fixture
def discord_poker_manager(mock_ctx, poker_game, mock_db_manager):
    return make_manager(mock_ctx, poker_game, mock_db_manager, model_name="test-model")

@pytest.mark.asyncio
async def test_initialization(discord_poker_manager, mock_db_manager, poker_game, mock_ctx):
    # Check that database was initialized properly
    mock_db_manager.initialize_game.assert_called_once_with(
        poker_game.small_blind,
        poker_game.big_blind,
        poker_game.starting_stack
    )

    # Check that manager holds the correct references
    assert discord_poker_manager.ctx == mock_ctx
    assert discord_poker_manager.game == poker_game
    assert discord_poker_manager.db == mock_db_manager
    assert discord_poker_manager.small_cards is False
    assert discord_poker_manager.timeout == 1.0
    assert discord_poker_manager.model_name == "test-model"

@pytest.mark.asyncio
async def test_play_round(discord_poker_manager, mock_db_manager):
    with patch.object(discord_poker_manager, 'pre_flop', AsyncMock()) as mock_pre_flop:
        await discord_poker_manager.play_round()

    mock_db_manager.initialize_hand.assert_called_once()
    mock_pre_flop.assert_called_once()

@pytest.mark.asyncio
@pytest.mark.parametrize("button,first_to_act", [
    (0, 1),  # user has the button, so PokerGPT (big blind) acts first
    (1, 0),  # PokerGPT has the button, so the user acts first
])
async def test_flop_big_blind_acts_first(discord_poker_manager, mock_ctx, poker_game, button, first_to_act):
    poker_game.button = button
    poker_game.round = Round.PRE_FLOP

    with patch.object(discord_poker_manager, 'offer_check', AsyncMock()) as mock_offer_check:
        await discord_poker_manager.next_street()

    assert poker_game.round == Round.FLOP
    assert len(poker_game.board) == 3
    assert mock_ctx.send.call_count >= 3
    mock_offer_check.assert_awaited_once_with(first_to_act)

@pytest.mark.asyncio
async def test_river_moves_to_showdown(discord_poker_manager, poker_game):
    poker_game.round = Round.RIVER

    with patch.object(discord_poker_manager, 'showdown', AsyncMock()) as mock_showdown:
        await discord_poker_manager.next_street()

    mock_showdown.assert_awaited_once()

@pytest.mark.asyncio
async def test_showdown(discord_poker_manager, mock_ctx, poker_game, mock_db_manager):
    # Set up player hands and board for testing
    poker_game.players[0].card1 = Card(Rank.ACE, Suit.SPADES)
    poker_game.players[0].card2 = Card(Rank.KING, Suit.HEARTS)
    poker_game.players[1].card1 = Card(Rank.QUEEN, Suit.DIAMONDS)
    poker_game.players[1].card2 = Card(Rank.JACK, Suit.CLUBS)
    poker_game.board = [
        Card(Rank.TEN, Suit.SPADES),
        Card(Rank.NINE, Suit.HEARTS),
        Card(Rank.EIGHT, Suit.DIAMONDS)
    ]
    poker_game.current_pot = 100

    await discord_poker_manager.showdown()

    # Check that community cards were dealt to 5
    assert len(poker_game.board) == 5

    # Verify database was updated
    mock_db_manager.update_community_cards.assert_called_once()
    mock_db_manager.end_hand.assert_called_once()

    # Check that context methods were called
    assert mock_ctx.send.call_count >= 5
    mock_ctx.respond.assert_called_once_with("Play another round?")

@pytest.mark.asyncio
async def test_player_wins_game(discord_poker_manager, mock_ctx, poker_game, mock_db_manager):
    # Set up scenario where player wins the game
    poker_game.players[0].card1 = Card(Rank.ACE, Suit.SPADES)
    poker_game.players[0].card2 = Card(Rank.KING, Suit.HEARTS)
    poker_game.players[1].card1 = Card(Rank.QUEEN, Suit.DIAMONDS)
    poker_game.players[1].card2 = Card(Rank.JACK, Suit.CLUBS)
    poker_game.board = [
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.ACE, Suit.DIAMONDS),
        Card(Rank.KING, Suit.SPADES),
        Card(Rank.QUEEN, Suit.HEARTS),
        Card(Rank.TWO, Suit.CLUBS)
    ]
    poker_game.current_pot = 1000
    poker_game.players[1].stack = 0  # Bot has no chips left

    await discord_poker_manager.showdown()

    mock_db_manager.end_game.assert_called_once_with(poker_game.players[0].stack)
    assert "TestUser wins the game! PokerGPT is out of chips." in sent_messages(mock_ctx)
    mock_ctx.respond.assert_not_called()

@pytest.mark.asyncio
async def test_result_embed_fields(discord_poker_manager, mock_ctx, poker_game):
    poker_game.players[0].stack = 1234
    poker_game.players[1].stack = 4321

    embed: discord.Embed = discord_poker_manager.result_embed()

    assert embed.title == "Results"
    assert len(embed.fields) == 2

    field_map = {f.name: f.value for f in embed.fields}
    assert field_map["PokerGPT"] == "4321"
    assert field_map[mock_ctx.author.name] == "1234"

@pytest.mark.asyncio
async def test_preflop_gpt_cant_cover_small_blind_button0(mock_ctx, poker_game, mock_db_manager):
    # button=0, GPT <= small_blind → GPT all-in, user auto-calls → showdown
    poker_game.button = 0
    poker_game.players[1].stack = 3  # ≤ SB
    m = make_manager(mock_ctx, poker_game, mock_db_manager)
    m.showdown = AsyncMock()

    await m.pre_flop()

    assert poker_game.players[1].round_pot_commitment == 3
    assert poker_game.players[0].round_pot_commitment == 3
    mock_ctx.send.assert_any_call("PokerGPT can't cover the small blind and is __All-in for 3 chips.__")
    mock_ctx.send.assert_any_call("TestUser calls.")
    m.showdown.assert_awaited_once()

@pytest.mark.asyncio
async def test_preflop_player_cant_cover_small_blind_button0(mock_ctx, poker_game, mock_db_manager):
    # button=0, user ≤ SB → user all-in, GPT auto-calls → showdown
    poker_game.button = 0
    poker_game.players[0].stack = 4  # ≤ SB
    m = make_manager(mock_ctx, poker_game, mock_db_manager)
    m.showdown = AsyncMock()

    await m.pre_flop()

    assert poker_game.players[0].round_pot_commitment == 4
    assert poker_game.players[1].round_pot_commitment == 4
    mock_ctx.send.assert_any_call("TestUser can't cover the small blind and is __All-in for 4 chips.__")
    mock_ctx.send.assert_any_call("PokerGPT calls.")
    m.showdown.assert_awaited_once()

@pytest.mark.asyncio
async def test_preflop_gpt_cant_cover_big_blind_button0(mock_ctx, poker_game, mock_db_manager):
    # button=0, user ≥ SB but GPT ≤ BB → SB & partial-BB, prompt via AllInCallView
    poker_game.button = 0
    poker_game.players[0].stack = 100
    poker_game.players[1].stack = 8   # ≤ BB, > SB
    m = make_manager(mock_ctx, poker_game, mock_db_manager)

    with patch('bot.bot_poker_handler.AllInCallView', return_value="ALLIN_VIEW"):
        await m.pre_flop()

    assert poker_game.players[0].round_pot_commitment == 5
    assert poker_game.players[1].round_pot_commitment == 8
    mock_ctx.send.assert_any_call("PokerGPT can't cover the big blind and is __All-in for 8 chips.__")
    mock_ctx.send.assert_any_call(
        "What do you want to do? You are in for 5 chips, it costs 3 more to call.",
        view="ALLIN_VIEW"
    )

@pytest.mark.asyncio
async def test_preflop_player_cant_cover_big_blind_button0(mock_ctx, poker_game, mock_db_manager):
    # button=0, user ≥ SB but ≤ BB → SB & partial-BB, prompt via AllInCallView
    poker_game.button = 0
    poker_game.players[0].stack = 7   # ≥ SB, ≤ BB
    poker_game.players[1].stack = 100
    m = make_manager(mock_ctx, poker_game, mock_db_manager)

    with patch('bot.bot_poker_handler.AllInCallView', return_value="ALLIN_VIEW"):
        await m.pre_flop()

    assert poker_game.players[0].round_pot_commitment == 5
    assert poker_game.players[1].round_pot_commitment == 7
    mock_ctx.send.assert_any_call("PokerGPT puts TestUser __All-in for 7 chips.__")
    mock_ctx.send.assert_any_call(
        "What do you want to do? You are in for 5 chips, it costs 2 more to call.",
        view="ALLIN_VIEW"
    )

@pytest.mark.asyncio
async def test_preflop_regular_button0_uses_call_view(mock_ctx, poker_game, mock_db_manager):
    # button=0, both ≥ BB → normal SB/BB, prompt via CallView
    poker_game.button = 0
    poker_game.players[0].stack = 100
    poker_game.players[1].stack = 100
    m = make_manager(mock_ctx, poker_game, mock_db_manager)

    with patch('bot.bot_poker_handler.CallView', return_value="CALL_VIEW"):
        await m.pre_flop()

    assert poker_game.players[0].round_pot_commitment == 5
    assert poker_game.players[1].round_pot_commitment == 10
    mock_ctx.send.assert_any_call("PokerGPT places big blind of 10 chips, and TestUser places small blind of 5 chips.")
    mock_ctx.send.assert_any_call("What do you want to do? You are in for 5", view="CALL_VIEW")

@pytest.mark.asyncio
async def test_preflop_player_cant_cover_small_blind_button1(mock_ctx, poker_game, mock_db_manager):
    # button=1, user ≤ SB → user all-in, GPT auto-calls → showdown
    poker_game.button = 1
    poker_game.players[0].stack = 3
    m = make_manager(mock_ctx, poker_game, mock_db_manager)
    m.showdown = AsyncMock()

    await m.pre_flop()

    assert poker_game.players[0].round_pot_commitment == 3
    assert poker_game.players[1].round_pot_commitment == 3
    mock_ctx.send.assert_any_call("TestUser can't cover the small blind and is __All-in for 3 chips.__")
    mock_ctx.send.assert_any_call("PokerGPT calls.")
    m.showdown.assert_awaited_once()

@pytest.mark.asyncio
async def test_preflop_gpt_cant_cover_small_blind_button1(mock_ctx, poker_game, mock_db_manager):
    # button=1, GPT ≤ SB → GPT all-in, user auto-calls → showdown
    poker_game.button = 1
    poker_game.players[1].stack = 4
    m = make_manager(mock_ctx, poker_game, mock_db_manager)
    m.showdown = AsyncMock()

    await m.pre_flop()

    assert poker_game.players[1].round_pot_commitment == 4
    assert poker_game.players[0].round_pot_commitment == 4
    mock_ctx.send.assert_any_call("PokerGPT can't cover the small blind and is __All-in for 4 chips.__")
    mock_ctx.send.assert_any_call("TestUser calls.")
    m.showdown.assert_awaited_once()

@pytest.mark.asyncio
async def test_preflop_player_cant_cover_big_blind_button1(mock_ctx, poker_game, mock_db_manager):
    # button=1, user ≥ SB but ≤ BB → user all-in on BB, GPT auto-calls → showdown
    poker_game.button = 1
    poker_game.players[0].stack = 7
    m = make_manager(mock_ctx, poker_game, mock_db_manager)
    m.showdown = AsyncMock()

    await m.pre_flop()

    assert poker_game.players[0].round_pot_commitment == 7
    assert poker_game.players[1].round_pot_commitment == 7
    mock_ctx.send.assert_any_call("TestUser can't cover the big blind and is __All-in for 7 chips.__")
    mock_ctx.send.assert_any_call("PokerGPT __Calls All-in.__")
    m.showdown.assert_awaited_once()

@pytest.mark.asyncio
async def test_preflop_gpt_cant_cover_big_blind_button1(mock_ctx, poker_game, mock_db_manager):
    # button=1, GPT ≥ SB but ≤ BB → GPT all-in, the user's big blind covers it → showdown
    poker_game.button = 1
    poker_game.players[1].stack = 8
    m = make_manager(mock_ctx, poker_game, mock_db_manager)
    m.showdown = AsyncMock()

    await m.pre_flop()

    assert poker_game.players[1].round_pot_commitment == 8
    assert poker_game.players[0].round_pot_commitment == 8
    mock_ctx.send.assert_any_call("TestUser puts PokerGPT __All-in for 8 chips.__")
    mock_ctx.send.assert_any_call("PokerGPT __Calls All-in.__")
    m.showdown.assert_awaited_once()
