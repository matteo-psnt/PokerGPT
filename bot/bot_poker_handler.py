import discord
from discord import ButtonStyle
from discord.ui import InputText, View
from bot.card_display import get_cards
from bot.gpt_player import GPTPlayer
from config.log_config import logger
from db.db_utils import DatabaseManager
from db.enums import ActionType, Round
from game.player import Player
from game.poker import GPT, USER, PokerGameManager

NEXT_ROUND = {Round.PRE_FLOP: Round.FLOP, Round.FLOP: Round.TURN, Round.TURN: Round.RIVER, Round.RIVER: Round.SHOWDOWN}
BOARD_SIZE = {Round.FLOP: 3, Round.TURN: 4, Round.RIVER: 5}


class DiscordPokerManager:
    def __init__(self, ctx, poker_game: PokerGameManager, db_manager: DatabaseManager, small_cards: bool, timeout: float,
                 model_name: str = "gpt-6-luna"):
        self.ctx = ctx
        self.game = poker_game
        self.db = db_manager
        self.small_cards = small_cards
        self.timeout = timeout
        self.model_name = model_name
        self.gpt_player = GPTPlayer(db_manager, model_name=model_name)

        db_manager.initialize_game(poker_game.small_blind, poker_game.big_blind, poker_game.starting_stack)

    @property
    def user(self) -> Player:
        return self.game.players[USER]

    @property
    def pokergpt(self) -> Player:
        return self.game.players[GPT]

    def log(self, message: str):
        logger.info(f"{self.ctx.author.name} - {message}")

    async def send(self, content: str, **kwargs):
        return await self.ctx.send(content, **kwargs)

    async def send_cards(self, cards):
        await self.ctx.send(get_cards(cards, self.small_cards))

    async def play_round(self):
        self.game.new_round()
        self.db.initialize_hand(self.user.hand_str(), self.pokergpt.hand_str(), self.user.stack)
        self.log("Starting a new round.")
        self.log(f"Player has {self.user.stack} chips, PokerGPT has {self.pokergpt.stack} chips.")
        await self.pre_flop()

    async def pre_flop(self):
        game = self.game
        game.round = Round.PRE_FLOP
        game.reset_betting()
        # Heads-up, the button posts the small blind
        sb, bb = game.button, 1 - game.button
        small, big = game.players[sb], game.players[bb]

        self.log(f"Pre-flop: Player has {self.user.hand_str()}, PokerGPT has {self.pokergpt.hand_str()}")
        await self.send("**Your Cards:**")
        await self.send_cards(self.user.hand)

        # A player who can't cover the small blind is all-in and called straight to showdown
        short = next((p for p in (bb, sb) if game.players[p].stack <= game.small_blind), None)
        if short is not None:
            caller = 1 - short
            await self.send(f"{game.players[short].name} can't cover the small blind and is __All-in for {game.players[short].stack} chips.__")
            await self.send(f"{game.players[caller].name} calls.")
            game.player_all_in(short)
            game.player_call(caller)
            return await self.showdown()

        # A player who can't cover the big blind is all-in, and the big blind is posted up to that amount
        short = next((p for p in (bb, sb) if game.players[p].stack <= game.big_blind), None)
        if short is not None:
            all_in = game.players[short].stack
            await self.send(f"{small.name} places small blind of {game.small_blind} chips.")
            if short == bb:
                await self.send(f"{big.name} can't cover the big blind and is __All-in for {all_in} chips.__")
            else:
                await self.send(f"{big.name} puts {small.name} __All-in for {all_in} chips.__")
            game.player_raise(sb, game.small_blind)
            game.player_raise(bb, all_in)

            if sb == USER:
                await self.send(f"You have {self.user.stack} chips.")
                await self.send(f"What do you want to do? You are in for {self.user.round_pot_commitment} chips, "
                                f"it costs {game.amount_to_call(USER)} more to call.", view=AllInCallView(self))
            else:
                await self.send("PokerGPT __Calls All-in.__")
                game.player_call(GPT)
                await self.showdown()
            return

        await self.send(f"{big.name} places big blind of {game.big_blind} chips, and {small.name} places small blind of {game.small_blind} chips.")
        game.player_raise(sb, game.small_blind)
        game.player_raise(bb, game.big_blind)

        if sb == USER:
            await self.send(f"You have {self.user.stack} chips.")
            await self.send(f"What do you want to do? You are in for {self.user.round_pot_commitment}", view=CallView(self))
        else:
            action, raise_amount = await self.gpt_player.pre_flop_small_blind(game)
            await self.gpt_acts(action, raise_amount, call_message="PokerGPT __Calls.__")

    async def next_street(self):
        game = self.game
        game.round = NEXT_ROUND[game.round]
        if game.round == Round.SHOWDOWN:
            return await self.showdown()

        game.reset_betting()
        game.deal_board(BOARD_SIZE[game.round])
        round_name = game.round.value.capitalize()
        self.log(f"{round_name} {game.board_str()}")
        await self.send(f"**Community Cards ({round_name}):**")
        await self.send_cards(game.board)
        await self.send(f"**Main pot:** {game.current_pot} chips.")
        await self.send(f"**{self.user.name} stack:** {self.user.stack} chips.")
        await self.send(f"**PokerGPT stack:** {self.pokergpt.stack} chips.")

        # After the flop the big blind acts first
        await self.offer_check(1 - game.button)

    # asks a player to act when there is no bet for them to face
    async def offer_check(self, player: int):
        game = self.game
        if player == USER:
            await self.send("What do you want to do?", view=CheckView(self))
        elif game.round == Round.PRE_FLOP:
            await self.gpt_acts(*await self.gpt_player.pre_flop_big_blind(game))
        elif game.button == USER:
            await self.gpt_acts(*await self.gpt_player.first_to_act(game))
        else:
            await self.gpt_acts(*await self.gpt_player.player_check(game))

    async def after_check(self, player: int):
        # The big blind's check closes the action pre-flop, and the button's check closes it after the flop
        if self.game.round == Round.PRE_FLOP or player == self.game.button:
            await self.next_street()
        else:
            await self.offer_check(1 - player)

    async def after_call(self):
        game = self.game
        if any(player.stack == 0 for player in game.players):
            # Someone is all-in, so there's no more betting
            await self.showdown()
        elif game.round == Round.PRE_FLOP and game.current_bet == game.big_blind:
            # The small blind limped in, so the big blind still gets to act
            await self.offer_check(1 - game.button)
        else:
            await self.next_street()

    async def gpt_acts(self, action: ActionType, raise_amount: int | None, call_message: str = "PokerGPT __Calls.__"):
        if action == ActionType.CHECK:
            self.log("PokerGPT Checks.")
            await self.send("PokerGPT __Checks.__")
            await self.after_check(GPT)
        elif action == ActionType.CALL:
            self.log("PokerGPT Calls.")
            await self.send(call_message)
            self.game.player_call(GPT)
            await self.after_call()
        elif action == ActionType.RAISE:
            await self.gpt_raise(raise_amount)
        elif action == ActionType.ALL_IN:
            await self.gpt_all_in()
        else:
            await self.gpt_fold()

    async def gpt_raise(self, amount: int):
        self.log(f"PokerGPT raises to {amount} chips")
        await self.send(f"PokerGPT __Raises to {amount} chips.__")
        self.game.player_raise(GPT, amount)
        await self.send(f"**Main pot:** {self.game.current_pot} chips")

        view: PokerView
        if self.user.total_chips <= self.game.current_bet:
            await self.send(f"PokerGPT puts you __All-In for {self.user.total_chips} chips.__")
            view = AllInCallView(self)
        else:
            view = CallView(self)
        await self.send(f"What do you want to do? You are in for {self.user.round_pot_commitment} chips, "
                        f"it costs __{self.game.amount_to_call(USER)} more to call.__", view=view)

    async def gpt_all_in(self):
        self.log("PokerGPT goes All-in")
        await self.send(f"PokerGPT is __All-in for {self.pokergpt.total_chips} chips.__")
        self.game.player_all_in(GPT)
        await self.send(f"What do you want to do? You are in for {self.user.round_pot_commitment} chips, "
                        f"it is {self.game.amount_to_call(USER)} more to call", view=AllInCallView(self))

    async def gpt_fold(self):
        self.log("PokerGPT Folds.")
        await self.send("PokerGPT Folds.")
        await self.send(f"You win __{self.game.current_pot} chips.__")
        await self.award_uncontested_pot(self.user)

    async def user_check(self):
        self.log("User Checks.")
        await self.after_check(USER)

    async def user_call(self):
        self.log("User Calls.")
        self.game.player_call(USER)
        await self.after_call()

    async def user_raise(self, amount: int):
        self.log(f"User raises to {amount} chips")
        self.game.player_raise(USER, amount)
        action, raise_amount = await self.gpt_player.player_raise(self.game)
        await self.gpt_acts(action, raise_amount, call_message="PokerGPT __Calls Raise.__")

    async def user_all_in(self):
        self.log("User goes All-in")
        self.game.player_all_in(USER)
        action, raise_amount = await self.gpt_player.player_all_in(self.game)
        await self.gpt_acts(action, raise_amount, call_message="PokerGPT __Calls All-in.__")

    async def user_fold(self):
        self.log("User Folds.")
        await self.send(f"PokerGPT wins __{self.game.current_pot} chips.__")
        await self.award_uncontested_pot(self.pokergpt)

    async def award_uncontested_pot(self, winner: Player):
        self.game.award_pot(winner)
        await self.send(f"You have {self.user.stack} chips.")
        await self.send(f"PokerGPT has {self.pokergpt.stack} chips.")
        self.end_hand()
        await self.prompt_new_round()

    async def showdown(self):
        game = self.game
        await self.send("***Showdown!!***")
        game.round = Round.SHOWDOWN

        game.deal_board(5)
        await self.send("**Community Cards:**")
        await self.send_cards(game.board)
        self.log(f"Showdown {game.board_str()}")

        game.evaluate_hands()
        for player in game.players:
            await self.send(f"{player.name} has:")
            await self.send_cards(player.hand)
            await self.send(f"**{player.hand_rank}**")
            await self.send_cards(player.hand_played)
            self.log(f"{player.name} has {player.hand_rank}")

        winners = game.determine_winners()
        pot = game.current_pot
        game.award_pot(*winners)
        if len(winners) > 1:
            self.log("Split pot")
            await self.send("**Split pot!!!**")
            for player in winners:
                await self.send(f"{player.name} wins {pot // len(winners)} chips and has {player.stack} chips.")
        else:
            winner = winners[0]
            self.log(f"{winner.name} wins {pot} chips")
            await self.send(f"{winner.name} wins **{pot} chips** and has {winner.stack} chips.")

        self.end_hand()
        loser = next((player for player in game.players if player.stack == 0), None)
        if loser is None:
            await self.prompt_new_round()
        else:
            winner = game.players[1 - game.players.index(loser)]
            await self.send(f"{winner.name} wins the game! {loser.name} is out of chips.", embeds=[self.end_game()])

    def end_hand(self):
        self.db.update_community_cards(self.game.board_str())
        self.db.end_hand(self.user.stack, self.game.round)

    # records the end of the game and returns the results embed
    def end_game(self) -> discord.Embed:
        self.db.end_game(self.user.stack)
        return self.result_embed()

    async def prompt_new_round(self):
        await self.ctx.respond("Play another round?")
        await self.send("", view=NewRoundView(self))

    def result_embed(self) -> discord.Embed:
        self.log(f"Game Results Player Stack: {self.user.stack} chips, PokerGPT Stack: {self.pokergpt.stack} chips.")
        embed = discord.Embed(title="Results")
        embed.add_field(name="PokerGPT", value=str(self.pokergpt.stack))
        embed.add_field(name=self.ctx.author.name, value=str(self.user.stack))
        return embed


