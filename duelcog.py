import common
from duel_item import DuelItem
from random import randint

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
