import json
import aiohttp
import discord
from discord.ext import commands


class Ffxiv():
    def __init__(self, bot):
        self.bot = bot
        self.parties = {'Light': {'dps': 2, 'tank': 1, 'healer': 1}, 'Full': {'dps': 4, 'tank': 2, 'healer': 2},
                        'Raid': {'dps': 12, 'tank': 6, 'healer': 6}}
        self.roles = ['dps', 'tank', 'healer']

    async def build_recipe(self, ctx, r_url: str):
        async with ctx.channel.typing():
            with aiohttp.ClientSession() as session:
                async with session.get(r_url, headers={'User-Agent': 'Smurf (https://www.github.com/ccubed)'}) as response:
                    jsd = await response.json()

                    data = {'level': jsd['level_view'], 'class_name': jsd['class_name'],
                            'star_level': ':star:' * jsd['stars'] if jsd['stars'] else None, 'materials': {},
                            'additional_classes': []}

                    for item in jsd['tree']:
                        if item['name'] in data['materials']:
                            data['materials'][item['name']] += item['quantity']
                        else:
                            data['materials'][item['name']] = item['quantity']

                        if 'synths' in item:
                            if len(item['synths']) > 1:
                                clist = [(item['synths'][x]['class_name'], item['synths'][x]['level_view'],
                                          item['synths'][x]['stars'])
                                         for x in item['synths']]
                                em = discord.Embed(
                                    description="There are multiple ways to craft {} in the recipe you requested.".format(item['synths'][list(item['synths'].keys())[0]]['name']),
                                    title="Select a class to use. Type the class name to select.")
                                for cl in clist:
                                    em.add_field(name=cl[0],
                                                 value="Level {}{}".format(cl[1], " :star:" * cl[2] if cl[2] else ""))
                                await ctx.send(embed=em)
                                resp = await self.bot.wait_for('message',
                                                               check=lambda
                                                                   m: m.author == ctx.author and m.channel == ctx.channel)

                                if resp.content.lower() not in [x[0].lower() for x in clist]:
                                    await ctx.send(
                                        "That's not a valid class. Please make sure you enter the class name.\nEX: Alchemist")
                                    return

                                actual = [item['synths'][x] for x in item['synths'] if item['synths'][x]['class_name'].lower() == resp.content.lower()]
                                data['additional_classes'].append(
                                    "{} Lv.{}".format(actual[0]['class_name'], actual[0]['level_view']))
                                for items in actual[0]['tree']:
                                    if items['name'] in data['materials']:
                                        data['materials'][items['name']] += items['quantity']
                                    else:
                                        data['materials'][items['name']] = items['quantity']
                            else:
                                data['additional_classes'].append(
                                    "{} Lv.{}".format(item['synths'][list(item['synths'].keys())[0]]['class_name'],
                                                      item['synths'][list(item['synths'].keys())[0]]['level_view'])
                                )
                                for items in item['synths'][list(item['synths'].keys())[0]]['tree']:
                                    if items['name'] in data['materials']:
                                        data['materials'][items['name']] += items['quantity']
                                    else:
                                        data['materials'][items['name']] = items['quantity']

                    em = discord.Embed(description="{} Lv.{}{}\nAdd'l Classes: {}".format(data['class_name'], data['level'],
                                                                                          data['star_level'] if data['star_level'] else "",
                                                                                          ', '.join(data['additional_classes'])))
                    em.title = jsd['name']
                    em.set_image(url=jsd['icon'])

                    for material in data['materials']:
                        em.add_field(name=material, value=data['materials'][material])

                    await ctx.send(embed=em)

    @commands.group()
    async def ff14(self, ctx):
        """
        final fantasy 14 specific commands
        """
        pass

    @ff14.command()
    async def craft(self, ctx, what: str):
        """
        Built in crafting helper. Given an item, will tell you the sum total of all items required to craft it yourself including items required for intermediate crafting recipes.
        """
        with aiohttp.ClientSession() as session:
            async with session.get("https://api.xivdb.com/search",
                                   params={'string': what.replace(" ", "+"), 'one': 'recipes'},
                                   headers={'User-Agent': 'Smurf (https://www.github.com/ccubed)'}) as response:
                jsd = await response.json()

                if jsd['recipes']['total'] > 1:
                    async with ctx.channel.typing():
                        items = [(x['name'], x['class_name'], x['level_view'], x['id']) for x in jsd['recipes']['results']]
                        em = discord.Embed(description="There were multiple items in that search.", title="Select an item by typing the ID number")
                        for item in items:
                            em.add_field(name=item[0],
                                         value="ID: {}\nClass: {}\nLevel: {}".format(item[3], item[1], item[2]))
                        await ctx.send(embed=em)
                    resp = await self.bot.wait_for('message',
                                                   check=lambda m: m.author == ctx.author and m.channel == ctx.channel)

                    if int(resp.content) not in [x[3] for x in items]:
                        await ctx.send("You entered an invalid ID.")

                    for recipe in jsd['recipes']['results']:
                        if recipe['id'] == int(resp.content):
                            await self.build_recipe(ctx, recipe['url_api'])
                            return
                elif jsd['recipes']['total'] == 1:
                    await self.build_recipe(ctx, jsd['recipes']['results'][0]['url_api'])
                else:
                    await ctx.send("Couldn't find a recipe with that search term.")

    @ff14.command()
    async def fc(self, ctx, name: str, server: str):
        """
        Set the name and server for the guild's FC. Need administrator or manage server role.
        :param name: FC Name
        :param server: FC Server
        """
        if not any([ctx.author.permissions_in(ctx.channel).administrator, ctx.author.permissions_in(ctx.channel).manage_guild]):
            return

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
