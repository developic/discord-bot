import whois

from discord.ui import LayoutView, Section, Separator, TextDisplay, Thumbnail
from discord.ext import commands


def _first(val):
    if isinstance(val, list):
        return val[0]
    return val


class Whois(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="whois")
    async def whois(self, ctx: commands.Context, domain: str):
        try:
            w = whois.whois(domain)
        except Exception as e:
            await ctx.send(f"Error looking up {domain}: {e}")
            return

        domain_name = _first(w.domain_name)
        creation = _first(w.creation_date)
        expiration = _first(w.expiration_date)
        name_servers = w.name_servers
        if isinstance(name_servers, list):
            name_servers = ", ".join(name_servers)
        status = _first(w.status)

        view = LayoutView()
        view.add_item(
            Section(
                f"🌐 **{domain_name}**",
                accessory=Thumbnail(
                    media=f"https://www.google.com/s2/favicons?domain={domain_name}&sz=64"
                ),
            )
        )
        view.add_item(
            TextDisplay(
                f"**Registrar:** {w.registrar or 'N/A'}\n**Status:** {status or 'N/A'}"
            )
        )
        view.add_item(Separator())
        view.add_item(
            TextDisplay(
                f"**Created:** {creation or 'N/A'}\n**Expires:** {expiration or 'N/A'}"
            )
        )
        if name_servers:
            view.add_item(Separator())
            view.add_item(
                TextDisplay(f"**Name Servers:**\n{name_servers[:4000]}")
            )

        await ctx.send(view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Whois(bot))
