import random
import re

import discord
from discord import app_commands
from discord.ext import commands

WORD_MAP = {
    r"\byou're\b": "chu're", r"\byou\b": "chu", r"\byour\b": "chur",
    r"\bmy\b": "mai", r"\bmyself\b": "mai sewf",
    r"\blove\b": "wuv", r"\blover\b": "wuvva", r"\blovely\b": "wuvely",
    r"\blike\b": "wike", r"\bliking\b": "wiking",
    r"\bplease\b": "pwease", r"\bpretty\b": "pwetty", r"\bperfect\b": "pwefect",
    r"\bwhat\b": "wut", r"\bwhere\b": "whewe",
    r"\bvery\b": "vewy", r"\bverily\b": "vewiwy",
    r"\bgreat\b": "gweat", r"\bground\b": "gwound", r"\bgrow\b": "gwow",
    r"\bsmall\b": "smol", r"\bsmol\b": "smol",
    r"\bcute\b": "kawaii",
    r"\bsad\b": "sad",
    r"\bfuck\b": "fwick",
    r"\bno\b": "nyo", r"\bnot\b": "nyot",
    r"\byes\b": "yeth", r"\byeah\b": "yeh",
    r"\bthat\b": "dat", r"\bthis\b": "dis", r"\bthere\b": "dere", r"\bthem\b": "dem",
    r"\bthe\b": "da",
    r"\bwith\b": "wif",
    r"\bfriend\b": "fwend", r"\bfriends\b": "fwiends",
    r"\bsorry\b": "sowwy",
    r"\blittle\b": "widdle",
    r"\bhello\b": "hewwo", r"\bhi\b": "haii",
    r"\bwell\b": "wewl",
    r"\bgirl\b": "guwl",
    r"\breally\b": "weawy",
    r"\bjust\b": "jus",
    r"\btoo\b": "to",
    r"\bso\b": "soo",
    r"\bwhat\b": "wut",
    r"\ball\b": "aww",
    r"\bawesome\b": "awesomes",
    r"\bcool\b": "coow",
    r"\bdick\b": "dwick",
    r"\bfeel\b": "feew",
    r"\bfeeling\b": "feewing",
    r"\bgood\b": "gud",
    r"\bhappy\b": "happi",
    r"\bhug\b": "huggie",
    r"\bhungry\b": "hungy",
    r"\bkiss\b": "kith",
    r"\blook\b": "wook",
    r"\bme\b": "mwah",
    r"\bmiss\b": "mish",
    r"\bnice\b": "nyice",
    r"\boh\b": "ohh",
    r"\bokay\b": "oki",
    r"\bpoor\b": "puwu",
    r"\bshut\b": "shwu",
    r"\bsleep\b": "sweep",
    r"\bsleepy\b": "sweepy",
    r"\bsnake\b": "snek",
    r"\bstop\b": "stawp",
    r"\bthanks\b": "tank chu",
    r"\bthank\b": "tank",
    r"\bwelcome\b": "wewcome",
    r"\bwhat's\b": "wuts",
    r"\bworried\b": "worwie",
}

SUFFIXES = ["owo", "uwu", "rawr", "nya~", ":3", ">_<", "x3"]


def _uwu(text: str) -> str:
    text = text.lower()
    for pattern, repl in WORD_MAP.items():
        text = re.sub(pattern, repl, text)
    text = text.replace("th", "d")
    text = re.sub(r"(?<=[aeiou])[rl](?=[aeiou])", "w", text)
    text = text.replace("ove", "uv")
    text = text.replace("ll", "ww")
    text = text.replace("le", "wel")
    words = text.split()
    result = []
    for word in words:
        if random.random() < 0.25:
            word = f"{word[0]}-{word}"
        result.append(word)
    text = " ".join(result)
    text = text.replace("!", f"! {random.choice(SUFFIXES)}")
    if random.random() < 0.2:
        text += " " + random.choice(SUFFIXES)
    return text


class Uwu(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="uwu", description="Convert text to uwu speak")
    @app_commands.allowed_installs(guilds=False, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(text="The text to uwu-ify")
    async def uwu(self, interaction: discord.Interaction, text: str):
        if len(text) > 1000:
            await interaction.response.send_message("Text too long (max 1000 chars).", ephemeral=True)
            return
        result = _uwu(text)
        await interaction.response.send_message(result)


async def setup(bot: commands.Bot):
    await bot.add_cog(Uwu(bot))
