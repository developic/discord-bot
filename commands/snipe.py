import discord
from collections import deque
from discord.ext import commands

from ._utils import COLOR, TimeoutView, ok, warn


class SnipeView(TimeoutView):
    def __init__(self, items, author_id, index):
        super().__init__(timeout=60)
        self.items = items
        self.author_id = author_id
        self.index = index
        self._update_buttons()

    def _update_buttons(self):
        self.clear_items()
        self.add_item(PrevButton(self.index > 1))
        self.add_item(NextButton(self.index < len(self.items)))

    def _embed(self):
        msg = self.items[-self.index]
        embed = discord.Embed(
            title=f"Deleted Message {self.index} / {len(self.items)}",
            description=msg["content"] or "*No text*",
            color=COLOR,
        )
        embed.set_author(
            name=str(msg["author"]),
            icon_url=msg["author"].display_avatar.url,
        )
        if msg["attachments"]:
            links = "\n".join(f"[{a.rsplit('/', 1)[-1].split('?')[0]}]({a})" for a in msg["attachments"])
            embed.add_field(
                name="Attachments",
                value=links,
                inline=False,
            )
            first = msg["attachments"][0]
            if first.rsplit(".", 1)[-1].split("?")[0].lower() in {"png", "jpg", "jpeg", "gif", "webp"}:
                embed.set_image(url=first)
        embed.set_footer(text=f"Deleted at")
        embed.timestamp = msg["deleted_at"]
        return embed


class PrevButton(discord.ui.Button):
    def __init__(self, enabled):
        super().__init__(label="◀", style=discord.ButtonStyle.gray, disabled=not enabled)

    async def callback(self, interaction: discord.Interaction):
        view: SnipeView = self.view
        if interaction.user.id != view.author_id:
            await interaction.response.send_message("Not your snipe.", ephemeral=True)
            return
        view.index = max(1, view.index - 1)
        view._update_buttons()
        await interaction.response.edit_message(embed=view._embed(), view=view)


class NextButton(discord.ui.Button):
    def __init__(self, enabled):
        super().__init__(label="▶", style=discord.ButtonStyle.gray, disabled=not enabled)

    async def callback(self, interaction: discord.Interaction):
        view: SnipeView = self.view
        if interaction.user.id != view.author_id:
            await interaction.response.send_message("Not your snipe.", ephemeral=True)
            return
        view.index = min(len(view.items), view.index + 1)
        view._update_buttons()
        await interaction.response.edit_message(embed=view._embed(), view=view)


class Snipe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.snipes = {}

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return

        self.snipes.setdefault(message.channel.id, deque(maxlen=20)).append({
            "author": message.author,
            "content": message.content,
            "attachments": [a.url for a in message.attachments],
            "created_at": message.created_at,
            "deleted_at": discord.utils.utcnow(),
        })

    @commands.command(name="cs")
    async def cs(self, ctx):
        self.snipes.pop(ctx.channel.id, None)
        await ctx.send(embed=ok("Cleared snipe cache for this channel."))

    @commands.command(name="s")
    async def s(self, ctx, index: int = 1):
        msgs = self.snipes.get(ctx.channel.id)
        if not msgs:
            await ctx.send(embed=warn("No deleted messages."))
            return

        if index < 1 or index > len(msgs):
            await ctx.send(embed=warn("Invalid index."))
            return

        items = list(msgs)
        view = SnipeView(items, ctx.author.id, index)
        await ctx.send(embed=view._embed(), view=view)

    @commands.command(name="is")
    async def is_(self, ctx):
        msgs = self.snipes.get(ctx.channel.id)
        count = len(msgs) if msgs else 0
        await ctx.send(embed=discord.Embed(
            description=f"{count} deleted message(s) stored for this channel.",
            color=COLOR,
        ))


async def setup(bot):
    await bot.add_cog(Snipe(bot))
