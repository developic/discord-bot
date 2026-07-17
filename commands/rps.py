import random

import discord
from discord import app_commands, ui
from discord.ext import commands

from ._utils import COLOR, check_allowed, ensure_author

CHOICES = ("rock", "paper", "scissors")
BEATS = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
CHOICE_EMOJIS = {"rock": "\U0001faa8", "paper": "\U0001f4c4", "scissors": "\u2702\ufe0f"}


class RPSView(ui.LayoutView):
    def __init__(self, author_id: int):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.done = False
        self._build_initial()

    def _build_initial(self):
        self.clear_items()

        action_row = ui.ActionRow()
        for choice in CHOICES:
            btn = ui.Button(
                label=choice.capitalize(),
                emoji=CHOICE_EMOJIS[choice],
                style=discord.ButtonStyle.secondary,
                custom_id=f"rps_{choice}",
            )
            btn.choice = choice
            btn.callback = self._on_choice(btn)
            action_row.add_item(btn)

        self._action_row = action_row

        container = ui.Container(
            ui.TextDisplay("### Rock Paper Scissors"),
            ui.TextDisplay("**Choose your move!**"),
            action_row,
        )
        self.add_item(container)

    def _on_choice(self, btn: ui.Button):
        async def callback(interaction: discord.Interaction):
            if self.done:
                await interaction.response.defer()
                return
            if not await ensure_author(interaction, self):
                return

            self.done = True
            bot_choice = random.choice(CHOICES)
            user_choice = btn.choice

            if user_choice == bot_choice:
                result = "It's a tie!"
                color = 0x2b2d31
            elif BEATS[user_choice] == bot_choice:
                result = "You win!"
                color = 0x57f287
            else:
                result = "You lose!"
                color = 0xed4245

            text = (
                f"{CHOICE_EMOJIS[user_choice]} **{user_choice.capitalize()}**"
                f" vs **{bot_choice.capitalize()}** {CHOICE_EMOJIS[bot_choice]}"
                f"\n**{result}**"
            )

            self.clear_items()

            play_row = ui.ActionRow()
            play_btn = ui.Button(
                label="Play Again",
                style=discord.ButtonStyle.primary,
                custom_id="rps_play_again",
            )
            play_btn.callback = self._on_play_again
            play_row.add_item(play_btn)
            self._action_row = play_row

            container = ui.Container(
                ui.TextDisplay("### Rock Paper Scissors"),
                ui.TextDisplay(text),
                play_row,
                accent_color=color,
            )
            self.add_item(container)

            await interaction.response.edit_message(view=self)

        return callback

    async def _on_play_again(self, interaction: discord.Interaction):
        if not await ensure_author(interaction, self):
            return

        self.done = False
        self._build_initial()
        await interaction.response.edit_message(view=self)

    async def on_timeout(self):
        for btn in self._action_row.children:
            btn.disabled = True
        try:
            await self.message.edit(view=self)
        except Exception:
            pass


class RPS(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="rps", description="Play Rock Paper Scissors")
    @app_commands.allowed_installs(guilds=False, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def rps(self, interaction: discord.Interaction):
        if not await check_allowed(interaction):
            return
        await interaction.response.send_message(view=RPSView(author_id=interaction.user.id))


async def setup(bot: commands.Bot):
    await bot.add_cog(RPS(bot))
