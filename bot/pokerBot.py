import discord
from discord.ui import View, InputText
from discord import Interaction, ButtonStyle
from game.poker import PokerGameManager
from bot.card_display import get_cards
from db.db_utils import DatabaseManager
from bot.GPTplayer import gptPlayer


class DiscordPokerManager:
    def __init__(self, ctx, pokerGame: PokerGameManager, db: DatabaseManager, timeout: float):
        self.ctx = ctx
        self.pokerGame = pokerGame
        self.db = db
        self.timeout = timeout
        self.gptAction = gptPlayer()

    async def play_round(self):
        self.pokerGame.new_round()
        self.gptAction = gptPlayer()
        await self.pre_flop()

    async def pre_flop(self):
        self.pokerGame.round = "preFlop"
        self.pokerGame.reset_betting()
        await self.ctx.send("**Your Cards:**")
        await self.ctx.send(get_cards(self.pokerGame.players[0].return_hand(), self.pokerGame.small_cards))
        print(self.pokerGame.players[0].player_name, self.pokerGame.players[0].return_hand(), self.pokerGame.players[1].return_hand())
        if self.pokerGame.small_cards == True:
            print("small cards")
        if self.pokerGame.button == 0:
            # Player can't cover small blind
            if self.pokerGame.players[0].stack < self.pokerGame.small_blind:
                await self.ctx.send(f"{self.pokerGame.players[0].player_name} can not cover small blind and is __All-in for {self.pokerGame.players[0].stack} chips.__")
                self.pokerGame.player_raise(0, self.pokerGame.players[0].stack)
                self.pokerGame.player_call(1)
                return
            
            # ChatGPT can't cover big blind
            if self.pokerGame.players[1].stack < self.pokerGame.big_blind:
                await self.ctx.send(f"{self.pokerGame.players[0].player_name} places small blind of {self.pokerGame.small_blind} chips.")
                await self.ctx.send(f"ChatGPT is __All-in for {self.pokerGame.players[1].stack} chips.__")
                self.pokerGame.player_raise(0, self.pokerGame.small_blind)
                self.pokerGame.player_raise(1, self.pokerGame.players[1].stack)
                view = self.allInCallView(self)
                await self.ctx.send(f"What do you want to do? You are in for {self.pokerGame.players[0].round_pot_commitment} chips, it costs {self.pokerGame.players[1].round_pot_commitment - self.pokerGame.players[0].round_pot_commitment} more to call.", view=view)
                return
            
            # Player can cover small blind but not big blind
            if self.pokerGame.players[0].stack < self.pokerGame.big_blind:
                await self.ctx.send(f"ChatGPT places big blind of {self.pokerGame.big_blind} chips, and {self.pokerGame.players[0].player_name} places small blind of {self.pokerGame.small_blind} chips.")
                self.pokerGame.player_raise(0, self.pokerGame.small_blind)
                self.pokerGame.player_raise(1, self.pokerGame.big_blind)
                view = self.allInCallView(self)
                await self.ctx.send(f"You have {self.pokerGame.players[0].stack} chips.")
                await self.ctx.send(f"What do you want to do? You are in for {self.pokerGame.players[0].round_pot_commitment}", view=view)
                return

            # Regular scenario, both players can cover blinds
            await self.ctx.send(f"ChatGPT places big blind of {self.pokerGame.big_blind} chips, and {self.pokerGame.players[0].player_name} places small blind of {self.pokerGame.small_blind} chips.")
            self.pokerGame.player_raise(0, self.pokerGame.small_blind)
            self.pokerGame.player_raise(1, self.pokerGame.big_blind)
            
            view = self.callView(self)
            await self.ctx.send(f"You have {self.pokerGame.players[0].stack} chips.")
            await self.ctx.send(f"What do you want to do? You are in for {self.pokerGame.players[0].round_pot_commitment}", view=view)

        elif self.pokerGame.button == 1:
            # Check if ChatGPT can cover the small blind
            if self.pokerGame.players[1].stack < self.pokerGame.small_blind:
                await self.ctx.send(f"ChatGPT can not cover the small blind and is __All-in for {self.pokerGame.players[1].stack} chips.__")
                self.pokerGame.player_raise(1, self.pokerGame.players[1].stack)
                self.pokerGame.player_call(0)
                return

            # Check if the player can cover the big blind
            if self.pokerGame.players[0].stack < self.pokerGame.big_blind:
                await self.ctx.send(f"ChatGPT places the small blind of {self.pokerGame.small_blind} chips.")
                await self.ctx.send(f"{self.pokerGame.players[0].player_name} is __All-in for {self.pokerGame.players[0].stack} chips.__")
                self.pokerGame.player_raise(1, self.pokerGame.small_blind)
                self.pokerGame.player_raise(0, self.pokerGame.players[0].stack)
                self.pokerGame.player_call(1)
                await self.ctx.send("ChatGPT __Calls.__")
                return

            # Check if ChatGPT can cover the big blind but not the player
            if self.pokerGame.players[1].stack < self.pokerGame.big_blind:
                await self.ctx.send(f"{self.pokerGame.players[0].player_name} places the big blind of {self.pokerGame.big_blind} chips, and ChatGPT places the small blind of {self.pokerGame.small_blind} chips.")
                self.pokerGame.player_raise(1, self.pokerGame.small_blind)
                self.pokerGame.player_raise(0, self.pokerGame.big_blind)
                await self.ctx.send(f"{self.pokerGame.players[0].player_name} is __All-in for {self.pokerGame.players[0].stack + self.pokerGame.players[0].round_pot_commitment} chips.__")
                view = self.allInCallView(self)
                await self.ctx.send(f"What do you want to do? You are in for {self.pokerGame.players[0].round_pot_commitment} chips, and it will cost you {self.pokerGame.players[1].round_pot_commitment - self.pokerGame.players[0].round_pot_commitment} more chips to call.", view=view)
                return
    
            # Regular scenario, both players can cover blinds
            await self.ctx.send(f"{self.pokerGame.players[0].player_name} places big blind of {self.pokerGame.big_blind} chips, and ChatGPT places small blind of {self.pokerGame.small_blind} chips.")
            self.pokerGame.player_raise(1, self.pokerGame.small_blind)
            self.pokerGame.player_raise(0, self.pokerGame.big_blind)

            action, raise_amount = self.gptAction.pre_flop_small_blind(self.pokerGame)

            if action == "Call":
                await self.ctx.send("ChatGPT __Calls.__")
                self.pokerGame.player_call(1)
                await self.next_action()
            elif action == "All-in":
                await self.chatGPT_all_in()
            elif action == "Fold":
                await self.fold_player(1)
            elif action == "Raise":
                await self.chatGPT_raise(raise_amount)
            else:
                print("Error move given:", action, raise_amount, ", doing Default move of: Fold")
                await self.fold_player(1)
                

    async def deal_community_cards(self, round_name: str):
        # Set the current round and deal the community cards
        self.pokerGame.round = round_name
        self.pokerGame.reset_betting()
        if round_name == "flop":
            self.pokerGame.deal_board(3)
        elif round_name == "turn":
            self.pokerGame.deal_board(4)
        elif round_name == "river":
            self.pokerGame.deal_board(5)
            
        # Announce the community cards
        await self.ctx.send(f"**Community Cards ({round_name.capitalize()}):**")
        await self.ctx.send(get_cards(self.pokerGame.board, self.pokerGame.small_cards))

        # Announce the current pot
        await self.ctx.send(f"**Main pot:** {self.pokerGame.current_pot} chips.")

        await self.ctx.send(f"**{self.pokerGame.players[0].player_name} stack:** {self.pokerGame.players[0].stack} chips.")
        await self.ctx.send(f"**ChatGPT stack:** {self.pokerGame.players[1].stack} chips.")

        
        # Determine who is first to act and prompt them for their move
        if self.pokerGame.button == 0:
            await self.chatGPT_acts_first()
        elif self.pokerGame.button == 1:
            await self.player_acts_first()

    async def showdown(self):
        await self.ctx.send("***Showdown!!***")
        self.pokerGame.round = "showdown"
        
        # Deal the community cards
        self.pokerGame.deal_board(5)
        
        # Display the community cards
        await self.ctx.send("**Community Cards:**")
        await self.ctx.send(get_cards(self.pokerGame.board, self.pokerGame.small_cards))
        
        self.pokerGame.evaluate_hands()
        
        # Display each player's hand and hand rank
        for player in self.pokerGame.players:
            await self.ctx.send(f"{player.player_name} has:")
            await self.ctx.send(get_cards(player.return_hand(), self.pokerGame.small_cards))
            
            await self.ctx.send(f"**{player.hand_rank}**")
            await self.ctx.send(get_cards(player.hand_played, self.pokerGame.small_cards))

        # Determine the winner(s) and handle the pot
        winner = self.pokerGame.determine_winner()
        if isinstance(winner, list):
            # Split pot
            await self.ctx.send("**Split pot!!!**")
            split_pot = self.pokerGame.current_pot // 2
            self.pokerGame.player_win(winner)
            await self.ctx.send(f"{self.pokerGame.players[0].player_name} wins {split_pot} chips and has {self.pokerGame.players[0].stack} chips.")
            await self.ctx.send(f"ChatGPT wins {split_pot} chips and has {self.pokerGame.players[1].stack} chips.")

        else:
            # Single winner
            pot = self.pokerGame.current_pot
            self.pokerGame.player_win(winner)
            await self.ctx.send(f"{winner.player_name} wins **{pot} chips** and has {winner.stack} chips.")
        
        # Check if either player is out of chips
        embed = discord.Embed(title="Results")
        embed.add_field(name="ChatGPT", value=str(self.pokerGame.players[1].stack))
        embed.add_field(name=self.ctx.author.name, value=str(self.pokerGame.players[0].stack))
        if self.pokerGame.players[0].stack == 0:
            await self.ctx.send(f"{self.pokerGame.players[1].player_name} wins the game! {self.pokerGame.players[0].player_name} is out of chips.", embeds=[embed])
        elif self.pokerGame.players[1].stack == 0:
            await self.ctx.send(f"{self.pokerGame.players[0].player_name} wins the game! {self.pokerGame.players[1].player_name} is out of chips.", embeds=[embed])
        else:
            # Prompt to play another round
            await self.ctx.respond("Play another round?")
            await self.ctx.send("", view=self.newRoundView(self))

    async def player_acts_first(self):
        view = self.checkView(self)
        await self.ctx.send(f"What do you want to do?", view=view)

    async def chatGPT_acts_first(self):
        action, raise_amount = self.gptAction.first_to_act(self.pokerGame)

        if action == "Check":
            await self.ctx.send("ChatGPT __Checks.__")
            await self.next_action()
        elif action == "All-in":
            await self.chatGPT_all_in()
        elif action == "Raise":
            await self.chatGPT_raise(raise_amount)
        else:
            print("Error move given:", action, raise_amount, ", doing Default move of: Check")
            await self.ctx.send("ChatGPT __Checks.__")
            await self.next_action()

    async def player_raise(self, amount: int):
        # Raise the player's bet
        self.pokerGame.player_raise(0, amount)

        # Get GPT's move and handle it
        action, raise_amount = self.gptAction.player_raise(self.pokerGame)

        if action == "Call":
            await self.ctx.send("ChatGPT __Calls Raise.__")
            self.pokerGame.player_call(1)
            await self.next_action()
        elif action == "Fold":
            await self.fold_player(1)
        elif action == "All-in":
            await self.chatGPT_all_in()
        elif action == "Raise":
            await self.chatGPT_raise(raise_amount)
        else:
            print("Error move given:", action, raise_amount, ", doing Default move of: Fold")
            await self.fold_player(1)


    async def chatGPT_raise(self, amount: int):
        # Raise the bet and announce it
        await self.ctx.send(f"ChatGPT __Raises to {amount} chips.__")
        self.pokerGame.player_raise(1, amount)
        await self.ctx.send(f"**Main pot:** {self.pokerGame.current_pot} chips")

        # Check if the player needs to go all-in
        if self.pokerGame.players[0].stack + self.pokerGame.players[0].round_pot_commitment <= self.pokerGame.current_bet:
            await self.ctx.send(f"ChatGPT puts you __All-In for {self.pokerGame.players[0].stack + self.pokerGame.players[0].round_pot_commitment} chips.__")
            view = self.allInCallView(self)
        else:
            view = self.callView(self)

        # Prompt the player for their action
        await self.ctx.send(f"What do you want to do? You are in for {self.pokerGame.players[0].round_pot_commitment} chips, it costs __{self.pokerGame.current_bet - self.pokerGame.players[0].round_pot_commitment} more to call.__", view=view)

    async def player_all_in(self):
        self.pokerGame.player_all_in_raise(0)
        action, raise_amount = self.gptAction.player_all_in(self.pokerGame)

        if action == "Call":
            await self.ctx.send(f"ChatGPT __Calls All-in.__")
            self.pokerGame.player_call(1)
            await self.showdown()
        elif action == "Fold":
            await self.fold_player(1)
        else:
            print("Error move given:", action, raise_amount, ", doing Default move of: Fold")
            await self.fold_player(1)

    async def chatGPT_all_in(self):
        await self.ctx.send(f"ChatGPT is __All-in for {self.pokerGame.players[1].stack + self.pokerGame.players[1].round_pot_commitment} chips.__")
        self.pokerGame.player_all_in_raise(1)
        view = self.allInCallView(self)
        await self.ctx.send(f"What do you want to do? You are in for {self.pokerGame.players[0].round_pot_commitment} chips, it is {self.pokerGame.current_bet - self.pokerGame.players[0].round_pot_commitment} more to call", view=view)

    async def move_to_next_betting_round(self):
        self.pokerGame.current_action = self.pokerGame.button
        if self.pokerGame.round == "preFlop":
            await self.deal_community_cards("flop")
        elif self.pokerGame.round == "flop":
            await self.deal_community_cards("turn")
        elif self.pokerGame.round == "turn":
            await self.deal_community_cards("river")
        elif self.pokerGame.round == "river":
            await self.showdown()

    async def next_action(self):
        self.pokerGame.current_action = (self.pokerGame.current_action + 1) % 2
        if self.pokerGame.round == "preFlop":
            if self.pokerGame.current_bet > self.pokerGame.big_blind:
                await self.move_to_next_betting_round()
                return
            if self.pokerGame.button == 0:
                action, raise_amount = self.gptAction.pre_flop_big_blind(self.pokerGame)
                if action == "Check":
                    await self.ctx.send("ChatGPT __Checks.__")
                    await self.move_to_next_betting_round()
                    return
                elif action == "All-in":
                    await self.chatGPT_all_in()
                    return
                elif action == "Raise":
                    await self.chatGPT_raise(raise_amount)
                    return
                else:
                    print("Error move given:", action, raise_amount, ", doing Default move of: Check")
                    await self.ctx.send("ChatGPT __Checks.__")
                    await self.move_to_next_betting_round()
                    return
                    
            if self.pokerGame.button == 1:
                if self.pokerGame.current_action == 0:
                    view = self.checkView(self)
                    await self.ctx.send(f"What do you want to do?", view=view)
                    return
                elif self.pokerGame.current_action == 1:
                    await self.move_to_next_betting_round()
        else:
            if self.pokerGame.current_bet > 0:
                await self.move_to_next_betting_round()
                return
            if self.pokerGame.button == 0:
                if self.pokerGame.current_action == 1:
                    view = self.checkView(self)
                    await self.ctx.send(f"What do you want to do?", view=view)
                    return
                elif self.pokerGame.current_action == 0:
                    await self.move_to_next_betting_round()
            elif self.pokerGame.button == 1:
                action, raise_amount = self.gptAction.player_check(self.pokerGame)

                if action == "Check":
                    await self.ctx.send("ChatGPT __Checks.__")
                    await self.move_to_next_betting_round()
                    return
                elif action == "All-in":
                    await self.chatGPT_all_in()
                    return
                elif action == "Raise":
                    await self.chatGPT_raise(raise_amount)
                    return
                else:
                    print("Error move given:", action, raise_amount, ", doing Default move of: Check")
                    await self.ctx.send("ChatGPT __Checks.__")
                    await self.move_to_next_betting_round()
                    return

    async def fold_player(self, player):
        if player == 0:
            await self.ctx.send(f"ChatGPT wins __{self.pokerGame.current_pot} chips.__")
            self.pokerGame.player_win(1)
            await self.ctx.send(f"You have {self.pokerGame.players[0].stack} chips.")
            await self.ctx.send(f"ChatGPT has {self.pokerGame.players[1].stack} chips.")
        elif player == 1:
            await self.ctx.send("ChatGPT Folds.")
            await self.ctx.send(f"You win __{self.pokerGame.current_pot} chips.__")
            self.pokerGame.player_win(0)
            await self.ctx.send(f"You have {self.pokerGame.players[0].stack} chips.")
            await self.ctx.send(f"ChatGPT has {self.pokerGame.players[1].stack} chips.")
        await self.ctx.respond("Play another round?")
        await self.ctx.send("", view=self.newRoundView(self))

    class raiseModal(discord.ui.Modal):
        def __init__(self, pokerManager):
            super().__init__(title = "Raise", timeout = pokerManager.timeout)
            self.ctx = pokerManager.ctx
            self.pokerGame = pokerManager.pokerGame
            self.db = pokerManager.db
            self.pokerManager = pokerManager

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
                    await self.pokerManager.player_all_in()
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
                    await self.pokerManager.player_all_in()

                await interaction.response.edit_message(content=f"You __Raise to {amount_raised} chips.__", view=None)
                await self.pokerManager.player_raise(amount_raised)
            
    class callView(View):
        def __init__(self, pokerManager):
            super().__init__(timeout=pokerManager.timeout)
            self.responded = False
            self.ctx = pokerManager.ctx
            self.pokerGame = pokerManager.pokerGame
            self.db = pokerManager.db
            self.pokerManager = pokerManager

        async def on_timeout(self):
            if not self.responded:
                if self.message:
                    await self.message.edit(content="You took too long! You __Fold.__", view=None)
                await self.pokerManager.fold_player(0)
        
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
                await self.pokerManager.next_action()

        @discord.ui.button(label="Raise", style=ButtonStyle.green)
        async def raise_button_callback(self, button, interaction):
            if await self.check(interaction):
                self.responded = True
                await interaction.response.send_modal(self.pokerManager.raiseModal(self.pokerManager))
        
        @discord.ui.button(label="All-in", style=ButtonStyle.green)
        async def all_in_button_callback(self, button, interaction):
            if await self.check(interaction):
                self.responded = True
                if self.message:
                    await self.message.edit(content=f"You are __All In for {self.pokerGame.players[0].stack + self.pokerGame.players[0].round_pot_commitment} chips.__", view=None)
                await self.pokerManager.player_all_in()
                
        
        @discord.ui.button(label="Fold", style=ButtonStyle.red)
        async def fold_button_callback(self, button, interaction):
            if await self.check(interaction):
                self.responded = True
                if self.message:
                    await self.message.edit(content="You __Fold.__", view=None)
                await self.pokerManager.fold_player(0)
        
    class checkView(View):
        def __init__(self, pokerManager):
            super().__init__(timeout=pokerManager.timeout)
            self.responded = False
            self.ctx = pokerManager.ctx
            self.pokerGame = pokerManager.pokerGame
            self.db = pokerManager.db
            self.pokerManager = pokerManager

        async def on_timeout(self):
            if not self.responded:
                if self.message:
                    await self.message.edit(content="You took too long! You __Check.__", view=None)
                await self.pokerManager.next_action()
            
        async def check(self, interaction: discord.Interaction):
            if interaction.user:
                return interaction.user.id == self.ctx.author.id
        
        @discord.ui.button(label="Check", style=ButtonStyle.blurple)
        async def call_button_callback(self, button, interaction):
            if await self.check(interaction):
                self.responded = True
                if self.message:
                    await self.message.edit(content="You __Check.__", view=None)
                await self.pokerManager.next_action()

        @discord.ui.button(label="Raise", style=ButtonStyle.green)
        async def raise_button_callback(self, button, interaction):
            if await self.check(interaction):
                self.responded = True
                await interaction.response.send_modal(self.pokerManager.raiseModal(self.pokerManager))
        
        @discord.ui.button(label="All-in", style=ButtonStyle.green)
        async def all_in_button_callback(self, button, interaction):
            if await self.check(interaction):
                self.responded = True
                if self.message:
                    await self.message.edit(content=f"You are __All-in for {self.pokerGame.players[0].stack + self.pokerGame.players[0].round_pot_commitment} chips.__", view=None)
                await self.pokerManager.player_all_in()

    class allInCallView(View):
        def __init__(self, pokerManager):
            super().__init__(timeout=pokerManager.timeout)
            self.responded = False
            self.ctx = pokerManager.ctx
            self.pokerGame = pokerManager.pokerGame
            self.db = pokerManager.db
            self.pokerManager = pokerManager

        async def on_timeout(self):
            if (self.responded == False):
                if self.message:
                    await self.message.edit(content="You took too long! You __Fold__.", view=None)
                await self.pokerManager.fold_player(0)
        
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
                await self.pokerManager.showdown()
        
        @discord.ui.button(label="Fold", style=ButtonStyle.red)
        async def fold_button_callback(self, button, interaction):
            if await self.check(interaction):
                self.responded = True
                if self.message:
                    await self.message.edit(content="You __Fold.__", view=None)
                await self.pokerManager.fold_player(0)

    class newRoundView(View):
        def __init__(self, pokerManager):
            super().__init__(timeout=pokerManager.timeout)
            self.responded = False
            self.ctx = pokerManager.ctx
            self.pokerGame = pokerManager.pokerGame
            self.db = pokerManager.db
            self.pokerManager = pokerManager
        
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
                await self.pokerManager.play_round()
            
        @discord.ui.button(label="End Game", style=ButtonStyle.red)
        async def end_game_button_callback(self, button, interaction):
            if await self.check(interaction):
                self.responded = True
                embed = discord.Embed(title="Results")
                embed.add_field(name="ChatGPT", value=str(self.pokerGame.players[1].stack))
                embed.add_field(name=self.ctx.author.name, value=str(self.pokerGame.players[0].stack))
                if self.message: 
                    await self.message.edit(content="*Game Ended*", view=None, embeds=[embed])