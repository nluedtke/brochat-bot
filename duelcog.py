import common
from duel_item import DuelItem
from random import randint
from discord.ext import commands


class DuelCog:
    """Handles Dueling commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name='duel', pass_context=True)
    async def shot_duel(self, ctx):
        """ Duel someone"""

        if ctx.invoked_subcommand is None:
            if common.shot_duel_running:
                await self.bot.say('There is a duel already running, wait your '
                                   'turn to challenge someone!')
                return

        members = self.get_all_members()
        map_disp_to_name = {}
        for m in members:
            map_disp_to_name[m.display_name.lower()] = m

        name = ctx.message.content[7:].lower()
        print(name)

        if len(name) < 1:
            await self.bot.say('Who do you want to duel?')
            return

        if name == ctx.message.author.display_name and message.channel.name != \
                'gen_testing':
            await
            client.send_message(message.channel, "Why not just drink your "
                                                 "tears away, instead of "
                                                 "including this channel?")
        elif name not in map_disp_to_name:
            await
            client.send_message(message.channel,
                                'That\'s not a real person...')
        elif name == 'brochat-bot':
            await
            client.send_message(message.channel,
                                'brochat-bot would drink you under the '
                                'table try another person!')
        elif str(map_disp_to_name[name].status) != 'online':
            await
            client.send_message(message.channel,
                                'That person is likely already passed out!')
        else:
            client.loop.create_task(event_handle_shot_duel(
                message.author, map_disp_to_name[name], message.channel))

    @shot_duel.command(name='ranking', aliases=['ranks'])
    async def get_duel_rankings(self):
        """Display Top 5 dueling rankings"""

        duelers = {}
        # Flatten user records
        for player in common.users:
            if 'duel_record' in common.users[player]:
                duelers[player] = common.users[player]['duel_record']
        if len(duelers) < 1:
            await self.bot.say("Ain't nobody been duelin' round these parts.")
            return
        duelers_sorted = sorted(duelers.items(), reverse=True,
                                key=lambda x: (x[1][0], -x[1][1]))
        output = "The battlefield is bloodied with the :crossed_swords: " \
                 "of these duelers:\n\n"

        ranking = 1
        for d in duelers_sorted:
            output += "**Rank {}**: **{}**, at {}/{}/{}!\n" \
                .format(ranking, d[0], d[1][0], d[1][1], d[1][2])
            ranking += 1
            if ranking > 5:
                break
        await self.bot.say(output)


async def item_chance_roll(ctx, player, max_roll=100):
    """
    Rolls for a chance at an item

    :param ctx: Context
    :param player: Person rolling
    :param max_roll: max roll to use
    """

    if player not in common.users:
        common.users[player] = {}
    init_player_duel_db(player)

    item = DuelItem(randint(1, max_roll + len(common.users[player][
                                              'inventory'])))
    if item.name is not None:
        common.items_awarded += 1
        await ctx.bot.say("Congratulations {}! You received the \"{}\"."
                          .format(player, item.name))
        if item.item_id in common.users[player]['inventory']:
            await ctx.bot.say("You already have that item, its uses have been "
                              "reset!")
        common.users[player]['inventory'][item.item_id] = 0
        return True
    return False


def init_player_duel_db(player):
    """
    Inits a player's DB for items and dueling.

    :param player: player to init
    :return: None
    """

    if 'inventory' not in common.users[player]:
        common.users[player]['inventory'] = {}
        common.users[player]['a_item'] = None
    if 'duel_record' not in common.users[player]:
        common.users[player]['duel_record'] = [0, 0, 0]
