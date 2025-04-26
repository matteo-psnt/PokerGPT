import argparse
import datetime
import discord
from discord import Option
from discord.ui import Button, View
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from config.config import TOKEN, DEV_TOKEN, DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE
from config.log_config import logger
from db.db_utils import DatabaseManager
from game.poker import PokerGameManager
from bot.bot_poker_handler import DiscordPokerManager


def parse_args():
    parser = argparse.ArgumentParser(description="Run PokerGPT")
    parser.add_argument("--dev", action="store_true", help="Use development Discord token")
    parser.add_argument("--no-db", action="store_true", help="Disable database-dependent commands")
    return parser.parse_args()


def get_token(use_dev: bool):
    return DEV_TOKEN if use_dev and DEV_TOKEN else TOKEN


DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_DATABASE}"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine, expire_on_commit=False)

args = parse_args()
token = get_token(args.dev)
bot = discord.Bot()


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="/play_poker"))
    logger.info(f"Logged in as {bot.user}")
    print(f"Logged in as {bot.user}")


@bot.event
async def on_guild_join(guild):
    logger.info(f"Bot added to server: {guild.name}")


@bot.event
async def on_guild_remove(guild):
    logger.info(f"Bot removed from server: {guild.name}")


@bot.slash_command(name="info", description="Information about the bot")
async def info(ctx):
    logger.info(f"{ctx.author} requested info")
    view = View()
    # Buttons for info panel
    view.add_item(Button(
        label="Add to Server",
        url="https://discord.com/oauth2/authorize?client_id=1102638957713432708&permissions=277025773568&scope=bot%20applications.commands"
    ))
    view.add_item(Button(
        label="Heads-Up Poker Rules",
        style=discord.ButtonStyle.url,
        url="https://www.wikihow.com/Heads-Up-Poker"
    ))
    view.add_item(Button(
        label="Source Code",
        style=discord.ButtonStyle.url,
        url="https://github.com/matteo-psnt/PokerGPT"
    ))
    view.add_item(Button(
        label="Feedback & Suggestions",
        style=discord.ButtonStyle.url,
        url="https://forms.gle/Cbai6VHxZt4GrewS9"
    ))
    await ctx.respond(
        "Hello! I am PokerGPT — play Texas Hold'em vs. me with `/play_poker`.",
        view=view
    )


@bot.slash_command(name="play_poker", description="Start a heads-up Texas Hold'em game")
async def play_poker(
        ctx,
        small_blind: Option(int, description="Small blind amount", default=5, min_value=1), # type: ignore
        big_blind: Option(int, description="Big blind amount", default=10, min_value=1), # type: ignore
        small_cards: Option(bool, description="Use smaller card images", default=False) # type: ignore
):
    logger.info(f"{ctx.author} started game SB={small_blind} BB={big_blind}")
    if small_blind > big_blind:
        return await ctx.respond("Small blind must be less than big blind.")

    buy_in = 100 * big_blind
    await ctx.respond("Starting PokerGPT…")
    await ctx.send(f"Both players start with {buy_in} chips.")
    await ctx.send(f"The small blind is {small_blind} chips and the big blind is {big_blind} chips.")

    poker = PokerGameManager(buy_in, small_blind, big_blind)
    poker.set_player_name(0, ctx.author.name)
    poker.set_player_name(1, "PokerGPT")
    poker.new_round()

    session = Session()
    
    db_mgr = DatabaseManager(session, ctx.author.id, ctx.author.name, ctx.guild.id, ctx.guild.name)
    handler = DiscordPokerManager(ctx, poker, db_mgr, small_cards, timeout=45)
    
    await handler.play_round()