class PokerView(View):
    """Buttons only the player who started the game can press. Answering stops the view, so its timeout never fires."""

    def __init__(self, manager: DiscordPokerManager):
        super().__init__(timeout=manager.timeout)
        self.manager = manager

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user is not None and interaction.user.id == self.manager.ctx.author.id

    async def on_check_failure(self, interaction: discord.Interaction):
        await interaction.response.send_message("This isn't your game.", ephemeral=True)

    # stops the view and replaces the prompt with the player's answer
    async def answer(self, interaction: discord.Interaction, content: str, **kwargs):
        self.stop()
        await interaction.response.edit_message(content=content, view=None, **kwargs)

    # replaces the prompt once the view has timed out
    async def expire(self, content: str, **kwargs):
        if self.message:
            await self.message.edit(content=content, view=None, **kwargs)

    async def open_raise_modal(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RaiseModal(self.manager, self))

    async def answer_all_in(self, interaction: discord.Interaction):
        await self.answer(interaction, f"You are __All-in for {self.manager.user.total_chips} chips.__")
        await self.manager.user_all_in()

    async def answer_fold(self, interaction: discord.Interaction):
        await self.answer(interaction, "You __Fold.__")
        await self.manager.user_fold()


class CallView(PokerView):
    async def on_timeout(self):
        await self.expire("You took too long! You __Fold.__")
        await self.manager.user_fold()

    @discord.ui.button(label="Call", style=ButtonStyle.blurple)
    async def call_button(self, button, interaction):
        await self.answer(interaction, "You __Call.__")
        await self.manager.user_call()

    @discord.ui.button(label="Raise", style=ButtonStyle.green)
    async def raise_button(self, button, interaction):
        await self.open_raise_modal(interaction)

    @discord.ui.button(label="All-in", style=ButtonStyle.green)
    async def all_in_button(self, button, interaction):
        await self.answer_all_in(interaction)

    @discord.ui.button(label="Fold", style=ButtonStyle.red)
    async def fold_button(self, button, interaction):
        await self.answer_fold(interaction)


