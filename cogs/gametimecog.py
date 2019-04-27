import asyncio
from datetime import datetime
from random import choice

import pytz

import common
from cogs.drinkingcog import consume_drink
from cogs.duelcog import item_chance_roll
from discord.ext import commands
from objs.duel_item import get_name, get_slot
from objs.weekend_games import pretty_date


class Gametime(commands.Cog):
    """ Gametime Commands"""

    @commands.group(name='gametime')
    async def gametime(ctx):
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
            await ctx.send(gametime_help_string)

    @gametime.command(name="list")
    async def list_gametimes(ctx):
        """List current gametimes"""
        await ctx.send(common.whos_in.get_gametimes())

    @gametime.command(name="add")
    async def add_gametime(ctx, day, start_time=None):
        """Create a new gametime"""
        await ctx.send(common.whos_in.create_gametime(day, start_time))

    @gametime.command(name="remove")
    async def rem_gametime(ctx, index):
        """Remove a gametime"""
        await ctx.send(common.whos_in.remove_gametime(index))

    @gametime.command(name="set")
    async def set_gametime(ctx, index, new_time):
        """Set a gametime"""
        await ctx.send(common.whos_in.set_gametime(index, new_time))

    @commands.group(name='poll')
    async def poll(ctx):
        """Handles Polls actions"""

        poll_help_string = \
            "That's not a valid command for **!poll**\n\n" \
            "Please use:\n" \
            "!poll start \"option 1\" \"option 2\" etc... to **start a " \
            "poll**\n" \
            "!poll stop to **delete the current poll**"
        if ctx.invoked_subcommand is None:
            await ctx.send(poll_help_string)

    @poll.command(name='start')
    async def start_poll(ctx):
        """Creates a poll"""
        await ctx.send(common.whos_in.create_poll(ctx.message.content[6:]))

    @poll.command(name='stop')
    async def stop_poll(ctx):
        """Stops a poll"""
        await ctx.send(common.whos_in.stop_poll())

    @commands.command(name='in')
    async def in_command(ctx, gt_num=""):
        """Marks you as in for a gametime"""

        if gt_num == "":
            await ctx.send("When are you in for, though?\n\n{}"
                               .format(common.whos_in.get_gametimes()))
        else:
            await ctx.send(common.whos_in.add(ctx.message.author, gt_num,
                               status="in"))

    @commands.command(name='possible')
    async def possible_command(ctx, gt_num=""):
        """Marks you as possible for a gametime"""
        if gt_num == "":
            await ctx.send("When are you possibly in for, though?\n\n{}"
                               .format(common.whos_in.get_gametimes()))
        else:
            await ctx.send(common.whos_in.add(ctx.message.author, gt_num,
                               status="possible"))

    @commands.command(name='late')
    async def late_command(ctx, gt_num=""):
        """Marks you as going to be late for a gametime"""
        if gt_num == "":
            await ctx.send("For what session are you going to be late for, "
                               "though?\n\n{}"
                               .format(common.whos_in.get_gametimes()))
        else:
            await ctx.send(common.whos_in.add(ctx.message.author, gt_num,
                               status="going to be late"))

    @commands.command(name='out')
    async def out_command(ctx, gt_num=""):
        """Removes you from a gametime"""
        if gt_num == "":
            await ctx.send("When are you out for, though?\n\n{}"
                               .format(common.whos_in.get_gametimes()))
        else:
            await ctx.send(common.whos_in.remove(ctx.message.author,
                                                     gt_num))

    @commands.command(name='whosin')
    async def whosin_command(ctx):
        """See who is in for a gametime"""
        await ctx.send(common.whos_in.whos_in())

    @commands.command(name='win')
    async def record_win(ctx):
        """Add a win to the record books"""

        common.whos_in.add_win()
        await ctx.send("Congrats on the win!")
        await ctx.invoke(ctx.get_command('get-record'))
        if common.whos_in.consecutive == 3:
            await common.trigger_social(ctx)
            common.whos_in.consecutive = 0
        else:
            await ctx.invoke(ctx.get_command('shot-lottery'), True)

    @commands.command(name='loss')
    async def record_loss(ctx):
        """Add a loss to the record books"""
        common.whos_in.add_loss()
        await ctx.send("You guys are bad!")
        await ctx.invoke(ctx.get_command('get-record'))
        if common.whos_in.consecutive == 3:
            await common.trigger_social(ctx)
            common.whos_in.consecutive = 0

    @commands.command(name='draw')
    async def record_draw(ctx):
        """Add a draw to the record books"""
        common.whos_in.add_draw()
        await ctx.send("What a waste!")
        await ctx.invoke(ctx.get_command('get-record'))
        if common.whos_in.consecutive == 3:
            await common.trigger_social(ctx)
            common.whos_in.consecutive = 0

    @commands.command(name='clear-record')
    async def record_clear(ctx):
        """Clears the session record."""
        record_string = "You went: {}".format(common.whos_in.get_record())
        await ctx.send(record_string)
        common.whos_in.clear_record()
        await ctx.send("Record Cleared!")

    @commands.command(name='get-record')
    async def record_get(ctx):
        """Get the current record."""
        record_string = "Current Record: {}".format(common.whos_in.get_record())
        await ctx.send(record_string)
        record_string = "Overall Record {}".format(
            common.whos_in.get_c_record())
        await ctx.send(record_string)

    @commands.command(name='vote')
    async def add_vote(ctx, option=""):
        """Vote in a poll"""

        if common.whos_in.poll is None:
            await ctx.send("No Poll currently taking place")
            return

        if option == "":
            await ctx.send("What are you voting for, though?\n\n{}"
                               .format(common.whos_in.poll.get_current_state()))
        else:
            try:
                await ctx.send(
                    common.whos_in.poll.add_vote(option, ctx.message.author))
            except IndexError:
                await ctx.send("Not a valid option!")


