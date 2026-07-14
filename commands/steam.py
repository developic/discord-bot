import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from ._utils import COLOR, fetch_json, handle_api_error, warn


def _format_price(price: dict | None) -> str:
    if price is None:
        return "Free"
    final = price.get("final_formatted")
    initial = price.get("initial_formatted")
    discount = price.get("discount_percent", 0)
    if discount:
        return f"~~{initial}~~ **{final}** (-{discount}%)"
    return final or "Free"


class Steam(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="steam", description="Look up a game on Steam")
    @app_commands.allowed_installs(guilds=False, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(game="The name of the game")
    async def steam(self, ctx: commands.Context, *, game: str):
        await ctx.defer()

        search_url = f"https://store.steampowered.com/api/storesearch/?term={game}&cc=us&l=en"

        async with aiohttp.ClientSession() as session:
            search_data = await fetch_json(session, search_url)

        if not search_data:
            await ctx.send(embed=warn("Could not search Steam right now."))
            return

        items = search_data.get("items", [])
        if not items:
            await ctx.send(embed=warn(f"No results found for `{game}`."))
            return

        app_id = items[0]["id"]
        detail_url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&cc=us"

        async with aiohttp.ClientSession() as session:
            detail_data = await fetch_json(session, detail_url)

        app_data = detail_data.get(str(app_id), {})
        if not app_data.get("success") or not app_data.get("data"):
            await ctx.send(embed=warn("Could not fetch game details."))
            return

        d = app_data["data"]
        name = d.get("name", "Unknown")
        short_desc = d.get("short_description", "")
        header = d.get("header_image", "")
        developers = d.get("developers", [])
        publishers = d.get("publishers", [])
        release = d.get("release_date", {})
        release_date = release.get("date", "TBA") if isinstance(release, dict) else "TBA"
        metacritic = d.get("metacritic", {})
        mc_score = metacritic.get("score") if isinstance(metacritic, dict) else None
        mc_url = metacritic.get("url") if isinstance(metacritic, dict) else None
        genres = d.get("genres", [])
        genre_list = ", ".join(g.get("description", "") for g in genres) if genres else "N/A"
        platforms = d.get("platforms", {})
        plat_parts = []
        if platforms.get("windows"):
            plat_parts.append("Windows")
        if platforms.get("mac"):
            plat_parts.append("macOS")
        if platforms.get("linux"):
            plat_parts.append("Linux")
        plat_str = ", ".join(plat_parts) if plat_parts else "N/A"
        price = d.get("price_overview")
        price_str = _format_price(price)

        embed = discord.Embed(
            title=name,
            url=f"https://store.steampowered.com/app/{app_id}",
            description=short_desc[:500],
            color=COLOR,
        )
        if header:
            embed.set_thumbnail(url=header)

        if mc_score:
            mc_field = f"{mc_score}/100"
            if mc_url:
                mc_field = f"[{mc_score}/100]({mc_url})"
            embed.add_field(name="Metacritic", value=mc_field, inline=True)

        embed.add_field(name="Price", value=price_str, inline=True)
        embed.add_field(name="Release", value=release_date, inline=True)
        embed.add_field(name="Genre", value=genre_list, inline=False)
        embed.add_field(name="Platforms", value=plat_str, inline=True)

        if developers:
            embed.add_field(name="Developer", value=", ".join(developers), inline=True)

        embed.set_footer(text=f"App ID: {app_id}")

        await ctx.send(embed=embed)

    @steam.error
    async def steam_error(self, ctx, error):
        if await handle_api_error(ctx, error, "Could not search Steam right now."):
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=warn("Usage: `!steam <game>`"))
        else:
            raise error


async def setup(bot: commands.Bot):
    await bot.add_cog(Steam(bot))
