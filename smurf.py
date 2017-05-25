import json
import aiomysql
import discord
from discord.ext import commands

startup_extensions = ['ffxiv']

bot = commands.Bot(command_prefix=">>", description="Smurf is an MMORPG Guild/Raid management focused Discord bot.")
settings = json.load(open('settings.json', 'r'))

async def sql_setup(bot):
    bot.sql = await aiomysql.create_pool(
        host="localhost", port=3306,
        user=settings['sql']['user'],
        password=settings['sql']['pass'],
        db=settings['sql']['dbname'],
        loop=bot.loop
    )

@bot.command()
async def load(ctx, what: str):
    """Load a Module"""
    await ctx.message.edit(content="Loading {}...".format(what))
    try:
        bot.load_extension(what)
        await ctx.message.edit(content="Loaded {}.".format(what))
    except ImportError as e:
        await ctx.message.delete()


@bot.command()
async def unload(ctx, what: str):
    """Unload Modules"""
    bot.unload_extension(what)
    await ctx.message.delete()


@bot.command()
async def kill(ctx):
    """Kill the Bot"""
    await ctx.message.delete()
    await bot.logout()


@bot.command()
async def status(ctx, what: str):
    """Set status"""
    await ctx.message.delete()
    if bot.is_ready():
        await bot.change_presence(game=discord.Game(name=what))


@bot.event
async def on_ready():
    print("Bot Ready to process commands\nLogged in as: {}".format(bot.user.name))


if __name__ == "__main__":
    for ext in startup_extensions:
        bot.load_extension(ext)
        
    bot.loop.run_until_complete(sql_setup(bot))

    bot.run("")
