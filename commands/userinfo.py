import discord
from discord import app_commands
from discord.ext import commands

from ._utils import COLOR, check_allowed


class Userinfo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="userinfo", description="Get info about a user")
    @app_commands.allowed_installs(guilds=False, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(target="The user to get info about")
    async def userinfo(self, interaction: discord.Interaction, target: discord.User | None = None):
        if not await check_allowed(interaction):
            return
        target = target or interaction.user

        embed = discord.Embed(title="User Info", color=target.accent_color or COLOR)
        embed.set_thumbnail(url=target.display_avatar.url)

        embed.add_field(name="Username", value=target.name, inline=True)
        embed.add_field(name="Global Name", value=target.global_name or "None", inline=True)
        embed.add_field(name="Display Name", value=target.display_name, inline=True)
        embed.add_field(name="ID", value=target.id, inline=True)
        embed.add_field(name="Bot", value="Yes" if target.bot else "No", inline=True)
        embed.add_field(name="Created", value=discord.utils.format_dt(target.created_at, style="R"), inline=False)

        if target.banner:
            embed.set_image(url=target.banner.url)

        if isinstance(target, discord.Member) and interaction.guild:
            embed.add_field(name="Nickname", value=target.nick or "None", inline=True)
            embed.add_field(name="Joined", value=discord.utils.format_dt(target.joined_at, style="R"), inline=True)

            roles = [r.mention for r in target.roles if r != interaction.guild.default_role]
            if roles:
                embed.add_field(name=f"Roles ({len(roles)})", value=" ".join(roles), inline=False)

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Userinfo(bot))
