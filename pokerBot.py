import discord
from discord.ui import View, InputText
from discord import Interaction, ButtonStyle
from poker import HeadsUpPoker
from card_display import get_cards
import GPTplayer


async def play_poker_round(ctx, pokerGame: HeadsUpPoker, timeout: float):
    pokerGame.new_round()
    await pre_flop(ctx, pokerGame, timeout)

async def pre_flop(ctx, pokerGame: HeadsUpPoker, timeout: float):
    pokerGame.round = "preFlop"
    pokerGame.reset_betting()
    await ctx.send("**Your Cards:**")
    await ctx.send(get_cards(pokerGame.players[0].return_hand(), pokerGame.small_cards))
    print(pokerGame.players[0].player_name, pokerGame.players[0].return_hand(), pokerGame.players[1].return_hand())
    if pokerGame.small_cards == True:
        print("small cards")
    if pokerGame.button == 0:
        # Player can't cover small blind
        if pokerGame.players[0].stack < pokerGame.small_blind:
            await ctx.send(f"{pokerGame.players[0].player_name} can not cover small blind and is __All-in for {pokerGame.players[0].stack} chips.__")
            pokerGame.player_raise(0, pokerGame.players[0].stack)
            pokerGame.player_call(1)
            return
        
        # ChatGPT can't cover big blind
        if pokerGame.players[1].stack < pokerGame.big_blind:
            await ctx.send(f"{pokerGame.players[0].player_name} places small blind of {pokerGame.small_blind} chips.")
            await ctx.send(f"ChatGPT is __All-in for {pokerGame.players[1].stack} chips.__")
            pokerGame.player_raise(0, pokerGame.small_blind)
            pokerGame.player_raise(1, pokerGame.players[1].stack)
            view = allInCallView(ctx, pokerGame, timeout)
            await ctx.send(f"What do you want to do? You are in for {pokerGame.players[0].round_pot_commitment} chips, it costs {pokerGame.players[1].round_pot_commitment - pokerGame.players[0].round_pot_commitment} more to call.", view=view)
            return
        
        # Player can cover small blind but not big blind
        if pokerGame.players[0].stack < pokerGame.big_blind:
            await ctx.send(f"ChatGPT places big blind of {pokerGame.big_blind} chips, and {pokerGame.players[0].player_name} places small blind of {pokerGame.small_blind} chips.")
            pokerGame.player_raise(0, pokerGame.small_blind)
            pokerGame.player_raise(1, pokerGame.big_blind)
            view = allInCallView(ctx, pokerGame, timeout)
            await ctx.send(f"You have {pokerGame.players[0].stack} chips.")
            await ctx.send(f"What do you want to do? You are in for {pokerGame.players[0].round_pot_commitment}", view=view)
            return

        await ctx.send(f"ChatGPT places big blind of {pokerGame.big_blind} chips, and {pokerGame.players[0].player_name} places small blind of {pokerGame.small_blind} chips.")
        pokerGame.player_raise(0, pokerGame.small_blind)
        pokerGame.player_raise(1, pokerGame.big_blind)
        
        view = callView(ctx, pokerGame, timeout)
        await ctx.send(f"You have {pokerGame.players[0].stack} chips.")
        await ctx.send(f"What do you want to do? You are in for {pokerGame.players[0].round_pot_commitment}", view=view)

    elif pokerGame.button == 1:
        # Check if ChatGPT can cover the small blind
        if pokerGame.players[1].stack < pokerGame.small_blind:
            await ctx.send(f"ChatGPT can not cover the small blind and is __All-in for {pokerGame.players[1].stack} chips.__")
            pokerGame.player_raise(1, pokerGame.players[1].stack)
            pokerGame.player_call(0)
            return

        # Check if the player can cover the big blind
        if pokerGame.players[0].stack < pokerGame.big_blind:
            await ctx.send(f"ChatGPT places the small blind of {pokerGame.small_blind} chips.")
            await ctx.send(f"{pokerGame.players[0].player_name} is __All-in for {pokerGame.players[0].stack} chips.__")
            pokerGame.player_raise(1, pokerGame.small_blind)
            pokerGame.player_raise(0, pokerGame.players[0].stack)
            pokerGame.player_call(1)
            await ctx.send("ChatGPT __Calls.__")
            return

        # Check if ChatGPT can cover the big blind but not the player
        if pokerGame.players[1].stack < pokerGame.big_blind:
            await ctx.send(f"{pokerGame.players[0].player_name} places the big blind of {pokerGame.big_blind} chips, and ChatGPT places the small blind of {pokerGame.small_blind} chips.")
            pokerGame.player_raise(1, pokerGame.small_blind)
            pokerGame.player_raise(0, pokerGame.big_blind)
            await ctx.send(f"{pokerGame.players[0].player_name} is __All-in for {pokerGame.players[0].stack + pokerGame.players[0].round_pot_commitment} chips.__")
            view = allInCallView(ctx, pokerGame, timeout)
            await ctx.send(f"What do you want to do? You are in for {pokerGame.players[0].round_pot_commitment} chips, and it will cost you {pokerGame.players[1].round_pot_commitment - pokerGame.players[0].round_pot_commitment} more chips to call.", view=view)
            return
   

        await ctx.send(f"{pokerGame.players[0].player_name} places big blind of {pokerGame.big_blind} chips, and ChatGPT places small blind of {pokerGame.small_blind} chips.")
        pokerGame.player_raise(1, pokerGame.small_blind)
        pokerGame.player_raise(0, pokerGame.big_blind)

        GPTmove = GPTplayer.pre_flop_small_blind(pokerGame)

        if GPTmove == "Call":
            await ctx.send("ChatGPT __Calls.__")
            pokerGame.player_call(1)
            await next_action(ctx, pokerGame, timeout)
        elif GPTmove == "All-in":
            await chatGPT_all_in(ctx, pokerGame, timeout)
        elif GPTmove == "Fold":
            await fold_player(ctx, pokerGame, timeout, 1)
        elif isinstance(GPTmove, list):
            await chatGPT_raise(ctx, pokerGame, timeout, GPTmove[1])
        else:
            print(GPTmove)
            raise Exception("pokerGPT outputted an invalid move")

