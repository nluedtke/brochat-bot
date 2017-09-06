import asyncio
from datetime import datetime
import pytz
from discord.ext import commands
import common
from cogs.duelcog import item_chance_roll
from objs.weekend_games import pretty_date
from random import choice
from objs.duel_item import get_slot, get_name
from cogs.drinkingcog import consume_drink


class Gametime:
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

    @gametime.command(name="add")
    async def add_gametime(self, day, start_time=None):
        """Create a new gametime"""
        await self.bot.say(common.whos_in.create_gametime(day, start_time))

    @gametime.command(name="remove")
    async def rem_gametime(self, index):
        """Remove a gametime"""
        await self.bot.say(common.whos_in.remove_gametime(index))

    @gametime.command(name="set")
    async def set_gametime(self, index, new_time):
        """Set a gametime"""
        await self.bot.say(common.whos_in.set_gametime(index, new_time))

    @commands.group(name='poll', pass_context=True)
    async def poll(self, ctx):
        """Handles Polls actions"""

        poll_help_string = \
            "That's not a valid command for **!poll**\n\n" \
            "Please use:\n" \
            "!poll start \"option 1\" \"option 2\" etc... to **start a " \
            "poll**\n" \
            "!poll stop to **delete the current poll**"
        if ctx.invoked_subcommand is None:
            await self.bot.say(poll_help_string)

    @poll.command(name='start', pass_context=True)
    async def start_poll(self, ctx):
        """Creates a poll"""
        await self.bot.say(common.whos_in.create_poll(ctx.message.content[6:]))

    @poll.command(name='stop')
    async def stop_poll(self):
        """Stops a poll"""
        await self.bot.say(common.whos_in.stop_poll())

    @commands.command(name='in', pass_context=True)
    async def in_command(self, ctx, gt_num=""):
        """Marks you as in for a gametime"""

        if gt_num == "":
            await self.bot.say("When are you in for, though?\n\n{}"
                               .format(common.whos_in.get_gametimes()))
        else:
            await self.bot.say(common.whos_in.add(ctx.message.author, gt_num,
                               status="in"))

    @commands.command(name='possible', pass_context=True)
    async def possible_command(self, ctx, gt_num=""):
        """Marks you as possible for a gametime"""
        if gt_num == "":
            await self.bot.say("When are you possibly in for, though?\n\n{}"
                               .format(common.whos_in.get_gametimes()))
        else:
            await self.bot.say(common.whos_in.add(ctx.message.author, gt_num,
                               status="possible"))

    @commands.command(name='late', pass_context=True)
    async def late_command(self, ctx, gt_num=""):
        """Marks you as going to be late for a gametime"""
        if gt_num == "":
            await self.bot.say("For what session are you going to be late for, "
                               "though?\n\n{}"
                               .format(common.whos_in.get_gametimes()))
        else:
            await self.bot.say(common.whos_in.add(ctx.message.author, gt_num,
                               status="going to be late"))

    @commands.command(name='out', pass_context=True)
    async def out_command(self, ctx, gt_num=""):
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

    @commands.command(name='vote', pass_context=True)
    async def add_vote(self, ctx, option=""):
        """Vote in a poll"""

        if common.whos_in.poll is None:
            await self.bot.say("No Poll currently taking place")
            return

        if option == "":
            await self.bot.say("What are you voting for, though?\n\n{}"
                               .format(common.whos_in.poll.get_current_state()))
        else:
            try:
                await self.bot.say(
                    common.whos_in.poll.add_vote(option, ctx.message.author))
            except IndexError:
                await self.bot.say("Not a valid option!")


async def print_at_midnight(bot):
    """
    Prints list at midnight
    :return:
    """
    c_to_send = None

    await bot.wait_until_ready()
    for channel in bot.get_all_channels():
        if channel.name == 'gen_testing' or \
                channel.name == common.ARGS['channel']:
            c_to_send = channel
            break

    while not bot.is_closed:
        now = datetime.now(pytz.timezone('US/Eastern'))
        midnight = now.replace(hour=23, minute=59, second=59, microsecond=59)
        if now > midnight:
            midnight = midnight.replace(day=(now.day + 1))
        print("Scheduling next list print at {}".format(pretty_date(midnight)))
        await asyncio.sleep((midnight - now).seconds)
        await bot.send_message(c_to_send, common.whos_in.whos_in())

        # Community Drop Time
        i_awarded = False
        i = False
        while not i_awarded:
            for m in bot.get_all_members():
                if m.display_name != 'brochat-bot' and m.display_name in \
                        common.users and \
                        'duel_record' in common.users[m.display_name]:
                    i = await item_chance_roll(bot, m.display_name, c_to_send)
                i_awarded = i_awarded or i

        # Drink Debt Enforcement
        for m in bot.get_all_members():
            nc = m.display_name
            if 'drinks_owed' in common.users[nc] \
                    and common.users[nc]['drinks_owed'] > 6 \
                    and 'inventory' in common.users[nc] \
                    and len(common.users[nc]['inventory']) > 0:
                item_take = choice(list(common.users[nc]['inventory'].keys()))
                await bot.send_message(c_to_send,
                                       "{}, the bank sent me to collect on "
                                       "your debt. I'll have to take your {} "
                                       "in lieu of one drink. Can't cheap "
                                       "friendship around these parts."
                                       .format(nc, get_name(item_take)))
                if get_slot(item_take) in common.users[nc]['equip']:
                    del(common.users[nc]['equip'][get_slot(item_take)])
                del common.users[nc]['inventory'][item_take]
                bot.send_message(c_to_send,
                                 "You now owe {} drinks."
                                 .format(consume_drink(nc)))
        common.whos_in.update_db()
        await asyncio.sleep(60 * 10)


def setup(bot):
    bot.add_cog(Gametime(bot))
    bot.loop.create_task(print_at_midnight(bot))
