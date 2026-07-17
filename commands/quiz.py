import html
import random

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from ._utils import COLOR, check_allowed, fetch_json, warn


class QuizView(discord.ui.LayoutView):
    def __init__(self, correct_answer: str, answers: list[str], category: str, question: str, difficulty: str):
        super().__init__(timeout=60)
        self.correct_answer = correct_answer
        self.answered = False

        action_row = discord.ui.ActionRow()
        for i, answer in enumerate(answers):
            is_correct = (answer == correct_answer)
            btn = discord.ui.Button(
                label=html.unescape(answer),
                style=discord.ButtonStyle.secondary,
                custom_id=str(i),
            )
            btn.is_correct = is_correct
            btn.callback = self._make_callback(btn)
            action_row.add_item(btn)

        self._action_row = action_row

        container = discord.ui.Container(
            discord.ui.TextDisplay(f"\U0001f4dd {category}"),
            discord.ui.TextDisplay(question),
            discord.ui.Separator(),
            discord.ui.TextDisplay(f"*Difficulty: {difficulty}*"),
            action_row,
            accent_color=COLOR,
        )
        self.add_item(container)

    def _make_callback(self, btn: discord.ui.Button):
        async def callback(interaction: discord.Interaction):
            if self.answered:
                await interaction.response.defer()
                return
            self.answered = True
            for b in self._action_row.children:
                b.disabled = True
                if b.is_correct:
                    b.style = discord.ButtonStyle.success
                elif b is btn and not btn.is_correct:
                    b.style = discord.ButtonStyle.danger
            await interaction.response.edit_message(view=self)
            if btn.is_correct:
                await interaction.followup.send("\u2705 Correct!", ephemeral=True)
            else:
                display = html.unescape(self.correct_answer)
                await interaction.followup.send(f"\u274c The answer was: **{display}**", ephemeral=True)
        return callback

    async def on_timeout(self):
        for btn in self._action_row.children:
            btn.disabled = True
        try:
            await self.message.edit(view=self)
        except Exception:
            pass


class Quiz(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="quiz", description="Test your knowledge with a trivia question")
    @app_commands.allowed_installs(guilds=False, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def quiz(self, interaction: discord.Interaction):
        if not await check_allowed(interaction):
            return
        await interaction.response.defer()

        async with aiohttp.ClientSession() as session:
            data = await fetch_json(session, "https://opentdb.com/api.php?amount=1")

        if data is None or data.get("response_code") != 0 or not data.get("results"):
            await interaction.followup.send(embed=warn("Could not fetch a question right now."))
            return

        result = data["results"][0]
        question = html.unescape(result["question"])
        correct = result["correct_answer"]
        incorrect = result["incorrect_answers"]
        category = html.unescape(result["category"])
        difficulty = result["difficulty"].capitalize()

        answers = [correct] + incorrect
        random.shuffle(answers)

        view = QuizView(correct, answers, category, question, difficulty)
        await interaction.followup.send(view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Quiz(bot))