async def deal_community_cards(ctx, pokerGame: HeadsUpPoker, round_name: str, timeout: float):
    # Set the current round and deal the community cards
    pokerGame.round = round_name
    pokerGame.reset_betting()
    if round_name == "flop":
        pokerGame.deal_board(3)
    elif round_name == "turn":
        pokerGame.deal_board(4)
    elif round_name == "river":
        pokerGame.deal_board(5)
        
    # Announce the community cards
    await ctx.send(f"**Community Cards ({round_name.capitalize()}):**")
    await ctx.send(get_cards(pokerGame.board, pokerGame.small_cards))

    # Announce the current pot
    await ctx.send(f"**Main pot:** {pokerGame.current_pot} chips.")

    await ctx.send(f"**{pokerGame.players[0].player_name} stack:** {pokerGame.players[0].stack} chips.")
    await ctx.send(f"**ChatGPT stack:** {pokerGame.players[1].stack} chips.")

    
    # Determine who is first to act and prompt them for their move
    if pokerGame.button == 0:
        await chatGPT_first_to_act(ctx, pokerGame, timeout)
    elif pokerGame.button == 1:
        await player_first_to_act(ctx, pokerGame, timeout)


async def showdown(ctx, pokerGame: HeadsUpPoker, timeout: float):
    await ctx.send("***Showdown!!***")
    
    # Deal the community cards
    pokerGame.deal_board(5)
    
    # Display the community cards
    await ctx.send("**Community Cards:**")
    await ctx.send(get_cards(pokerGame.board, pokerGame.small_cards))
    
    pokerGame.evaluate_hands()
    
    # Display each player's hand and hand rank
    for player in pokerGame.players:
        await ctx.send(f"{player.player_name} has:")
        await ctx.send(get_cards(player.return_hand(), pokerGame.small_cards))
        
        await ctx.send(f"**{player.hand_rank}**")
        await ctx.send(get_cards(player.hand_played, pokerGame.small_cards))

    # Determine the winner(s) and handle the pot
    winner = pokerGame.determine_winner()
    if isinstance(winner, list):
        # Split pot
        await ctx.send("**Split pot!!!**")
        split_pot = pokerGame.current_pot // 2
        pokerGame.player_win(winner)
        await ctx.send(f"{pokerGame.players[0].player_name} wins {split_pot} chips and has {pokerGame.players[0].stack} chips.")
        await ctx.send(f"ChatGPT wins {split_pot} chips and has {pokerGame.players[1].stack} chips.")

    else:
        # Single winner
        pot = pokerGame.current_pot
        pokerGame.player_win(winner)
        await ctx.send(f"{winner.player_name} wins **{pot} chips** and has {winner.stack} chips.")
    
    # Check if either player is out of chips
    embed = discord.Embed(title="Results")
    embed.add_field(name="ChatGPT", value=str(pokerGame.players[1].stack))
    embed.add_field(name=ctx.author.name, value=str(pokerGame.players[0].stack))
    if pokerGame.players[0].stack == 0:
        await ctx.send(f"{pokerGame.players[1].player_name} wins the game! {pokerGame.players[0].player_name} is out of chips.", embeds=[embed])
    elif pokerGame.players[1].stack == 0:
        await ctx.send(f"{pokerGame.players[0].player_name} wins the game! {pokerGame.players[1].player_name} is out of chips.", embeds=[embed])
    else:
        # Prompt to play another round
        await ctx.respond("Play another round?")
        await ctx.send("", view=newRoundView(ctx, pokerGame, timeout))


