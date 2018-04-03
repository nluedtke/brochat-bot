from pubg_python import PUBG, Shard
import common


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

    #TODO continue here


def setup(bot):
    bot.add_cog(Puby(bot))
    bot.loop.create_task(check_pubg_matches(bot))
