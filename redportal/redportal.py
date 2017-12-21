from urllib.parse import quote
import discord
from discord.ext import commands
import aiohttp

from redbot.core.context import RedContext


numbs = {
    "next": "➡",
    "back": "⬅",
    "exit": "❌"
}


class Redportal:
    """Interact with cogs.red through your bot"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=['redp'])
    async def redportal(self, ctx: RedContext):
        """Interact with cogs.red through your bot"""

        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    async def _search_redportal(self, ctx: RedContext, url):
        # future response dict
        data = None

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={"User-Agent": "Sono-Bot"}) as response:
                    data = await response.json()
        except:
            return None

        if data is not None and not data['error'] and len(data['results']['list']) > 0:

            # a list of embeds
            embeds = []

            for cog in data['results']['list']:
                embed = discord.Embed(title=cog['name'],
                                      url='https://cogs.red{}'.format(cog['links']['self']),
                                      description=((cog['description'] and len(cog['description']) > 175 and '{}...'.format(cog['description'][:175])) or cog['description']) or cog['short'],
                                      color=0xfd0000)
                embed.add_field(name='Type', value=cog['repo']['type'], inline=True)
                embed.add_field(name='Author', value=cog['author']['name'], inline=True)
                embed.add_field(name='Repo', value=cog['repo']['name'], inline=True)
                embed.add_field(name='Command to add repo',
                                value='{}cog repo add {} {}'.format(ctx.prefix, cog['repo']['name'], cog['links']['github']['repo']),
                                inline=False)
                embed.add_field(name='Command to add cog',
                                value='{}cog install {} {}'.format(ctx.prefix, cog['repo']['name'], cog['name']),
                                inline=False)
                embed.set_footer(text='{}{}'.format('{} ⭐ - '.format(cog['votes']),
                                                    (len(cog['tags'] or []) > 0 and '🔖 {}'.format(', '.join(cog['tags']))) or 'No tags set 😢'
                                                    ))
                embeds.append(embed)

            return embeds

        else:
            return None

    @redportal.command()
    async def search(self, ctx: RedContext, *, term: str):
        """Searches for a cog"""

        # base url for the cogs.red search API
        base_url = 'https://cogs.red/api/v1/search/cogs'

         # final request url
        url = '{}/{}'.format(base_url, quote(term))

        embeds = await self._search_redportal(ctx, url)

        if embeds is not None:
            await self.cogs_menu(ctx, embeds, message=None, page=0, timeout=30)
        else:
            await ctx.send('No cogs were found or there was an error in the process')

    async def cogs_menu(self, ctx: RedContext, cog_list: list,
                        message: discord.Message=None,
                        page=0, timeout: int=30):
        """menu control logic for this taken from
           https://github.com/Lunar-Dust/Dusty-Cogs/blob/master/menu/menu.py"""
        cog = cog_list[page]
        expected = ["➡", "⬅", "❌"]

        if not message:
            message =\
                await ctx.send(embed=cog)
            await message.add_reaction("⬅")
            await message.add_reaction("❌")
            await message.add_reaction("➡")
        else:
            await message.edit(embed=cog)

        def react_check(reaction, user):
            return user == ctx.author \
                   and str(reaction.emoji) in expected
        try:
            react, _ = await self.bot.wait_for(
                "reaction_add", timeout=timeout, check=react_check
            )
        except:
            try:
                try:
                    await message.clear_reactions()
                except:
                    await message.remove_reaction("⬅", self.bot.user)
                    await message.remove_reaction("❌", self.bot.user)
                    await message.remove_reaction("➡", self.bot.user)
            except:
                pass
            return None
        reacts = {v: k for k, v in numbs.items()}
        react = reacts[react.emoji]
        if react == "next":
            page += 1
            next_page = page % len(cog_list)
            try:
                await message.remove_reaction("➡", ctx.author)
            except:
                pass
            return await self.cogs_menu(ctx, cog_list, message=message,
                                        page=next_page, timeout=timeout)
        elif react == "back":
            page -= 1
            next_page = page % len(cog_list)
            try:
                await message.remove_reaction("⬅", ctx.author)
            except:
                pass
            return await self.cogs_menu(ctx, cog_list, message=message,
                                        page=next_page, timeout=timeout)
        else:
            try:
                return await message.delete()
            except:
                pass
