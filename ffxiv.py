import json
import discord
from discord.ext import commands


class Ffxiv():
    def __init__(self, bot):
        self.bot = bot
        self.parties = {'Light': {'dps': 2, 'tank': 1, 'healer': 1}, 'Full': {'dps': 4, 'tank': 2, 'healer': 2},
                        'Raid': {'dps': 12, 'tank': 6, 'healer': 6}}
        self.roles = ['dps', 'tank', 'healer']

    @commands.group()
    async def ff14(self):
        pass

    @ff14.comamnd()
    async def craft(self, ctx, what: str):
        """
        Built in crafting helper. Given an item, will tell you what materials are needed to craft it.
        """
        pass

    @ff14.command()
    async def fc(self, ctx, name: str, server: str):
        """
        Set the name and server for the guild's FC.
        :param name: FC Name
        :param server: FC Server
        """
        jsd = {'name': name, 'server': server}
        jsd = json.dumps(jsd)

        async with self.bot.sql.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM Guilds WHERE id = {}".format(ctx.guild.id))
                if cur.rowcount:
                    await cur.execute("UPDATE Guilds SET ffxiv = '{}' WHERE id = {}".format(jsd, ctx.guild.id))
                    await conn.commit()
                else:
                    await cur.execute("INSERT INTO Guilds (id, ffxiv) VALUES ('{}', '{}')".format(ctx.guild.id, jsd))
                    await conn.commit()

        await ctx.send("Set your FC details.")


def setup(bot):
    bot.add_cog(Ffxiv(bot))
