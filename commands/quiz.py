import html
import random

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from ._utils import COLOR, check_allowed, fetch_json, TimeoutView, warn


class QuizButton(discord.ui.Button):
    def __init__(self, label: str, is_correct: bool):
        super().__init__(label=html.unescape(label), style=discord.ButtonStyle.secondary)
        self.is_correct = is_correct

    async def callback(self, interaction: discord.Interaction):
        view: QuizView = self.view
        if view.answered:
            await interaction.response.defer()
            return

        view.answered = True
        for child in view.children:
            child.disabled = True
            if isinstance(child, QuizButton) and child.is_correct:
                child.style = discord.ButtonStyle.success
            elif child is self and not self.is_correct:
                child.style = discord.ButtonStyle.danger

        await interaction.response.edit_message(view=view)

        if self.is_correct:
            await interaction.followup.send("\u2705 Correct!", ephemeral=True)
        else:
            await interaction.followup.send(f"\u274c The answer was: **{html.unescape(view.correct_answer)}**", ephemeral=True)


class QuizView(TimeoutView):
    def __init__(self, correct_answer: str, answers: list[str]):
        super().__init__(timeout=60)
        self.correct_answer = correct_answer
        self.answered = False
        for answer in answers:
            self.add_item(QuizButton(answer, answer == correct_answer))


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

        embed = discord.Embed(
            title=f"\ud83d\udcdd {category}",
            description=question,
            color=COLOR,
        )
        embed.set_footer(text=f"Difficulty: {difficulty}")

        view = QuizView(correct, answers)
        await interaction.followup.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Quiz(bot))
