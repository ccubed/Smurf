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
    async def craft(self, what: str):
        """
        Built in crafting helper. Given an item, will tell you what materials are needed to craft it.
        """
        pass

    @ff14.command()
    async def fc(self, name: str, server: str):
        """
        Set the name and server for the guild's FC.
        :param name: FC Name
        :param server: FC Server
        """
        pass


def setup(bot):
    bot.add_cog(Ffxiv(bot))
