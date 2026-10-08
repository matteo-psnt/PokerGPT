import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bot.bot_poker_handler import DiscordPokerManager
from game.poker import PokerGameManager

AUTHOR_ID = 1234

@pytest.fixture
def manager():
    ctx = MagicMock()
    ctx.send = AsyncMock()
    ctx.respond = AsyncMock()
    ctx.author.id = AUTHOR_ID
    ctx.author.name = "TestUser"
    game = PokerGameManager(buy_in=1000, small_blind=5, big_blind=10)
    with patch('bot.bot_poker_handler.GPTPlayer'):
        m = DiscordPokerManager(ctx, game, MagicMock(), small_cards=False, timeout=60.0)
    m.user_raise = AsyncMock()
    m.user_all_in = AsyncMock()
    m.user_fold = AsyncMock()
    m.next_action = AsyncMock()
    return m

def make_interaction(user_id=AUTHOR_ID):
    interaction = MagicMock()
    interaction.user.id = user_id
    interaction.response.edit_message = AsyncMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.send_modal = AsyncMock()
    return interaction

def make_modal(manager, view, amount):
    modal = manager.raiseModal(manager, view)
    modal.children[0].value = amount
    return modal

@pytest.mark.asyncio
async def test_dismissed_raise_modal_still_folds_on_timeout(manager):
    view = manager.callView(manager)
    await view.raise_button_callback.callback(make_interaction())

    # Player closed the modal without submitting, so the timeout should still fold
    assert view.responded is False
    view.message = MagicMock()
    view.message.edit = AsyncMock()
    await view.on_timeout()
    manager.user_fold.assert_awaited_once()

@pytest.mark.asyncio
async def test_raise_covering_gpt_stack_goes_all_in_once(manager):
    game = manager.pokerGame
    game.players[1].stack = 200
    view = manager.callView(manager)
    interaction = make_interaction()

    await make_modal(manager, view, "500").callback(interaction)

    manager.user_all_in.assert_awaited_once()
    manager.user_raise.assert_not_awaited()
    interaction.response.edit_message.assert_awaited_once()
    assert view.responded is True
    assert view.is_finished()

@pytest.mark.asyncio
async def test_valid_raise_locks_view(manager):
    view = manager.callView(manager)
    interaction = make_interaction()

    await make_modal(manager, view, "100").callback(interaction)

    manager.user_raise.assert_awaited_once_with(100)
    assert view.responded is True
    assert view.is_finished()

@pytest.mark.asyncio
async def test_invalid_raise_keeps_view_open(manager):
    view = manager.callView(manager)
    interaction = make_interaction()

    await make_modal(manager, view, "abc").callback(interaction)

    manager.user_raise.assert_not_awaited()
    assert view.responded is False
    assert not view.is_finished()

@pytest.mark.asyncio
async def test_raise_after_timeout_is_rejected(manager):
    view = manager.callView(manager)
    view.stop()
    interaction = make_interaction()

    await make_modal(manager, view, "100").callback(interaction)

    manager.user_raise.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()

@pytest.mark.asyncio
async def test_button_click_answers_interaction(manager):
    view = manager.callView(manager)
    interaction = make_interaction()

    await view.fold_button_callback.callback(interaction)

    interaction.response.edit_message.assert_awaited_once()
    manager.user_fold.assert_awaited_once()

@pytest.mark.asyncio
async def test_other_user_click_is_rejected(manager):
    view = manager.callView(manager)
    interaction = make_interaction(user_id=9999)

    await view.fold_button_callback.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    assert interaction.response.send_message.call_args.kwargs.get("ephemeral") is True
    manager.user_fold.assert_not_awaited()
    assert view.responded is False
