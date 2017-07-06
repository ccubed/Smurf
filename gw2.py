import json
import aiohttp
import discord
from discord.ext import commands


class Gw2():
    def __init__(self, bot):
        self.bot = bot
        self.roles = ['Mesmer', 'Guardian', 'Necromancer', 
                      'Ranger', 'Elementalist', 'Warrior', 
                      'Thief', 'Engineer', 'Revenant']
        self.parties = {'Raid': 10, 'Normal': 2, 'Aetherpath': 5, 'Crucible of Eternity': 4,
                        'Citadel of Flame': 5, 'Arah Story': 4}
