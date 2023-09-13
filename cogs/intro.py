import discord
from discord import app_commands
from discord.ext.commands import Cog
from enum import Enum
from bot import CustomBot
from database.intro_queries import IntroQueries
from discord.utils import get

class Role(Enum):
    ADMIN = "Admins"
    DISCORD_MODERATOR = "Discord Moderator"
    FELLOW = "Fellow"
    ASSOCIATE = "Associate"
    APPRAISER = "Appraiser"


class IntroCog(Cog):
    """An example cog for adding an app command to the bot tree"""

    def __init__(self, bot: CustomBot) -> None:
        self.bot = bot
        self.intro_queries = IntroQueries(self.bot.db)

    @app_commands.command(name="intro", description="intro to mulearn")
    async def intro(self, interaction: discord.Interaction, user: discord.Member = None):
        #task already done checking
        guild = interaction.guild
        category = get(guild.categories, name='Intro To MuLearn')
        if category is None:
            category = await guild.create_category('Intro To MuLearn')
            discord_moderator = get(guild.roles, name=Role.DISCORD_MODERATOR.value)
            await category.set_permissions(guild.default_role, read_messages=False)
            await category.set_permissions(discord_moderator, read_messages=True, send_messages=True)
        channel = await guild._create_channel(category=category)
        #set channel permission
        await interaction.response.send_message("hello", delete_after=10)

    @Cog.listener()
    async def on_message(self, message):
        await message.reply("Welcome")

async def setup(bot: CustomBot) -> None:
    """Add the Example cog to the bot tree"""
    await bot.add_cog(IntroCog(bot))
