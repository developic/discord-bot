import aiohttp
import discord
from discord import app_commands, ui
from discord.ext import commands

from ._utils import COLOR, check_allowed, fetch_json, warn


class QuoteLayout(ui.LayoutView):
    def __init__(self, text: str, author: str):
        super().__init__(timeout=120)

        container = ui.Container[
            "QuoteLayout"
        ](
            ui.TextDisplay(f"*{text}*\n\n— **{author}**"),
            accent_color=COLOR,
        )
        self.add_item(container)


class Quote(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="quote", description="Get a random quote")
    @app_commands.allowed_installs(guilds=False, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def quote(self, interaction: discord.Interaction):
        if not await check_allowed(interaction):
            return
        await interaction.response.defer()

        async with aiohttp.ClientSession() as session:
            data = await fetch_json(session, "https://zenquotes.io/api/random")

        if data is None or not isinstance(data, list):
            await interaction.followup.send(embed=warn("Could not fetch a quote right now."))
            return

        view = QuoteLayout(data[0]["q"], data[0]["a"])
        await interaction.followup.send(view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Quote(bot))
