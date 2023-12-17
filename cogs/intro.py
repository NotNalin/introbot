import discord
from discord import app_commands
from discord.ext.commands import Cog
from enum import Enum
from bot import CustomBot
from database.intro_queries import IntroQueries
from discord.utils import get
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import asyncio
from decouple import config
import random

TASK_DROPBOX = config('TASK_DROPBOX')


def return_names(list_of_enums):
    return [name.value for name in list_of_enums]


class Role(Enum):
    ADMIN = "Admins"
    DISCORD_MODERATOR = "Discord Moderator"
    FELLOW = "Fellow"
    ASSOCIATE = "Associate"
    APPRAISER = "Appraiser"

    @classmethod
    def discord_managers(cls):
        return return_names([cls.ADMIN, cls.FELLOW, cls.DISCORD_MODERATOR])


step = {
    0: "Hey user,\nWelcome to the \"Intro to Discord\" task. Are you ready to explore our Discord server?\nType “Let’s go!” to move on!☺️",
    1: "Hope your onboarding went smoothly. Our mention_channel channel is where we extend a warm welcome to new members of our community.",
    2: "Make sure to read up our rules! Check out mention_channel channel! After all, your learning space; our rules! 😁",
    3: "Get the latest news and updates on your fav events at mention_channel! Keep your eyes and ears peeled for more news! 👀",
    4: "Stay in the loop with our latest events and unexpected surprises by following us on Instagram! Check out our profile at https://www.instagram.com/mulearn.official/ for updates.",
    5: "Excited to start your career? It all starts at mention_channel! Get your hiring call today! 📢",
    6: "Confused about what tasks you have to do? Visit the mention_channel channel for the complete rundown! ✨",
    7: "Bring yourself to the spotlight at mention_channel! Introduce yourself and show ‘em what you got using the hashtag **#ge-self-intro**",
    8: "You submit projects, you get karma points! Simple as that! Rack up those karma points for greater rewards! 🤩\nWanna get your μID in an instant? Use the /get-muid command!\nCopy-paste that μID and reply with **#my-muid <μID>**\ne.g.: #my-muid name@mulearn",
    9: "Your task submission happens here!\n🚩 **Red Flag** means there is an issue with the task submission and Discord mods will even point out the error!\n🏁 **Checkered Flag** means it’s all good! 😎🏁",
    10: "Wanna know if a task has been awarded karma points? If the task got a “✅”, then it’s all good! 😎",
    11: "message_id is where all karma alerts happen! You could even say it’s Karma Central! Track the flow of your karma points there! ✨",
    12: "Don’t keep the rooms silent! Chat like there’s no tomorrow! You can earn upto 900 karma points per month😉",
    13: "Want to know where you stand in the community? Type **/rank** in mention_channel to know your rank!",
    14: "Need technical support? We gotchu! Use /support-ticket command to get a support ticket and raise your issue!🤝",
    15: "Need some help on a task or having trouble? We’re here to rescue the day! Type @Discord Moderators to ping a discord mod to take care of the matter!🔥"
}


class Flags(Enum):
    CHECKERED_FLAG = '🏁'
    RED_FLAG = '🚩'
    CHECKBOX = '✅'


