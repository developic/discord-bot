import discord
from discord import ui
from discord.ext import commands
from ._utils import ALLOWED_USERS, COLOR, warn


class ComponentsView(ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=120)

        button_row = ui.ActionRow[
            "ComponentsView"
        ]()

        yes_btn = ui.Button["ComponentsView"](
            label="Yes",
            style=discord.ButtonStyle.success,
        )
        yes_btn.callback = self._yes_callback
        button_row.add_item(yes_btn)

        no_btn = ui.Button["ComponentsView"](
            label="No",
            style=discord.ButtonStyle.danger,
        )
        no_btn.callback = self._no_callback
        button_row.add_item(no_btn)

        container = ui.Container[
            "ComponentsView"
        ](
            ui.TextDisplay(
                "## Compunet V2 Components Test\n"
                "This is a **TextDisplay** inside a **Container**."
            ),
            ui.Separator(spacing=discord.SeparatorSpacing.small),
            ui.TextDisplay(
                "Below the separator you can put more content.\n"
                "Containers support an `accent_color` and `spoiler` too."
            ),
            button_row,
            accent_color=COLOR,
        )
        self.add_item(container)

    async def _yes_callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("You clicked **Yes**!", ephemeral=True)

    async def _no_callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("You clicked **No**!", ephemeral=True)


class Components(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="cv2")
    async def cv2(self, ctx: commands.Context):
        if ALLOWED_USERS and ctx.author.id not in ALLOWED_USERS:
            await ctx.send(embed=warn("You are not allowed to use this command."))
            return
        view = ComponentsView()
        await ctx.send(view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Components(bot))
