import discord
from discord import app_commands
from discord.ext import commands

from ._utils import handle_command_error, ok, parse_duration, warn

MAX_SECONDS = 21600


class Slowmode(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="slowdown", usage="<duration>", description="Set channel slowmode")
    @commands.has_permissions(manage_channels=True)
    @app_commands.describe(duration="Duration (e.g. 10, 2s, 5m, 1h) or 0/off to disable")
    async def slowdown(self, ctx: commands.Context, duration: str):
        seconds = parse_duration(duration)

        if seconds is None:
            await ctx.send(embed=warn("Invalid duration. Use e.g. `10`, `2s`, `5m`, `1h`"))
            return

        if seconds < 0 or seconds > MAX_SECONDS:
            await ctx.send(embed=warn(f"Slowmode must be between 0 and {MAX_SECONDS} seconds (6 hours)."))
            return

        await ctx.channel.edit(slowmode_delay=seconds)

        if seconds == 0:
            await ctx.send(embed=ok("Slowmode has been disabled."))
        else:
            await ctx.send(embed=ok(f"Slowmode set to {seconds} seconds."))

    @commands.hybrid_group(name="slowmode", invoke_without_command=True)
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx: commands.Context):
        await ctx.send(embed=warn(
            f"Usage: `{ctx.prefix}slowdown <duration>` or `{ctx.prefix}slowmode off`\n"
            f"Duration examples: `10` (seconds), `2s`, `5m`, `1h`, `6h` (max)"
        ))

    @slowmode.command(name="off")
    async def slowmode_off(self, ctx: commands.Context):
        await ctx.channel.edit(slowmode_delay=0)
        await ctx.send(embed=ok("Slowmode has been disabled."))

    @slowdown.error
    async def slowdown_error(self, ctx, error):
        await handle_command_error(ctx, error, permission_msg="You don't have permission to manage channels.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Slowmode(bot))
