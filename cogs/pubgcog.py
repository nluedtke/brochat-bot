import asyncio
import json
import math
import statistics as stats
import sys
import traceback
from json import JSONDecodeError

import matplotlib
import matplotlib.pyplot as plt
import requests
from scipy.misc import imread

import common as c
from discord.ext import commands
from pubg_python import PUBG, Shard
from pubg_python.exceptions import APIError, NotFoundError

matplotlib.use('Agg')

with open("objs/itemId.json", 'r') as infile:
    items = json.load(infile)

with open("objs/damageCauserName.json", 'r') as infile:
    dcauses = json.load(infile)

# Number of match ids to store
max_mids_records = 20


class Puby(commands.Cog):
    """ Pubg Fetchers"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name='getmap')
    async def get_map(self, ctx):
        """ Gets the Map of your last PUBG Match"""

        auth = ctx.message.author.display_name
        if auth not in c.users or 'pubg' not in c.users[auth]:
            await ctx.send('I don\'t know your PUBG name')
            return
        elif 'pubg_match' not in c.users[auth] or \
                        len(c.users[auth]['pubg_match']) < 1:
            await ctx.send('I haven\'t see you play a match yet.')
            return
        await ctx.send("Plotting map. One minute.")
        await ctx.trigger_typing()
        match_to_get = c.users[auth]['pubg_match'][-1]
        map_file = get_map_byid(match_to_get)
        await ctx.send("", file=discord.File(map_file))


def build_map(url, names):
    """
    Builds a map by the telemetry url
    :param url: telemetry url
    :param names: names to include in map
    :return: map file
    """
    scale = 100
    map_name = "Unk"
    fig, ax = plt.subplots(figsize=(8.192, 8.192), dpi=100)
    fig.subplots_adjust(0, 0, 1, 1)

    r = requests.get(url)
    data = r.json()
    for t in data:
        if t['_T'] == "LogMatchStart":
            map_name = t['mapName']
            break

    img = imread("objs/{0}.jpg".format(map_name))

    if "Savage" in map_name:
        scale = 50

    for n in names:
        startlogging = False
        x = []
        y = []
        for t in data:
            if t["_T"] == "LogItemUnequip" and \
                            t["character"]["name"] == n and \
                            t["item"][
                                "itemId"] == "Item_Back_B_01_StartParachutePack_C":
                startlogging = True
            if startlogging and t["_T"] == "LogPlayerPosition" and \
                            t["character"]["name"] == n:
                x.append(t["character"]["location"]["x"] / scale)
                y.append(t["character"]["location"]["y"] / scale)

            if t["_T"] == "LogPlayerKill" and t["killer"]["name"] == n:
                kl = t['killer']['location']
                vl = t['victim']['location']
                if kl['x'] == 0 or vl['x'] == 0:
                    continue
                plt.plot([kl['x'] / scale, vl['x'] / scale],
                         [kl['y'] / scale, vl['y'] / scale], color="lime",
                         zorder=2)
                plt.plot(vl['x'] / scale, vl['y'] / scale, 'g+', zorder=3)
            elif t["_T"] == "LogPlayerKill" and t["victim"]["name"] == n:
                kl = t['killer']['location']
                vl = t['victim']['location']
                if kl['x'] == 0 or vl['x'] == 0:
                    continue
                plt.plot([kl['x'] / scale, vl['x'] / scale],
                         [kl['y'] / scale, vl['y'] / scale], color="red",
                         zorder=2)
                plt.plot(vl['x'] / scale, vl['y'] / scale, 'rx', zorder=3)
                ax.annotate(n, (vl['x'] / scale, vl['y'] / scale))
        if len(x) > 0 and len(y) > 0:
            plt.plot(x[0], y[0], 'k+', label="SP", zorder=5)
            plt.plot(x, y, color="yellow", zorder=1)
    ax.set_aspect('equal', 'datalim')
    ax.autoscale(False)
    # plt.axis([0, 8192, 0, 8192])
    ax.invert_yaxis()
    plt.axis('off')
    plt.imshow(img)

    # plt.show()
    plt.savefig('/tmp/map.png', dpi=200)
    return '/tmp/map.png'


def get_known_pubg_names():
    """
    Gets known pubg names from data base

    :return:
    """
    names_to_find = []
    r_map = {}

    for u in c.users:
        if 'pubg' in c.users[u]:
            names_to_find.append(c.users[u]['pubg'])
            r_map[c.users[u]['pubg']] = u
    return names_to_find, r_map


def get_map_byid(match_to_get):
    """
    Gets a map by match id
    :param match_to_get: match id
    :return: returns the filename of the map
    """
    if c.pubg_api is None:
        c.pubg_api = PUBG(c.pubg_api_key, Shard.PC_NA)
    match = c.pubg_api.matches().get(match_to_get)
    url = match.assets[0].url
    names, toss = get_known_pubg_names()
    return build_map(url, names)


def distance(p0, p1):
    """
    returns distance between two pubg points in meters
    :param p0: point 1
    :param p1: point 2
    :return:
    """
    return math.sqrt((p0[0] - p1[0]) ** 2 + (p0[1] - p1[1]) ** 2 +
                     (p0[2] - p1[2]) ** 2) / 100


def filter_data(d_to_filt, names_to_include):
    """
    Filters telemetry data
    :param d_to_filt: Unfiltered telemetry data
    :param names_to_include: list of names to include
    :return: filter event list
    """
    data = []
    for t in d_to_filt:
        if 'character' in t and t['character']['name'] in names_to_include:
            data.append(t)
        elif 'attacker' in t and t['attacker'] is not None and \
                t['attacker']['name'] in names_to_include:
            data.append(t)
        elif 'victim' in t and t['victim']['name'] in names_to_include:
            data.append(t)
        elif 'killer' in t and t['killer']['name'] in names_to_include:
            data.append(t)
    return data


def get_attackId(data, aId):
    """
    returns the Attack record and Damage record given an attack id
    :param data: data to scan.
    :param aId: Attack id to look for
    :return: pair [AttackRecord, DamageRecord]
    """

    dr = None
    ar = None
    for t in data:
        if 'attackId' in t and t['attackId'] == aId:
            if t['_T'] == 'LogPlayerAttack':
                ar = t
            elif t['_T'] == 'LogPlayerTakeDamage':
                dr = t
        if dr is not None and ar is not None:
            break
    return ar, dr


def add_match_id(name, mp_id):
    """
    Adds a match id to players record and removes an old if needed
    :param name: Name of player
    :param mp_id: match id to add
    :return:
    """
    if 'pubg_match' not in c.users[name]:
        c.users[name]["pubg_match"] = []
    c.users[name]["pubg_match"].append(mp_id)
    while len(c.users[name]["pubg_match"]) > max_mids_records:
        c.users[name]["pubg_match"].pop(0)


def calc_p_dist(player1, player2):
    """
    Calculates the distance between two players
    :param player2: First player
    :param player1: Second player
    :return: distance in meters
    """
    p0 = [player1['location']['x'], player1['location']['y'],
          player1['location']['z']]
    p1 = [player2['location']['x'], player2['location']['y'],
          player2['location']['z']]
    return distance(p0, p1)


def add_rank(name, rank):
    """
    Manages average rank over last 10 games for player

    :param name: Name of player
    :param rank: rank to add
    :return: Average rank
    """
    if 'pubg_ranks' not in c.users[name]:
        c.users[name]["pubg_ranks"] = []
    c.users[name]["pubg_ranks"].append(rank)
    while len(c.users[name]["pubg_ranks"]) > 10:
        c.users[name]["pubg_ranks"].pop(0)
    return stats.mean(c.users[name]["pubg_ranks"])


def add_wep_kill(name, weapon):
    """
    Manage weapon kills in player record
    :param name: name of player
    :param weapon: weapon to add kill to
    :return:
    """
    if "pubg_weps" not in c.users[name]:
        c.users[name]["pubg_weps"] = {}
    if weapon not in c.users[name]["pubg_weps"]:
        c.users[name]["pubg_weps"][weapon] = 1
    else:
        c.users[name]["pubg_weps"][weapon] += 1


async def get_pubg_report(match, names, partis, r_map, chan):
    """
    Constructs and returns a pubg match report
    :param match: Match Object
    :param names: Names to filter for in report
    :param partis: Participant Objects
    :param r_map: PUBG name to Discord name
    :param chan: channel to send to
    :return: None
    """

    out_str = ".\n!!!PUBG Report!!!\n"
    out_str += "Mode: {}\n".format(match.game_mode)
    out_str += "Players: {}\n".format(", ".join(names))
    out_str += "Rank: {}/{}\n\n" \
        .format(partis[0].win_place, len(match.rosters))

    url = match.assets[0].url
    if partis[0].win_place <= 10:
        map_file = build_map(url, names)
        await chan.send(out_str)
        await chan.send("", file=discord.File(map_file))
        out_str = ""

    r = requests.get(url)
    try:
        data = r.json()
    except JSONDecodeError:
        for pp in partis:
            add_match_id(r_map[pp.name], match.id)
            add_rank(r_map[pp.name], partis[0].win_place)
        return
    data = filter_data(data, names)

    # Get individual stats
    for pp in partis:
        add_match_id(r_map[pp.name], match.id)
        add_rank(r_map[pp.name], partis[0].win_place)
        out_str += "{} stats:\n".format(pp.name)
        out_str += "{} damage for {} kills and {} knocks. " \
            .format(pp.damage_dealt, pp.kills, pp.dbnos)

        wep_str = "WepProg: Fist"
        # ArmShot, HeadShot, LegShot, PelvisShot, TorsoShot
        tor_s = 0
        hea_s = 0
        arm_s = 0
        pel_s = 0
        leg_s = 0
        ns_s = 0
        hits = []
        shots = []

        for t in data:
            if "character" in t and t["character"]['name'] == pp.name and \
                            t["_T"] == "LogItemPickup" and \
                            t['item']['category'] == "Weapon":
                if "FlareGun" in t['item']['itemId']:
                    wep = "FlareGun"
                else:
                    wep = items[t['item']['itemId']]
                wep_str += "->{}".format(wep)

            if t["_T"] == "LogPlayerTakeDamage" and \
                            t["attacker"] is not None and \
                            t["attacker"]["name"] == pp.name and \
                            t["damageTypeCategory"] == "Damage_Gun":
                if t['damageReason'] == 'TorsoShot':
                    tor_s += 1
                elif t['damageReason'] == 'HeadShot':
                    hea_s += 1
                elif t['damageReason'] == 'ArmShot':
                    arm_s += 1
                elif t['damageReason'] == 'LegShot':
                    leg_s += 1
                elif t['damageReason'] == 'PelvisShot':
                    pel_s += 1
                else:
                    ns_s += 1
                if t['attackId'] not in hits:
                    hits.append(t['attackId'])
            elif t["_T"] == "LogPlayerAttack" and \
                            t["attacker"] is not None and \
                            t["attacker"]["name"] == pp.name and \
                            t['attackType'] == 'Weapon' and \
                    t['weapon']['itemId'].startswith("Item_Weapon_"):
                if t['attackId'] not in shots:
                    shots.append(t['attackId'])
            elif t["_T"] == "LogPlayerKill" and \
                            t["killer"]["name"] == pp.name and \
                            t["damageTypeCategory"] == "Damage_Gun" and \
                            "damageCauserName" in t:
                add_wep_kill(r_map[pp.name], dcauses[t["damageCauserName"]])

        ts = hea_s + tor_s + pel_s + arm_s + leg_s + ns_s
        if len(shots) > 0:
            out_str += "{}% accuracy.".format(round(len(hits) * 100 /
                                                    len(shots)))
        out_str += "\n"
        wep_str += "\n"
        out_str += wep_str
        if ts > 0:
            out_str += "{} Hits - ".format(ts)
            out_str += "Head: {} ({}%), ".format(hea_s, round(hea_s * 100 / ts))
            out_str += "Torso: {} ({}%), ".format(tor_s, round(tor_s * 100 /
                                                               ts))
            out_str += "Pelvis: {} ({}%), ".format(pel_s, round(pel_s * 100 /
                                                                ts))
            out_str += "Arm: {} ({}%), ".format(arm_s, round(arm_s * 100 / ts))
            out_str += "Leg: {} ({}%), ".format(leg_s, round(leg_s * 100 / ts))
            out_str += "Unk: {} ({}%)\n".format(ns_s, round(ns_s * 100 / ts))

        h_dists = []
        for h in hits:
            ar, dr = get_attackId(data, h)
            if 'victim' in dr and 'attacker' in ar:
                h_dists.append(calc_p_dist(ar['attacker'], dr['victim']))
        if len(h_dists) > 0:
            out_str += "Avg Hit Dist: {}m, Longest Hit: {}m\n" \
                .format(round(stats.mean(h_dists)), round(max(h_dists)))
            if 'pubg_recs' not in c.users[r_map[pp.name]]:
                c.users[r_map[pp.name]]['pubg_recs'] = {}
            r_data = c.users[r_map[pp.name]]['pubg_recs']
            if "dam" not in r_data or pp.damage_dealt > r_data['dam']:
                out_str += "New personal best in damage! ({})\n" \
                    .format(pp.damage_dealt)
                r_data['dam'] = pp.damage_dealt
            if "kills" not in r_data or pp.kills > r_data['kills']:
                out_str += "New personal best in kills! ({})\n".format(pp.kills)
                r_data['kills'] = pp.kills
            if "long_h" not in r_data or max(h_dists) > r_data['long_h']:
                out_str += "New personal best in longest hit! ({})\n" \
                    .format(max(h_dists))
                r_data['long_h'] = max(h_dists)
        out_str += "\n"
    del data
    await chan.send(out_str)


async def update_last_10():
    """
    Updates the last ten matches silently.
    :return: None
    """
    try:
        names_to_find, r_map = get_known_pubg_names()
        players = None
        while players is None:
            players = c.pubg_api.players().filter(
                player_names=names_to_find)
            await asyncio.sleep(60)

        for p in players:
            i = 0
            m_to_add = []
            if not hasattr(p, 'matches'):
                continue
            for m in p.matches:
                # for the first 3 matches
                i += 1
                if i > 10:
                    break

                # if that match isn't in the players queue
                if 'pubg_match' not in c.users[r_map[p.name]] or \
                                m.id not in c.users[r_map[p.name]][
                            'pubg_match']:
                    mp_id = m.id
                    m_to_add.append(c.pubg_api.matches().get(mp_id))
                    await asyncio.sleep(10)

            for m in reversed(m_to_add):
                if m.game_mode.startswith("warmode"):
                    continue

                # Find the team roster
                found = False
                partis = []
                names = []
                for wr in m.rosters:
                    if found:
                        break
                    for part in wr.participants:
                        if part.name == p.name:
                            partis.append(part)
                            names.append(part.name)
                            found = True
                            break

                url = m.assets[0].url
                r = requests.get(url)
                try:
                    data = r.json()
                except JSONDecodeError:
                    for pp in partis:
                        add_match_id(r_map[pp.name], m.id)
                        add_rank(r_map[pp.name], partis[0].win_place)
                    return
                data = filter_data(data, names)

                # Get individual stats
                for pp in partis:
                    add_match_id(r_map[pp.name], m.id)
                    add_rank(r_map[pp.name], partis[0].win_place)

                    # ArmShot, HeadShot, LegShot, PelvisShot, TorsoShot
                    hits = []
                    shots = []

                    for t in data:
                        if t["_T"] == "LogPlayerTakeDamage" and \
                                        t["attacker"] is not None and \
                                        t["attacker"]["name"] == pp.name and \
                                        t["damageTypeCategory"] == "Damage_Gun":
                            if t['attackId'] not in hits:
                                hits.append(t['attackId'])
                        elif t["_T"] == "LogPlayerAttack" and \
                                        t["attacker"] is not None and \
                                        t["attacker"]["name"] == pp.name and \
                                        t['attackType'] == 'Weapon' and \
                                t['weapon']['itemId'].startswith(
                                    "Item_Weapon_"):
                            if t['attackId'] not in shots:
                                shots.append(t['attackId'])
                        elif t["_T"] == "LogPlayerKill" and \
                                        t["killer"]["name"] == pp.name and \
                                        t["damageTypeCategory"] == "Damage_Gun" and \
                                        "damageCauserName" in t:
                            add_wep_kill(r_map[pp.name],
                                         dcauses[t["damageCauserName"]])

                    h_dists = []
                    for h in hits:
                        ar, dr = get_attackId(data, h)
                        if 'victim' in dr and 'attacker' in ar:
                            h_dists.append(calc_p_dist(ar['attacker'], dr['victim']))
                    if len(h_dists) > 0:
                        if 'pubg_recs' not in c.users[r_map[pp.name]]:
                            c.users[r_map[pp.name]]['pubg_recs'] = {}
                        r_data = c.users[r_map[pp.name]]['pubg_recs']
                        if "dam" not in r_data or pp.damage_dealt > r_data[
                            'dam']:
                            r_data['dam'] = pp.damage_dealt
                        if "kills" not in r_data or pp.kills > r_data['kills']:
                            r_data['kills'] = pp.kills
                        if "long_h" not in r_data or max(h_dists) > r_data[
                            'long_h']:
                            r_data['long_h'] = max(h_dists)
                del data
                await asyncio.sleep(10)
            await asyncio.sleep(60)

    except (APIError, NotFoundError) as e:
        print("PUBG API Error caught, ignoring.")
        traceback.print_exception(type(e), e, e.__traceback__, file=sys.stderr)
    c.whos_in.update_db()
    print("Finished updating last 10.")


async def check_pubg_matches(ctx):
    """
    Checks for new matches
    :return: None
    """
    c_to_send = None

    await ctx.wait_until_ready()
    await asyncio.sleep(60)
    for channel in ctx.get_all_channels():
        if channel.name == 'gen_testing' \
                or channel.name == c.ARGS['channel']:
            c_to_send = channel
            break

    if c.pubg_api_key is None:
        return

    if c.pubg_api is None:
        c.pubg_api = PUBG(c.pubg_api_key, Shard.PC_NA)

    await update_last_10()

    while True:
        try:
            # get pubg account names to look for and build a reverse map to discord
            names_to_find, r_map = get_known_pubg_names()

            players = None
            while players is None:
                players = c.pubg_api.players().filter(
                    player_names=names_to_find)
                await asyncio.sleep(60)

            for p in players:
                i = 0
                if not hasattr(p, 'matches'):
                    continue
                for m in p.matches:
                    # for the first 3 matches
                    i += 1
                    if i > 3:
                        break

                    # if that match isn't in the players queue
                    if 'pubg_match' not in c.users[r_map[p.name]] or \
                                    m.id not in c.users[r_map[p.name]][
                                'pubg_match']:
                        mp_id = m.id
                        match = c.pubg_api.matches().get(mp_id)
                        if match.game_mode.startswith("warmode"):
                            continue

                        # Find the team roster
                        found = False
                        r = None
                        partis = []
                        names = []
                        for wr in match.rosters:
                            if found:
                                break
                            for part in wr.participants:
                                if part.name == p.name:
                                    partis.append(part)
                                    names.append(part.name)
                                    r = wr
                                    found = True
                                    break

                        # See if we know teammates
                        for pp in r.participants:
                            if pp.name in names_to_find and \
                                            pp.name not in names:
                                partis.append(pp)
                                names.append(pp.name)

                        # Construct the report
                        await get_pubg_report(match, names, partis, r_map,
                                              c_to_send)

                    c.whos_in.update_db()
                await asyncio.sleep(60)
        except (APIError, NotFoundError) as e:
            print("PUBG API Error caught, ignoring.")
            traceback.print_exception(type(e), e, e.__traceback__,
                                      file=sys.stderr)
        await asyncio.sleep(60 * 10)


def setup(bot):
    bot.add_cog(Puby(bot))
    bot.loop.create_task(check_pubg_matches(bot))
