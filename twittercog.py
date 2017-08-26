import discord
from discord.ext import commands
from common import twitter, trump_chance_roll_rdy, last_id
from twython import Twython, TwythonError
from duelcog import item_chance_roll


class TwitterCog:
    """ Twitter Fetchers"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="trump", pass_context=True)
    async def get_trump(self, ctx):
        """
        Gets a presidential tweet

        :param client: The Client
        :param message: The message
        :return: None
        """
        if twitter is None:
            await ctx.send_message("Twitter not activated.")
            return

        twitter_id = 'realdonaldtrump'
        tweet_text = \
            ':pen_ballpoint::monkey: Trump has been saying things, as ' \
            'usual...'
        rt_text = \
            ':pen_ballpoint::monkey: Trump has been repeating things, as ' \
            'usual... (RT ALERT)'

        try:
            await get_last_tweet(twitter_id, tweet_text, rt_text, ctx)
        except TwythonError:
            await ctx.send_message("Twitter is acting up, try again later.")

        if trump_chance_roll_rdy:
            await item_chance_roll(ctx.message.channel,
                                   ctx.message.author.display_name)
            trump_chance_roll_rdy = False

async def get_last_tweet(_id, tweet_text, rt_text, ctx):
    """
    Gets the last tweet for id.
    :param _id: Twitter id
    :param tweet_text: flavor text for tweets
    :param rt_text: flavor text for retweets
    :param client: discord client
    :param message: discord message
    :return:
    """
    if twitter is None:
        await ctx.channel.send_message("Twitter not activated.")
        return

    if _id == 'realdonaldtrump':
        last_id = _id
    try:
        last_tweet = twitter.get_user_timeline(screen_name=_id, count=1,
                                               include_retweets=True)
    except TwythonError as e:
        raise e
    else:
        # if it's a retweet, send the original tweet
        if 'retweeted_status' in last_tweet[0]:
            if _id == 'realdonaldtrump':
                last_id = last_tweet[0]['id']
            rt_id = last_tweet[0]['retweeted_status']['id']
            rt_screen_name = last_tweet[0]['retweeted_status']['user'][
                    'screen_name']
            await ctx.channel.send_message('{}\n\nhttps://twitter.com/{}'
                                           '/status/{}'
                                           .format(rt_text, rt_screen_name,
                                                   str(rt_id)))
        # otherwise, send the tweet
        else:
            if _id == 'realdonaldtrump':
                last_id = last_tweet[0]['id']
            await ctx.channel.send_message('{}\n\nhttps://twitter.com/{}'
                                           '/status/{}'
                                           .format(tweet_text, last_tweet[0]
                                                   ['user']['screen_name'],
                                                   str(last_tweet[0]['id'])))


def setup(bot):
    bot.add_cog(TwitterCog(bot))