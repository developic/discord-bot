import discord
from discord import app_commands, ui
from discord.ext import commands

from ._utils import COLOR, check_allowed


class UserinfoLayout(ui.LayoutView):
    def __init__(self, target: discord.User | discord.Member, interaction: discord.Interaction):
        super().__init__()

        lines = [
            f"**Username:** {target.name}",
            f"**Global Name:** {target.global_name or 'None'}",
            f"**Display Name:** {target.display_name}",
            f"**ID:** `{target.id}`",
            f"**Bot:** {'Yes' if target.bot else 'No'}",
            f"**Created:** {discord.utils.format_dt(target.created_at, style='R')}",
        ]

        if isinstance(target, discord.Member) and interaction.guild:
            lines.append(f"**Nickname:** {target.nick or 'None'}")
            lines.append(f"**Joined:** {discord.utils.format_dt(target.joined_at, style='R')}")

        section = ui.Section(
            ui.TextDisplay(f"### who is {target.name}?"),
            ui.TextDisplay("\n".join(lines)),
            accessory=ui.Thumbnail(
                media=discord.UnfurledMediaItem(url=target.display_avatar.url),
            ),
        )

        children: list = [section]

        if target.banner:
            children.append(ui.Separator())
            gallery = ui.MediaGallery()
            gallery.add_item(media=target.banner.url)
            children.append(gallery)

        container = ui.Container(*children, accent_color=target.accent_color or COLOR)
        self.add_item(container)


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

        view = UserinfoLayout(target, interaction)
        await interaction.response.send_message(view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Userinfo(bot))
