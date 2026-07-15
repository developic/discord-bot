import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from ._utils import COLOR, check_allowed, fetch_json, handle_api_error, warn

CONDITION_EMOJIS = {
    "113": "\u2600\ufe0f",
    "116": "\u26c5",
    "119": "\u2601\ufe0f",
    "122": "\u2601\ufe0f",
    "143": "\ud83c\udf2b\ufe0f",
    "176": "\ud83c\udf26\ufe0f",
    "179": "\ud83c\udf28\ufe0f",
    "182": "\ud83c\udf28\ufe0f",
    "185": "\ud83c\udf28\ufe0f",
    "200": "\ud83c\udf29\ufe0f",
    "227": "\ud83c\udf28\ufe0f",
    "230": "\ud83c\udf28\ufe0f",
    "248": "\ud83c\udf2b\ufe0f",
    "260": "\ud83c\udf2b\ufe0f",
    "263": "\ud83c\udf26\ufe0f",
    "266": "\ud83c\udf26\ufe0f",
    "281": "\ud83c\udf27\ufe0f",
    "284": "\ud83c\udf27\ufe0f",
    "293": "\ud83c\udf26\ufe0f",
    "296": "\ud83c\udf26\ufe0f",
    "299": "\ud83c\udf27\ufe0f",
    "302": "\ud83c\udf27\ufe0f",
    "305": "\ud83c\udf27\ufe0f",
    "308": "\ud83c\udf27\ufe0f",
    "311": "\ud83c\udf27\ufe0f",
    "314": "\ud83c\udf27\ufe0f",
    "317": "\ud83c\udf28\ufe0f",
    "320": "\ud83c\udf28\ufe0f",
    "323": "\ud83c\udf28\ufe0f",
    "326": "\ud83c\udf28\ufe0f",
    "329": "\ud83c\udf28\ufe0f",
    "332": "\ud83c\udf28\ufe0f",
    "335": "\ud83c\udf28\ufe0f",
    "338": "\ud83c\udf28\ufe0f",
    "350": "\ud83e\uddca",
    "353": "\ud83c\udf26\ufe0f",
    "356": "\ud83c\udf27\ufe0f",
    "359": "\ud83c\udf27\ufe0f",
    "362": "\ud83c\udf28\ufe0f",
    "365": "\ud83c\udf28\ufe0f",
    "368": "\ud83c\udf28\ufe0f",
    "371": "\ud83c\udf28\ufe0f",
    "374": "\ud83e\uddca",
    "377": "\ud83e\uddca",
    "386": "\ud83c\udf29\ufe0f",
    "389": "\ud83c\udf29\ufe0f",
    "392": "\ud83c\udf29\ufe0f",
    "395": "\ud83c\udf29\ufe0f",
}


class Weather(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="weather", description="Get current weather for a city")
    @app_commands.allowed_installs(guilds=False, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(city="The city to look up")
    async def weather(self, interaction: discord.Interaction, city: str):
        if not await check_allowed(interaction):
            return
        await interaction.response.defer()

        url = f"https://wttr.in/{city}?format=j1"

        async with aiohttp.ClientSession() as session:
            data = await fetch_json(session, url, timeout=aiohttp.ClientTimeout(total=10))

        if not data.get("current_condition"):
            await interaction.followup.send(embed=warn(f"Could not find weather for `{city}`."))
            return

        cc = data["current_condition"][0]
        area = data["nearest_area"][0]

        city_name = area["areaName"][0]["value"]
        country = area["country"][0]["value"]
        temp = cc["temp_C"]
        feels_like = cc["FeelsLikeC"]
        condition = cc["weatherDesc"][0]["value"].strip()
        icon = cc["weatherIconUrl"][0]["value"]
        humidity = cc["humidity"]
        wind_speed = cc["windspeedKmph"]
        wind_dir = cc["winddir16Point"]
        weather_code = cc.get("weatherCode", "")

        emoji = CONDITION_EMOJIS.get(weather_code, "")

        embed = discord.Embed(
            title=f"\U0001f3d9\ufe0f Weather in {city_name}, {country}",
            description=f"{emoji} **{temp}\u00b0C** \u2014 {condition}",
            color=COLOR,
        )
        embed.set_thumbnail(url=icon)
        embed.add_field(name="\ud83d\udca7 Humidity", value=f"{humidity}%", inline=True)
        embed.add_field(name="\ud83d\udca8 Wind", value=f"{wind_speed} km/h {wind_dir}", inline=True)
        embed.add_field(name="\ud83c\udf21\ufe0f Feels Like", value=f"{feels_like}\u00b0C", inline=True)
        embed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Weather(bot))
