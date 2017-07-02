import discord
from discord.ext import commands

class Ffxiv():
    def __init__(self, bot):
        self.bot = bot
        self.parties = {'Light': {'dps': 2, 'tank': 1, 'healer': 1}, 'Full': {'dps': 4, 'tank': 2, 'healer': 2}, 'Raid': {'dps': 12, 'tank': 6, 'healer': 6}}
        self.roles = ['dps', 'tank', 'healer']
        
def setup(bot):
    bot.add_cog(Ffxiv(bot))