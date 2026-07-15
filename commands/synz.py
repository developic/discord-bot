import discord
from discord import app_commands
from discord.ext import commands

from ._utils import COLOR, check_allowed, warn


class Synz(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="synz", description="Sync all slash commands")
    @app_commands.allowed_installs(guilds=False, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def synz(self, interaction: discord.Interaction):
        if not await check_allowed(interaction):
            return
        await interaction.response.defer(ephemeral=True)
        await self.bot.tree.sync()
        embed = discord.Embed(description="Synced all slash commands.", color=COLOR)
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Synz(bot))
