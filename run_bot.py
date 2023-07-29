import discord
from discord import Option
from discord.ui import View, Button
from game.poker import HeadsUpPokerGameHandeler
from bot.card_display import *
from config.config import TOKEN
from db.db_utils import DatabaseManager
from bot.pokerBotClass import DiscordPoker


bot = discord.Bot()

@bot.event
async def on_ready():
    print(f"I have logged in as {bot.user}")

@bot.event
async def on_guild_join(guild):
    print(f"The bot has been added to the server: {guild.name}")

@bot.event
async def on_guild_remove(guild):
    print(f"The bot has been kicked from the server: {guild.name}")


@bot.slash_command(name="info", description="Information about the bot")
async def name(ctx):
    print("info")
    view = View()
    view.add_item(Button(label="Add to Server", url="https://discord.com/oauth2/authorize?client_id=1102638957713432708&permissions=277025773568&scope=bot%20applications.commands"))
    view.add_item(Button(label="Heads Up Texas Hold'em Rules", style=discord.ButtonStyle.url, url="https://www.wikihow.com/Heads-Up-Poker"))
    view.add_item(Button(label="Source Code", style=discord.ButtonStyle.url, url="https://github.com/matteo-psnt/PokerGPT"))
    view.add_item(Button(label="Feedback and Suggestions", style=discord.ButtonStyle.url, url="https://forms.gle/Cbai6VHxZt4GrewS9"))
    view.add_item(Button(label="Help Server", style=discord.ButtonStyle.url, url="https://discord.gg/xEuzZQEr"))
    await ctx.respond("Hello, I am PokerGPT, a poker bot that plays poker against you using GPT-4.\nJust type `/play_poker` to start a game.", view=view)


@bot.slash_command(name="play_poker", description="Starts a game of Texas hold'em against chatGPT-3.5.")
async def play_poker(ctx, 
                     buy_in:        Option(int, name="buy-in", description="Set starting chips", default=1000, min_value=10, max_value=10000000), # type: ignore
                     small_blind:   Option(int, name="small-blind", description="Set small blind", default=5, min_value=1, max_vlaue=2500000), # type: ignore
                     big_blind:     Option(int, name="big-blind", description="Set big blind", default=10, min_value=2, max_value=5000000), # type: ignore
                     timeout:       Option(float, name="timeout", description="Set how amny seconds to make a move", default=30, min_value=5, max_value=180), # type: ignore
                     small_cards:   Option(bool, name="small-cards", description="Use small cards", default=False)): # type: ignore
    if (buy_in < 2 * big_blind):
        await ctx.respond("Buy-in must be at least twice the big blind.")
        return
    
    if (small_blind > big_blind):
        await ctx.respond("Small blind must be less than the big blind.")
        return
    
    if (buy_in < 2 * (big_blind)):
        await ctx.respond("Buy-in must be at least twice the big blind.")
        return

    await ctx.respond("Starting a game of poker against chatGPT.")
    await ctx.send(f"Both players start with {buy_in} chips.")
    await ctx.send(f"The small blind is {small_blind} chips and the big blind is {big_blind} chips.")
    pokerGame = HeadsUpPokerGameHandeler(buy_in, small_blind, big_blind, small_cards)
    pokerGame.players[0].player_name = ctx.author.name
    pokerGame.players[1].player_name = "ChatGPT"
    pokerGame.new_round()

    
    with DatabaseManager(ctx.author.id, ctx.author.name, ctx.guild.id, ctx.guild.name) as db:
        discordHandler = DiscordPoker(ctx, pokerGame, db, timeout)
        await discordHandler.play_round()

@bot.slash_command(name="card_print", description="prints the emoji for a card")
async def play_poker(ctx,
                        rank: Option(str, name="rank", description="The rannk of the card, use A,K,Q,J for face cards", default="A", choices=["A","K","Q","J","10","9","8","7","6","5","4","3","2"]),
                        suit: Option(str, name="suit", description="The suit of the card, use S,H,D,C for spades, hearts, diamonds, and clubs", default="S", choices=["S","H","D","C"])):
    print("card_print")
    rank = rank.upper()
    suit = suit.upper()
    if rank == "A":
        rank = Rank.ACE
    elif rank == "K":
        rank = Rank.KING
    elif rank == "Q":
        rank = Rank.QUEEN
    elif rank == "J":
        rank = Rank.JACK
    elif rank == "10":
        rank = Rank.TEN
    elif rank == "9":
        rank = Rank.NINE
    elif rank == "8":
        rank = Rank.EIGHT
    elif rank == "7":
        rank = Rank.SEVEN
    elif rank == "6":
        rank = Rank.SIX
    elif rank == "5":
        rank = Rank.FIVE
    elif rank == "4":
        rank = Rank.FOUR
    elif rank == "3":
        rank = Rank.THREE
    elif rank == "2":
        rank = Rank.TWO
    else:
        await ctx.respond("Invalid rank")
        return
    if suit == "S":
        suit = Suit.SPADES
    elif suit == "H":
        suit = Suit.HEARTS
    elif suit == "D":
        suit = Suit.DIAMONDS
    elif suit == "C":
        suit = Suit.CLUBS
    else:
        await ctx.respond("Invalid suit")
        return
    card = Card(rank, suit)
    await ctx.respond(get_cards([card], False))


bot.run(TOKEN)