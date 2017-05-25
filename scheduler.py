import asyncio
import discord
import pytz
from discord.ext import commands


class Scheduler():
    def __init__(self, bot):
        self.bot = bot
        self.games = {'FF14': bot.get_cog("ffxiv")}

    async def get_response(self, ctx, pm, destination):
        if pm:
            resp = await self.bot.wait_for('message',
                                           check=lambda m: m.author == ctx.author and isinstance(m, discord.DMChannel))
        else:
            resp = await self.bot.wait_for('message',
                                           check=lambda m: m.author == ctx.author and m.channel == destination)

        return resp

    @commands.group()
    async def raid(self, ctx):
        pass

    @raid.command()
    async def schedule(self, ctx, pm: bool = False):
        game, raid, party, date, time, timezone = None, None, None, None, None, None

        em = discord.Embed(description="Please enter the ID for the game you're playing.")
        em.title = 'Select Game'
        em.set_author(name=str(self.bot.user), icon_url=self.bot.user.avatar_url)
        em.add_field(name="FFXIV", value="ID: 0")
        await ctx.send(embed=em)

        resp = await self.get_response(ctx, pm, destination)

        if resp.content == '0':
            game = 'FF14'
            raid = None
            party = None
        else:
            await ctx.send("Invalid ID.")
            asyncio.sleep(3)
            return

        await ctx.send("What's the name of the dungeon, raid or activity you will be doing?")
        resp = await self.get_response(ctx, pm, destination)
        raid = resp.content

        em.clear_fields()
        em.title = "Select Party Type Required"
        em.description = "Enter the ID for the party type required for this activity."
        for idx, name in enumerate(self.games[game].parties.keys()):
            em.add_field(name=name, value="ID: {}".format(idx))
        await ctx.send(embed=em)
        resp = await self.get_response(ctx, pm, destination)

        try:
            int(resp.content)
        except ValueError:
            await ctx.send("That wasn't a valid number.")
            asyncio.sleep(3)
            return
        else:
            if int(resp.content) <= len(self.games[game].parties.keys()):
                party = int(resp.content)
            else:
                await ctx.send("That wasn't a valid ID.")
                asyncio.sleep(3)
                return

        await ctx.send("What date will this occur? Enter the date in the format MMDDYYYY.")
        resp = await self.get_response(ctx, pm, destination)

        if len(resp.content) != 8:
            await ctx.send("Date in wrong format.")
            asyncio.sleep(3)
            return

        date = (resp.content[:2], resp.content[2:4], resp.content[4:])

        await ctx.send("What time will this event happen? Please enter time in the format HHMM(AM/PM).")
        resp = await self.get_response(ctx, pm, destination)

        if len(resp.content) != 6:
            await ctx.send("Time in wrong format.")
            asyncio.sleep(3)
            return

        if resp.content[4:] == "PM":
            time = (int(resp.content[:2]) + 12, int(resp.content[2:4]))
        else:
            time = (int(resp.content[:2]), int(resp.content[2:4]))

        await ctx.send(
            "Please enter your timezone so times can be adjusted for others. You can enter a number (-5,+5,-430) or a name from the common list here {} or the list of all timezones here {}.".format(
                "<https://gist.github.com/ccubed/1a9d671ffefb2b0b3a1f4b7c098b2b69>",
                "<https://gist.github.com/ccubed/b30beb4515a65fc26fe82ba7dff23f2d>")
        )
        resp = await self.get_response(ctx, pm, destination)

        if resp.content[0] in ['+', '-']:
            timezone = resp.content
        else:
            if resp.content in pytz.all_timezones:
                timezone = datetime.datetime.utcoffset(pytz.timezone(resp.content))
                timezone = timezone.utcoffset().total_seconds() / 60 / 60
            else:
                await ctx.send("That was an invalid timezone name. Please see the list at {}.".format(
                    "<https://gist.github.com/ccubed/1a9d671ffefb2b0b3a1f4b7c098b2b69>")
                )
                asyncio.sleep(3)
                return
                
        async with self.bot.sql.acquire() as conn:
            async with conn.cursor() as cur:
                statement = "INSERT INTO Raids (guild_id, name, party_size, when, offset) VALUES (%s,%s,%s,%s,%s)"
                await cur.execute(statement, 
                (ctx.guild, raid, party, 
                "{}-{}-{} {}:{}:00".format(date[2], date[0], date[1], time[0], time[1]),
                timezone))
        
        # Event embed
            

    @raid.command()
    async def raids(self, ctx, full: bool = False):
        # display a list of raids, omitting full by default, for this server
        pass

    @raid.command()
    async def signup(self, ctx):

    # Display a list of raids

    # wait for response

    # ask for role

    # wait for response

    # verify role is valid for raid

    # sign them up

    # if raid is now full, notify participants raid is full

    @raid.command()
    async def remove(self, ctx):

    # Display a list of raids you made

    # wait for response

    # remove that raid, notify sign ups

    @raid.command()
    async def notice(self, ctx):

    # display a list of raids person is in

    # wait for response

    # Ask for message

    # wait for response

    # send message to participants

    @raid.command()
    async def withdraw(self, ctx):

# display list of raids person is in

# wait for response

# remove person from raid

# if raid is no longer full, notify participants raid is no longer full
