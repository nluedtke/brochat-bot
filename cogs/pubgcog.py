from pubg_python import PUBG, Shard
import common
import asyncio
import datetime
import requests


class Puby:
    """ Pubg Fetchers"""

    def __init__(self, bot):
        self.bot = bot


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
                if datetime.datetime(match.created_at) <= \
                   datetime.datetime(common.db["pubg_info"][p.name][1]):
                    continue
                found = False
                for r in match.rosters:
                    if found:
                        break
                    for part in r.participants:
                        if part.name == p.name:
                            players = [part.name]
                            for pp in r.participants:
                                if pp.name in names_to_find:
                                    players.append(pp.name)
                            out_str = ".\n!!!PUBG Report!!\n!"
                            out_str += "Mode: {}\n".format(match.game_mode)
                            out_str += "Players: {}\n".format(players)
                            out_str += "Rank: {}/{}\n\n"\
                                       .format(part.win_place,
                                               len(match.rosters))

                            url = match.assets[0].url
                            r = requests.get(url)
                            data = r.json()
                            for pp in players:
                                common.db["pubg_info"][pp.name] = \
                                    [mp_id, match.created_at]
                                out_str += "{} stats:\n"
                                out_str += "{} damage for {} kills.\n"\
                                           .format(pp.damage_dealt, pp.kills)
                                wep_str = "WepProg: Fist"
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

                                    # TODO re add logic for hits.

                                    # TODO add logic for Distance

                                wep_str += "\n"
                                out_str += wep_str
                            del data
                            await bot.send_message(c_to_send, out_str)
                            found = True
                            common.db["pubg_info"][p.name] = mp_id
                            common.whos_in.update_db()
                            break
            await asyncio.sleep(60)
        await asyncio.sleep(60*10)


def setup(bot):
    bot.add_cog(Puby(bot))
    bot.loop.create_task(check_pubg_matches(bot))
