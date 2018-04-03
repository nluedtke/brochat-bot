from pubg_python import PUBG, Shard
import common
import asyncio


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
        players = common.pubg_api.players().filter(
            player_names=['palu1', 'qtstrm',
                          'OhDip',
                          'MrDuck34',
                          'Janus113'])
        for p in players:
            if p not in common.db["pubg_info"] or \
               common.db["pubg_info"][p] != p.matches[0].id:
                mp_id = p.matches[0].id
                common.db["pubg_info"][p] = mp_id
                match = common.pubg_api.matches().get(mp_id)
                for r in match.rosters:
                    for part in r.participants:
                        if part.name == p.name:
                            await bot.send_message(
                                c_to_send, "{} completed a {} PUBG game."
                                           .format(part.name, match.game_mode))
                            await bot.send_message(
                                c_to_send, "{} survived for {} dealing {} "
                                           "damage and killing {} people."
                                           .format(part.name,
                                                   part.time_survived,
                                                   part.damage_dealt,
                                                   part.kills))
                            await bot.send_message(
                                c_to_send, "{} placed {}."
                                           .format(part.name, part.win_place))
                        break
            await asyncio.sleep(60)
        await asyncio.sleep(60*10)


def setup(bot):
    bot.add_cog(Puby(bot))
    bot.loop.create_task(check_pubg_matches(bot))
