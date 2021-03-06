import asyncio
import datetime
import discord
import pytz
from discord.ext import commands


class Scheduler:
    def __init__(self, bot):
        self.bot = bot
        self.games = {'FF14': bot.get_cog('Ffxiv')}
        self.bot.loop.create_task(self.do_notifications())

    async def do_notifications(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            async with self.bot.sql.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "SELECT * FROM Raids WHERE DATE_ADD(UTC_TIMESTAMP(), INTERVAL 1 HOUR) > IF(timezone > 0, DATE_SUB(scheduled, INTERVAL timezone HOUR), DATE_ADD(scheduled, INTERVAL ABS(timezone) HOUR))")
                    if cur.rowcount:
                        results = await cur.fetchall()
                        for raid in results:
                            guild = self.bot.get_guild(raid[1])
                            await cur.execute("SELECT * FROM Signups WHERE raid_id = {}".format(raid[0]))
                            people = await cur.fetchall()
                            for person in people:
                                if not person[5]:
                                    await guild.get_member(person[0]).send(
                                        "You are signed up for {} in {} set for {} {}{}".format(raid[3], raid[2],
                                                                                                raid[5],
                                                                                                datetime.timezone(
                                                                                                    datetime.timedelta(
                                                                                                        hours=raid[
                                                                                                            6])).tzname(
                                                                                                    None),
                                                                                                "as a backup." if
                                                                                                person[3] else "."))
                                    await cur.execute(
                                        "UPDATE Signups SET reminded = 1 WHERE player_id = {} AND raid_id = {}".format(
                                            person[0], raid[0]))
                                    await conn.commit()
            await asyncio.sleep(600)

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
                    offset = await cur.fetchone()
                    offset = offset[0]
                else:
                    await cur.execute("SELECT timezone FROM Guilds WHERE id={}".format(ctx.guild.id))
                    if cur.rowcount:
                        offset = await cur.fetchone()
                        offset = offset[0]
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
            return "{}-{}-{} {}:{}:00 {}".format(final.year, final.month, final.day, final.hour, final.minute,
                                                 final.tzinfo.tzname(None))
        else:
            return "{} {}".format(timestamp, datetime.timezone(datetime.timedelta(hours=timezone)).tzname(None))

    async def check_full(self, ctx, raid_info):
        roles_needed = self.games[raid_info[2]].parties[
            sorted(list(self.games[raid_info[2]].parties.keys()))[raid_info[4]]]
        current_roles = []
        async with self.bot.sql.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT role FROM Signups WHERE raid_id = {}".format(raid_info[0]))
                if cur.rowcount:
                    current_roles = await cur.fetchall()

        for rname in roles_needed.keys():
            if len([x[0] for x in current_roles if x[0].lower() == rname]) < roles_needed[rname]:
                return

        async with self.bot.sql.acquire() as conn:
            async with conn.cursor() as cur:
                statement = "SELECT player_id, notify FROM Signups WHERE raid_id = {}".format(raid_info[0])
                await cur.execute(statement)
                people = await cur.fetchall()
                for person in people:
                    if not person[1]:
                        await ctx.guild.get_member(person[0]).send(
                            "This is a notice that a raid you had signed up for has a full party. Details follow.\n{} on {} {}".format(
                                raid_info[3], raid_info[5],
                                datetime.timezone(datetime.timedelta(hours=raid_info[6])).tzname(None)))
                        await cur.execute("UPDATE Signups SET notify = 1 WHERE player_id = {}".format(person[0]))
                        await conn.commit()
                if not raid_info[7]:
                    statement = "UPDATE Raids SET filled = 1 WHERE id = {}".format(raid_info[0])
                    await cur.execute(statement)
                    await conn.commit()

    @commands.group(invoke_without_command=True)
    async def raid(self, ctx, rid: int = None):
        """
        Display a list of currently scheduled raids for this guild.
        """
        if rid:
            async with self.bot.sql.acquire() as conn:
                async with conn.cursor() as cur:
                    raid, signups = None, None
                    await cur.execute("SELECT * FROM Raids WHERE guild_id={} and id={}".format(ctx.guild.id, rid))
                    if not cur.rowcount:
                        await ctx.send("No raid found for that ID.")
                        return
                    raid = await cur.fetchall()

                    await cur.execute("SELECT player_id, role, backup FROM Signups WHERE raid_id={}".format(rid))
                    if cur.rowcount:
                        signups = await cur.fetchall()

                    party_type = sorted(list(self.games[raid[0][2]].parties.keys()))[raid[0][4]]
                    em = discord.Embed(title=raid[0][3], description="Details for this raid in {} follow.".format(raid[0][2]))
                    em.add_field(name="Scheduled For", value="{} {}".format(raid[0][5], datetime.timezone(datetime.timedelta(hours=raid[0][6])).tzname(None)))
                    em.add_field(name="{} Party Needed".format(party_type),
                                 value=", ".join(
                                     ["{} {}".format(self.games[raid[0][2]].parties[party_type][x], x.upper()) for x in self.games[raid[0][2]].parties[party_type]]
                                 ))
                    if signups:
                        for role in set([x[1].lower() for x in signups]):
                            # Add primary
                            val = ""
                            for person in [x for x in signups if not x[2] and x[1].lower() == role]:
                                val += "{}\n".format(ctx.guild.get_member(person[0]).display_name)
                            em.add_field(name=role.upper(), value=val or "None")
                            # Add ZWSP
                            em.add_field(name="\u200b", value="\u200b")
                            # Add backups
                            val = ""
                            for person in [x for x in signups if x[2] and x[1].lower() == role]:
                                val += "{}\n".format(ctx.guild.get_member(person[0]).display_name)
                            em.add_field(name="Backup {}".format(role), value=val or "None")
                    else:
                        em.add_field(name="Signups", value="Currently there are no signups.")
                    await ctx.send(embed=em)
        else:
            results = None
            async with self.bot.sql.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT * FROM Raids WHERE guild_id={} ORDER BY game".format(ctx.guild.id))
                    results = await cur.fetchall()

            game_list = set([x[2] for x in results])

            if not game_list:
                await ctx.send("There are no raids scheduled for your guild.")
                return

            for game in game_list:
                async with ctx.channel.typing():
                    rem = discord.Embed(title="{}".format(game), description="Raids and Events for your guild.")
                    for raid in [x for x in results if x[2] == game]:
                        real_time = await self.calc_offset(raid[5], raid[6], ctx)
                        rem.add_field(
                            name=raid[3],
                            value="Party Size: {}\nScheduled: {}\nFull: {}\nSignup: >>raid signup {} <role>".format(
                                sorted(list(self.games[game].parties.keys()))[raid[4]],
                                real_time,
                                "Yes" if raid[7] else "No",
                                raid[0]
                            )
                        )
                    await ctx.send(embed=rem)

    @raid.command()
    async def tz(self, ctx, offset: str):
        """
        Set your  player's default timezone.
        :param offset: The offset as a name or number.
        If using a name, see <https://gist.github.com/ccubed/1a9d671ffefb2b0b3a1f4b7c098b2b69>.
        """
        try:
            timezone = float(offset)
        except ValueError:
            timezone = None

        if not timezone:
            if offset in pytz.all_timezones:
                timezone = datetime.datetime.now(pytz.timezone(offset))
                timezone = timezone.utcoffset().total_seconds() / 60 / 60
            else:
                await ctx.send(
                    "I couldn't parse that timezone. Make sure it's either a number or one of PyTZ's accepted timezones.")
                return

        async with self.bot.sql.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM Players WHERE id = {}".format(ctx.author.id))
                if cur.rowcount:
                    await cur.execute("UPDATE Players SET timezone = {} WHERE id = {}".format(timezone, ctx.author.id))
                    await conn.commit()
                else:
                    await cur.execute(
                        "INSERT INTO Players (id, timezone) VALUES ('{}', '{}')".format(ctx.author.id, timezone))
                    await conn.commit()

        await ctx.send("Set your timezone offset to {}".format(timezone))

    @raid.command()
    async def guildtz(self, ctx, offset: str):
        """
        Set your guild's default timezone.
        :param offset: The offset as a name or number.
        If using a name, see <https://gist.github.com/ccubed/1a9d671ffefb2b0b3a1f4b7c098b2b69>.
        """
        try:
            timezone = float(offset)
        except ValueError:
            timezone = None

        if not timezone:
            if offset in pytz.all_timezones:
                timezone = datetime.datetime.now(pytz.timezone(offset))
                timezone = timezone.utcoffset().total_seconds() / 60 / 60
            else:
                await ctx.send(
                    "I couldn't parse that timezone. Make sure it's either a number or one of PyTZ's accepted timezones.")
                return

        async with self.bot.sql.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM Guilds WHERE id = {}".format(ctx.guild.id))
                if cur.rowcount:
                    await cur.execute("UPDATE Guilds SET timezone = {} WHERE id = {}".format(timezone, ctx.guild.id))
                    await conn.commit()
                else:
                    await cur.execute(
                        "INSERT INTO Guilds (id, timezone) VALUES ('{}', '{}')".format(ctx.guild.id, timezone))
                    await conn.commit()

        await ctx.send("Set your guild's timezone offset to {}".format(timezone))

    @raid.command()
    async def schedule(self, ctx):
        """
        Schedule a new raid for this guild.
        """
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
            for idx, name in enumerate(sorted(list(self.games[game].parties.keys()))):
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

        await ctx.send(
            "What time will this event happen? Please enter time in military format. IE: HHMM.\nEX: 1630, 2245")
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
    async def signup(self, ctx, rid: int, role: str):
        """
        Signup for a raid that is currently scheduled in this guild.

        :param rid: The ID of the raid as given in >>raid
        :param role:  What role you'll fill in the raid
        """
        results = None
        async with self.bot.sql.acquire() as conn:
            async with conn.cursor() as cur:
                statement = "SELECT * FROM Raids WHERE id = {}".format(rid)
                await cur.execute(statement)
                if cur.rowcount:
                    results = await cur.fetchall()
                else:
                    await ctx.send("Couldn't find that raid.")
                    return

        async with self.bot.sql.acquire() as cur:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT * FROM Signups WHERE player_id = {} and raid_id = {}".format(ctx.author.id, rid))
                if cur.rowcount:
                    await ctx.send("You're already signed up for this raid. Did you mean to withdraw?")
                    return

        results = results[0]

        if role.lower() not in self.games[results[2]].roles:
            await ctx.send(
                "That was not a valid role. This game accepts: {}".format(",".join(self.games[results[2]].roles)))
            return

        current_roles = None
        async with self.bot.sql.acquire() as conn:
            async with conn.cursor() as cur:
                statement = "SELECT role FROM Signups WHERE raid_id = {}".format(rid)
                await cur.execute(statement)
                if cur.rowcount:
                    current_roles = await cur.fetchall()

        if current_roles:
            if (len([x[0] for x in current_roles if x[0].lower() == role.lower()]) + 1) <= \
                    self.games[results[2]].parties[sorted(list(self.games[results[2]].parties.keys()))[results[4]]][
                        role.lower()]:
                async with self.bot.sql.acquire() as conn:
                    async with conn.cursor() as cur:
                        statement = "INSERT INTO Signups (player_id, raid_id, role) VALUES ('{}', '{}', '{}')"
                        statement = statement.format(ctx.author.id, rid, role.lower())
                        await cur.execute(statement)
                        await conn.commit()
                        await ctx.send("Signed up {} for {} on {} {}".format(ctx.author.mention, results[3], results[5],
                                                                             datetime.timezone(datetime.timedelta(
                                                                                 hours=results[6])).tzname(None)))
            else:
                async with self.bot.sql.acquire() as conn:
                    async with conn.cursor() as cur:
                        statement = "INSERT INTO Signups (player_id, raid_id, role, backup) VALUES ('{}', '{}', '{}', '{}')"
                        statement = statement.format(ctx.author.id, rid, role.lower(), 1)
                        await cur.execute(statement)
                        await conn.commit()
                        await ctx.send(
                            "Signed up {} for {} on {} {} as a backup.".format(ctx.author.mention, results[3],
                                                                               results[5],
                                                                               datetime.timezone(datetime.timedelta(
                                                                                   hours=results[6])).tzname(None)))
        else:
            async with self.bot.sql.acquire() as conn:
                async with conn.cursor() as cur:
                    statement = "INSERT INTO Signups (player_id, raid_id, role) VALUES ('{}', '{}', '{}')"
                    statement = statement.format(ctx.author.id, rid, role.lower())
                    await cur.execute(statement)
                    await conn.commit()
                    await ctx.send("Signed up {} for {} on {} {}".format(ctx.author.mention, results[3], results[5],
                                                                         datetime.timezone(datetime.timedelta(
                                                                             hours=results[6])).tzname(None)))

        if current_roles:
            await self.check_full(ctx, results)

    @raid.command()
    async def withdraw(self, ctx):
        """
        Withdraw from a raid you have signed up for.
        """
        raids = []
        async with self.bot.sql.acquire() as conn:
            async with conn.cursor() as cur:
                statement = "SELECT raid_id FROM Signups WHERE player_id = {}".format(ctx.author.id)
                await cur.execute(statement)
                if not cur.rowcount:
                    await ctx.send("You haven't signed up for any raids or events.")
                    return
                raid_ids = await cur.fetchall()
                for rid in raid_ids:
                    await cur.execute("SELECT * FROM Raids WHERE id = {}".format(rid))
                    if cur.rowcount:
                        await raids.append(cur.fetchone())

        em = discord.Embed(description="Select a raid to withdraw from. To select type the ID number.")
        em.title = "Raid List"
        for raid in raids:
            em.add_field(name="ID: {}".format(raid[0]),
                         value="{} in {}\nScheduled for {} {}".format(raid[3], raid[2], raid[5], datetime.timezone(
                             datetime.timedelta(hours=raid[6])).tzname(None)))

        await ctx.send(embed=em)

        resp = await self.get_response(ctx, ctx.channel)

        raids = [x for x in raids if x[0] == int(resp.content)]
        if not raids:
            await ctx.send(
                "That doesn't seem to have matched the ID of a raid you signed up for. Make sure you are entering a number.")
            return

        print(raids)
        raids = raids[0]

        statement = "DELETE FROM Signups WHERE player_id = {} AND raid_id = {}".format(ctx.author.id, resp.content)
        await cur.execute(statement)
        await conn.commit()
        await ctx.send(
            "{} - Removed you from {} which was set to occur on {} {}".format(ctx.author.mention, raids[3], raids[5],
                                                                              datetime.timezone(datetime.timedelta(
                                                                                  hours=raids[6])).tzname(None)))

        if raids[7]:
            await self.check_full(ctx, raids)


def setup(bot):
    bot.add_cog(Scheduler(bot))
