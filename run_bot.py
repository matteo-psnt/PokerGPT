import discord
from discord import Option
from discord.ui import View, Button
import datetime
from game.poker import PokerGameManager
from bot.card_display import *
from config.config import TOKEN
from db.db_utils import DatabaseManager
from bot.pokerBot import DiscordPokerManager

bot = discord.Bot()

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="/play_poker"))
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
    await ctx.respond("Hello, I am PokerGPT, a poker bot that plays poker against you using GPT-4.\nJust type `/play_poker` to start a game.", view=view)


@bot.slash_command(name="play_poker", description="Starts a game of Texas hold'em against ChatGPT.")
async def play_poker(ctx, 
                     small_blind:   Option(int, name="small-blind", description="Set small blind", default=5, min_value=1),
                     big_blind:     Option(int, name="big-blind", description="Set big blind", default=10, min_value=1),
                     small_cards:   Option(bool, name="small-cards", description="Use smaller card images", default=False)):
    
    if (small_blind > big_blind):
        await ctx.respond("Small blind must be less than the big blind.")
        return
    
    timeout = 45
    buy_in = 100 * big_blind
    
    await ctx.respond("Starting a game of poker against chatGPT.")
    await ctx.send(f"Both players start with {buy_in} chips.")
    await ctx.send(f"The small blind is {small_blind} chips and the big blind is {big_blind} chips.")
    pokerGame = PokerGameManager(buy_in, small_blind, big_blind)
    pokerGame.set_player_name(0, ctx.author.name)
    pokerGame.set_player_name(1, "chatGPT")
    pokerGame.new_round()
    
    db_manager = DatabaseManager(ctx.author.id, ctx.author.name, ctx.guild.id, ctx.guild.name)
    try:
        discordHandler = DiscordPokerManager(ctx, pokerGame, db_manager, small_cards, timeout, model_name="gpt-3.5-turbo", memory=False)
        await discordHandler.play_round()
    finally:
        db_manager.close


@bot.slash_command(name="player_leaderboard", description="Leaderbord of the top 10 players by total wins against PokerGPT.")
async def player_leaderboard(ctx):
    db_manager = DatabaseManager(ctx.author.id, ctx.author.name, ctx.guild.id, ctx.guild.name)
    try:
        top_players = db_manager.get_top_players()
        user_place = db_manager.get_user_place()
        user_stats = db_manager.get_user_stats_of_player()
        
        embed = discord.Embed(title="🏆 PokerGPT Leaderboard", color=discord.Color.blurple())
        
        # Add top players to the embed
        rank_text = ""
        bb_wins_text = ""
        for index, player in enumerate(top_players, start=1):
            rank_text += f"{index} **{player[0]}**\n"
            bb_wins_text += f"  {round(player[1])}\n"
        embed.add_field(name="Player Rank  ", value=rank_text, inline=True)
        embed.add_field(name="Big Blind Wins", value=bb_wins_text, inline=True)
        # Add user place and stats to the embed
        if user_stats:
            if 10 <= user_place % 100 <= 20:
                suffix = "th"
            else:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(user_place % 10, "th")
            embed.add_field(name="Your Stats", value=f"Current Place: **{user_place}{suffix}**\nNet BB Wins: **{user_stats[3]:.1f}**\n", inline=False)
        
        await ctx.respond(embed=embed)
    finally:
        db_manager.close


