import discord
from discord import Option
from poker import HeadsUpPoker
from settings import TOKEN
import pokerBot

bot = discord.Bot()


@bot.event
async def on_ready():
    print(f"I have logged in as {bot.user}")

@bot.slash_command(name="ping", description="Replies with the bots ping.")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.respond(f"Pong!! {latency}ms :ping_pong:")

@bot.slash_command(name="play_poker", description="Starts a game of Texas hold'em against chatGPT-3.5.")
async def play_poker(ctx, 
                     buy_in:        Option(int, name="buy-in", description="Set starting chips", default=1000, min_value=10), # type: ignore
                     small_blind:   Option(int, name="small-blind", description="Set small blind", default=5, min_value=1), # type: ignore
                     big_blind:     Option(int, name="big-blind", description="Set big blind", default=10, min_value=2), # type: ignore
                     timeout:       Option(float, name="timeout", description="Set how amny seconds to make a move", default=30, min_value=5, max_value=180)): # type: ignore
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
    pokerGame = HeadsUpPoker(buy_in, small_blind, big_blind)

    pokerGame.players[0].player_name = ctx.author.name
    pokerGame.players[1].player_name = "ChatGPT"
    pokerGame.new_round()
    await pokerBot.play_poker_round(ctx, pokerGame, timeout)



bot.run(TOKEN)