class CheckView(PokerView):
    async def on_timeout(self):
        await self.expire("You took too long! You __Check.__")
        await self.manager.user_check()

    @discord.ui.button(label="Check", style=ButtonStyle.blurple)
    async def check_button(self, button, interaction):
        await self.answer(interaction, "You __Check.__")
        await self.manager.user_check()

    @discord.ui.button(label="Raise", style=ButtonStyle.green)
    async def raise_button(self, button, interaction):
        await self.open_raise_modal(interaction)

    @discord.ui.button(label="All-in", style=ButtonStyle.green)
    async def all_in_button(self, button, interaction):
        await self.answer_all_in(interaction)


class AllInCallView(PokerView):
    async def on_timeout(self):
        await self.expire("You took too long! You __Fold__.")
        await self.manager.user_fold()

    @discord.ui.button(label="Call All-in", style=ButtonStyle.blurple)
    async def call_button(self, button, interaction):
        await self.answer(interaction, "You __Call the All-in.__")
        await self.manager.user_call()

    @discord.ui.button(label="Fold", style=ButtonStyle.red)
    async def fold_button(self, button, interaction):
        await self.answer_fold(interaction)


class NewRoundView(PokerView):
    async def on_timeout(self):
        await self.expire("*Game Ended*", embeds=[self.manager.end_game()])

    @discord.ui.button(label="New Round", style=ButtonStyle.blurple)
    async def new_round_button(self, button, interaction):
        await self.answer(interaction, "*Starting a new round.*")
        await self.manager.play_round()

    @discord.ui.button(label="End Game", style=ButtonStyle.red)
    async def end_game_button(self, button, interaction):
        await self.answer(interaction, "*Game Ended*", embeds=[self.manager.end_game()])


