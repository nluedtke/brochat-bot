import discord
from discord.ext import commands
import requests
from random import randint
import common


class RedditCog:
    """ Reddit Fetchers"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='dankmeme', aliases=['dankmay'])
    @commands.cooldown(2, 60 * 5)
    async def dankmeme(self):
        """Gets a dank meme"""
        await self.bot.say(get_reddit("dankmemes"))

    @commands.command(name='bertstrip', aliases=['badchildhood'])
    @commands.cooldown(2, 60 * 5)
    async def bertstrip(self):
        """Gets a bertstrip"""
        await self.bot.say(get_reddit("bertstrips"))


def get_reddit(subreddit):
    """
    Function that fetches dank memes.

    :param subreddit: Subreddit to use for the reddit fetch
    :return: a string to send the client
    """
    number_to_fetch = str(100)
    url = 'https://www.reddit.com/r/{}.json?limit={}'.format(
        subreddit,
        number_to_fetch)
    headers = {
        'User-Agent': 'Brochat-Bot {}.{}'.format(common.VERSION_YEAR,
                                                 common.VERSION_MONTH)
    }
    response = requests.get(url, headers=headers)
    response_json = response.json()

    if 'data' in response_json:
        for entry in response_json['data']['children']:
            if entry['data']['stickied'] is True \
                    or (entry['data']['url'][-4:] != '.png' and
                        entry['data']['url'][-4:] != '.jpg'):
                response_json['data']['children'].remove(entry)
        print(str(len(response_json['data']['children'])))
        seed = randint(0, len(response_json['data']['children']) - 1)
        link = response_json['data']['children'][seed]['data']['url']

        return '{}'.format(link)
    else:
        print('Error, response code: {}'.format(response.status_code))
        return "Looks like an adversary developer pwned " \
               "us...\nhttps://cdn.meme.am/cache/instances/" \
               "folder861/20989861.jpg"


def setup(bot):
    bot.add_cog(RedditCog(bot))