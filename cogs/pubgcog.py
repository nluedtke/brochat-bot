from pubg_python import PUBG, Shard
from pubg_python.exceptions import NotFoundError
import common
import asyncio
from datetime import datetime as dt
import requests
import math
import statistics as stats
import json

with open("cogs/itemId.json", 'r') as infile:
    items = json.load(infile)


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
                or channel.name == common.ARGS['channel']:
            c_to_send = channel
            break

    if common.pubg_api_key is None:
        await bot.say("PUBG not activated.")
        return

    if common.pubg_api is None:
        common.pubg_api = PUBG(common.pubg_api_key, Shard.PC_NA)

    # TODO New database should be added to users info
    if "pubg_info" not in common.db:
        common.db['pubg_info'] = {}

    while True:
        # TODO Hardcoded names, should come from database
        names_to_find = ['palu1', 'qtstrm', 'OhDip', 'Mrduck34', 'Janus113']
        players = None
        while players is None:
            try:
                players = common.pubg_api.players().filter(
                    player_names=names_to_find)
            except NotFoundError:
                players = None
                await asyncio.sleep(60)

        for p in players:
            if p.name not in common.db["pubg_info"] or \
                    common.db["pubg_info"][p.name][0] != p.matches[0].id:
                mp_id = p.matches[0].id
                match = common.pubg_api.matches().get(mp_id)

                if p.name in common.db["pubg_info"] and \
                   dt.strptime(match.created_at, "%Y-%m-%dT%H:%M:%SZ") <= \
                   dt.strptime(common.db["pubg_info"][p.name][1],
                               "%Y-%m-%dT%H:%M:%SZ"):
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
                            break
                            found = True

                # See if we know teammates
                for pp in r.participants:
                    if pp.name in names_to_find and \
                       pp.name not in names:
                        partis.append(pp)
                        names.append(pp.name)

                # Construct the report
                out_str = ".\n!!!PUBG Report!!!\n"
                out_str += "Mode: {}\n".format(match.game_mode)
                out_str += "Players: {}\n".format(names)
                out_str += "Rank: {}/{}\n\n"\
                           .format(part.win_place,
                                   len(match.rosters))

                url = match.assets[0].url
                r = requests.get(url)
                data = r.json()
                data = filter_data(data, names_to_find)

                # Get individual stats
                for pp in partis:
                    common.db["pubg_info"][pp.name] = \
                        [mp_id, match.created_at]
                    out_str += "{} stats:\n".format(pp.name)
                    out_str += "{} damage for {} kills.".format(pp.damage_dealt,
                                                                pp.kills)
                    wep_str = "WepProg: Fist"
                    # ArmShot, HeadShot, LegShot, PelvisShot, TorsoShot
                    tor_s = 0
                    hea_s = 0
                    arm_s = 0
                    pel_s = 0
                    leg_s = 0
                    hits = []
                    shots = []

                    for t in data:
                        if "character" in t and \
                           t["character"]['name'] == pp.name and \
                           t["_T"] == "LogItemPickup" and \
                           t['item']['category'] == "Weapon":
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
                            hits.append(t['attackId'])
                        if t["_T"] == "LogPlayerAttack" and \
                           t["attacker"]["name"] == pp.name and \
                           t['attackType'] == 'Weapon' and \
                           t['weapon']['itemId'].startswith("Item_Weapon_"):
                            shots.append(t['attackId'])

                    ts = hea_s + tor_s + pel_s + arm_s + leg_s
                    if len(shots) > 0:
                        out_str += " {}% accuracy.\n"\
                                   .format(round(len(hits) * 100 /
                                                 len(shots)))
                    if ts > 0:
                        wep_str += "\n"
                        out_str += wep_str
                        out_str += "{} Hits - ".format(ts)
                        out_str += "HeadShot {} ({}%), "\
                                   .format(hea_s, round(hea_s * 100 / ts))
                        out_str += "TorsoShot {} ({}%), "\
                                   .format(tor_s, round(tor_s * 100 / ts))
                        out_str += "PelvisShot {} ({}%), "\
                                   .format(pel_s, round(pel_s * 100 / ts))
                        out_str += "ArmShot {} ({}%), " \
                                   .format(arm_s, round(arm_s * 100 / ts))
                        out_str += "LegShot {} ({}%)\n" \
                                   .format(leg_s, round(leg_s * 100 / ts))
                    else:
                        out_str += "No Hits.\n"

                    h_dists = []
                    for h in hits:
                        ar, dr = get_attackId(data, h)
                        p0 = [ar['attacker']['location']['x'],
                              ar['attacker']['location']['y'],
                              ar['attacker']['location']['z']]
                        p1 = [dr['victim']['location']['x'],
                              dr['victim']['location']['y'],
                              dr['victim']['location']['z']]
                        h_dists.append(distance(p0, p1))
                    out_str += "Avg Hit Dist: {}m, Longest Hit: {}m\n\n"\
                               .format(round(stats.mean(h_dists)),
                                       round(max(h_dists)))

                del data
                await bot.send_message(c_to_send, out_str)
                common.whos_in.update_db()
                break
            await asyncio.sleep(60)
        await asyncio.sleep(60*15)


def setup(bot):
    bot.add_cog(Puby(bot))
    bot.loop.create_task(check_pubg_matches(bot))