class IntroCog(Cog):
    """An example cog for adding an app command to the bot tree"""

    def __init__(self, bot: CustomBot) -> None:
        self.bot = bot
        self.intro_queries = IntroQueries(self.bot.db)

    @Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        await self.aaronchettan_status(message)
        await self.check_msg(message)

    async def aaronchettan_status(self, message):
        if not self.intro_queries.is_aaronchettan_up():
            s = [
                "Aaronchettan is not here right now. In the meantime, try the typing challenge.",
                "Aaronchettan has got to run some errands. He’ll be back by the time you follow our [Instagram](https://www.instagram.com/mulearn.official).",
                "Aaronchettan is facing some issues right now. Mingle with your fellow learners while you wait.",
                "Aaronchettan is currently unavailable, but hey when was the last time you checked your rank?",
                "Aaronchettan is under maintenance. Feel free to check out the leaderboards!",
                "Aaronchettan has some secret dealings. Check out our latest announcements.",
                "Aaronchettan is busy right now, but try checking out some projects from the projects channel."
            ]
            return message.reply(random.choice(s))

    @app_commands.command(name="intro", description="intro to mulearn")
    async def intro(self, interaction: discord.Interaction):
        if self.intro_queries.is_intro_done(interaction.user.id):
            return await interaction.response.send_message("You have already completed the intro task", ephemeral=True)

        if self.intro_queries.is_intro_started(interaction.user.id):
            channel_id = self.intro_queries.fetch_channel_id(interaction.user.id)
            channel = interaction.guild.get_channel(int(channel_id))
            return await interaction.response.send_message(
                f"You have already started the intro task. Please navigate to {channel.mention}", ephemeral=True)

        guild = interaction.guild
        access_roles = [get(guild.roles, name=name) for name in Role.discord_managers()]
        category = get(guild.categories, name="INTRO TO MULEARN")
        if category is None:
            category = await guild.create_category("INTRO TO MULEARN")
        old_overwrites = {key: discord.PermissionOverwrite(
            read_messages=True, send_messages=True, read_message_history=True
        ) for key in access_roles}
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True),
            interaction.user: discord.PermissionOverwrite(
                read_messages=True, send_messages=True, read_message_history=True
            ),
        }
        overwrites.update(old_overwrites)
        channel = await guild.create_text_channel(
            f"intro-{interaction.user.name}",
            overwrites=overwrites,
            category=category,
        )

        self.intro_queries.insert_user(interaction.user.id, channel.id)
        await interaction.response.send_message(f"Please navigate to {channel.mention} to complete the intro-task",
                                                ephemeral=True)
        await channel.send(step[0].replace('user', interaction.user.mention))
        await asyncio.sleep(3600)
        self.intro_queries.delete_log(interaction.user.id)
        await channel.delete()

    async def check_msg(self, message):
        if not self.intro_queries.is_valid_channel(
                message.channel.id, message.author.id
        ):
            return
        order = self.intro_queries.check_step_order(message.author.id)
        if order == 8 and self.intro_queries.is_muidtask_done(message.author.id):
            order = 12
        if order == 9 and not await self.peer_approve(message):
            return
        if order == 10:
            task_message_id = self.intro_queries.fetch_task_message_id(message.author.id)
            if not await self.appraiser_approval(message.channel, task_message_id):
                return
        if order == 16:
            await message.channel.send(
                "Great news! You've successfully completed the task. Your certificate will be sent to you via direct message")
            await message.author.send(
                f'You have successfully completed the intro task. Here is your certificate🎉. Please post the certificate in {TASK_DROPBOX} channel with the hashtag **#ge-discord-guide** to avail 100 karma points')
            await self.award_certificate(message)
            self.intro_queries.delete_log(message.author.id)
            return await message.channel.delete()

        mention_channel_name = None
        if order == 1:
            mention_channel_name = "welcome"
        elif order == 13:
            mention_channel_name = "know-your-rank"
        elif order == 2:
            mention_channel_name = "rules-and-readme"
        elif order == 3:
            mention_channel_name = "announcements"
        elif order == 5:
            mention_channel_name = "career-labs"
        elif order == 6:
            mention_channel_name = "lvl1-info"
        elif order == 7:
            mention_channel_name = "self-introduction"
        if mention_channel_name:
            for channel in message.guild.channels:
                if channel.name == mention_channel_name:
                    break
            await message.channel.send(step[order].replace("mention_channel", channel.mention))
            if order == 1:
                await message.channel.send(
                    "Note: Remember to come back here to complete the full process after navigating through our server! 😅")
        elif order == 11:
            lobby_message_id = self.intro_queries.fetch_lobby_message_id(message.author.id)
            for channel in message.guild.channels:
                if channel.name == 'karma-alerts':
                    break
            lobby_message = await channel.fetch_message(lobby_message_id)
            await message.channel.send(step[order].replace("message_id", lobby_message.jump_url))
        else:
            await message.channel.send(step[order])
        if order != 8:
            await message.channel.send("Type **done** to move on!")
        self.intro_queries.update_progress(message.author.id, order + 1)

    async def peer_approve(self, message):
        if not message.content.startswith("#my-muid"):
            await message.channel.send("Please repost with correct hashtag 🥲")
            return False
        hashtag = message.content.split()[1] if len(message.content.split()) > 1 else None
        if hashtag is None or self.intro_queries.check_muid(message.author.id, hashtag) is None:
            await message.add_reaction(Flags.RED_FLAG.value)
            await message.channel.send("Invalid muid. Please repost with correct muid 🥲")
            return False
        await message.add_reaction(Flags.CHECKERED_FLAG.value)
        return True

    async def appraiser_approval(self, channel, message_id):
        message = await channel.fetch_message(message_id)
        emoji = [reaction.emoji for reaction in message.reactions]
        if Flags.CHECKERED_FLAG.value in emoji and Flags.CHECKBOX.value not in emoji and Flags.RED_FLAG.value not in emoji:
            await message.add_reaction(Flags.CHECKBOX.value)
            return True
        return False

    async def award_certificate(self, message):
        author = message.author
        bg_image_path = "assets/certificate/certificate.png"
        color_white = "rgb(255, 255, 255)"
        name = author.display_name.split("(")[0]
        name = name.title()
        font_bigger = ImageFont.truetype("assets/fonts/Poppins-SemiBold.ttf", 100)
        background = Image.open(bg_image_path)
        draw = ImageDraw.Draw(background)
        draw.text((150, 900), name, fill=color_white, font=font_bigger, align="center")
        out = BytesIO()
        background.save(out, format="PNG")
        out.seek(0)
        await message.author.send(file=discord.File(out, filename="certificate.png"))


async def setup(bot: CustomBot) -> None:
    """Add the Example cog to the bot tree"""
    await bot.add_cog(IntroCog(bot))
