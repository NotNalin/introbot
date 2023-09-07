import discord
from discord import app_commands
from discord.ext.commands import Cog

from bot import CustomBot
from database.intro_queries import IntroQueries


class IntroCog(Cog):
    """An example cog for adding an app command to the bot tree"""

    def __init__(self, bot: CustomBot) -> None:
        self.bot = bot
        self.intro_queries = IntroQueries(self.bot.db)

    @app_commands.command(name="intro", description="intro to mulearn")
    async def intro(self, interaction: discord.Interaction, user: discord.Member = None):
        return await interaction.response.send_message("hello", delete_after=10)


async def setup(bot: CustomBot) -> None:
    """Add the Example cog to the bot tree"""
    await bot.add_cog(IntroCog(bot))
