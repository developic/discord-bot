import os

import discord
import psutil
from discord.ext import commands
from dotenv import load_dotenv

from commands._utils import set_allowed_users

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
COMMAND_PREFIX = "!"

allowed_ids = os.getenv("ALLOWED_USER_IDS")
if allowed_ids:
    set_allowed_users([int(i) for i in allowed_ids.split(",") if i.strip()])


class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()

        super().__init__(
            command_prefix=COMMAND_PREFIX,
            intents=intents,
            help_command=None,
        )

    async def setup_hook(self):
        for file in os.listdir("commands"):
            if file.endswith(".py") and not file.startswith("_"):
                await self.load_extension(f"commands.{file[:-3]}")

    async def on_ready(self):
        process = psutil.Process(os.getpid())
        ram = process.memory_info().rss / 1024 / 1024
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print(f"RAM Usage: {ram:.2f} MB")


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not set in .env file.")

    bot = Bot()
    bot.run(BOT_TOKEN)


if __name__ == "__main__":
    main()
