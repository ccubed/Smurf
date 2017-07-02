import asyncio
import json
import aiomysql
import discord
from discord.ext import commands

startup_extensions = ['ffxiv', 'scheduler']

bot = commands.Bot(command_prefix=">>", description="Smurf is an MMORPG Guild/Raid management focused Discord bot.")
settings = json.load(open('settings.json', 'r'))


async def sql_setup(botto):
    botto.sql = await aiomysql.create_pool(
        host="192.168.1.110", port=3306,
        user=settings['sql']['user'],
        password=settings['sql']['pass'],
        db=settings['sql']['dbname'],
        loop=botto.loop
    )


@bot.command()
async def load(ctx, what: str):
    """Load a Module"""
    msg = await ctx.send("Loading {}...".format(what))
    try:
        bot.load_extension(what)
        await msg.edit(content="Loaded {}.".format(what))
    except ImportError as e:
        await msg.edit(content="Failed to load {}.".format(what))
    finally:
        await asyncio.sleep(3)
        await msg.delete()


@bot.command()
async def unload(ctx, what: str):
    """Unload Modules"""
    bot.unload_extension(what)
    await ctx.send("Unloaded {}".format(what))


@bot.command()
async def kill(ctx):
    """Kill the Bot"""
    bot.sql.close()
    await bot.sql.wait_closed()
    await bot.logout()


@bot.command()
async def status(ctx, what: str):
    """Set status"""
    await ctx.message.delete()
    if bot.is_ready():
        await bot.change_presence(game=discord.Game(name=what))


@bot.command()
async def whut(ctx, what: str):
    """eval some code"""
    try:
        result = eval(what, globals(), locals())
    except BaseException as e:
        await ctx.send("Encountered an Exception.")
    else:
        await ctx.send(result)


@bot.event
async def on_ready():
    pass


if __name__ == "__main__":
    for ext in startup_extensions:
        bot.load_extension(ext)

    bot.loop.run_until_complete(sql_setup(bot))

    bot.run(settings['token'])
