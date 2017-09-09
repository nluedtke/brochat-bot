import asyncio
from random import randint, choice
from discord.ext import commands
import common
from objs.duel_item import DuelItem, PoisonEffect, get_name, get_slot, \
    get_text, get_uses, item_exists
from cogs.drinkingcog import in_deep_debt


class Duels:
    """Handles Dueling commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name='duel', pass_context=True)
    @commands.cooldown(1, 120)
    async def shot_duel(self, ctx):
        """ Duel someone"""

        if ctx.invoked_subcommand is None:
            if common.shot_duel_running:
                await self.bot.say('There is a duel already running, wait your '
                                   'turn to challenge someone!')
                self.bot.get_command('duel').reset_cooldown(ctx)
                return

            if in_deep_debt(ctx.message.author.display_name):
                await self.bot.say('Hey there, I can\'t let you do that till '
                                   'you pay down some of that friendship you '
                                   'owe.')
                self.bot.get_command('duel').reset_cooldown(ctx)
                return

            members = self.bot.get_all_members()
            map_disp_to_name = {}
            for m in members:
                map_disp_to_name[m.display_name.lower()] = m

            name = ctx.message.content[6:].lower()

            if len(name) < 1:
                await self.bot.say('Who do you want to duel?')
                self.bot.get_command('duel').reset_cooldown(ctx)
                return

            if name == ctx.message.author.display_name.lower() and \
                    ctx.message.channel.name != 'gen_testing':
                await self.bot.say("Why not just drink your tears away, "
                                   "instead of including this channel?")
            elif name not in map_disp_to_name:
                await self.bot.say('That\'s not a real person...')
                self.bot.get_command('duel').reset_cooldown(ctx)
            elif name == 'brochat-bot':
                await self.bot.say('brochat-bot would drink you under the '
                                   'table, try another person!')
                self.bot.get_command('duel').reset_cooldown(ctx)
            elif str(map_disp_to_name[name].status) != 'online':
                await self.bot.say('That person is likely already passed out!')
                self.bot.get_command('duel').reset_cooldown(ctx)
            else:
                await event_handle_shot_duel(ctx, map_disp_to_name[name])

    @shot_duel.command(name='ranking', aliases=['ranks'], pass_context=True)
    async def get_duel_rankings(self, ctx):
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
        self.bot.get_command('duel').reset_cooldown(ctx)

    @commands.command(name='accept', pass_context=True)
    async def toggle_accept(self, ctx):
        """Accept a challenge"""

        if common.shot_duel_running and ctx.message.author.display_name == \
                common.vict_name:
            common.accepted = True
        else:
            await self.bot.say("You weren't challenged!")

    @commands.command(name='use', aliases=['inv', 'equip'], pass_context=True)
    async def use_command(self, ctx, item_num=""):
        """ Use an item"""

        name = ctx.message.author.display_name
        init_player_duel_db(name)
        inv = common.users[name]['inventory']
        equip = common.users[name]['equip']
        if item_num == "":
            if len(inv) == 0:
                await self.bot.say("You have no items!")
            else:
                inv_string = "Item_ID: Item_Name (Description)\n"
                for it in inv:
                    inv_string += "{}: {} ({})\n".format(it, get_name(it),
                                                         get_text(it))
                # If any are in use, go ahead print that info
                if len(equip) > 0:
                    icons = {'armor': ":shirt:",
                             'weapon': ":dagger:",
                             'other': ":ring:"}
                    inv_string += "\nYour current loadout is:\n"
                    for i in equip:
                        item_num = equip[i]
                        used_amount = inv[item_num]
                        inv_string += "{}: {} - {} use(s) remaining.\n" \
                                      .format(icons[i],
                                              get_name(item_num),
                                              (get_uses(item_num)
                                               - used_amount))

                await self.bot.say(inv_string)
        elif item_exists(item_num) and item_num in inv and \
                get_slot(item_num) in equip:
            slot = get_slot(item_num)
            await self.bot.say("You already have the {} equipped in the {} "
                               "slot.".format(get_name(equip[slot]), slot))
        elif item_exists(item_num) and item_num not in inv:
            await self.bot.say("You don't have that item!")
        elif item_exists(item_num) and item_num in inv:
            await self.bot.say("Item \"{}\" will be active starting with your "
                               "next duel.".format(get_name(item_num)))
            common.users[name]['equip'][get_slot(item_num)] = item_num
        else:
            await self.bot.say("**!use <item_id>**: To use an item \n"
                               "**!use**: to view your inventory")

    @commands.command(name='unequip', pass_context=True)
    async def unequip_command(self, ctx, slot: str):
        """Unequips an item in use"""

        name = ctx.message.author.display_name

        if 'equip' not in common.users[name] or len(common.users[name]) < 1:
            await self.bot.say("You have no items equipped!")
        elif slot not in common.users[name]['equip']:
            for s in common.users[name]['equip']:
                if common.users[name]['equip'][s] == slot:
                    item_num = common.users[name]['equip'][s]
                    await self.bot.say("You have unquipped the {}"
                                       .format(get_name(item_num)))
                    del (common.users[name]['equip'][s])
                    return
            await self.bot.say("You don't have an item equipped in that slot!")
        else:
            item_num = common.users[name]['equip'][slot]
            await self.bot.say("You have unquipped the {}"
                               .format(get_name(item_num)))
            del(common.users[name]['equip'][slot])

async def item_chance_roll(bot, player, channel, max_roll=100):
    """
    Rolls for a chance at an item

    :param channel: Channel to send message to
    :param bot: Bot
    :param player: Person rolling
    :param max_roll: max roll to use
    """

    init_player_duel_db(player)
    item = DuelItem(randint(1, max_roll + (len(common.users[player][
                                              'inventory']) * 3)))
    if item.name is not None:
        common.items_awarded += 1
        await bot.send_message(channel, "Congratulations {}! You received "
                                        "the \"{}\"."
                                        .format(player, item.name))
        if item.item_id in common.users[player]['inventory']:
            await bot.send_message(channel, "You already have that item, its "
                                            "uses have been reset!")
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
        ret_str += "    All damage increased by {}.\n".format(item.prop['roll'])
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
    if 'poison_effect' in item.type:
        ret_str += "    The opponent, when hit, will be poisoned for {} " \
                   "round(s), taking {} damage each round.\n" \
            .format(item.prop['duration'], item.prop['poison'])
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
                if i == 'armor' or i == 'other':
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
                if i == 'armor' or i == 'other':
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

    await ctx.bot.say(notif_str)
    return c_item_ret, v_item_ret


async def death_check(ctx, chal, c_life, vict, v_life):
    """
    Checks if someone has died

    :param ctx: Context
    :param chal: Challenger
    :param c_life: Challenger's Life
    :param vict: Victim
    :param v_life: Victim's Life
    :return: True if death
    :rtype: bool
    """

    death_string = ""

    if v_life < 1 and c_life < 1:
        death_string = "\nBoth players have died!\n{} and {} " \
                       "both drink!".format(chal.mention,
                                            vict.mention)
        common.users[vict.display_name]['duel_record'][2] += 1
        common.users[chal.display_name]['duel_record'][2] += 1
        common.add_drink(vict.display_name)
        common.add_drink(chal.display_name)
    elif v_life < 1:
        death_string = "\n{} has died!\n{} wins the duel!\n" \
                       "{} drinks!".format(vict.display_name,
                                           chal.display_name, vict.mention)
        common.users[vict.display_name]['duel_record'][1] += 1
        common.users[chal.display_name]['duel_record'][0] += 1
        common.add_drink(vict.display_name)
    elif c_life < 1:
        death_string = "\n{} has died!\n{} wins the duel!\n" \
                       "{} drinks!".format(chal.display_name, vict.display_name,
                                           chal.mention)
        common.users[vict.display_name]['duel_record'][0] += 1
        common.users[chal.display_name]['duel_record'][1] += 1
        common.add_drink(chal.display_name)
    if len(death_string) > 1:
        await ctx.bot.say(death_string)
        return True
    return False


def build_duel_str(c_name, c_roll, v_name, v_roll, c_life, v_life):
    """
    :param c_name: Challenger's name
    :param c_roll: Challenger's roll
    :param c_life: Challenger's life
    :param v_life: Victim's life
    :param v_name: Victim's name
    :param v_roll: Victim's roll
    """
    a_types = ["lunge", "jab", "chop", "slice", "sweep", "thrust"]

    r_string = ".\n"
    if c_roll < 0:
        r_string += ":banana: **{}** fell on his own sword and did {} to " \
                    "himself!".format(c_name, abs(c_roll))
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
        r_string += ":banana: **{}** fell on his own sword and did {} to " \
                    "himself!".format(v_name, abs(v_roll))
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

async def event_handle_shot_duel(ctx, victim):
    """
    Handles a shot_duel should a victim accept.

    :param ctx: Context
    :param victim: Person challenged
    :return: None
    """
    common.shot_duel_running = True
    vict_name = common.vict_name = victim.display_name
    chal_name = ctx.message.author.display_name

    await ctx.bot.say('.\nThe challenge has been laid down!\n'
                      '{}, {} has asked you to duel!\n'
                      'Do you accept?!?!?! (!accept)\n'
                      'You have 90 seconds to decide.'
                      .format(victim.mention, chal_name))

    waited = 5
    while waited < 90:
        await asyncio.sleep(5)
        waited += 5
        if common.accepted:
            init_player_duel_db(vict_name)
            init_player_duel_db(chal_name)
            c_rec = common.users[chal_name]['duel_record']
            v_rec = common.users[common.vict_name]['duel_record']
            life = 12
            common.duels_conducted += 1
            await ctx.bot.say(".\nDuel Accepted! Here we go!\n"
                              "{} is {} - {} - {}\n"
                              "{} is {} - {} - {}\n"
                              "Good Luck!!!"
                              .format(chal_name, c_rec[0], c_rec[1], c_rec[2],
                                      common.vict_name, v_rec[0], v_rec[1],
                                      v_rec[2]))
            c_total = []
            v_total = []

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
                await ctx.bot.say(notif_str)

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
                await ctx.bot.say(notif_str)

            # PRE COMBAT START PHASE (ADD SPEC_EFFECT CHECKS HERE)

            # spec_effect check (disarm_effect)
            if (c_wep is not None and 'disarm_effect' in c_wep.type) \
                    or (v_wep is not None and 'disarm_effect' in v_wep.type):
                # If a player losses an item, remove it from active list
                ci_to_rem, vi_to_rem = await item_disarm_check(ctx, c_wep,
                                                               v_wep, chal_name,
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

            # Inital ITEM CHANCE ROLLS (If needed modify chance rolls here)
            luck_mod = 0
            if c_item is not None and "luck_effect" in c_item.type:
                luck_mod = c_item.prop['luck']
            await item_chance_roll(ctx.bot, chal_name, ctx.message.channel,
                                   100 - luck_mod)
            luck_mod = 0
            if v_item is not None and "luck_effect" in v_item.type:
                luck_mod = v_item.prop['luck']
            await item_chance_roll(ctx.bot, common.vict_name,
                                   ctx.message.channel, 100 - luck_mod)

            await ctx.bot.say(".\n{} has {} life.\n{} has {} life."
                              .format(chal_name, c_life_start,
                                      common.vict_name, v_life_start))
            c_life = c_life_start
            v_life = v_life_start
            # COMBAT PHASE
            _round = 1
            c_pos_eff, v_pos_eff = [], []
            while True:
                await ctx.bot.say("Round {}!".format(_round))
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
                    await ctx.bot.say("{} takes {} poison damage and is now at "
                                      "{} life.".format(chal_name, pos_dam,
                                                        c_life))
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
                    await ctx.bot.say("{} takes {} poison damage and is now at "
                                      "{} life.".format(common.vict_name,
                                                        pos_dam, v_life))

                death = await death_check(ctx, ctx.message.author, c_life,
                                          victim, v_life)
                if death:
                    # END OF DUEL PHASE
                    common.whos_in.update_db()
                    break

                # ATTACK PHASE (Both attacks happen at same time!)
                await ctx.bot.send_typing(ctx.message.channel)
                await asyncio.sleep(10)
                c_roll, v_roll = dual_dice_roll()

                if c_item is not None and "roll_effect" in c_item.type \
                        and c_roll >= 0:
                    c_roll += c_item.prop['roll']
                elif c_item is not None and "roll_effect" in c_item.type \
                        and c_roll < 0:
                    c_roll -= c_item.prop['roll']
                if v_item is not None and "roll_effect" in v_item.type \
                        and v_roll >= 0:
                    v_roll += v_item.prop['roll']
                elif v_item is not None and "roll_effect" in v_item.type \
                        and v_roll < 0:
                    v_roll -= v_item.prop['roll']

                # DAMAGE APPLIED HERE
                if c_roll >= 0:
                    c_total.append(c_roll)
                else:
                    v_total.append(abs(c_roll))

                if v_roll >= 0:
                    v_total.append(v_roll)
                else:
                    c_total.append(abs(v_roll))

                c_life = c_life_start - sum(v_total)
                v_life = v_life_start - sum(c_total)
                duel_string = build_duel_str(chal_name, c_roll,
                                             common.vict_name, v_roll, c_life,
                                             v_life)

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

                await ctx.bot.say(duel_string)

                _round += 1
                death = await death_check(ctx, ctx.message.author, c_life,
                                          victim, v_life)
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
                    await ctx.bot.say("{} has regen'd {} life and is now at {}."
                                      .format(chal_name, reg_tot, (c_life +
                                              reg_tot)))

                if v_item is not None and "regen_effect" in v_item.type \
                        and v_life < v_life_start:
                    if (v_life_start - v_life) < v_item.prop['regen']:
                        reg_tot = v_life_start - v_life
                    else:
                        reg_tot = v_item.prop['regen']
                    c_total.append(-reg_tot)
                    await ctx.bot.say("{} has regen'd {} life and is now at {}."
                                      .format(common.vict_name, reg_tot,
                                              (v_life + reg_tot)))

                # end of round drop chance
                luck_mod = 0
                if c_item is not None and "luck_effect" in c_item.type:
                    luck_mod = c_item.prop['luck']
                await item_chance_roll(ctx.bot, chal_name,
                                       ctx.message.channel,
                                       int(1000 / _round) - luck_mod)
                luck_mod = 0
                if v_item is not None and "luck_effect" in v_item.type:
                    luck_mod = v_item.prop['luck']
                await item_chance_roll(ctx.bot, common.vict_name,
                                       int(1000 / _round) - luck_mod)

                await asyncio.sleep(15)
            break

    if not common.accepted:
        await ctx.bot.say("Shot duel not accepted! Clearly {} is better than "
                          "{}.".format(chal_name, common.vict_name))

    common.shot_duel_running = False
    common.accepted = False
    common.vict_name = ""


def setup(bot):
    bot.add_cog(Duels(bot))
