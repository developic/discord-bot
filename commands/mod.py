import datetime

import discord
from discord import app_commands
from discord.ext import commands

from ._utils import check_target, handle_command_error, ok, parse_duration, warn


class Mod(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="kick", usage="<member> [reason=No reason provided]", description="Kick a member from the server")
    @commands.has_permissions(kick_members=True)
    @app_commands.describe(member="The member to kick", reason="Reason for the kick")
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        if not await check_target(ctx, member, "kick"):
            return

        await member.kick(reason=reason)
        await ctx.send(embed=ok(f"Kicked {member.mention} | {reason}"))

    @commands.hybrid_command(name="ban", usage="<member> [reason=No reason provided]", description="Ban a member from the server")
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(member="The member to ban", reason="Reason for the ban")
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        if not await check_target(ctx, member, "ban"):
            return

        await member.ban(reason=reason)
        await ctx.send(embed=ok(f"Banned {member.mention} | {reason}"))

    @commands.hybrid_command(name="unban", usage="<user>", description="Unban a user by name or ID")
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(user="The username or ID of the banned user")
    async def unban(self, ctx: commands.Context, *, user: str):
        async for ban_entry in ctx.guild.bans():
            if str(ban_entry.user) == user or str(ban_entry.user.id) == user:
                await ctx.guild.unban(ban_entry.user)
                await ctx.send(embed=ok(f"Unbanned {ban_entry.user.mention}"))
                return

        await ctx.send(embed=warn(f"Could not find banned user `{user}`"))

    @commands.hybrid_command(name="mute", usage="<member> <duration> [reason=No reason provided]", description="Mute a member for a duration")
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(member="The member to mute", duration="Duration (e.g. 10m, 1h, 2d)", reason="Reason for the mute")
    async def mute(self, ctx: commands.Context, member: discord.Member, duration: str, *, reason: str = "No reason provided"):
        if not await check_target(ctx, member, "mute"):
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
