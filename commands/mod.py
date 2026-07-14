import datetime

import discord
from discord.ext import commands

from ._utils import handle_command_error, ok, parse_duration, warn


class Mod(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="kick", usage="<member> [reason=No reason provided]")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        if member == ctx.author:
            await ctx.send(embed=warn("You can't kick yourself."))
            return
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send(embed=warn("You can't kick someone with an equal or higher role."))
            return

        await member.kick(reason=reason)
        await ctx.send(embed=ok(f"Kicked {member.mention} | {reason}"))

    @commands.command(name="ban", usage="<member> [reason=No reason provided]")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        if member == ctx.author:
            await ctx.send(embed=warn("You can't ban yourself."))
            return
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send(embed=warn("You can't ban someone with an equal or higher role."))
            return

        await member.ban(reason=reason)
        await ctx.send(embed=ok(f"Banned {member.mention} | {reason}"))

    @commands.command(name="unban", usage="<user>")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, *, user: str):
        async for ban_entry in ctx.guild.bans():
            if str(ban_entry.user) == user or str(ban_entry.user.id) == user:
                await ctx.guild.unban(ban_entry.user)
                await ctx.send(embed=ok(f"Unbanned {ban_entry.user.mention}"))
                return

        await ctx.send(embed=warn(f"Could not find banned user `{user}`"))

    @commands.command(name="mute", usage="<member> <duration> [reason=No reason provided]")
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx: commands.Context, member: discord.Member, duration: str, *, reason: str = "No reason provided"):
        if member == ctx.author:
            await ctx.send(embed=warn("You can't mute yourself."))
            return
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send(embed=warn("You can't mute someone with an equal or higher role."))
            return

        seconds = parse_duration(duration)
        if seconds is None:
            await ctx.send(embed=warn("Invalid duration format. Use e.g. `10m`, `1h`, `2d`"))
            return
        until = discord.utils.utcnow() + datetime.timedelta(seconds=seconds)

        await member.timeout(until, reason=reason)
        unix_ts = int(until.timestamp())
        await ctx.send(embed=ok(f"Muted {member.mention} for {duration} | expires <t:{unix_ts}:R> | {reason}"))

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await handle_command_error(ctx, error)


async def setup(bot: commands.Bot):
    await bot.add_cog(Mod(bot))
