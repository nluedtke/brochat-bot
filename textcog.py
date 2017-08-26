import discord
from discord.ext import commands
import common


class TextCog:
    """ Send Text Handlers"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='text', type=commands.BucketType.user)
    @commands.cooldown(1, 60 * 5)
    async def dankmeme(self, person=""):
        """Get a fool in the loop"""
        if common.twilio_client is None:
            await self.bot.say('Text functionality turned off.')
            return

        if person == "":
            await self.bot.say('Just give me a name, I\'ll do the rest!')
        elif person not in common.users:
            await self.bot.say('That\'s not a real name...')
        elif 'mobile' not in common.users[person]:
            await self.bot.say('That person doesn\'t have a mobile. So poor!')
        else:
            try:
                twilio_message = common.twilio_client.messages.create(
                    to=common.users[person]['mobile'], from_="+16088880320",
                    body="@brochat-bot: Brochat calls, {}. "
                         "Friendship and glory await you. Join us!".format(
                        person))
                await self.bot.say('Text message sent!')
            except:
                await self.bot.say('Could not send text message!')


def setup(bot):
    bot.add_cog(TextCog(bot))
