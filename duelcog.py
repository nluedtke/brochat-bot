from common import users, items_awarded
from duel_item import DuelItem
from random import randint

async def item_chance_roll(channel, player, max_roll=100):
    """
    Rolls for a chance at an item

    :param channel: channel roll is taking place in
    :param player: Person rolling
    :param max_roll: max roll to use
    """

    if player not in users:
        users[player] = {}
    init_player_duel_db(player)

    item = DuelItem(randint(1, max_roll + len(users[player]['inventory'])))
    if item.name is not None:
        global items_awarded
        items_awarded += 1
        await channel.send_message("Congratulations {}! You received "
                                   "the \"{}\"."
                                   .format(player, item.name))
        if item.item_id in users[player]['inventory']:
            await channel.send_message("You already have that item, its uses "
                                       "have been reset!")
        users[player]['inventory'][item.item_id] = 0
        return True
    return False


def init_player_duel_db(player):
    """
    Inits a player's DB for items and dueling.

    :param player: player to init
    :return: None
    """

    if 'inventory' not in users[player]:
        users[player]['inventory'] = {}
        users[player]['a_item'] = None
    if 'duel_record' not in users[player]:
        users[player]['duel_record'] = [0, 0, 0]
