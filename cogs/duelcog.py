import asyncio
from random import choice, randint

import common
from cogs.drinkingcog import in_deep_debt
from discord.ext import commands
from objs.duel_item import (DuelItem, PoisonEffect, get_name, get_slot,
                            get_text, get_uses, item_exists)


class Duels(commands.Cog):
    """Handles Dueling commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name='duel')
    @commands.cooldown(1, 120)
    async def shot_duel(self, ctx):
        """ Duel someone"""

        if ctx.invoked_subcommand is None:
            if common.shot_duel_running:
                await ctx.send('There is a duel already running, wait your '
                               'turn to challenge someone!',
                               delete_after=60*60*1)
                self.bot.get_command('duel').reset_cooldown(ctx)
                return

            if in_deep_debt(ctx.message.author.display_name):
                await ctx.send('Hey there, I can\'t let you do that till '
                               'you pay down some of that friendship you '
                               'owe.',
                               delete_after=60*60*1)
                self.bot.get_command('duel').reset_cooldown(ctx)
                return

            members = self.bot.get_all_members()
            map_disp_to_name = {}
            for m in members:
                map_disp_to_name[m.display_name.lower()] = m

            name = ctx.message.content[6:].lower()

            if len(name) < 1:
                await ctx.send('Who do you want to duel?',
                               delete_after=60*60*1)
                self.bot.get_command('duel').reset_cooldown(ctx)
                return

            if name == ctx.message.author.display_name.lower() and \
                    ctx.message.channel.name != 'gen_testing':
                await ctx.send("Why not just drink your tears away, "
                               "instead of including this channel?",
                               delete_after=60*60*1)
            elif name not in map_disp_to_name:
                await ctx.send('That\'s not a real person...',
                               delete_after=60*60*1)
                self.bot.get_command('duel').reset_cooldown(ctx)
            elif name == 'brochat-bot':
                await ctx.send('brochat-bot would drink you under the '
                               'table, try another person!',
                               delete_after=60*60*1)
                self.bot.get_command('duel').reset_cooldown(ctx)
            elif str(map_disp_to_name[name].status) != 'online':
                await ctx.send('That person is likely already passed out!',
                               delete_after=60*60*1)
                self.bot.get_command('duel').reset_cooldown(ctx)
            else:
                await event_handle_shot_duel(ctx, map_disp_to_name[name],
                                             self.bot)

    @shot_duel.command(name='ranking', aliases=['ranks'])
    async def get_duel_rankings(self, ctx):
        """Display Top 5 dueling rankings"""

        duelers = {}
        # Flatten user records
        for player in common.users:
            if 'duel_record' in common.users[player]:
                duelers[player] = common.users[player]['duel_record']
        if len(duelers) < 1:
            await ctx.send("Ain't nobody been duelin' round these parts.",
                           delete_after=60*60*1)
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
        await ctx.send(output, delete_after=60*60*1)
        self.bot.get_command('duel').reset_cooldown(ctx)

    @shot_duel.command(name='random', aliases=['rand'])
    async def duel_random(self, ctx):
        """Duel a random person"""
        members = self.bot.get_all_members()
        map_disp_to_name = {}
        for m in members:
            map_disp_to_name[m.display_name.lower()] = m

        while True:
            if len(map_disp_to_name) <= 0:
                await ctx.send('No one found to duel!', delete_after=60*60*1)
                self.bot.get_command('duel').reset_cooldown(ctx)
                return
            p = choice(list(map_disp_to_name.keys()))[:]
            if str(map_disp_to_name[p].status) == 'online' and \
                    p != ctx.message.author.display_name and \
                    p != 'brochat-bot' and 'duel_record' in \
                    common.users[map_disp_to_name[p].display_name]:
                await event_handle_shot_duel(ctx, map_disp_to_name[p],
                                             self.bot)
                return
            else:
                del(map_disp_to_name[p])

    @commands.command(name='accept')
    async def toggle_accept(self, ctx):
        """Accept a challenge"""

        if common.shot_duel_running and ctx.message.author.display_name == \
                common.vict_name:
            common.accepted = True
        else:
            await ctx.send("You weren't challenged!", delete_after=60*60*1)

    @commands.command(name='use', aliases=['inv', 'equip'])
    async def use_command(self, ctx, item_num=""):
        """ Use an item"""

        name = ctx.message.author.display_name
        init_player_duel_db(name)
        inv = common.users[name]['inventory']
        equip = common.users[name]['equip']
        if item_num == "":
            if len(inv) == 0:
                await ctx.send("You have no items!", delete_after=60*60*1)
            else:
                inv_string = "Item_ID: Item_Name (Description)\n"
                for it in inv:
                    inv_string += "{}: {} ({})\n".format(it, get_name(it),
                                                         get_text(it))
                # If any are in use, go ahead print that info
                if len(equip) > 0:
                    icons = {'armor': ":shirt:",
                             'weapon': ":dagger:",
                             'other': ":ring:",
                             'offhand': ":shield:"}
                    inv_string += "\nYour current loadout is:\n"
                    for i in equip:
                        item_num = equip[i]
                        used_amount = inv[item_num]
                        inv_string += "{}: {} - {} use(s) remaining.\n" \
                                      .format(icons[i],
                                              get_name(item_num),
                                              (get_uses(item_num)
                                               - used_amount))

                await ctx.send(inv_string, delete_after=60*60*1)
        elif item_exists(item_num) and item_num in inv and \
                get_slot(item_num) in equip:
            slot = get_slot(item_num)
            await ctx.send("You already have the {} equipped in the {} "
                           "slot.".format(get_name(equip[slot]), slot),
                           delete_after=60*60*1)
        elif item_exists(item_num) and item_num not in inv:
            await ctx.send("You don't have that item!", delete_after=60*60*1)
        elif item_exists(item_num) and item_num in inv:
            await ctx.send("Item \"{}\" will be active starting with your "
                           "next duel.".format(get_name(item_num)),
                           delete_after=60*60*1)
            common.users[name]['equip'][get_slot(item_num)] = item_num
        else:
            await ctx.send("**!use <item_id>**: To use an item \n"
                           "**!use**: to view your inventory",
                           delete_after=60*60*1)

    @commands.command(name='unequip')
    async def unequip_command(self, ctx, slot: str):
        """Unequips an item in use"""

        name = ctx.message.author.display_name

        if 'equip' not in common.users[name] or len(common.users[name]) < 1:
            await ctx.send("You have no items equipped!", delete_after=60*60*1)
        elif slot == "all":
            for s in common.users[name]['equip']:
                item_num = common.users[name]['equip'][s]
                await ctx.send("You have unquipped the {}."
                               .format(get_name(item_num)),
                               delete_after=60*60*1)
            common.users[name]['equip'] = {}
            return
        elif slot not in common.users[name]['equip']:
            for s in common.users[name]['equip']:
                if common.users[name]['equip'][s] == slot:
                    item_num = common.users[name]['equip'][s]
                    await ctx.send("You have unquipped the {}"
                                   .format(get_name(item_num)),
                                   delete_after=60*60*1)
                    del (common.users[name]['equip'][s])
                    return
            await ctx.send("You don't have an item equipped in that slot!",
                           delete_after=60*60*1)
        else:
            item_num = common.users[name]['equip'][slot]
            await ctx.send("You have unquipped the {}"
                           .format(get_name(item_num)),
                           delete_after=60*60*1)
            del(common.users[name]['equip'][slot])


async def item_chance_roll(player, channel, max_roll=90):
    """
    Rolls for a chance at an item
    :param channel: Channel to send message to
    :param player: Person rolling
    :param max_roll: max roll to use
    """

    init_player_duel_db(player)
    item = DuelItem(randint(1, (max_roll + (len(common.users[player][
                                              'inventory']) * 25))))
    if item.name is not None:
        common.items_awarded += 1
        await channel.send("Congratulations {}! You received "
                           "the \"{}\".".format(player, item.name),
                           delete_after=60*60*1)
        if item.item_id in common.users[player]['inventory']:
            await channel.send("You already have that item, its "
                               "uses have been reset!", delete_after=60*60*1)
        common.users[player]['inventory'][item.item_id] = 0
        return True
    return False


def init_player_duel_db(player):
    """
    Inits a player's DB for items and dueling.

    :param player: player to init
    :return: None
    """

    if player not in common.users:
        common.users[player] = {}
    if 'inventory' not in common.users[player]:
        common.users[player]['inventory'] = {}
    if 'duel_record' not in common.users[player]:
        common.users[player]['duel_record'] = [0, 0, 0]
    if 'equip' not in common.users[player]:
        common.users[player]['equip'] = {}


def item_eff_str(item):
    """
    Forms a string for item in use.
    :param item: Item in use
    :return: Sting containing info on how the round is affected
    :rtype: str
    """

    ret_str = ""

    if hasattr(item, 'spec_text'):
        return item.spec_text
    if "roll_effect" in item.type:
        ret_str += "    All damage increased by {}.\n"
                   .format(item.prop['roll'])
    if 'life_effect' in item.type:
        ret_str += "    Life increased by {}.\n".format(item.prop['life'])
    if 'regen_effect' in item.type:
        ret_str += "    Will regen {} life at the end of each round.\n" \
            .format(item.prop['regen'])
    if 'luck_effect' in item.type:
        ret_str += "    Item chance luck increased!\n"
    if 'disarm_effect' in item.type:
        ret_str += "    The opponent's item will be removed if there is one " \
                   "equipped.\n"
    if 'res_effect' in item.type:
        ret_str += "    Will come back to life one time.\n"
    if 'poison_effect' in item.type:
        ret_str += "    The opponent, when hit, will be poisoned for {} " \
                   "round(s), taking {} damage each round.\n" \
            .format(item.prop['duration'], item.prop['poison'])
    if 'sh_effect' in item.type:
        ret_str += "    {}% chance to block an attack.\n"\
            .format(item.prop['shield'])
    if 'hm_effect' in item.type:
        ret_str += "    50% chance to hit with fixed damage.\n"
    if 'p_effect' in item.type:
        ret_str += "    Self-Inflicted wounds heal the wearer.\n"
    if len(ret_str) > 1:
        return ret_str
    else:
        return "    This item has an unknown or not implemented effect."


def return_item(item, player):
    """
    Returns an item to inventory, ie. the item wasn't used. A return may just
    be the return of a charge.

    :param item: Item to return.
    :param player: Player owning the item
    :return: None
    """
    if item.item_id in common.users[player]['inventory']:
        common.users[player]['inventory'][item.item_id] -= 1
    else:
        common.users[player]['inventory'][item.item_id] = item.uses - 1
        common.users[player]['equip'][item.slot] = item.item_id


async def item_disarm_check(ctx, c_item, v_item, c_name, v_name):
    """
    Handles the Disarming spec_effect

    :param ctx: Context
    :param c_item: Challenger's weapon
    :param v_item: Victim's weapon
    :param c_name: Challenger's Display name
    :param v_name: Victim's Display name
    """
    notif_str = ""
    c_item_ret = None
    v_item_ret = None
    if c_item is not None and 'disarm_effect' in c_item.type:
        if len(common.users[v_name]['equip']) < 1:
            notif_str += "{} has nothing to disarm, the {} has no effect!\n"\
                         .format(v_name, c_item.name)
            if len(c_item.type) == 1:
                return_item(c_item, c_name)
        else:  # Does the victim have an item that can be disarmed?
            poss_items = []
            for i in common.users[v_name]['equip']:
                if i != 'weapon':
                    poss_items.append(i)
                elif i == 'weapon' and 'disarm_effect' not in v_item.type:
                    poss_items.append(i)

            if len(poss_items) < 1:  # If no possible items give up
                notif_str += "{} only has a disarm item, the {} has no " \
                             "effect!\n".format(v_name, c_item.name)
                if len(c_item.type) == 1:
                    return_item(c_item, c_name)
            else:  # We can disarm something, do so.
                item_to_disarm = common.users[v_name]['equip'][choice(
                    poss_items)]
                notif_str += "{}'s {} has been removed by the {}!\n"\
                             .format(v_name, get_name(item_to_disarm),
                                     c_item.name)
                v_item_ret = DuelItem(0, item_to_disarm)
                return_item(v_item_ret, v_name)

    if v_item is not None and 'disarm_effect' in v_item.type:
        if len(common.users[c_name]['equip']) < 1:
            notif_str += "{} has nothing to disarm, the {} has no effect!\n"\
                         .format(c_name, v_item.name)
            if len(v_item.type) == 1:
                return_item(v_item, v_name)
        else:  # Does the challenger have an item that can be disarmed?
            poss_items = []
            for i in common.users[c_name]['equip']:
                if i != 'weapon':
                    poss_items.append(i)
                elif i == 'weapon' and 'disarm_effect' not in c_item.type:
                    poss_items.append(i)
            if len(poss_items) < 1:  # If no possible items give up
                notif_str += "{} only has a disarm item, the {} has no " \
                             "effect!\n".format(c_name, v_item.name)
                if len(v_item.type) == 1:
                    return_item(v_item, v_name)
            else:  # We can disarm something, do so.
                item_to_disarm = common.users[c_name]['equip'][choice(
                    poss_items)]
                notif_str += "{}'s {} has been removed by the {}!\n"\
                             .format(c_name, get_name(item_to_disarm),
                                     v_item.name)
                c_item_ret = DuelItem(0, item_to_disarm)
                return_item(c_item_ret, c_name)

    await ctx.send(notif_str, delete_after=60*60*1)
    return c_item_ret, v_item_ret


async def death_check(ctx, chal, c_life, vict, v_life, c_res, v_res):
    """
    Checks if someone has died

    :param ctx: Context
    :param chal: Challenger
    :param c_life: Challenger's Life
    :param vict: Victim
    :param v_life: Victim's Life
    :param c_res: Does chal have a res item?
    :param v_res: Does vict have a res item?
    :return: True if res for player, True if death
    :rtype: bool, bool, bool
    """

    death_string = ""
    cres = False
    vres = False
    death = False

    # Both players died
    if v_life < 1 and c_life < 1:
        death_string = "\nBoth players have died!\n{} and {} " \
                       "both drink!".format(chal.mention,
                                            vict.mention)
        # Both players resurrect
        if c_res and v_res:
            death_string = "\nBoth players have died!\nBoth Players " \
                           "miraculously come back to life! It's anyone's " \
                           "game now!"
            cres = True
            vres = True
        # Chal resurrect
        elif c_res and not v_res:
            death_string = "\nBoth players have died!\n{} " \
                           "miraculously came back to life! What a turn! {} " \
                           "wins the duel!\n{} drinks!"\
                           .format(chal.display_name, chal.display_name,
                                   vict.mention)
            cres = True
            death = True
            common.add_drink(vict.display_name)
            common.users[vict.display_name]['duel_record'][1] += 1
            common.users[chal.display_name]['duel_record'][0] += 1
        # Vict resurrect
        elif v_res and not c_res:
            death_string = "\nBoth players have died!\n{} " \
                           "miraculously came back to life! What a turn! {} " \
                           "wins the duel!\n{} drinks!"\
                           .format(vict.display_name, vict.display_name,
                                   chal.mention)
            vres = True
            death = True
            common.add_drink(chal.display_name)
            common.users[vict.display_name]['duel_record'][0] += 1
            common.users[chal.display_name]['duel_record'][1] += 1
        # No resurrect
        else:
            common.add_drink(vict.display_name)
            common.add_drink(chal.display_name)
            common.users[vict.display_name]['duel_record'][2] += 1
            common.users[chal.display_name]['duel_record'][2] += 1
            death = True
    # Vict death
    elif v_life < 1:
        death_string = "\n{} has died!\n{} wins the duel!\n" \
                       "{} drinks!".format(vict.display_name,
                                           chal.display_name, vict.mention)
        # Vict Res
        if v_res:
            death_string = "\n{} has died!\n{} " \
                           "miraculously came back to life! What a turn!"\
                .format(vict.display_name, vict.display_name)
            vres = True
        else:
            death = True
            common.users[vict.display_name]['duel_record'][1] += 1
            common.users[chal.display_name]['duel_record'][0] += 1
            common.add_drink(vict.display_name)
    # Chal death
    elif c_life < 1:
        death_string = "\n{} has died!\n{} wins the duel!\n" \
                       "{} drinks!".format(chal.display_name,
                                           vict.display_name,
                                           chal.mention)
        # Chal Res
        if c_res:
            death_string = "\n{} has died!\n{} " \
                           "miraculously came back to life! What a turn!" \
                .format(chal.display_name, chal.display_name)
            cres = True
        else:
            common.users[vict.display_name]['duel_record'][0] += 1
            common.users[chal.display_name]['duel_record'][1] += 1
            common.add_drink(chal.display_name)
            death = True

    if len(death_string) > 1:
        await ctx.send(death_string, delete_after=60*60*1)
    return cres, vres, death


def build_duel_str(params):
    """
    :param c_name: Challenger's name
    :param c_roll: Challenger's roll
    :param c_life: Challenger's life
    :param v_life: Victim's life
    :param v_name: Victim's name
    :param v_roll: Victim's roll
    :param cblk: Did chal block?
    :param vblk: Did vict block?
    """
    c_name = params['c_name']
    c_roll = params['c_roll']
    v_name = params['v_name']
    v_roll = params['v_roll']
    c_life = params['c_life']
    v_life = params['v_life']
    a_types = ["lunge", "jab", "chop", "slice", "sweep", "thrust"]

    r_string = ".\n"
    if c_roll < 0:
        if 'c_heal' in params:
            r_string += ":banana: **{}** fell on his own sword and magically" \
                        " healed himself for {}!" \
                        .format(c_name, params['c_heal'])
        else:
            r_string += ":banana: **{}** fell on his own sword and did {} to" \
                        " himself!".format(c_name, abs(c_roll))
    elif 'vblk' in params:
        r_string += ":shield: **{}** blocks **{}'s** attack!" \
                    .format(v_name, c_name)
    elif c_roll == 0:
        r_string += ":cloud_tornado: **{}** misses with his attack!" \
            .format(c_name)
    elif 0 < c_roll < 6:
        r_string += ":dagger: **{}** lands a {} and deals {} damage!".format(
            c_name, choice(a_types), c_roll)
    elif c_roll >= 6:
        r_string += ":knife: **{}** lands a **MASSIVE** strike and deals {} " \
                    "damage!".format(c_name, c_roll)

    r_string += "\n"
    if v_roll < 0:
        if 'v_heal' in params:
            r_string += ":banana: **{}** fell on his own sword and magically" \
                        " healed himself for {}!" \
                        .format(v_name, params['v_heal'])
        else:
            r_string += ":banana: **{}** fell on his own sword and did {} to" \
                        " himself!".format(v_name, abs(v_roll))
    elif 'cblk' in params:
        r_string += ":shield: **{}** blocks **{}'s** attack!" \
                    .format(c_name, v_name)
    elif v_roll == 0:
        r_string += ":cloud_tornado: **{}** misses with his attack!" \
            .format(v_name)
    elif 0 < v_roll < 6:
        r_string += ":dagger: **{}** lands a {} and deals {} damage!".format(
            v_name, choice(a_types), v_roll)
    elif v_roll >= 6:
        r_string += ":knife: **{}** lands a **MASSIVE** strike and deals {} " \
                    "damage!".format(v_name, v_roll)

    r_string += "\n**{}** is at {}.\n**{}** is at {}.\n" \
        .format(c_name, c_life, v_name, v_life)
    return r_string


def dual_dice_roll():
    """
    Return two rolls
    """

    return randint(-1, 6), randint(-1, 6)


def add_pos_eff(pos_effects, new_poss_eff):
    """
    Handles new poison effect

    :param pos_effects: List to add to
    :param new_poss_eff: new poison effect
    return: modified list
    """

    if new_poss_eff not in pos_effects:
        pos_effects.append(new_poss_eff)
        return pos_effects
    else:
        for index, p in enumerate(pos_effects):
            if p == new_poss_eff:
                pos_effects[index] += new_poss_eff
                return pos_effects


async def event_handle_shot_duel(ctx, victim, bot):
    """
    Handles a shot_duel should a victim accept.

    :param ctx: Context
    :param victim: Person challenged
    :return: None
    """
    fog = False
    cap = False
    h_life = None
    h_dam = None
    common.shot_duel_running = True
    vict_name = common.vict_name = victim.display_name
    chal_name = ctx.message.author.display_name

    await ctx.send('.\nThe challenge has been laid down!\n'
                   '{}, {} has asked you to duel!\n'
                   'Do you accept?!?!?! (!accept)\n'
                   'You have 90 seconds to decide.'
                   .format(victim.mention, chal_name),
                   delete_after=60*60*1)

    waited = 5
    while waited < 90:
        await asyncio.sleep(5)
        waited += 5
        if common.accepted:
            init_player_duel_db(vict_name)
            init_player_duel_db(chal_name)
            c_rec = common.users[chal_name]['duel_record']
            v_rec = common.users[common.vict_name]['duel_record']
            life = 13
            common.duels_conducted += 1
            await ctx.send(".\nDuel Accepted! Here we go!\n"
                           "{} is {} - {} - {}\n"
                           "{} is {} - {} - {}\n"
                           "Good Luck!!!"
                           .format(chal_name, c_rec[0], c_rec[1], c_rec[2],
                                   common.vict_name, v_rec[0], v_rec[1],
                                   v_rec[2]),
                           delete_after=60*60*1)
            c_total = []
            v_total = []
            c_pos_eff, v_pos_eff = [], []

            # Check if a player has active items
            vi_list = []
            ci_list = []
            crem_list = []
            vrem_list = []
            c_wep = None
            v_wep = None
            if len(common.users[chal_name]['equip']) > 0:
                notif_str = "{} is using the following items:\n"\
                            .format(chal_name)
                for a_item in common.users[chal_name]['equip']:
                    c_item = DuelItem(0,
                                      common.users[chal_name]['equip'][a_item])
                    ci_list.append(c_item)
                    if c_item.slot == 'weapon':
                        c_wep = c_item
                    common.users[chal_name]['inventory'][c_item.item_id] += 1
                    notif_str += "  {}:\n{}" \
                                 .format(c_item.name, item_eff_str(c_item))
                    if common.users[chal_name]['inventory'][c_item.item_id] \
                            >= c_item.uses:
                        del(common.users[chal_name]['inventory']
                            [c_item.item_id])
                        crem_list.append(c_item.slot)
                        notif_str += "    This is the last use for this item!\n"
                await ctx.send(notif_str, delete_after=60*60*1)

            if len(common.users[vict_name]['equip']) > 0:
                notif_str = "{} is using the following items:\n"\
                            .format(vict_name)
                for a_item in common.users[vict_name]['equip']:
                    v_item = DuelItem(0,
                                      common.users[vict_name]['equip'][a_item])
                    vi_list.append(v_item)
                    if v_item.slot == 'weapon':
                        v_wep = v_item
                    common.users[vict_name]['inventory'][v_item.item_id] += 1
                    notif_str += "  {}:\n{}" \
                                 .format(v_item.name, item_eff_str(v_item))
                    if common.users[vict_name]['inventory'][v_item.item_id] \
                            >= v_item.uses:
                        del (common.users[vict_name]['inventory']
                             [v_item.item_id])
                        vrem_list.append(v_item.slot)
                        notif_str += "    This is the last use for this item!\n"
                await ctx.send(notif_str, delete_after=60*60*1)

            # PRE COMBAT START PHASE (ADD SPEC_EFFECT CHECKS HERE)
            await asyncio.sleep(5)
            # Environment effects
            e_roll = randint(5, 20)
            # fog
            if e_roll == 20:
                await ctx.send("A dense fog rolls in. "
                               "(Chance to miss increased)",
                               delete_after=60*60*1)
                fog = True
            # damper
            elif e_roll == 19:
                await ctx.send("A weird pink glow surrounds the battlefield."
                               " (Damage is capped)", delete_after=60*60*1)
                cap = True
            # PoisonDarts
            elif e_roll == 17:
                await ctx.send("Darts begin flying across the battlefield. "
                               "One striking each dueler!",
                               delete_after=60*60*1)
                c_pos_eff.append(PoisonEffect(DuelItem(100, 9999), "env"))
                v_pos_eff.append(PoisonEffect(DuelItem(100, 9999), "env"))
            elif e_roll == 16:
                targ = choice([vict_name, chal_name])
                await ctx.send("Darts begin flying across the battlefield. "
                               "One striking {}!".format(targ),
                               delete_after=60*60*1)
                if chal_name == targ:
                    c_pos_eff.append(PoisonEffect(DuelItem(100, 9999), "env"))
                elif vict_name == targ:
                    v_pos_eff.append(PoisonEffect(DuelItem(100, 9999), "env"))
            # red button event
            elif e_roll == 18:
                await ctx.send("A big red button appears. Would you like "
                               "to press it? (If you want to type \"$press\""
                               ". You have 10 seconds to decide.)",
                               delete_after=60*60*1)
                msg = await ctx.wait_for_message(timeout=10.0,
                                                 content='$press')
                if msg is not None:
                    nc = msg.author.display_name
                    await ctx.send("{} pressed the button!".format(nc),
                                   delete_after=60*60*1)
                    if nc not in [chal_name, vict_name]:
                        await ctx.send("{} is not in this duel and suddenly "
                                       "feels less burdened.".format(nc),
                                       delete_after=60*60*1)
                        if len(list(common.users[nc]['inventory'].keys())) > 0:
                            item_take = choice(
                                list(common.users[nc]['inventory'].keys()))
                            if get_slot(item_take) in common.users[nc]['equip']:
                                del (common.users[nc]['equip']
                                     [get_slot(item_take)])
                            del common.users[nc]['inventory'][item_take]
                    await ctx.send("The red button disappears but a loud "
                                   "banging noise can be heard!",
                                   delete_after=60*60*1)
                    await ctx.trigger_typing()
                    eff = randint(0, 2)
                    await asyncio.sleep(10)
                    if eff == 0:
                        h_life = choice([vict_name, chal_name])
                        await ctx.send("{} will start at half life."
                                       .format(h_life), delete_after=60*60*1)
                    elif eff == 1:
                        h_dam = choice([vict_name, chal_name])
                        await ctx.send("{} will do half damage."
                                       .format(h_dam), delete_after=60*60*1)
                    elif eff == 2:
                        targ = choice([vict_name, chal_name])
                        await ctx.send("A dart strikes {}!".format(targ),
                                       delete_after=60*60*1)
                        if chal_name == targ:
                            c_pos_eff.append(
                                PoisonEffect(DuelItem(100, 9999), "env"))
                        elif vict_name == targ:
                            v_pos_eff.append(
                                PoisonEffect(DuelItem(100, 9999), "env"))
                elif msg is None:
                    await ctx.send("Unpressed, the button disappears.",
                                   delete_after=60*60*1)

            # spec_effect check (disarm_effect)
            if (c_wep is not None and 'disarm_effect' in c_wep.type) \
                    or (v_wep is not None and 'disarm_effect' in v_wep.type):
                # If a player losses an item, remove it from active list
                ci_to_rem, vi_to_rem = await item_disarm_check(ctx, c_wep,
                                                               v_wep,
                                                               chal_name,
                                                               vict_name)
                if ci_to_rem is not None:
                    if ci_to_rem.slot in crem_list:
                        crem_list.remove(ci_to_rem.slot)
                    ci_list.remove(ci_to_rem)
                if vi_to_rem is not None:
                    if vi_to_rem.slot in vrem_list:
                        vrem_list.remove(vi_to_rem.slot)
                    vi_list.remove(vi_to_rem)

            # Remove equipped items that were used up
            for i in crem_list:
                del(common.users[chal_name]['equip'][i])
            for i in vrem_list:
                del(common.users[vict_name]['equip'][i])

            # Determine cumulative item effect
            if len(ci_list) < 1:
                c_item = None
            else:
                c_item = DuelItem(99)  # Set to empty item
                for i in ci_list:  # Combine items into one
                    c_item += i

            if len(vi_list) < 1:
                v_item = None
            else:
                v_item = DuelItem(99)  # Set to empty item
                for i in vi_list:  # Combine items into one
                    v_item += i

            await asyncio.sleep(2)
            # END OF PRECOMBAT PHASE

            # LIFE EFFECT CHECK
            c_life_start = life
            v_life_start = life
            if c_item is not None and "life_effect" in c_item.type:
                c_life_start += c_item.prop['life']
            if v_item is not None and "life_effect" in v_item.type:
                v_life_start += v_item.prop['life']

            # half life check (red button mystery)
            if h_life is not None:
                if h_life == chal_name:
                    c_life_start = int(c_life_start / 2)
                elif h_life == vict_name:
                    v_life_start = int(v_life_start / 2)

            # Initial ITEM CHANCE ROLLS (If needed modify chance rolls here)
            luck_mod = 0
            if c_item is not None and "luck_effect" in c_item.type:
                luck_mod = c_item.prop['luck']
            for i in range(3):
                await item_chance_roll(chal_name, ctx.message.channel,
                                       (100 - luck_mod)*(i+1))
            luck_mod = 0
            if v_item is not None and "luck_effect" in v_item.type:
                luck_mod = v_item.prop['luck']
            for i in range(3):
                await item_chance_roll(vict_name, ctx.message.channel,
                                       (100 - luck_mod)*(i+1))

            await ctx.send(".\n{} has {} life.\n{} has {} life."
                           .format(chal_name, c_life_start, vict_name,
                                   v_life_start),
                           delete_after=60*60*1)
            c_life = c_life_start
            v_life = v_life_start
            # COMBAT PHASE
            _round = 1

            while True:
                await ctx.send("Round {}!".format(_round),
                               delete_after=60*60*1)
                # PRE ATTACK PHASE (spec_effect check here)
                # Poison Damage check
                if len(c_pos_eff) > 0:
                    pos_dam = 0
                    e_effects = []
                    for p in c_pos_eff:
                        pos_dam += p.dam
                        p -= 1
                        if p.ended():
                            e_effects.append(p)
                    for p in e_effects:
                        c_pos_eff.remove(p)
                    v_total.append(pos_dam)
                    c_life = c_life_start - sum(v_total)
                    await ctx.send("{} takes {} poison damage and is now at "
                                   "{} life.".format(chal_name, pos_dam,
                                                     c_life),
                                   delete_after=60*60*1)
                if len(v_pos_eff) > 0:
                    pos_dam = 0
                    e_effects = []
                    for p in v_pos_eff:
                        pos_dam += p.dam
                        p -= 1
                        if p.ended():
                            e_effects.append(p)
                    for p in e_effects:
                        v_pos_eff.remove(p)
                    c_total.append(pos_dam)
                    v_life = v_life_start - sum(c_total)
                    await ctx.send("{} takes {} poison damage and is now at "
                                   "{} life.".format(common.vict_name,
                                                     pos_dam, v_life),
                                   delete_after=60*60*1)

                cres, vres, death = \
                    await death_check(ctx, ctx.message.author,
                                      c_life, victim, v_life,
                                      (c_item is not None and
                                       "res_effect" in c_item.type),
                                      (v_item is not None and
                                       "res_effect" in v_item.type))
                if cres:
                    c_item.type.remove('res_effect')
                    v_total = [c_life_start - randint(1, 2)]
                    c_life = c_life_start - sum(v_total)
                if vres:
                    v_item.type.remove('res_effect')
                    c_total = [v_life_start - randint(1, 2)]
                    v_life = v_life_start - sum(c_total)
                if death:
                    # END OF DUEL PHASE
                    common.whos_in.update_db()
                    break

                # ATTACK PHASE (Both attacks happen at same time!)
                await ctx.trigger_typing()
                await asyncio.sleep(10)
                c_roll, v_roll = dual_dice_roll()

                # Modify for fog
                if fog:
                    if c_roll == 1 or (c_roll == 2 and randint(0, 1) == 0) \
                       or (c_roll == 3 and randint(0, 2) == 0):
                        c_roll = 0
                    if v_roll == 1 or (v_roll == 2 and randint(0, 1) == 0) \
                       or (v_roll == 3 and randint(0, 2) == 0):
                        v_roll = 0

                # Item modifications
                # for challenger
                if c_item is not None:
                    # Hit Miss items
                    if "hm_effect" in c_item.type:
                        if c_roll > 4:
                            c_roll = c_item.prop['damage']
                        elif c_roll < 1:
                            c_roll = -1 * int(c_item.prop['damage'] / 2)
                        else:
                            c_roll = 0

                    # Roll effects
                    if "roll_effect" in c_item.type and c_roll > 0:
                        c_roll += c_item.prop['roll']
                    elif "roll_effect" in c_item.type \
                            and c_roll < 0:
                        c_roll -= c_item.prop['roll']

                # Vict items
                if v_item is not None:
                    if "hm_effect" in v_item.type:
                        if v_roll > 4:
                            v_roll = v_item.prop['damage']
                        elif v_roll < 1:
                            v_roll = -1 * int(v_item.prop['damage'] / 2)
                        else:
                            v_roll = 0

                    if "roll_effect" in v_item.type \
                            and v_roll > 0:
                        v_roll += v_item.prop['roll']
                    elif "roll_effect" in v_item.type \
                            and v_roll < 0:
                        v_roll -= v_item.prop['roll']

                if cap:
                    c_roll = min(4, c_roll)
                    v_roll = min(4, v_roll)

                # half dam check (red button mystery)
                if h_dam is not None:
                    if h_dam == chal_name:
                        c_roll = int(c_roll / 2)
                    elif h_dam == vict_name:
                        v_roll = int(v_roll / 2)

                # Blocks
                cblk = False
                if c_item is not None and v_roll > 0 \
                        and "sh_effect" in c_item.type:
                    if randint(0, 100/c_item.prop['shield'] - 1) == 0:
                        cblk = True
                        v_roll = 0
                vblk = False
                if v_item is not None and c_roll > 0 \
                        and "sh_effect" in v_item.type:
                    if randint(0, 100 / v_item.prop['shield'] - 1) == 0:
                        vblk = True
                        c_roll = 0

                c_heal = False
                v_heal = False
                # Hit Affects
                if c_item is not None and 'p_effect' in c_item.type and \
                   c_roll < 0:
                    c_heal = True
                    c_heal_amt = abs(c_roll)
                    if (c_life_start - c_life - max(0, v_roll)) < c_heal_amt:
                        c_heal_amt = c_life_start - c_life - max(0, v_roll)
                    v_total.append(-c_heal_amt)
                if v_item is not None and 'p_effect' in v_item.type and \
                   v_roll < 0:
                    v_heal = True
                    v_heal_amt = abs(v_roll)
                    if (v_life_start - v_life - max(0, c_roll)) < v_heal_amt:
                        v_heal_amt = v_life_start - v_life - max(0, c_roll)
                    c_total.append(-v_heal_amt)

                # DAMAGE APPLIED HERE
                if c_roll >= 0:
                    c_total.append(c_roll)
                elif not c_heal:
                    v_total.append(abs(c_roll))

                if v_roll >= 0:
                    v_total.append(v_roll)
                elif not v_heal:
                    c_total.append(abs(v_roll))

                c_life = c_life_start - sum(v_total)
                v_life = v_life_start - sum(c_total)
                d_params = {'c_name': chal_name,
                            'c_roll': c_roll,
                            'v_name': common.vict_name,
                            'v_roll': v_roll,
                            'c_life': c_life,
                            'v_life': v_life}
                if cblk:
                    d_params['cblk'] = cblk
                if vblk:
                    d_params['vblk'] = vblk
                if c_heal:
                    d_params['c_heal'] = c_heal_amt
                if v_heal:
                    d_params['v_heal'] = v_heal_amt

                duel_string = build_duel_str(d_params)

                # POST COMBAT PHASE (Damage resolved here, on_death effects
                # should be implemented here)
                # Poison Effects
                if c_item is not None and "poison_effect" in c_item.type and \
                        c_roll != 0:
                    p_e = PoisonEffect(c_item, chal_name)
                    if c_roll > 0:
                        v_pos_eff = add_pos_eff(v_pos_eff, p_e)
                    elif c_roll < 0:
                        c_pos_eff = add_pos_eff(c_pos_eff, p_e)

                if v_item is not None and "poison_effect" in v_item.type and \
                        v_roll != 0:
                    p_e = PoisonEffect(v_item, common.vict_name)
                    if v_roll > 0:
                        c_pos_eff = add_pos_eff(c_pos_eff, p_e)
                    elif v_roll < 0:
                        v_pos_eff = add_pos_eff(v_pos_eff, p_e)

                await ctx.send(duel_string, delete_after=60*60*1)

                _round += 1
                cres, vres, death = \
                    await death_check(ctx, ctx.message.author,
                                      c_life, victim, v_life,
                                      (c_item is not None and
                                       "res_effect" in c_item.type),
                                      (v_item is not None and
                                       "res_effect" in v_item.type))
                if cres:
                    c_item.type.remove('res_effect')
                    v_total = [c_life_start - randint(1, 2)]
                    c_life = c_life_start - sum(v_total)
                if vres:
                    v_item.type.remove('res_effect')
                    c_total = [v_life_start - randint(1, 2)]
                    v_life = v_life_start - sum(c_total)
                if death:
                    # END OF DUEL PHASE
                    common.whos_in.update_db()
                    break

                # END OF ROUND PHASE
                # regen checks
                if c_item is not None and "regen_effect" in c_item.type \
                        and c_life < c_life_start:
                    if (c_life_start - c_life) < c_item.prop['regen']:
                        reg_tot = c_life_start - c_life
                    else:
                        reg_tot = c_item.prop['regen']
                    v_total.append(-reg_tot)
                    await ctx.send("{} has regen'd {} life and is now at {}."
                                   .format(chal_name, reg_tot, (c_life +
                                           reg_tot)), delete_after=60*60*1)

                if v_item is not None and "regen_effect" in v_item.type \
                        and v_life < v_life_start:
                    if (v_life_start - v_life) < v_item.prop['regen']:
                        reg_tot = v_life_start - v_life
                    else:
                        reg_tot = v_item.prop['regen']
                    c_total.append(-reg_tot)
                    await ctx.send("{} has regen'd {} life and is now at {}."
                                   .format(common.vict_name, reg_tot,
                                           (v_life + reg_tot)),
                                   delete_after=60*60*1)

                # end of round drop chance
                luck_mod = 0
                if c_item is not None and "luck_effect" in c_item.type:
                    luck_mod = c_item.prop['luck']
                await item_chance_roll(chal_name, ctx.message.channel,
                                       max(20, int(1000 / _round) - luck_mod))
                luck_mod = 0
                if v_item is not None and "luck_effect" in v_item.type:
                    luck_mod = v_item.prop['luck']
                await item_chance_roll(vict_name, ctx.message.channel,
                                       max(20, int(1000 / _round) - luck_mod))

                await asyncio.sleep(15)
            break

    if not common.accepted:
        await ctx.send("Shot duel not accepted! Clearly {} is better than "
                       "{}.".format(chal_name, common.vict_name),
                       delete_after=60*60*1)
        await item_chance_roll(chal_name, ctx.message.channel, 250)
        await item_chance_roll(common.vict_name,
                               ctx.message.channel, 500)
        bot.get_command('duel').reset_cooldown(ctx)
    common.shot_duel_running = False
    common.accepted = False
    common.vict_name = ""


def setup(bot):
    bot.add_cog(Duels(bot))
