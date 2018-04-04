from pubg_python import PUBG, Shard
import common
import asyncio
from datetime import datetime as dt
import requests
import math

known_points = {}


class Puby:
    """ Pubg Fetchers"""

    def __init__(self, bot):
        self.bot = bot


def distance(p0, p1):
    return math.sqrt((p0[0] - p1[0])**2 + (p0[1] - p1[1])**2)


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
        players = common.pubg_api.players().filter(
            player_names=names_to_find)
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
                found = False
                for r in match.rosters:
                    if found:
                        break
                    for part in r.participants:
                        if part.name == p.name:
                            partis = [part]
                            names = [part.name]
                            for pp in r.participants:
                                if pp.name in names_to_find:
                                    partis.append(pp)
                                    names.append(pp.name)
                            out_str = ".\n!!!PUBG Report!!!\n"
                            out_str += "Mode: {}\n".format(match.game_mode)
                            out_str += "Players: {}\n".format(names)
                            out_str += "Rank: {}/{}\n\n"\
                                       .format(part.win_place,
                                               len(match.rosters))

                            url = match.assets[0].url
                            r = requests.get(url)
                            data = r.json()
                            for pp in partis:
                                common.db["pubg_info"][pp.name] = \
                                    [mp_id, match.created_at]
                                out_str += "{} stats:\n".format(pp.name)
                                out_str += "{} damage for {} kills.\n"\
                                           .format(pp.damage_dealt, pp.kills)
                                wep_str = "WepProg: Fist"

                                # ArmShot, HeadShot, LegShot, PelvisShot,
                                # TorsoShot
                                tor_s = 0
                                hea_s = 0
                                arm_s = 0
                                pel_s = 0
                                leg_s = 0
                                first = False

                                for t in data:
                                    if "character" in t and \
                                       t["character"]['name'] == pp.name and \
                                       t["_T"] == "LogItemPickup" and \
                                       t['item']['category'] == "Weapon":
                                        wep = t['item']['itemId']\
                                            .replace("Item_Weapon_", "")\
                                            .replace("_C", "")\
                                            .replace("HK416", "M4")\
                                            .replace("Nagrant", "")
                                        wep_str += "->{}".format(wep)
                                        # if not first:
                                        #     x1 = t['location']['x']
                                        #     y1 = t['location']['y']
                                        #     first = True

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
                                    # TODO add logic for Distance

                                wep_str += "\n"
                                out_str += wep_str

                                ts = hea_s + tor_s + pel_s + arm_s + leg_s
                                out_str += "{} Hits, ".format(ts)
                                out_str += "HeadShot {} ({}%), " \
                                           .format(hea_s,
                                                   round(hea_s * 100 / ts))
                                out_str += "TorsoShot {} ({}%), " \
                                           .format(tor_s,
                                                   round(tor_s * 100 / ts))
                                out_str += "PelvisShot {} ({}%), " \
                                           .format(pel_s,
                                                   round(pel_s * 100 / ts))
                                out_str += "ArmShot {} ({}%), " \
                                           .format(arm_s,
                                                   round(arm_s * 100 / ts))
                                out_str += "LegShot {} ({}%)\n\n" \
                                           .format(leg_s,
                                                   round(leg_s * 100 / ts))

                            del data
                            await bot.send_message(c_to_send, out_str)
                            found = True
                            common.whos_in.update_db()
                            break
            await asyncio.sleep(60)
        await asyncio.sleep(60*10)


def setup(bot):
    bot.add_cog(Puby(bot))
    bot.loop.create_task(check_pubg_matches(bot))
