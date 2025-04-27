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
    db = MagicMock()
    db.initialize_game = MagicMock()
    db.initialize_hand = MagicMock()
    db.record_gpt_action = MagicMock()
    db.update_community_cards = MagicMock()
    db.end_hand = MagicMock()
    db.end_game = MagicMock()
    return db

@pytest.fixture
def poker_game():
    game = PokerGameManager(buy_in=1000, small_blind=5, big_blind=10)
    return game

@pytest.fixture
def discord_poker_manager(mock_ctx, poker_game, mock_db_manager):
    with patch('bot.bot_poker_handler.GPTPlayer'):
        manager = DiscordPokerManager(
            ctx=mock_ctx,
            pokerGame=poker_game,
            db_manager=mock_db_manager,
            small_cards=False,
            timeout=60.0,
            model_name="test-model"
        )
        # Mock the card display
        with patch('bot.bot_poker_handler.get_cards', return_value="[Card Display]"):
            return manager

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
    assert discord_poker_manager.pokerGame == poker_game
    assert discord_poker_manager.db_manager == mock_db_manager
    assert discord_poker_manager.small_cards is False
    assert discord_poker_manager.timeout == 60.0
    assert discord_poker_manager.model_name == "test-model"

@pytest.mark.asyncio
async def test_play_round(discord_poker_manager, mock_ctx, poker_game, mock_db_manager):
    # Mock GPT player
    with patch.object(discord_poker_manager, 'pre_flop', AsyncMock()) as mock_pre_flop, \
         patch('bot.bot_poker_handler.GPTPlayer') as MockGPTPlayer:
        
        # Set up GPT player mock
        mock_gpt_player = MockGPTPlayer.return_value
        
        # Call play_round
        await discord_poker_manager.play_round()
        
        # Check that new round is initialized
        assert discord_poker_manager.gpt_action == mock_gpt_player
        mock_db_manager.initialize_hand.assert_called_once()
        mock_pre_flop.assert_called_once()

@pytest.mark.asyncio
async def test_deal_community_cards_flop(discord_poker_manager, mock_ctx, poker_game):
    # Set up player hands for testing
    poker_game.players[0].card1 = Card(Rank.ACE, Suit.SPADES)
    poker_game.players[0].card2 = Card(Rank.KING, Suit.HEARTS)
    poker_game.players[1].card1 = Card(Rank.QUEEN, Suit.DIAMONDS)
    poker_game.players[1].card2 = Card(Rank.JACK, Suit.CLUBS)
    
    # Mock the actions
    with patch.object(discord_poker_manager, 'pokerGPT_acts_first', AsyncMock()) as mock_gpt_acts, \
         patch.object(discord_poker_manager, 'user_acts_first', AsyncMock()) as mock_user_acts:
        
        # Test flop
        poker_game.button = 0  # GPT acts first
        await discord_poker_manager.deal_community_cards(Round.FLOP)
        
        # Check that community cards were dealt
        assert len(poker_game.board) == 3
        assert mock_ctx.send.call_count >= 3  # Multiple calls to send messages
        mock_gpt_acts.assert_called_once()
        mock_user_acts.assert_not_called()
        
        # Test with player acting first
        mock_gpt_acts.reset_mock()
        mock_user_acts.reset_mock()
        poker_game.board = []  # Reset board
        poker_game.button = 1  # Player acts first
        
        await discord_poker_manager.deal_community_cards(Round.FLOP)
        assert len(poker_game.board) == 3
        mock_gpt_acts.assert_not_called()
        mock_user_acts.assert_called_once()

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
    
    # Mock the result_embed method
    with patch.object(discord_poker_manager, 'result_embed', return_value=discord.Embed(title="Results")):
        # Call showdown
        await discord_poker_manager.showdown()
        
        # Check that community cards were dealt to 5
        assert len(poker_game.board) == 5
        
        # Verify database was updated
        mock_db_manager.update_community_cards.assert_called_once()
        mock_db_manager.end_hand.assert_called_once()
        
        # Check that context methods were called
        assert mock_ctx.send.call_count >= 5  # Multiple messages sent
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
    
    # Mock the result_embed method
    with patch.object(discord_poker_manager, 'result_embed', return_value=discord.Embed(title="Results")):
        # Call showdown
        await discord_poker_manager.showdown()
        
        # Verify game was ended
        mock_db_manager.end_game.assert_called_once_with(poker_game.return_player_stack(0))
        
        # Check that victory message was sent
        victory_message_sent = False
        for call in mock_ctx.send.call_args_list:
            args, kwargs = call
            if args and "wins the game" in args[0]:
                victory_message_sent = True
                break
        assert victory_message_sent

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
    # button=0, GPT <= small_blind → GPT all-in on SB, user auto-calls → showdown
    poker_game.button = 0
    poker_game.small_blind = 5
    poker_game.big_blind = 10
    poker_game.players[1].stack = 3  # ≤ SB
    m = DiscordPokerManager(mock_ctx, poker_game, mock_db_manager, small_cards=False, timeout=1.0)
    m.showdown = AsyncMock()

    await m.pre_flop()

    assert poker_game.players[1].round_pot_commitment == 3
    assert poker_game.players[0].round_pot_commitment == 3
    mock_ctx.send.assert_any_call(
        "PokerGPT can't cover small blind and is __All-in for 3 chips.__"
    )
    mock_ctx.send.assert_any_call(f"{poker_game.players[0].player_name} calls.")
    m.showdown.assert_awaited_once()