class RaiseModal(discord.ui.Modal):
    def __init__(self, manager: DiscordPokerManager, parent_view: PokerView):
        super().__init__(title="Raise", timeout=manager.timeout)
        self.manager = manager
        # The prompt that opened this modal; it only counts as answered once a valid raise is submitted
        self.parent_view = parent_view
        self.add_item(InputText(label="Amount", value="", placeholder="Enter amount"))

    async def callback(self, interaction: discord.Interaction):
        if self.parent_view.is_finished():
            await interaction.response.send_message("Too late, this action has already timed out.", ephemeral=True)
            return

        text = self.children[0].value
        if not text.isdigit():
            await interaction.response.send_message("Please enter a valid number.")
            return

        amount = int(text)
        min_raise, max_raise = self.manager.game.raise_limits(USER)
        if amount == max_raise:
            await self.parent_view.answer(interaction, "You are __All-in.__")
            await self.manager.user_all_in()
        elif amount > max_raise:
            await interaction.response.send_message("You do not have enough chips.")
        elif amount < min_raise:
            await interaction.response.send_message(f"You must raise to at least {min_raise} chips.")
        elif amount >= self.manager.pokergpt.total_chips:
            await self.parent_view.answer(interaction, f"You put PokerGPT __All-in for {self.manager.pokergpt.total_chips} chips.__")
            await self.manager.user_all_in()
        else:
            await self.parent_view.answer(interaction, f"You __Raise to {amount} chips.__")
            await self.manager.user_raise(amount)
