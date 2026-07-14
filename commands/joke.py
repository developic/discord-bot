import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from ._utils import COLOR, fetch_json, handle_api_error


class Joke(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="joke", description="Get a random dark joke")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def joke(self, ctx: commands.Context):
        async with aiohttp.ClientSession() as session:
            data = await fetch_json(session, "https://v2.jokeapi.dev/joke/Dark")

        if data is None or data.get("error"):
            await ctx.send(embed=warn("Could not fetch a joke right now."))
            return

        if data["type"] == "single":
            text = data["joke"]
        else:
            text = f"{data['setup']}\n\n{data['delivery']}"

        await ctx.send(embed=discord.Embed(description=text, color=COLOR))

    @joke.error
    async def joke_error(self, ctx, error):
        if not await handle_api_error(ctx, error, "Could not fetch a joke right now."):
            raise error


async def setup(bot: commands.Bot):
    await bot.add_cog(Joke(bot))