@pytest.mark.asyncio
async def test_preflop_player_cant_cover_small_blind_button0(mock_ctx, poker_game, mock_db_manager):
    # button=0, user ≤ SB → user all-in on SB, GPT auto-calls → showdown
    poker_game.button = 0
    poker_game.small_blind = 5
    poker_game.big_blind = 10
    poker_game.players[0].stack = 4  # ≤ SB
    m = DiscordPokerManager(mock_ctx, poker_game, mock_db_manager, small_cards=False, timeout=1.0)
    m.showdown = AsyncMock()

    await m.pre_flop()

    assert poker_game.players[0].round_pot_commitment == 4
    assert poker_game.players[1].round_pot_commitment == 4
    mock_ctx.send.assert_any_call(
        f"{poker_game.players[0].player_name} can't cover small blind and is __All-in for 4 chips.__"
    )
    mock_ctx.send.assert_any_call("PokerGPT calls.")
    m.showdown.assert_awaited_once()

@pytest.mark.asyncio
async def test_preflop_gpt_cant_cover_big_blind_button0(mock_ctx, poker_game, mock_db_manager):
    # button=0, user ≥ SB but GPT ≤ BB → SB & partial-BB, prompt via allInCallView
    poker_game.button = 0
    poker_game.small_blind = 5
    poker_game.big_blind = 10
    poker_game.players[0].stack = 100
    poker_game.players[1].stack = 8   # ≤ BB, > SB
    m = DiscordPokerManager(mock_ctx, poker_game, mock_db_manager, small_cards=False, timeout=1.0)
    m.allInCallView = lambda *_: "ALLIN_VIEW"

    await m.pre_flop()

    assert poker_game.players[0].round_pot_commitment == 5
    assert poker_game.players[1].round_pot_commitment == 8
    mock_ctx.send.assert_any_call(
        "What do you want to do? You are in for 5 chips, it costs 3 more to call.",
        view="ALLIN_VIEW"
    )

@pytest.mark.asyncio
async def test_preflop_player_cant_cover_big_blind_button0(mock_ctx, poker_game, mock_db_manager):
    # button=0, user ≥ SB but ≤ BB → SB & partial-BB, prompt via allInCallView
    poker_game.button = 0
    poker_game.small_blind = 5
    poker_game.big_blind = 10
    poker_game.players[0].stack = 7   # ≥ SB, ≤ BB
    poker_game.players[1].stack = 100
    m = DiscordPokerManager(mock_ctx, poker_game, mock_db_manager, small_cards=False, timeout=1.0)
    m.allInCallView = lambda *_: "ALLIN_VIEW"

    await m.pre_flop()

    assert poker_game.players[0].round_pot_commitment == 5
    assert poker_game.players[1].round_pot_commitment == 7
    mock_ctx.send.assert_any_call(
        "What do you want to do? You are in for 5 chips, it costs 2 more to call.",
        view="ALLIN_VIEW"
    )