async def player_first_to_act(ctx, pokerGame: HeadsUpPoker, timeout: float):
    view = checkView(ctx, pokerGame, timeout)
    await ctx.send(f"What do you want to do?", view=view)

async def chatGPT_first_to_act(ctx, pokerGame: HeadsUpPoker, timeout: float):      
    GPTmove = GPTplayer.first_to_act(pokerGame)
    if GPTmove == "Check":
        await ctx.send("ChatGPT __Checks.__")
        await next_action(ctx, pokerGame, timeout)
    elif GPTmove == "All-in":
        await chatGPT_all_in(ctx, pokerGame, timeout)
    elif isinstance(GPTmove, list):
        await chatGPT_raise(ctx, pokerGame, timeout, GPTmove[1])
    else:
        print(GPTmove)
        raise Exception("pokerGPT outputted an invalid move")

async def player_raise(ctx, pokerGame, timeout: float, amount: int):
    # Raise the player's bet
    pokerGame.player_raise(0, amount)

    # Get GPT's move and handle it
    GPTmove = GPTplayer.player_raise(pokerGame)
    if GPTmove == "Call":
        await ctx.send("ChatGPT __Calls Raise.__")
        pokerGame.player_call(1)
        await next_action(ctx, pokerGame, timeout)
    elif GPTmove == "All-in":
        await chatGPT_all_in(ctx, pokerGame, timeout)
    elif GPTmove == "Fold":
        await fold_player(ctx, pokerGame, timeout, 1)
    elif isinstance(GPTmove, list):
        await chatGPT_raise(ctx, pokerGame, timeout, GPTmove[1])
    else:
        print(GPTmove)
        raise Exception("pokerGPT outputted an invalid move")


async def chatGPT_raise(ctx, pokerGame: HeadsUpPoker, timeout: float, amount: int):
    # Raise the bet and announce it
    await ctx.send(f"ChatGPT __Raises to {amount} chips.__")
    pokerGame.player_raise(1, amount)
    await ctx.send(f"**Main pot:** {pokerGame.current_pot} chips")

    # Check if the player needs to go all-in
    if pokerGame.players[0].stack + pokerGame.players[0].round_pot_commitment <= pokerGame.current_bet:
        await ctx.send(f"ChatGPT puts you __All-In for {pokerGame.players[0].stack + pokerGame.players[0].round_pot_commitment} chips.__")
        view = allInCallView(ctx, pokerGame, timeout)
    else:
        view = callView(ctx, pokerGame, timeout)

    # Prompt the player for their action
    await ctx.send(f"What do you want to do? You are in for {pokerGame.players[0].round_pot_commitment} chips, it costs __{pokerGame.current_bet - pokerGame.players[0].round_pot_commitment} more to call.__", view=view)


async def player_all_in(ctx, pokerGame: HeadsUpPoker, timeout: float):
    pokerGame.player_all_in_raise(0)
    GPTmove = GPTplayer.player_all_in(pokerGame)
    if GPTmove == "Call":
        await ctx.send(f"ChatGPT __Calls All-in.__")
        pokerGame.player_call(1)
        await showdown(ctx, pokerGame, timeout)
    elif GPTmove == "Fold":
        await fold_player(ctx, pokerGame, timeout, 1)
    else:
        print(GPTmove)
        raise Exception("pokerGPT outputted an invalid move")


