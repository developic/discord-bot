import gc
import sys

import aiohttp
import discord
from discord.ext import commands

COLOR = 0x2b2d31


def ok(description: str) -> discord.Embed:
    return discord.Embed(description=description, color=COLOR)


def warn(description: str) -> discord.Embed:
    return discord.Embed(description=description, color=COLOR)


async def ensure_author(interaction: discord.Interaction, view) -> bool:
    if interaction.user.id != getattr(view, "author_id", None):
        await interaction.response.send_message("This isn't your game!", ephemeral=True)
        return False
    return True


class TimeoutView(discord.ui.View):
    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        try:
            await self.message.edit(view=self)
        except Exception:
            pass


def parse_duration(duration: str) -> int | None:
    unit = duration[-1]
    if unit.isdigit():
        return int(duration)

    try:
        amount = int(duration[:-1])
    except ValueError:
        return None

    multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    if unit not in multipliers:
        return None

    return amount * multipliers[unit]


async def fetch_json(session: aiohttp.ClientSession, url: str, **kwargs) -> dict | None:
    async with session.get(url, **kwargs) as resp:
        if resp.status != 200:
            return None
        return await resp.json(content_type=None)


async def handle_api_error(ctx, error, message: str = "Something went wrong.") -> bool:
    if isinstance(error, (commands.CommandInvokeError, commands.HybridCommandError)):
        await ctx.send(embed=warn(message))
        return True
    return False


async def handle_command_error(ctx, error, permission_msg: str | None = None):
    usage = getattr(ctx.command, "usage", None) or ctx.command.signature

    if isinstance(error, commands.MissingPermissions):
        await ctx.send(embed=warn(permission_msg or "You don't have permission to use this command."))
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send(embed=warn("Member not found."))
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(embed=warn(f"Usage: `{ctx.prefix}{ctx.command.name} {usage}`"))
    elif isinstance(error, commands.BadArgument):
        await ctx.send(embed=warn(f"Usage: `{ctx.prefix}{ctx.command.name} {usage}`"))
    else:
        raise error


def get_cogs_memory(bot) -> list[tuple[str, int, int]]:
    modules = {}
    for name, cog in bot.cogs.items():
        modules[type(cog).__module__] = {"name": name, "count": 0, "size": 0}

    for obj in gc.get_objects():
        mod = getattr(obj, "__module__", None)
        if mod in modules:
            modules[mod]["count"] += 1
            try:
                modules[mod]["size"] += sys.getsizeof(obj)
            except Exception:
                pass

    sorted_cogs = sorted(modules.values(), key=lambda x: x["size"], reverse=True)
    return [(c["name"], c["count"], c["size"]) for c in sorted_cogs]


async def check_target(ctx, member: discord.Member, action: str) -> bool:
    if member == ctx.author:
        await ctx.send(embed=warn(f"You can't {action} yourself."))
        return False
    if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
        await ctx.send(embed=warn(f"You can't {action} someone with an equal or higher role."))
        return False
    return True