@pytest.mark.asyncio
async def test_preflop_regular_button0_uses_call_view(mock_ctx, poker_game, mock_db_manager):
    # button=0, both ≥ BB → normal SB/BB, prompt via callView
    poker_game.button = 0
    poker_game.small_blind = 5
    poker_game.big_blind = 10
    poker_game.players[0].stack = 100
    poker_game.players[1].stack = 100
    m = DiscordPokerManager(mock_ctx, poker_game, mock_db_manager, small_cards=False, timeout=1.0)
    m.callView = lambda *_: "CALL_VIEW"

    await m.pre_flop()

    assert poker_game.players[0].round_pot_commitment == 5
    assert poker_game.players[1].round_pot_commitment == 10
    mock_ctx.send.assert_any_call(
        "What do you want to do? You are in for 5",
        view="CALL_VIEW"
    )

@pytest.mark.asyncio
async def test_preflop_player_cant_cover_small_blind_button1(mock_ctx, poker_game, mock_db_manager):
    # button=1, user ≤ SB → user all-in on SB, GPT auto-calls → showdown
    poker_game.button = 1
    poker_game.small_blind = 5
    poker_game.big_blind = 10
    poker_game.players[0].stack = 3
    m = DiscordPokerManager(mock_ctx, poker_game, mock_db_manager, small_cards=False, timeout=1.0)
    m.showdown = AsyncMock()

    await m.pre_flop()

    assert poker_game.players[0].round_pot_commitment == 3
    assert poker_game.players[1].round_pot_commitment == 3
    mock_ctx.send.assert_any_call(
        f"{poker_game.players[0].player_name} can't cover small blind and is __All-in for 3 chips.__"
    )
    mock_ctx.send.assert_any_call("PokerGPT calls.")
    m.showdown.assert_awaited_once()

@pytest.mark.asyncio
async def test_preflop_gpt_cant_cover_small_blind_button1(mock_ctx, poker_game, mock_db_manager):
    # button=1, GPT ≤ SB → GPT all-in on SB, user auto-calls → showdown
    poker_game.button = 1
    poker_game.small_blind = 5
    poker_game.big_blind = 10
    poker_game.players[1].stack = 4
    m = DiscordPokerManager(mock_ctx, poker_game, mock_db_manager, small_cards=False, timeout=1.0)
    m.showdown = AsyncMock()

    await m.pre_flop()

    assert poker_game.players[1].round_pot_commitment == 4
    assert poker_game.players[0].round_pot_commitment == 4
    mock_ctx.send.assert_any_call(
        "PokerGPT can't cover the small blind and is __All-in for 4 chips.__"
    )
    mock_ctx.send.assert_any_call(f"{poker_game.players[0].player_name} calls.")
    m.showdown.assert_awaited_once()

@pytest.mark.asyncio
async def test_preflop_player_cant_cover_big_blind_button1(mock_ctx, poker_game, mock_db_manager):
    # button=1, user ≥ SB but ≤ BB → user all-in on BB, GPT auto-calls → showdown
    poker_game.button = 1
    poker_game.small_blind = 5
    poker_game.big_blind = 10
    poker_game.players[0].stack = 7
    m = DiscordPokerManager(mock_ctx, poker_game, mock_db_manager, small_cards=False, timeout=1.0)
    m.showdown = AsyncMock()

    await m.pre_flop()

    assert poker_game.players[0].round_pot_commitment == 7
    assert poker_game.players[1].round_pot_commitment == 7
    mock_ctx.send.assert_any_call(
        f"{poker_game.players[0].player_name} is __All-in for 7 chips.__"
    )
    mock_ctx.send.assert_any_call("PokerGPT __Calls.__")
    m.showdown.assert_awaited_once()

@pytest.mark.asyncio
async def test_preflop_gpt_cant_cover_big_blind_button1(mock_ctx, poker_game, mock_db_manager):
    # button=1, GPT ≥ SB but ≤ BB → GPT all-in on BB, user auto-calls → showdown
    poker_game.button = 1
    poker_game.small_blind = 5
    poker_game.big_blind = 10
    poker_game.players[1].stack = 8
    m = DiscordPokerManager(mock_ctx, poker_game, mock_db_manager, small_cards=False, timeout=1.0)
    m.showdown = AsyncMock()

    await m.pre_flop()

    assert poker_game.players[1].round_pot_commitment == 8
    assert poker_game.players[0].round_pot_commitment == 8
    mock_ctx.send.assert_any_call("You put PokerGPT __All-in for 8 chips.__")
    mock_ctx.send.assert_any_call("PokerGPT __Calls All-in.__")
    m.showdown.assert_awaited_once()