async def print_at_midnight(ctx):
    """
    Prints list at midnight
    :return:
    """
    c_to_send = None

    await ctx.wait_until_ready()
    for channel in ctx.get_all_channels():
        if channel.name == 'gen_testing' or \
                channel.name == common.ARGS['channel']:
            c_to_send = channel
            break

    while not ctx.is_closed:
        now = datetime.now(pytz.timezone('US/Eastern'))
        midnight = now.replace(hour=23, minute=59, second=59, microsecond=59)
        if now > midnight:
            midnight = midnight.replace(day=(now.day + 1))
        print("Scheduling next list print at {}".format(pretty_date(midnight)))
        await asyncio.sleep((midnight - now).seconds)
        common.whos_in.remove_old_gametimes()
        await c_to_send.send(common.whos_in.whos_in())

        # Community Drop Time
        i_awarded = False
        i = False
        while not i_awarded:
            for m in ctx.get_all_members():
                if m.display_name != 'brochat-bot' and m.display_name in \
                        common.users and \
                        'duel_record' in common.users[m.display_name]:
                    i = await item_chance_roll(m.display_name, c_to_send)
                i_awarded = i_awarded or i

        # Drink Debt Enforcement
        for m in ctx.get_all_members():
            nc = m.display_name
            if nc != 'brochat-bot' and nc in common.users and \
                    'drinks_owed' in common.users[nc] \
                    and common.users[nc]['drinks_owed'] > 6 \
                    and 'inventory' in common.users[nc] \
                    and len(common.users[nc]['inventory']) > 0:
                item_take = choice(list(common.users[nc]['inventory'].keys()))
                await c_to_send.send("{}, the bank sent me to collect on "
                                       "your debt. I'll have to take your {} "
                                       "in lieu of one drink. Can't cheat "
                                       "friendship around these parts."
                                       .format(nc, get_name(item_take)))
                if get_slot(item_take) in common.users[nc]['equip']:
                    del(common.users[nc]['equip'][get_slot(item_take)])
                del common.users[nc]['inventory'][item_take]
                await c_to_send.send("You now owe {} drinks."
                                                  .format(consume_drink(nc)))
        common.whos_in.update_db()
        await asyncio.sleep(60 * 10)


def setup(bot):
    bot.add_cog(Gametime(bot))
    bot.loop.create_task(print_at_midnight(bot))
