import random

import discord
from discord import app_commands
from discord.ext import commands

from ._utils import COLOR, ensure_author, handle_api_error, TimeoutView

CHOICES = ("rock", "paper", "scissors")
BEATS = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
CHOICE_EMOJIS = {"rock": "\U0001faa8", "paper": "\U0001f4c4", "scissors": "\u2702\ufe0f"}


class RPSButton(discord.ui.Button):
    def __init__(self, choice: str):
        super().__init__(
            label=choice.capitalize(),
            emoji=CHOICE_EMOJIS[choice],
            style=discord.ButtonStyle.secondary,
        )
        self.choice = choice

    async def callback(self, interaction: discord.Interaction):
        view: RPSView = self.view
        if view.done:
            await interaction.response.defer()
            return

        if not await ensure_author(interaction, view):
            return

        view.done = True
        for child in view.children:
            child.disabled = True

        bot_choice = random.choice(CHOICES)
        user_choice = self.choice

        if user_choice == bot_choice:
            result = "It's a tie!"
            color = 0x2b2d31
        elif BEATS[user_choice] == bot_choice:
            result = "You win!"
            color = 0x57f287
        else:
            result = "You lose!"
            color = 0xed4245

        embed = discord.Embed(
            title="Rock Paper Scissors",
            description=f"{CHOICE_EMOJIS[user_choice]} **{user_choice.capitalize()}** vs **{bot_choice.capitalize()}** {CHOICE_EMOJIS[bot_choice]}\n**{result}**",
            color=color,
        )

        view.clear_items()
        view.add_item(PlayAgainButton())

        await interaction.response.edit_message(embed=embed, view=view)


class PlayAgainButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Play Again", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        if not await ensure_author(interaction, self.view):
            return

        view = RPSView(author_id=interaction.user.id)
        embed = discord.Embed(
            title="Rock Paper Scissors",
            description="**Choose your move!**",
            color=COLOR,
        )
        await interaction.response.edit_message(embed=embed, view=view)


class RPSView(TimeoutView):
    def __init__(self, author_id: int):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.done = False
        for choice in CHOICES:
            self.add_item(RPSButton(choice))


class RPS(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="rps", description="Play Rock Paper Scissors")
    @app_commands.allowed_installs(guilds=False, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def rps(self, ctx: commands.Context):
        embed = discord.Embed(
            title="Rock Paper Scissors",
            description="**Choose your move!**",
            color=COLOR,
        )
        await ctx.send(embed=embed, view=RPSView(author_id=ctx.author.id))

    @rps.error
    async def rps_error(self, ctx, error):
        if not await handle_api_error(ctx, error):
            raise error


async def setup(bot: commands.Bot):
    await bot.add_cog(RPS(bot))
