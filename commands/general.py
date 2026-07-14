import discord
from discord import app_commands
from discord.ext import commands

from ._utils import COLOR, ok, warn


class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="help", description="Show all available commands")
    async def help(self, ctx: commands.Context):
        embed = discord.Embed(
            title="Moderation Commands",
            color=COLOR,
        )
        embed.add_field(
            name=f"`{ctx.prefix}kick <member> [reason]`",
            value="Kick a member from the server.",
            inline=False,
        )
        embed.add_field(
            name=f"`{ctx.prefix}ban <member> [reason]`",
            value="Ban a member from the server.",
            inline=False,
        )
        embed.add_field(
            name=f"`{ctx.prefix}unban <user>`",
            value="Unban a user by name or ID.",
            inline=False,
        )
        embed.add_field(
            name=f"`{ctx.prefix}mute <member> <duration> [reason]`",
            value="Mute a member (e.g. `10m`, `1h`, `2d`).",
            inline=False,
        )
        embed.add_field(
            name=f"`{ctx.prefix}jail <member>`",
            value="Jail a member by removing all roles.",
            inline=False,
        )
        embed.add_field(
            name=f"`{ctx.prefix}unjail <member>`",
            value="Restore a member's roles and unjail them.",
            inline=False,
        )
        embed.add_field(
            name=f"`{ctx.prefix}purge <amount>`",
            value="Bulk delete messages (1-100).",
            inline=False,
        )
        embed.add_field(
            name=f"`{ctx.prefix}slowdown <duration>` / `{ctx.prefix}slowmode off`",
            value="Set or disable channel slowmode (e.g. `10`, `2s`, `5m`, `1h`).",
            inline=False,
        )
        embed.add_field(
            name=f"`{ctx.prefix}warn <member> [reason]`",
            value="Issue a warning to a member.",
            inline=False,
        )
        embed.add_field(
            name=f"`{ctx.prefix}warn list <member>`",
            value="List warnings for a member.",
            inline=False,
        )
        embed.add_field(
            name=f"`{ctx.prefix}unwarn <member> <id>`",
            value="Remove a specific warning by ID.",
            inline=False,
        )
        embed.add_field(
            name=f"`{ctx.prefix}joke`",
            value="Get a random dark joke.",
            inline=False,
        )
        embed.add_field(
            name=f"`{ctx.prefix}weather <city>`",
            value="Get current weather for a city.",
            inline=False,
        )
        embed.add_field(
            name=f"`{ctx.prefix}quiz`",
            value="Test your knowledge with a trivia question.",
            inline=False,
        )
        embed.add_field(
            name=f"`{ctx.prefix}rps`",
            value="Play Rock Paper Scissors.",
            inline=False,
        )
        embed.add_field(
            name=f"`{ctx.prefix}steam <game>`",
            value="Look up a game on Steam.",
            inline=False,
        )
        embed.add_field(
            name=f"`{ctx.prefix}sync`",
            value="Sync slash commands (admin only).",
            inline=False,
        )
        await ctx.send(embed=embed)

    @commands.command(name="sync")
    @commands.has_permissions(administrator=True)
    async def sync(self, ctx: commands.Context):
        await self.bot.tree.sync()
        await ctx.send(embed=ok("Synced all slash commands."))

    @sync.error
    async def sync_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=warn("You need administrator permission to sync commands."))


async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