async def chatGPT_all_in(ctx, pokerGame: HeadsUpPoker, timeout: float):
    await ctx.send(f"ChatGPT is __All-in for {pokerGame.players[1].stack + pokerGame.players[1].round_pot_commitment} chips.__")
    pokerGame.player_all_in_raise(1)
    view = allInCallView(ctx, pokerGame, timeout)
    await ctx.send(f"What do you want to do? You are in for {pokerGame.players[0].round_pot_commitment} chips, it is {pokerGame.current_bet - pokerGame.players[0].round_pot_commitment} more to call", view=view)


async def next_betting_round(ctx, pokerGame: HeadsUpPoker, timeout: float):
    pokerGame.current_action = pokerGame.button
    if pokerGame.round == "preFlop":
        await deal_community_cards(ctx, pokerGame, "flop", timeout)
    elif pokerGame.round == "flop":
        await deal_community_cards(ctx, pokerGame, "turn", timeout)
    elif pokerGame.round == "turn":
        await deal_community_cards(ctx, pokerGame, "river", timeout)
    elif pokerGame.round == "river":
        await showdown(ctx, pokerGame, timeout)


async def next_action(ctx, pokerGame: HeadsUpPoker, timeout: float):
    pokerGame.current_action = (pokerGame.current_action + 1) % 2
    if pokerGame.round == "preFlop":
        if pokerGame.current_bet > pokerGame.big_blind:
            await next_betting_round(ctx, pokerGame, timeout)
            return
        if pokerGame.button == 0:
            GPTmove = GPTplayer.pre_flop_big_blind(pokerGame)
            if GPTmove == "Check":
                await ctx.send("ChatGPT __Checks.__")
                await next_betting_round(ctx, pokerGame, timeout)
                return
            elif GPTmove == "All-in":
                await chatGPT_all_in(ctx, pokerGame, timeout)
                return
            elif isinstance(GPTmove, list):
                await chatGPT_raise(ctx, pokerGame, timeout, GPTmove[1])
                return
            else:
                print(GPTmove)
                raise Exception("pokerGPT outputted an invalid move")
                
        if pokerGame.button == 1:
            if pokerGame.current_action == 0:
                view = checkView(ctx, pokerGame, timeout)
                await ctx.send(f"What do you want to do?", view=view)
                return
            elif pokerGame.current_action == 1:
                await next_betting_round(ctx, pokerGame, timeout)
    else:
        if pokerGame.current_bet > 0:
            await next_betting_round(ctx, pokerGame, timeout)
            return
        if pokerGame.button == 0:
            if pokerGame.current_action == 1:
                view = checkView(ctx, pokerGame, timeout)
                await ctx.send(f"What do you want to do?", view=view)
                return
            elif pokerGame.current_action == 0:
                await next_betting_round(ctx, pokerGame, timeout)
        elif pokerGame.button == 1:
            GPTmove = GPTplayer.player_check(pokerGame)
            if GPTmove == "Check":
                await ctx.send("ChatGPT __Checks.__")
                await next_betting_round(ctx, pokerGame, timeout)
                return
            elif GPTmove == "All-in":
                await chatGPT_all_in(ctx, pokerGame, timeout)
                return
            elif isinstance(GPTmove, list):
                await chatGPT_raise(ctx, pokerGame, timeout, GPTmove[1])
                return
            else:
                print(GPTmove)
                raise Exception("pokerGPT outputted an invalid move")


async def fold_player(ctx, pokerGame: HeadsUpPoker, timeout: float, player):
    if player == 0:
        await ctx.send(f"ChatGPT wins __{pokerGame.current_pot} chips.__")
        pokerGame.player_win(1)
        await ctx.send(f"You have {pokerGame.players[0].stack} chips.")
        await ctx.send(f"ChatGPT has {pokerGame.players[1].stack} chips.")
    elif player == 1:
        await ctx.send("ChatGPT Folds.")
        await ctx.send(f"You win __{pokerGame.current_pot} chips.__")
        pokerGame.player_win(0)
        await ctx.send(f"You have {pokerGame.players[0].stack} chips.")
        await ctx.send(f"ChatGPT has {pokerGame.players[1].stack} chips.")
    await ctx.respond("Play another round?")
    await ctx.send("", view=newRoundView(ctx, pokerGame, timeout))

