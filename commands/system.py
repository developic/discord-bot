import datetime
import platform
import time

import discord
import psutil
from discord import app_commands
from discord.ext import commands
from ._utils import COLOR, check_allowed, get_cogs_memory


def _format_bytes(b: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


def _format_uptime(seconds: float) -> str:
    delta = datetime.timedelta(seconds=int(seconds))
    d = delta.days
    h, rem = divmod(delta.seconds, 3600)
    m, s = divmod(rem, 60)
    parts = []
    if d:
        parts.append(f"{d}d")
    if h:
        parts.append(f"{h}h")
    if m:
        parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts)


class System(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="system", description="Show system information")
    @app_commands.allowed_installs(guilds=False, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def system(self, interaction: discord.Interaction):
        if not await check_allowed(interaction):
            return

        cpu_usage = psutil.cpu_percent(interval=0.5)
        cpu_freq = psutil.cpu_freq()
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        boot_time = psutil.boot_time()
        uptime = _format_uptime(time.time() - boot_time)
        temps = psutil.sensors_temperatures()

        cpu_temp = "N/A"
        if "coretemp" in temps:
            cpu_temp = f"{temps['coretemp'][0].current}\u00b0C"
        elif "acpitz" in temps:
            cpu_temp = f"{temps['acpitz'][0].current}\u00b0C"
        elif "dell_smm" in temps:
            for t in temps["dell_smm"]:
                if t.label == "CPU":
                    cpu_temp = f"{t.current}\u00b0C"
                    break
            else:
                cpu_temp = f"{temps['dell_smm'][0].current}\u00b0C"

        freq = f"{cpu_freq.current:.0f} MHz" if cpu_freq else "N/A"
        freq_max = f"{cpu_freq.max:.0f} MHz" if cpu_freq and cpu_freq.max else None

        embed = discord.Embed(
            title="System",
            color=COLOR,
        )

        cpu_desc = f"**{cpu_usage}%**"
        if freq_max:
            cpu_desc += f"  |  {freq} / {freq_max}"
        else:
            cpu_desc += f"  |  {freq}"
        cpu_desc += f"\nTemperature: **{cpu_temp}**"
        embed.add_field(name="CPU", value=cpu_desc, inline=False)

        mem_desc = (
            f"**{mem.percent}%** used\n"
            f"{_format_bytes(mem.used)} / {_format_bytes(mem.total)}"
        )
        embed.add_field(name="Memory", value=mem_desc, inline=True)

        disk_desc = (
            f"**{disk.percent}%** used\n"
            f"{_format_bytes(disk.used)} / {_format_bytes(disk.total)}"
        )
        embed.add_field(name="Disk", value=disk_desc, inline=True)

        embed.add_field(name="Uptime", value=uptime, inline=False)
        embed.add_field(name="OS", value=platform.platform(), inline=False)
        embed.set_footer(text=f"Python {platform.python_version()}")

        cogs = get_cogs_memory(self.bot)
        lines = "\n".join(
            f"**{name}**  {count} obj  {_format_bytes(size)}"
            for name, count, size in cogs
        )
        embed.add_field(name="Cogs Memory", value=lines, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(System(bot))