# Register leaderboard and stats commands only if DB is enabled
if not args.no_db:
    @bot.slash_command(name="player_leaderboard", description="Top 10 players by BB wins vs. PokerGPT")
    async def player_leaderboard(ctx):
        logger.info(f"{ctx.author} requested player leaderboard")
        session = Session()
        db_mgr = DatabaseManager(session, ctx.author.id, ctx.author.name, ctx.guild.id, ctx.guild.name)
        try:
            top = db_mgr.get_top_players()
            place = db_mgr.get_user_place()
            stats = db_mgr.get_user_stats_of_player()
            embed = discord.Embed(title="🏆 PokerGPT Leaderboard", color=discord.Color.blue())
            ranks = "\n".join(f"{i + 1}. **{u[0]}**" for i, u in enumerate(top))
            wins = "\n".join(f"{round(u[1])}" for u in top)
            embed.add_field(name="Player Rank", value=ranks, inline=True)
            embed.add_field(name="Big Blind Wins", value=wins, inline=True)
            if stats:
                suffix = "th" if 10 <= place % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(place % 10, "th")
                embed.add_field(
                    name="Your Stats",
                    value=f"Current Place: **{place}{suffix}**\nNet BB Wins: **{stats[3]:.1f}**",
                    inline=False
                )
            await ctx.respond(embed=embed)
        finally:
            db_mgr.close()


    @bot.slash_command(name="player_stats", description="Show stats for you or another player")
    async def player_stats(
            ctx,
            username: Option(str, description="Player username", default="self") # type: ignore
    ):
        logger.info(f"{ctx.author} requested stats for {username}")
        session = Session()
        db_mgr = DatabaseManager(session, ctx.author.id, ctx.author.name, ctx.guild.id, ctx.guild.name)
        try:
            if username == "self":
                row = db_mgr.get_user_stats_of_player()
                username = ctx.author.name
            else:
                row = db_mgr.get_user_stats_by_username(username)
            if not row:
                return await ctx.respond(f"No stats for {username}", ephemeral=True)

            hands = max(1, row[0])
            embed = discord.Embed(title=f"📊 Stats for {username}", color=discord.Color.green())
            embed.add_field(name="Hands Played", value=row[0])
            embed.add_field(name="Games Played", value=row[1])
            embed.add_field(name="Time Played", value=str(datetime.timedelta(seconds=row[2])))
            embed.add_field(name="Net BB Total", value=f"{row[3]:.1f}")
            embed.add_field(name="BB Wins/Losses", value=f"{row[4]:.1f} / {row[5]:.1f}")
            embed.add_field(name="Win/Loss/Draw", value=f"{row[6]} / {row[7]} / {row[8]}")
            embed.add_field(name="Win Rate", value=f"{row[6] / hands * 100:.1f}%")
            embed.add_field(name="Hi Win/Loss Streak", value=f"{row[9]} / {row[10]}")
            await ctx.respond(embed=embed)
        finally:
            db_mgr.close()


    @bot.slash_command(name="server_leaderboard", description="Top 10 servers by BB wins vs. PokerGPT")
    async def server_leaderboard(ctx):
        logger.info(f"{ctx.author} requested server leaderboard")
        session = Session()
        db_mgr = DatabaseManager(session, ctx.author.id, ctx.author.name, ctx.guild.id, ctx.guild.name)
        try:
            top = db_mgr.get_top_servers()
            place = db_mgr.get_server_place()
            stats = db_mgr.get_server_stats()
            embed = discord.Embed(title="🏆 PokerGPT Server Leaderboard", color=discord.Color.gold())
            ranks = "\n".join(f"{i + 1}. **{s[0]}**" for i, s in enumerate(top))
            wins = "\n".join(f"{round(s[1])}" for s in top)
            embed.add_field(name="Server Rank", value=ranks, inline=True)
            embed.add_field(name="Big Blind Wins", value=wins, inline=True)
            if stats:
                suffix = "th" if 10 <= place % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(place % 10, "th")
                embed.add_field(
                    name="Your Server",
                    value=f"Current Place: **{place}{suffix}**\nTotal BB Wins: **{stats[4]:.1f}**",
                    inline=False
                )
            await ctx.respond(embed=embed)
        finally:
            db_mgr.close()


    @bot.slash_command(name="server_stats", description="Show stats for this or another server")
    async def server_stats(
            ctx,
            server_name: Option(str, name="server_name", description="Server name", default="current server") # type: ignore
    ):
        logger.info(f"{ctx.author} requested server stats for {server_name}")
        session = Session()
        db_mgr = DatabaseManager(session, ctx.author.id, ctx.author.name, ctx.guild.id, ctx.guild.name)
        try:
            if server_name == "current server":
                row = db_mgr.get_server_stats()
                server_name = ctx.guild.name
            else:
                row = db_mgr.get_server_stats_by_name(server_name)
            if not row:
                return await ctx.respond(f"No stats for {server_name}", ephemeral=True)

            embed = discord.Embed(title=f"📊 Stats for {server_name}", color=discord.Color.purple())
            embed.add_field(name="Players", value=row[0])
            embed.add_field(name="Hands Played", value=row[1])
            embed.add_field(name="Time Played", value=str(datetime.timedelta(seconds=row[2])))
            embed.add_field(name="Net BB Total", value=f"{row[3]:.1f}")
            embed.add_field(name="BB Wins/Losses", value=f"{row[4]:.1f} / {row[5]:.1f}")
            embed.add_field(name="Win/Loss/Draw", value=f"{row[6]} / {row[7]} / {row[8]}")
            await ctx.respond(embed=embed)
        finally:
            db_mgr.close()

if __name__ == "__main__":
    bot.run(token)