class raiseModal(discord.ui.Modal):
    def __init__(self, title : str, ctx, pokerGame: HeadsUpPoker, timeout: float):
        super().__init__(title = title, timeout = timeout)
        self.ctx = ctx
        self.pokerGame = pokerGame
        self.timeout = timeout

        self.add_item(InputText(label="Amount",
                                value="",
                                placeholder="Enter amount"))

    async def callback(self, interaction: discord.Interaction):
        if self.children[0]:
            amount_raised = self.children[0].value
            if not amount_raised.isdigit(): # type: ignore
                await interaction.response.send_message("Please enter a valid number.")
                return
            amount_raised = int(amount_raised) # type: ignore
            if amount_raised == self.pokerGame.players[0].stack + self.pokerGame.players[0].round_pot_commitment:
                await interaction.response.send_message("You are __All-in.__")
                await player_all_in(self.ctx, self.pokerGame, self.timeout) # type: ignore
                return
            if amount_raised > self.pokerGame.players[0].stack + self.pokerGame.players[0].round_pot_commitment:
                await interaction.response.send_message("You do not have enough chips.")
                return
            if amount_raised < self.pokerGame.big_blind:
                await interaction.response.send_message("Raise must be at least the big blind.")
                return
            if amount_raised < 2 * self.pokerGame.current_bet:
                await interaction.response.send_message("You must raise to at least double the current bet.")
                return
            if amount_raised >= self.pokerGame.players[1].stack + self.pokerGame.players[1].round_pot_commitment:
                opponent_stack = self.pokerGame.players[1].stack + self.pokerGame.players[1].round_pot_commitment
                await interaction.response.edit_message(content=f"You put chat gpt __All-in for {opponent_stack} chips.__", view=None)
                await player_all_in(self.ctx, self.pokerGame, self.timeout) # type: ignore

            await interaction.response.edit_message(content=f"You __Raise to {amount_raised} chips.__", view=None)
            await player_raise(self.ctx, self.pokerGame, self.timeout, amount_raised) # type: ignore
        
class callView(View):
    def __init__(self, ctx, pokerGame: HeadsUpPoker, timeout: float):
        super().__init__(timeout=timeout)
        self.timeout = timeout
        self.responded = False
        self.pokerGame = pokerGame
        self.ctx = ctx

    async def on_timeout(self):
        if not self.responded:
            if self.message:
                await self.message.edit(content="You took too long! You __Fold.__", view=None)
            await fold_player(self.ctx, self.pokerGame, self.timeout, 0)
    
    async def check(self, interaction: discord.Interaction):
        if interaction.user:
            return interaction.user.id == self.ctx.author.id
    
    @discord.ui.button(label="Call", style=ButtonStyle.blurple)
    async def call_button_callback(self, button, interaction):
        if await self.check(interaction):
            self.responded = True
            self.pokerGame.player_call(0)
            if self.message:
                await self.message.edit(content="You __Call.__", view=None)
            await next_action(self.ctx, self.pokerGame, self.timeout)

    @discord.ui.button(label="Raise", style=ButtonStyle.green)
    async def raise_button_callback(self, button, interaction):
        if await self.check(interaction):
            self.responded = True
            await interaction.response.send_modal(raiseModal(title="Raised", ctx=self.ctx, pokerGame=self.pokerGame, timeout=self.timeout))
    
    @discord.ui.button(label="All-in", style=ButtonStyle.green)
    async def all_in_button_callback(self, button, interaction):
        if await self.check(interaction):
            self.responded = True
            if self.message:
                await self.message.edit(content=f"You are __All In for {self.pokerGame.players[0].stack + self.pokerGame.players[0].round_pot_commitment} chips.__", view=None)
            await player_all_in(self.ctx, self.pokerGame, self.timeout) # type: ignore
            
    
    @discord.ui.button(label="Fold", style=ButtonStyle.red)
    async def fold_button_callback(self, button, interaction):
        if await self.check(interaction):
            self.responded = True
            if self.message:
                await self.message.edit(content="You __Fold.__", view=None)
            await fold_player(self.ctx, self.pokerGame, self.timeout, 0)
    
