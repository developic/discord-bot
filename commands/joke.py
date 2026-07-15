import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from ._utils import COLOR, check_allowed, fetch_json, warn


class Joke(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="joke", description="Get a random dark joke")
    @app_commands.allowed_installs(guilds=False, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def joke(self, interaction: discord.Interaction):
        if not await check_allowed(interaction):
            return
        await interaction.response.defer()

        async with aiohttp.ClientSession() as session:
            data = await fetch_json(session, "https://v2.jokeapi.dev/joke/Dark")

        if data is None or data.get("error"):
            await interaction.followup.send(embed=warn("Could not fetch a joke right now."))
            return

        if data["type"] == "single":
            text = data["joke"]
        else:
            text = f"{data['setup']}\n\n{data['delivery']}"

        await interaction.followup.send(embed=discord.Embed(description=text, color=COLOR))


async def setup(bot: commands.Bot):
    await bot.add_cog(Joke(bot))
