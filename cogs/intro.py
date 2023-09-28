import discord
from discord import app_commands
from discord.ext.commands import Cog
from discord import ui
from enum import Enum
from bot import CustomBot
from database.intro_queries import IntroQueries
from discord.utils import get
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import asyncio
from decouple import config


def return_names(list_of_enums):
    return [name.value for name in list_of_enums]

TASK_DROPBOX = config('TASK_DROPBOX')

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
    0: "Hey user,\nWelcome to the \"Intro to Discord\" task. Are you ready to explore our Discord server?",
    1: "I hope your onboarding process went smoothly. Our mention_channel channel is where we extend a warm welcome to new members of our community. There's actually a special greeting card waiting for you in that very channel. Feel free to take a moment and check it out!",
    2: "Please take a moment to visit our rules and readme in mention_channel channel, and kindly adhere to our straightforward guidelines to become a valued member of our community.",
    3: "Keen to follow up the activities of μLearn? We've compiled the schedules of all our current and upcoming events just for you 📣\nHead on to the mention_channel channel for all our updates!",
    4: "Ever thought of acquiring a job through μLearn? You'll be glad to know that not just students, even companies onboard GTech μLearn in search of talent 💫\nVisit mention_channel to keep track of announcements and opportunities from our partner companies.",
    5: "Tasks are allotted according to your current level in the μLearn Discord server. Visit the channel corresponding to your current level to know more about the tasks and their corresponding Karma Points ✨",
    6: "Hello µLearner! Great to have you onboard. Eager to know about your peers? Start by posting an introduction about yourself 🙋\nHead on to mention_channel channel to meet your peers and introduce yourself to them!",
    7: "Karma Point is a digital score system implemented at μLearn. Each task is associated with a specific amount of Karma Points that can be earned once the proof of completion of that task has been submitted 🪙Buckle up and mine Karma Points and climb all the way up the leaderboard! Here is a task for you\n\nMy Muid\n Post your muid with the hashtag '#my-muid' in this channel\nEg: #my-muid ousu@mulearn",
    8: "μLearn follows a peer approval system, which means all tasks submitted by you are reviewed by none other than your peers!\nThe reviewers are specially assigned for this role and their task is to flag your proof of work according to its validity.\n• 🚩 - A red flag means your task is ineligible to get Karma points due to some reason.\n• 🏁 - A checkered flag means your task is eligible and Karma Points will be awarded shortly.\nSo next time you submit a task, pay heed to its peer approval status and do rectify errors if any 😇",
    9: "Once you've submitted a task and your proof of work has been reviewed, the next step is awarding of Karma Points!\n• ✅ - A green tick box means your task has been awarded Karma Points.\nAll tasks that have been appraised as shown above are automatically rewarded Karma Points ✨",
    10: "Once your task has been verified and rewarded Karma Points, you'll be notified about the same in your Discord DM by our bot 💫\nmessage_id can be used to keep track of all the tasks for which you've earned Karma Points systematically!",
    11: "What if I said you can earn Karma points just by chatting? μLearn now awards you Chat Karma for connecting with your peers in the respective text channel 🥳\nMaintain your streak and walk away with a daily bundle of Karma Points just by chatting!",
    12: "Who does not like a bit a competition amongst their peers? Your Rank tells you how far you're ahead of your peers. Maximize your Karma mining and don't let the others topple you on your way to the leaderboard 🔥\nVisit the mention_channel channel and use the /rank command to see where you stand among your fellow learners!",
    13: "Have any doubts regarding the task? Were your Karma Points not allotted properly? Is there any error in your rank? Facing any further other issue at μLearn Discord server? Worry not! We're always here to help 😌\nAll you got to do is raise a support ticket using the command /support-ticket in any of our text channels and our moderators will be in touch shortly to resolve all your current issues!",
    14: "Need real-time help or support in our sever? Tag the Discord Moderator by selecting @Discord Moderator from the pop in any available text channel.\nWe'll make sure your issue gets resolved as soon as possible "
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
        await self.check_msg(message)

    @app_commands.command(name="intro", description="intro to mulearn")
    async def intro(self, interaction: discord.Interaction):
        if self.intro_queries.is_intro_done(interaction.user.id):
            await interaction.response.send_message("You have already completed the intro task", ephemeral=True)
            return
        if self.intro_queries.is_intro_started(interaction.user.id):
            await interaction.response.send_message("You have already started the intro task", ephemeral=True)
            return
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
        await interaction.response.send_message(f"Please navigate to {channel.mention} to complete the intro-task", ephemeral=True)
        await channel.send(step[0].replace('user', interaction.user.mention))
        await asyncio.sleep(3600)
        self.intro_queries.delete_log(interaction.user.id)
        await channel.delete()

    async def check_msg(self, message):
        if self.intro_queries.is_valid_channel(message.channel.id, message.author.id):
            order = self.intro_queries.check_step_order(message.author.id)
            if order == 7:
                if self.intro_queries.is_muidtask_done(message.author.id):
                    order = 11
            if order == 8:
                if not await self.peer_approve(message):
                    return
            if order == 9:
                task_message_id = self.intro_queries.fetch_task_message_id(message.author.id)
                if not await self.appraiser_approval(message.channel, task_message_id):
                    return
            if order == 15:
                await message.channel.send("You will recieve your certificate in dm")
                await message.author.send(f'You have successfully completed the intro task. Here is your certificate🎉. Please post the certificate in {TASK_DROPBOX} channel with the hashtag **#ge-intro-to-discord** to avail 100 karma points')
                await self.award_certificate(message)
                self.intro_queries.delete_log(message.author.id)
                await message.channel.delete()
                return
            mention_channel_name = None
            if order == 1:
                mention_channel_name = "welcome"
            elif order == 2:
                mention_channel_name = "rules-and-readme"
            elif order == 3:
                mention_channel_name = "announcements"
            elif order == 4:
                mention_channel_name = "career-labs"
            elif order == 5:
                mention_channel_name = "lvl1-info"
            elif order == 6:
                mention_channel_name = "self-introduction"
            elif order == 12:
                mention_channel_name = "know-your-rank"
            if mention_channel_name:
                for channel in message.guild.channels:
                    if channel.name == mention_channel_name:
                        break
                await message.channel.send(step[order].replace("mention_channel", channel.mention))
                await message.channel.send("NB: Please return back to intro channel")
            elif order == 10:
                lobby_messagge_id = self.intro_queries.fetch_lobby_message_id(message.author.id)
                for channel in message.guild.channels:
                    if channel.name == 'karma-alerts':
                        break
                lobby_message = await channel.fetch_message(lobby_messagge_id)
                await message.channel.send(step[order].replace("message_id", lobby_message.jump_url))
            else :
                await message.channel.send(step[order])
            self.intro_queries.update_progress(message.author.id, order + 1)

    async def peer_approve(self, message):
        if not message.content.startswith("#my-muid"):
            await message.channel.send("Please use hashtag")
            return False
        hashtag = message.content.split()[1] if len(message.content.split())>1 else None
        if hashtag is None or self.intro_queries.check_muid(message.author.id, hashtag) is None:
            await message.add_reaction(Flags.RED_FLAG.value)
            await message.channel.send("Please submit your valid muid")
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
        draw.text((150, 900), name, fill=color_white,font=font_bigger, align="center")
        out = BytesIO()
        background.save(out, format="PNG")
        out.seek(0)
        await message.author.send(file=discord.File(out, filename="certificate.png"))

async def setup(bot: CustomBot) -> None:
    """Add the Example cog to the bot tree"""
    await bot.add_cog(IntroCog(bot))