@bot.slash_command(name="player_stats", description="Get PokerGPT statistics about yourself or another player.")
async def player_stats(ctx,
                username: Option(str, name="username", description="Username of the player to get stats for", default="Yourself")):
    db_manager = DatabaseManager(ctx.author.id, ctx.author.name, ctx.guild.id, ctx.guild.name)
    try:
        if username == "Yourself":
            user_stats = db_manager.get_user_stats_of_player()
            username = ctx.author.name
        else:
            user_stats = db_manager.get_user_stats_by_username(username)
        
        if user_stats:
            embed = discord.Embed(title=f"📊 Stats for {username}", color=discord.Color.blue())
            
            hands = user_stats[0]
            if hands == 0:
                hands = 1
            
            embed.add_field(name="Total Hands Played", value=user_stats[0])
            embed.add_field(name="Total Games Played", value=user_stats[1])
            embed.add_field(name="Total Time Played", value=datetime.timedelta(seconds=user_stats[2]))
            embed.add_field(name="Big Blind Total", value=f"{user_stats[3]:.1f}")
            embed.add_field(name="Big Blind Wins", value=f"{user_stats[4]:.1f}")
            embed.add_field(name="Big Blind Losses", value=f"{user_stats[5]:.1f}")
            embed.add_field(name="Total Wins", value=user_stats[6])
            embed.add_field(name="Total Losses", value=user_stats[7])
            embed.add_field(name="Total Split Pots", value=user_stats[8])
            embed.add_field(name="Win Rate", value=f"{user_stats[6] / hands * 100:.1f}%")
            embed.add_field(name="Highest Win Streak", value=user_stats[9])
            embed.add_field(name="Highest Loss Streak", value=user_stats[10])

        else:
            embed = discord.Embed(title="🚫 Error", description=f"No stats found for {username}", color=discord.Color.red())
        
        await ctx.respond(embed=embed)
    finally:
        db_manager.close()


@bot.slash_command(name="server_leaderboard", description="Leaderbord of the top 10 servers by wins against PokerGPT.")
async def server_leaderboard(ctx):
    db_manager = DatabaseManager(ctx.author.id, ctx.author.name, ctx.guild.id, ctx.guild.name)
    try:
        top_servers = db_manager.get_top_servers()
        server_place = db_manager.get_server_place()
        server_stats = db_manager.get_server_stats()
        
        embed = discord.Embed(title="🏆 PokerGPT Server Leaderboard", color=discord.Color.gold())
        
        rank_text = ""
        bb_wins_text = ""
        for index, server in enumerate(top_servers, start=1):
            rank_text += f"{index} **{server[0]}**\n"
            bb_wins_text += f"  {round(server[1])}\n"
        embed.add_field(name="Server Rank  ", value=rank_text, inline=True)
        embed.add_field(name="Big Blind Wins", value=bb_wins_text, inline=True)        
        
        if server_stats:
            if 10 <= server_place % 100 <= 20:
                suffix = "th"
            else:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(server_place % 10, "th")
            embed.add_field(name="Your Server's Stats", value=f"Current Place: **{server_place}{suffix}**\nTotal BB Wins: **{server_stats[4]:.1f}**\n", inline=False)
    
        
        await ctx.respond(embed=embed)
    finally:
        db_manager.close()


@bot.slash_command(name="server_stats", description="Get PokerGPT statistics about a server.")
async def server_stats(ctx,
                       server_name: Option(str, name="server_name", description="Name of the server to get stats for", default="Your Server")):
    db_manager = DatabaseManager(ctx.author.id, ctx.author.name, ctx.guild.id, ctx.guild.name)
    try:
        if server_name == "Your Server":
            server_stats = db_manager.get_server_stats()
        else:
            server_stats = db_manager.get_server_stats_by_name(server_name)
        
        # total_players, total_hands, total_time_played, 
        # net_bb_total, net_bb_wins, net_bb_losses, 
        # total_wins, total_losses, total_draws
        
        if server_stats:
            embed = discord.Embed(title=f"📊 Stats for {server_name}", color=discord.Color.purple())
            embed.add_field(name="Total Players", value=server_stats[0])
            embed.add_field(name="Total Hands Played", value=server_stats[1])
            embed.add_field(name="Net Time Played", value=datetime.timedelta(seconds=server_stats[2]))
            embed.add_field(name="Big Blind Total", value=f"{server_stats[3]:.1f}")
            embed.add_field(name="Big Blind Wins", value=f"{server_stats[4]:.1f}")
            embed.add_field(name="Big Blind Losses", value=f"{server_stats[5]:.1f}")
            embed.add_field(name="Total Wins", value=server_stats[6])
            embed.add_field(name="Total Losses", value=server_stats[7])
            embed.add_field(name="Total Dplit Pots", value=server_stats[8])
        else:
            embed = discord.Embed(title="🚫 Error", description=f"No stats found for {server_name}", color=discord.Color.red())
        
        await ctx.respond(embed=embed)
    finally:
        db_manager.close()


bot.run(TOKEN)