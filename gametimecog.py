import discord
from discord.ext import commands
import common


class GametimeCog:
    """ Gametime Commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name='gametime', pass_context=True)
    async def gametime(self, ctx):
        """Handles gametime actions"""

        gametime_help_string = \
            "That's not a valid command for **!gametime**\n\n" \
            "Please use:\n" \
            "!gametime <add> <day of the week>" \
            "<_optional_: military time, HH:MM> to **add a gametime**\n" \
            "!gametime <remove> <index> to **delete a gametime**\n" \
            "!gametime <list> to **list current gametimes**\n" \
            "!gametime <set> <index> <time> to " \
            "**set the time of a gametime**"
        if ctx.invoked_subcommand is None:
            await self.bot.say(gametime_help_string)

    @gametime.command(name="list")
    async def list_gametimes(self):
        """List current gametimes"""
        await self.bot.say(common.whos_in.get_gametimes())

    @commands.command(name='in', pass_context=True)
    async def in_command(self, ctx, gt_num):
        """Marks you as in for a gametime"""

        if gt_num == "":
            await self.bot.say("When are you in for, though?\n\n{}"
                               .format(common.whos_in.get_gametimes()))
        else:
            await self.bot.say(common.whos_in.add(ctx.message.author, gt_num,
                                           status="in"))

    @commands.command(name='possible', pass_context=True)
    async def possible_command(self, ctx, gt_num):
        """Marks you as possible for a gametime"""
        if gt_num == "":
            await self.bot.say("When are you possibly in for, though?\n\n{}"
                               .format(common.whos_in.get_gametimes()))
        else:
            await self.bot.say(common.whos_in.add(ctx.message.author, gt_num,
                                           status="possible"))

    @commands.command(name='late', pass_context=True)
    async def late_command(self, ctx, gt_num):
        """Marks you as going to be late for a gametime"""
        if gt_num == "":
            await self.bot.say("For what session are you going to be late for, "
                               "though?\n\n{}"
                               .format(common.whos_in.get_gametimes()))
        else:
            await self.bot.say(common.whos_in.add(ctx.message.author, gt_num,
                                           status="going to be late"))

    @commands.command(name='out', pass_context=True)
    async def out_command(self, ctx, gt_num):
        """Removes you from a gametime"""
        if gt_num == "":
            await self.bot.say("When are you out for, though?\n\n{}"
                               .format(common.whos_in.get_gametimes()))
        else:
            await self.bot.say(common.whos_in.remove(ctx.message.author,
                                                     gt_num))

    @commands.command(name='whosin')
    async def whosin_command(self):
        """See who is in for a gametime"""
        await self.bot.say(common.whos_in.whos_in())


def setup(bot):
    bot.add_cog(GametimeCog(bot))