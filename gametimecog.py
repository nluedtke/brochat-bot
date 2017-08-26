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

    @commands.command(name='win', pass_context=True)
    async def record_win(self, ctx):
        """Add a win to the record books"""

        common.whos_in.add_win()
        await self.bot.say("Congrats on the win!")
        await ctx.invoke(self.bot.get_command('get-record'))
        if common.whos_in.consecutive == 3:
            await common.trigger_social(ctx)
            common.whos_in.consecutive = 0
        else:
            await ctx.invoke(self.bot.get_command('shot-lottery'), True)

    @commands.command(name='loss', pass_context=True)
    async def record_loss(self, ctx):
        """Add a loss to the record books"""
        common.whos_in.add_loss()
        await self.bot.say("You guys are bad!")
        await ctx.invoke(self.bot.get_command('get-record'))
        if common.whos_in.consecutive == 3:
            await common.trigger_social(ctx)
            common.whos_in.consecutive = 0

    @commands.command(name='draw', pass_context=True)
    async def record_draw(self, ctx):
        """Add a draw to the record books"""
        common.whos_in.add_draw()
        await self.bot.say("What a waste!")
        await ctx.invoke(self.bot.get_command('get-record'))
        if common.whos_in.consecutive == 3:
            await common.trigger_social(ctx)
            common.whos_in.consecutive = 0

    @commands.command(name='clear-record')
    async def record_clear(self):
        """Clears the session record."""
        record_string = "You went: {}".format(common.whos_in.get_record())
        await self.bot.say(record_string)
        common.whos_in.clear_record()
        await self.bot.say("Record Cleared!")

    @commands.command(name='get-record')
    async def record_get(self):
        """Get the current record."""
        record_string = "Current Record: {}".format(common.whos_in.get_record())
        await self.bot.say(record_string)
        record_string = "Overall Record {}".format(
            common.whos_in.get_c_record())
        await self.bot.say(record_string)


def setup(bot):
    bot.add_cog(GametimeCog(bot))