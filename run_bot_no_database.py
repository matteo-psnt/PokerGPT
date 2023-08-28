import discord
from discord import Option
from discord.ui import Button, View
from bot.bot_poker_handler import DiscordPokerManager
from bot.card_display import *
from config.config import TOKEN
from config.log_config import logger
from db.db_utils import DatabaseManager
from game.poker import PokerGameManager

bot = discord.Bot()

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="/play_poker"))
    logger.info(f"I have logged in as {bot.user}")
    print(f"I have logged in as {bot.user}")

@bot.event
async def on_guild_join(guild):
    logger.info(f"The bot has been added to the server: {guild.name}")

@bot.event
async def on_guild_remove(guild):
    logger.info(f"The bot has been removed from the server: {guild.name}")

@bot.slash_command(name="info", description="Information about the bot")
async def name(ctx):
    logger.info(f"{ctx.author.name} requested bot info.")
    view = View()
    view.add_item(Button(label="Add to Server", url="https://discord.com/oauth2/authorize?client_id=1102638957713432708&permissions=277025773568&scope=bot%20applications.commands"))
    view.add_item(Button(label="Heads Up Texas Hold'em Rules", style=discord.ButtonStyle.url, url="https://www.wikihow.com/Heads-Up-Poker"))
    view.add_item(Button(label="Source Code", style=discord.ButtonStyle.url, url="https://github.com/matteo-psnt/PokerGPT"))
    view.add_item(Button(label="Feedback and Suggestions", style=discord.ButtonStyle.url, url="https://forms.gle/Cbai6VHxZt4GrewS9"))
    await ctx.respond("Hello, I am PokerGPT, a poker bot that plays poker against you using GPT-4.\nJust type `/play_poker` to start a game.", view=view)


@bot.slash_command(name="play_poker", description="Starts a game of Texas hold'em against chatGPT-3.5.")
async def play_poker(ctx, 
                     small_blind:   Option(int, name="small-blind", description="Set small blind", default=5, min_value=1),
                     big_blind:     Option(int, name="big-blind", description="Set big blind", default=10, min_value=1),
                     small_cards:   Option(bool, name="small-cards", description="Use smaller card images", default=False)):
    logger.info(f"{ctx.author.name} started a poker game with {small_blind} small blind and {big_blind} big blind")
    if small_cards:
        logger.info(f"{ctx.author.name} is using small cards")
    if (small_blind > big_blind):
        await ctx.respond("Small blind must be less than the big blind.")
        return
    
    timeout = 45
    buy_in = 100 * big_blind
    
    await ctx.respond("Starting a game of poker against PokerGPT.")
    await ctx.send(f"Both players start with {buy_in} chips.")
    await ctx.send(f"The small blind is {small_blind} chips and the big blind is {big_blind} chips.")
    pokerGame = PokerGameManager(buy_in, small_blind, big_blind)
    pokerGame.set_player_name(0, ctx.author.name)
    pokerGame.set_player_name(1, "PokerGPT")
    pokerGame.new_round()
    
    db_manager = DatabaseManager(ctx.author.id, ctx.author.name, ctx.guild.id, ctx.guild.name)
    try:
        discordHandler = DiscordPokerManager(ctx, pokerGame, db_manager, small_cards, timeout)
        await discordHandler.play_round()
    finally:
        db_manager.close
    

bot.run(TOKEN)