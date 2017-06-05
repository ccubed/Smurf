import asyncio
import datetime
import discord
import pytz
from discord.ext import commands


class Scheduler:
    def __init__(self, bot):
        self.bot = bot
        self.games = {'FF14': bot.get_cog('Ffxiv')}
        print(self.games)

    async def get_response(self, ctx, destination):
        resp = await self.bot.wait_for('message',
                                       check=lambda m: m.author == ctx.author and m.channel == destination)
        return resp

    async def calc_offset(self, timestamp, timezone, ctx):
        offset = None
        async with self.bot.sql.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT timezone FROM Players WHERE id={}".format(ctx.author.id))
                if cur.rowcount:
                    offset = await cur.fetchone()[0]
                else:
                    await cur.execute("SELECT timezone FROM Guilds WHERE id={}".format(ctx.guild.id))
                    if cur.rowcount:
                        offset = await cur.fetchone()[0]
        if offset:
            # make our datetime objects
            initial = datetime.datetime(
                year=timestamp.year,
                month=timestamp.month,
                day=timestamp.day,
                hour=timestamp.hour,
                minute=timestamp.minute,
                tzinfo=datetime.timezone(datetime.timedelta(hours=timezone))
            )
            final = initial.astimezone(datetime.timezone(datetime.timedelta(hours=offset)))
            return "{}-{}-{} {}:{}:00 {}".format(final.year, final.month, final.day, final.hour, final.minute, final.tzinfo.tzname(None))
        else:
            return "{} {}".format(timestamp, datetime.timezone(datetime.timedelta(hours=timezone)).tzname(None))


    @commands.group(invoke_without_command=True)
    async def raid(self, ctx):
        results = None
        async with self.bot.sql.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM Raids WHERE guild_id={} ORDER BY game".format(ctx.guild.id))
                results = await cur.fetchall()

        game_list = set([x[2] for x in results])

        for game in game_list:
            async with ctx.channel.typing():
                rem = discord.Embed(title="{}".format(game), description="Raids and Events for your guild.")
                for raid in [x for x in results if x[2] == game]:
                    real_time = await self.calc_offset(raid[5], raid[6], ctx)
                    rem.add_field(
                        name=raid[3],
                        value="Party Size: {}\nScheduled: {}\nFull: {}".format(
                            list(self.games[game].parties.keys())[raid[4]],
                            real_time,
                            "Yes" if raid[7] else "No"
                        )
                    )
                await ctx.send(embed=rem)


    @raid.command()
    async def schedule(self, ctx):
        game, raid, party, date, time, timezone = None, None, None, None, None, None

        async with ctx.channel.typing():
            em = discord.Embed(description="Please enter the ID for the game you're playing.")
            em.title = 'Select Game'
            em.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
            em.add_field(name="FFXIV", value="ID: 0")
            await ctx.send(embed=em)

        resp = await self.get_response(ctx, ctx.channel)

        if resp.content == '0':
            game = 'FF14'
            raid = None
            party = None
        else:
            await ctx.send("Invalid ID.")
            return

        await ctx.send("What's the name of the dungeon, raid or activity you will be doing?")
        resp = await self.get_response(ctx, ctx.channel)
        raid = resp.content

        async with ctx.channel.typing():
            em.clear_fields()
            em.title = "Select Party Type Required"
            em.description = "Enter the ID for the party type required for this activity."
            for idx, name in enumerate(self.games[game].parties.keys()):
                em.add_field(name=name, value="ID: {}".format(idx))
            await ctx.send(embed=em)

        resp = await self.get_response(ctx, ctx.channel)

        try:
            int(resp.content)
        except ValueError:
            await ctx.send("That wasn't a valid number.")
            return
        else:
            if int(resp.content) <= len(self.games[game].parties.keys()):
                party = int(resp.content)
            else:
                await ctx.send("That wasn't a valid ID.")
                return

        await ctx.send("What date will this occur? Enter the date in the format MMDDYYYY.")
        resp = await self.get_response(ctx, ctx.channel)

        if len(resp.content) != 8:
            await ctx.send("Date in wrong format.")
            return

        date = (resp.content[:2], resp.content[2:4], resp.content[4:])

        await ctx.send("What time will this event happen? Please enter time in military format. IE: HHMM.\nEX: 1630, 2245")
        resp = await self.get_response(ctx, ctx.channel)

        if len(resp.content) != 4:
            await ctx.send("Time in wrong format.")
            return

        time = (int(resp.content[:2]), int(resp.content[2:]))

        await ctx.send(
            "Please enter your timezone so times can be adjusted for others. You can enter a number (-5,+5,-4.5) or a name from the common list here {} or the list of all timezones here {}.".format(
                "<https://gist.github.com/ccubed/1a9d671ffefb2b0b3a1f4b7c098b2b69>",
                "<https://gist.github.com/ccubed/b30beb4515a65fc26fe82ba7dff23f2d>")
        )
        resp = await self.get_response(ctx, ctx.channel)

        if resp.content[0] in ['+', '-']:
            timezone = resp.content
        else:
            if resp.content in pytz.all_timezones:
                timezone = datetime.datetime.now(pytz.timezone(resp.content))
                timezone = timezone.utcoffset().total_seconds() / 60 / 60
            else:
                await ctx.send("That was an invalid timezone name. Please see the list at {}.".format(
                    "<https://gist.github.com/ccubed/1a9d671ffefb2b0b3a1f4b7c098b2b69>")
                )
                asyncio.sleep(3)
                return

        async with ctx.channel.typing():
            timestamp = "{}-{}-{} {}:{}:00".format(date[2], date[0], date[1], time[0], time[1])

            async with self.bot.sql.acquire() as conn:
                async with conn.cursor() as cur:
                    statement = "INSERT INTO Raids (guild_id, game, raid, party_size, scheduled, timezone) VALUES ('{}', '{}','{}','{}','{}','{}')".format(
                        ctx.guild.id, game, raid, party, timestamp, timezone)
                    await cur.execute(statement)
                    await conn.commit()

            em.clear_fields()
            em.title = "Event Scheduled"
            em.description = "Event {} scheduled on {} for {} (UTC {})".format(
                raid, "{}/{}/{}".format(date[0], date[1], date[2]),
                "{}:{}{}".format(time[0] - 12 if time[0] > 12 else time[0], time[1], "PM" if time[0] > 12 else "AM"),
                timezone
            )
            await ctx.send(embed=em)

    @raid.command()
    async def signup(self, ctx):
        pass

    # Display a list of raids

    # wait for response

    # ask for role

    # wait for response

    # verify role is valid for raid

    # sign them up

    # if raid is now full, notify participants raid is full

    @raid.command()
    async def remove(self, ctx):
        pass

    # Display a list of raids you made

    # wait for response

    # remove that raid, notify sign ups

    @raid.command()
    async def notice(self, ctx):
        pass

    # display a list of raids person is in

    # wait for response

    # Ask for message

    # wait for response

    # send message to participants

    @raid.command()
    async def withdraw(self, ctx):
        pass

        # display list of raids person is in

        # wait for response

        # remove person from raid

        # if raid is no longer full, notify participants raid is no longer full


def setup(bot):
    bot.add_cog(Scheduler(bot))