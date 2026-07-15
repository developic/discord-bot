import discord
from discord import app_commands
from discord.ext import commands

from ._utils import handle_command_error, ok, warn


class Purge(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="purge", usage="<amount>", description="Bulk delete messages (1-100)")
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(amount="Number of messages to delete (1-100)")
    async def purge(self, ctx: commands.Context, amount: int):
        if amount < 1 or amount > 100:
            await ctx.send(embed=warn("Amount must be between 1 and 100."))
            return

        await ctx.channel.purge(limit=amount + 1)
        msg = await ctx.send(embed=ok(f"Deleted {amount} messages."))
        await msg.delete(delay=3)

    @purge.error
    async def purge_error(self, ctx, error):
        await handle_command_error(ctx, error, permission_msg="You don't have permission to purge messages.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Purge(bot))
