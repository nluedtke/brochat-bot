import common
import discord
from discord.ext import commands


class Texting(commands.Cog):
    """ Send Text Handlers"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='text', type=commands.BucketType.user)
    @commands.cooldown(1, 60 * 5)
    async def dankmeme(self, ctx, person=""):
        """Get a fool in the loop"""
        if common.twilio_client is None:
            await ctx.send('Text functionality turned off.')
            return

        if person == "":
            await ctx.send('Just give me a name, I\'ll do the rest!')
        elif person not in common.users:
            await ctx.send('That\'s not a real name...')
        elif 'mobile' not in common.users[person]:
            await ctx.send('That person doesn\'t have a mobile. So poor!')
        else:
            try:
                twilio_message = common.twilio_client.messages.create(
                    to=common.users[person]['mobile'], from_="+16088880320",
                    body="@brochat-bot: Brochat calls, {}. "
                         "Friendship and glory await you. Join us!".format(
                        person))
                await ctx.send('Text message sent!')
            except:
                await ctx.send('Could not send text message!')


def setup(bot):
    bot.add_cog(Texting(bot))
