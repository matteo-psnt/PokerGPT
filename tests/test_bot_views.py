import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bot.bot_poker_handler import CallView, DiscordPokerManager, RaiseModal
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
    m.user_call = AsyncMock()
    return m

def make_interaction(user_id=AUTHOR_ID):
    interaction = MagicMock()
    interaction.user.id = user_id
    interaction.response.edit_message = AsyncMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.send_modal = AsyncMock()
    return interaction

def make_modal(manager, view, amount):
    modal = RaiseModal(manager, view)
    modal.children[0].value = amount
    return modal

@pytest.mark.asyncio
async def test_dismissed_raise_modal_still_folds_on_timeout(manager):
    view = CallView(manager)
    await view.raise_button.callback(make_interaction())

    # Player closed the modal without submitting, so the view is still waiting and the timeout should fold
    assert not view.is_finished()
    view.message = MagicMock()
    view.message.edit = AsyncMock()
    await view.on_timeout()
    manager.user_fold.assert_awaited_once()

@pytest.mark.asyncio
async def test_raise_covering_gpt_stack_goes_all_in_once(manager):
    manager.game.players[1].stack = 200
    view = CallView(manager)
    interaction = make_interaction()

    await make_modal(manager, view, "500").callback(interaction)

    manager.user_all_in.assert_awaited_once()
    manager.user_raise.assert_not_awaited()
    interaction.response.edit_message.assert_awaited_once()
    assert view.is_finished()

@pytest.mark.asyncio
async def test_valid_raise_locks_view(manager):
    view = CallView(manager)
    interaction = make_interaction()

    await make_modal(manager, view, "100").callback(interaction)

    manager.user_raise.assert_awaited_once_with(100)
    assert view.is_finished()

@pytest.mark.asyncio
@pytest.mark.parametrize("amount", ["abc", "5", "5000"])
async def test_invalid_raise_keeps_view_open(manager, amount):
    view = CallView(manager)
    interaction = make_interaction()

    await make_modal(manager, view, amount).callback(interaction)

    manager.user_raise.assert_not_awaited()
    manager.user_all_in.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()
    assert not view.is_finished()

@pytest.mark.asyncio
async def test_raise_after_timeout_is_rejected(manager):
    view = CallView(manager)
    view.stop()
    interaction = make_interaction()

    await make_modal(manager, view, "100").callback(interaction)

    manager.user_raise.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()

@pytest.mark.asyncio
async def test_button_click_answers_interaction_and_stops_view(manager):
    view = CallView(manager)
    interaction = make_interaction()

    await view.fold_button.callback(interaction)

    interaction.response.edit_message.assert_awaited_once()
    manager.user_fold.assert_awaited_once()
    assert view.is_finished()

@pytest.mark.asyncio
async def test_other_user_click_is_rejected(manager):
    view = CallView(manager)
    interaction = make_interaction(user_id=9999)

    assert await view.interaction_check(interaction) is False
    await view.on_check_failure(interaction)

    interaction.response.send_message.assert_awaited_once()
    assert interaction.response.send_message.call_args.kwargs.get("ephemeral") is True

@pytest.mark.asyncio
async def test_author_click_is_allowed(manager):
    view = CallView(manager)
    assert await view.interaction_check(make_interaction()) is True
