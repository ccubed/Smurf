import discord
from discord.ext import commands

class Ffxiv():
    def __init__(self, bot):
        self.bot = bot
        self.parties = {'Light': {'DPS':2, 'TANK': 1, 'HEALER': 1}, 'Full': {'DPS': 4, 'TANK': 2, 'HEALER': 2}, 'Raid': {'DPS': 12, 'TANK': 6, 'HEALERS': 6}}
        
