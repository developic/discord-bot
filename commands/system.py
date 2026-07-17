import datetime
import platform
import time

import discord
import psutil
from discord import app_commands, ui
from discord.ext import commands
from ._utils import COLOR, check_allowed


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


class SystemLayout(ui.LayoutView):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=120)
        self.bot = bot
        self._build()

    def _build(self):
        self.clear_items()

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

        cpu_desc = f"**{cpu_usage}%**"
        if freq_max:
            cpu_desc += f"  |  {freq} / {freq_max}"
        else:
            cpu_desc += f"  |  {freq}"
        cpu_desc += f"\nTemperature: **{cpu_temp}**"

        mem_desc = f"**{mem.percent}%** used\n{_format_bytes(mem.used)} / {_format_bytes(mem.total)}"
        disk_desc = f"**{disk.percent}%** used\n{_format_bytes(disk.used)} / {_format_bytes(disk.total)}"

        body = (
            f"**CPU:** {cpu_desc}\n"
            f"**Memory:** {mem_desc}\n"
            f"**Disk:** {disk_desc}\n"
            f"**Uptime:** {uptime}"
        )

        children = [
            ui.TextDisplay("### System"),
            ui.Separator(),
            ui.TextDisplay(body),
            ui.Separator(),
            ui.TextDisplay(f"-# Python {platform.python_version()}"),
        ]

        refresh_btn = ui.Button(label="Refresh", style=discord.ButtonStyle.primary, custom_id="sys_refresh")
        refresh_btn.callback = self._on_refresh
        children.append(ui.ActionRow(refresh_btn))

        container = ui.Container(*children, accent_color=COLOR)
        self.add_item(container)

    async def _on_refresh(self, interaction: discord.Interaction):
        self._build()
        await interaction.response.edit_message(view=self)


class System(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="system", description="Show system information")
    @app_commands.allowed_installs(guilds=False, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def system(self, interaction: discord.Interaction):
        if not await check_allowed(interaction):
            return

        await interaction.response.send_message(view=SystemLayout(self.bot), ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(System(bot))
