import json
import os

import discord
from discord import app_commands
from discord.ext import commands

from ._utils import check_target, handle_command_error, ok, warn


class Jail(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data_file = "jail_data.json"

        if os.path.exists(self.data_file):
            with open(self.data_file) as f:
                self.saved_roles = json.load(f)
        else:
            self.saved_roles = {}

    def save_data(self):
        with open(self.data_file, "w") as f:
            json.dump(self.saved_roles, f, indent=4)

    async def get_jail_role(self, guild: discord.Guild):
        role = discord.utils.get(guild.roles, name="Jailed")

        if role:
            return role

        role = await guild.create_role(
            name="Jailed",
            colour=discord.Colour.dark_grey(),
            reason="Automatic jail role"
        )

        for channel in guild.channels:
            overwrite = channel.overwrites_for(role)
            overwrite.view_channel = False

            if isinstance(channel, (discord.TextChannel, discord.ForumChannel)):
                overwrite.send_messages = False
                overwrite.add_reactions = False
                overwrite.create_public_threads = False
                overwrite.create_private_threads = False
                overwrite.send_messages_in_threads = False
            elif isinstance(channel, (discord.VoiceChannel, discord.StageChannel)):
                overwrite.connect = False
                overwrite.speak = False

            await channel.set_permissions(role, overwrite=overwrite)

        return role

    @commands.hybrid_command(name="jail", usage="<member>", description="Jail a member by removing all roles")
    @commands.has_permissions(manage_roles=True)
    @app_commands.describe(member="The member to jail")
    async def jail(self, ctx, member: discord.Member):
        if not await check_target(ctx, member, "jail"):
            return

        jail_role = await self.get_jail_role(ctx.guild)

        if jail_role in member.roles:
            await ctx.send(embed=warn("That member is already jailed."))
            return

        self.saved_roles[str(member.id)] = [
            role.id
            for role in member.roles
            if role != ctx.guild.default_role and role != jail_role
        ]
        self.save_data()

        await member.edit(roles=[jail_role], reason=f"Jailed by {ctx.author}")
        await ctx.send(embed=ok(f"{member.mention} has been jailed."))

    @commands.hybrid_command(name="unjail", usage="<member>", description="Restore a member's roles and unjail them")
    @commands.has_permissions(manage_roles=True)
    @app_commands.describe(member="The member to unjail")
    async def unjail(self, ctx, member: discord.Member):
        if not await check_target(ctx, member, "unjail"):
            return

        jail_role = await self.get_jail_role(ctx.guild)

        if jail_role not in member.roles:
            await ctx.send(embed=warn("That member is not jailed."))
            return

        role_ids = self.saved_roles.get(str(member.id), [])
        roles = [r for r in [ctx.guild.get_role(rid) for rid in role_ids] if r]

        await member.edit(roles=roles, reason=f"Unjailed by {ctx.author}")

        self.saved_roles.pop(str(member.id), None)
        self.save_data()

        await ctx.send(embed=ok(f"{member.mention} has been unjailed."))

    @jail.error
    @unjail.error
    async def error(self, ctx, error):
        await handle_command_error(ctx, error)


async def setup(bot: commands.Bot):
    await bot.add_cog(Jail(bot))
