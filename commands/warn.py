import json
import os
import datetime

import discord
from discord.ext import commands

from ._utils import COLOR, handle_command_error, ok, warn


class Warn(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data_file = "warn_data.json"

        if os.path.exists(self.data_file):
            with open(self.data_file) as f:
                self.data = json.load(f)
        else:
            self.data = {}

    def save_data(self):
        with open(self.data_file, "w") as f:
            json.dump(self.data, f, indent=4)

    @commands.group(name="warn", invoke_without_command=True, usage="<member> [reason=No reason provided]")
    @commands.has_permissions(moderate_members=True)
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        if member == ctx.author:
            await ctx.send(embed=warn("You can't warn yourself."))
            return
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send(embed=warn("You can't warn someone with an equal or higher role."))
            return

        guild_id = str(ctx.guild.id)
        member_id = str(member.id)
        self.data.setdefault(guild_id, {})
        self.data[guild_id].setdefault(member_id, [])
        warnings = self.data[guild_id][member_id]

        warn_id = len(warnings) + 1
        warnings.append({
            "id": warn_id,
            "reason": reason,
            "date": discord.utils.utcnow().isoformat(),
        })
        self.save_data()

        await ctx.send(embed=ok(f"Warned {member.mention} | {reason} (warning #{warn_id})"))

    @warn.command(name="list", usage="<member>")
    async def warn_list(self, ctx: commands.Context, member: discord.Member):
        guild_id = str(ctx.guild.id)
        member_id = str(member.id)
        warnings = self.data.get(guild_id, {}).get(member_id, [])

        if not warnings:
            await ctx.send(embed=warn(f"{member.mention} has no warnings."))
            return

        lines = "\n".join(
            f"`#{w['id']}` — {w['reason']} (<t:{int(datetime.datetime.fromisoformat(w['date']).timestamp())}:R>)"
            for w in warnings
        )
        await ctx.send(embed=discord.Embed(
            title=f"Warnings for {member}",
            description=lines,
            color=COLOR,
        ))

    @commands.command(name="unwarn", usage="<member> <warn_id>")
    @commands.has_permissions(moderate_members=True)
    async def unwarn(self, ctx: commands.Context, member: discord.Member, warn_id: int):
        guild_id = str(ctx.guild.id)
        member_id = str(member.id)
        warnings = self.data.get(guild_id, {}).get(member_id, [])

        found = None
        for i, w in enumerate(warnings):
            if w["id"] == warn_id:
                found = i
                break

        if found is None:
            await ctx.send(embed=warn(f"Warning #{warn_id} not found for {member.mention}."))
            return

        warnings.pop(found)
        for i, w in enumerate(warnings):
            w["id"] = i + 1

        self.save_data()
        await ctx.send(embed=ok(f"Removed warning #{warn_id} from {member.mention}."))

    @warn.error
    @warn_list.error
    @unwarn.error
    async def warn_error(self, ctx, error):
        await handle_command_error(ctx, error)


async def setup(bot: commands.Bot):
    await bot.add_cog(Warn(bot))
