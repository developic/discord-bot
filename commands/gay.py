import random

import discord
from discord import app_commands
from discord.ext import commands

from ._utils import COLOR


class Gay(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="gay", description="Check how gay someone is")
    @app_commands.allowed_installs(guilds=False, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(target="The person to check")
    async def gay(self, interaction: discord.Interaction, target: discord.User | None = None):
        target = target or interaction.user
        percent = random.randint(0, 100)

        embed = discord.Embed(
            title="Gay Meter",
            description=f"**{target.mention}** is **{percent}%** gay.",
            color=COLOR,
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Gay(bot))
