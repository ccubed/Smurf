import discord
from discord.ext import commands

class Roles():
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def gm(self, ctx):
        pass
