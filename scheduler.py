import discord
from discord.ext import commands

class Scheduler():
    def __init__(self, bot):
        self.bot = bot
        self.games = {'FF14': bot.get_cog("ffxiv")}

    async def get_response(self, ctx, pm, destination):
        if pm:
            resp = await self.bot.wait_for('message', check=lambda m:m.author == ctx.author and isinstance(m, discord.DMChannel))
        else:
            resp = await self.bot.wait_for('message', check=lambda m:m.author == ctx.author and m.channel == destination)

        return resp

    @commands.group()
    async def raid(self, ctx):
        pass

    @raid.command()
    async def schedule(self, ctx, pm: bool = False):
        game, raid, party, date, time, timezone = None

        if pm:
            destination = ctx.author
        else:
            destination = ctx.channel

        em = discord.Embed(description="Please enter the ID for the game you're playing.")
        em.title = 'Select Game'
        em.set_author(name=str(self.bot.user), icon_url=self.bot.user.avatar_url)
        em.add_field(name="FFXIV",value="ID: 0")
        msg = await destination.send(embed=em)

        resp = await self.get_response(ctx, pm, destination)

        if resp.content == '0':
            game = 'FF14'
            raid = None
            party = None
        else:
            await destination.send("Invalid ID.")
            return

        await destination.send("What's the name of the dungeon, raid or activity you will be doing?")
        resp = await self.get_response(ctx, pm, destination)
        raid = resp.content

        em.clear_fields()
        em.title = "Select Party Type Required"
        em.description = "Enter the ID for the party type required for this activity."
        for idx, name in enumerate(self.games[game].parties.keys()):
            em.add_field(name=name, value="ID: {}".format(idx))
        await destination.send(embed=em)
        resp = await self.get_response(ctx, pm, destination)

        try:
            int(resp.content)
        except ValueError:
            await destination.send("That wasn't a valid number.")
            return
        else:
            if int(resp.content) <= len(self.games[game].parties.keys()):
                party = list(self.games[game].parties.keys())[int(resp.content)]
            else:
                await destination.send("That wasn't a valid ID.")
                return

        await destination.send("What date will this occur? Enter the date in the format MMDDYYYY.")
        resp = await self.get_response(ctx, pm, destination)

        if len(resp.content) != 8:
            await destination.send("Date in wrong format.")
            return

        date = (resp.content[:2], resp.content[2:4], resp.content[4:])

        await destination.send("What time will this event happen? Please enter time in the format HHMM(AM/PM).")
        resp = await self.get_response(ctx, pm, destination)

        if len(resp.content) != 6:
            await destination.send("Time in wrong format.")
            return

        if resp.content[4:] == "PM":
            time = (int(test[:2])+12, int(test[2:4]))
        else:
            time = (int(test[:2]), int(test[2:4]))

        await destination.send("Please enter your timezone so times can be adjusted for others. You can enter a number (-5,+5,-430) or a name (EST,EDT,MST,JST).")
        resp = await self.get_response(ctx, pm, destination)

        if resp.content[0] in ['+', '-']:


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
