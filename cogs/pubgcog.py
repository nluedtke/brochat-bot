from pubg_python import PUBG, Shard
from pubg_python.exceptions import NotFoundError
import common as c
import asyncio
import requests
import math
import statistics as stats
import json

with open("objs/itemId.json", 'r') as infile:
    items = json.load(infile)

# Number of match ids to store
max_mids_records = 20

class Puby:
    """ Pubg Fetchers"""

    def __init__(self, bot):
        self.bot = bot


def distance(p0, p1):
    """
    returns distance between two pubg points in meters
    :param p0: point 1
    :param p1: point 2
    :return:
    """
    return math.sqrt((p0[0] - p1[0])**2 + (p0[1] - p1[1])**2 +
                     (p0[2] - p1[2])**2) / 100


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
        elif 'attacker' in t and t['attacker']['name'] in names_to_include:
            data.append(t)
        elif 'victim' in t and t['victim']['name'] in names_to_include:
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
    if len(c.users[name]["pubg_match"]) > 10:
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
    if len(c.users[name]["pubg_ranks"]) > max_mids_records:
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
    if weapon not in c.users[name]["pub_weps"]:
        c.users[name]["pub_weps"][weapon] = 1
    else:
        c.users[name]["pub_weps"][weapon] += 1


def get_pubg_report(match, names, partis, r_map):
    """
    Constructs and returns a pubg match report
    :param match: Match Object
    :param names: Names to filter for in report
    :param partis: Participant Objects
    :param r_map: PUBG name to Discord name
    :return: Str containing report
    """

    out_str = ".\n!!!PUBG Report!!!\n"
    out_str += "Mode: {}\n".format(match.game_mode)
    out_str += "Players: {}\n".format(", ".join(names))
    out_str += "Rank: {}/{}\n\n" \
        .format(partis[0].win_place, len(match.rosters))

    url = match.assets[0].url
    r = requests.get(url)
    data = r.json()
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
               t["_T"] == "LogItemPickup" and t['item']['category'] == "Weapon":
                wep = items[t['item']['itemId']]
                wep_str += "->{}".format(wep)

            if t["_T"] == "LogPlayerTakeDamage" and \
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
                hits.append(t['attackId'])
            elif t["_T"] == "LogPlayerAttack" and \
               t["attacker"]["name"] == pp.name and \
               t['attackType'] == 'Weapon' and \
               t['weapon']['itemId'].startswith("Item_Weapon_"):
                shots.append(t['attackId'])
            elif t["_T"] == "LogPlayerKill" and \
                            t["attacker"]["name"] == pp.name and \
                            "damageCauserName" in t:
                add_wep_kill(r_map[pp.name], items[t["damageCauserName"]])

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
    return out_str


async def check_pubg_matches(bot):
    """
    Checks for new matches
    :return: None
    """
    c_to_send = None

    await bot.wait_until_ready()
    await asyncio.sleep(60)
    for channel in bot.get_all_channels():
        if channel.name == 'gen_testing' \
                or channel.name == c.ARGS['channel']:
            c_to_send = channel
            break

    if c.pubg_api_key is None:
        await bot.say("PUBG not activated.")
        return

    if c.pubg_api is None:
        c.pubg_api = PUBG(c.pubg_api_key, Shard.PC_NA)

    while True:
        # get pubg account names to look for and build a reverse map to discord
        names_to_find = []
        r_map = {}

        for u in c.users:
            if 'pubg' in c.users[u]:
                names_to_find.append(c.users[u]['pubg'])
                r_map[c.users[u]['pubg']] = u
        players = None
        while players is None:
            try:
                players = c.pubg_api.players().filter(
                    player_names=names_to_find)
            except NotFoundError:
                players = None
                await asyncio.sleep(60*10)

        for p in players:
            i = 0
            for m in p.matches:
                # for the first 3 matches
                i += 1
                if i > 3:
                    break

                # if that match isn't in the players queue
                if 'pubg_match' not in c.users[r_map[p.name]] or \
                   m.id not in c.users[r_map[p.name]]['pubg_match']:
                    mp_id = m.id
                    match = c.pubg_api.matches().get(mp_id)

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
                    out_str = get_pubg_report(match, names, partis, r_map)

                    await bot.send_message(c_to_send, out_str)
                c.whos_in.update_db()
            await asyncio.sleep(60)
        await asyncio.sleep(60*10)


def setup(bot):
    bot.add_cog(Puby(bot))
    bot.loop.create_task(check_pubg_matches(bot))