class checkView(View):
    def __init__(self, ctx, pokerGame: HeadsUpPoker, timeout: float):
        super().__init__(timeout=timeout)
        self.timeout = timeout
        self.responded = False
        self.pokerGame = pokerGame
        self.ctx = ctx

    async def on_timeout(self):
        if not self.responded:
            if self.message:
                await self.message.edit(content="You took too long! You __Check.__", view=None)
            await next_action(self.ctx, self.pokerGame, self.timeout)
        
    async def check(self, interaction: discord.Interaction):
        if interaction.user:
            return interaction.user.id == self.ctx.author.id
    
    @discord.ui.button(label="Check", style=ButtonStyle.blurple)
    async def call_button_callback(self, button, interaction):
        if await self.check(interaction):
            self.responded = True
            if self.message:
                await self.message.edit(content="You __Check.__", view=None)
            await next_action(self.ctx, self.pokerGame, self.timeout)

    @discord.ui.button(label="Raise", style=ButtonStyle.green)
    async def raise_button_callback(self, button, interaction):
        if await self.check(interaction):
            self.responded = True
            await interaction.response.send_modal(raiseModal(title="Raised", ctx=self.ctx, pokerGame=self.pokerGame, timeout=self.timeout))
    
    @discord.ui.button(label="All-in", style=ButtonStyle.green)
    async def all_in_button_callback(self, button, interaction):
        if await self.check(interaction):
            self.responded = True
            if self.message:
                await self.message.edit(content=f"You are __All-in for {self.pokerGame.players[0].stack + self.pokerGame.players[0].round_pot_commitment} chips.__", view=None)
            await player_all_in(self.ctx, self.pokerGame, self.timeout)

class allInCallView(View):
    def __init__(self, ctx, pokerGame: HeadsUpPoker, timeout: float):
        super().__init__(timeout=timeout)
        self.timeout = timeout
        self.responded = False
        self.pokerGame = pokerGame
        self.ctx = ctx

    async def on_timeout(self):
        if (self.responded == False):
            if self.message:
                await self.message.edit(content="You took too long! You __Fold__.", view=None)
            await fold_player(self.ctx, self.pokerGame, self.timeout, 0)
    
    async def check(self, interaction: discord.Interaction):
        if interaction.user:
            return interaction.user.id == self.ctx.author.id

    @discord.ui.button(label="Call All-in", style=ButtonStyle.blurple)
    async def call_button_callback(self, button, interaction):
        if await self.check(interaction):
            self.responded = True
            if self.message:
                await self.message.edit(content="You __Call the All-in.__", view=None)
            self.pokerGame.player_call(0)
            await showdown(self.ctx, self.pokerGame, self.timeout)
    
    @discord.ui.button(label="Fold", style=ButtonStyle.red)
    async def fold_button_callback(self, button, interaction):
        if await self.check(interaction):
            self.responded = True
            if self.message:
                await self.message.edit(content="You __Fold.__", view=None)
            await fold_player(self.ctx, self.pokerGame, self.timeout, 0)

class newRoundView(View):
    def __init__(self, ctx, pokerGame: HeadsUpPoker, timeout: float):
        super().__init__(timeout=timeout)
        self.timeout = timeout
        self.responded = False
        self.pokerGame = pokerGame
        self.ctx = ctx
    
    async def on_timeout(self):
        if (self.responded == False):
            embed = discord.Embed(title="Results")
            embed.add_field(name="ChatGPT", value=str(self.pokerGame.players[1].stack))
            embed.add_field(name=self.ctx.author.name, value=str(self.pokerGame.players[0].stack))
            if self.message: 
                await self.message.edit(content="*Game Ended*", view=None, embeds=[embed])

    async def check(self, interaction: Interaction):
        if interaction.user:
            return interaction.user.id == self.ctx.author.id

    @discord.ui.button(label="New Round", style=ButtonStyle.blurple)
    async def new_round_button_callback(self, button, interaction):
        if await self.check(interaction):
            self.responded = True
            if self.message:
                await self.message.edit(content="*Starting a new round.*", view=None)
            await play_poker_round(self.ctx, self.pokerGame, self.timeout)
        
    @discord.ui.button(label="End Game", style=ButtonStyle.red)
    async def end_game_button_callback(self, button, interaction):
        if await self.check(interaction):
            self.responded = True
            embed = discord.Embed(title="Results")
            embed.add_field(name="ChatGPT", value=str(self.pokerGame.players[1].stack))
            embed.add_field(name=self.ctx.author.name, value=str(self.pokerGame.players[0].stack))
            if self.message: 
                await self.message.edit(content="*Game Ended*", view=None, embeds=[embed])