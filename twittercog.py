import discord
from discord.ext import commands
import common
from twython import Twython, TwythonError
from duelcog import item_chance_roll
from random import shuffle


class TwitterCog:
    """ Twitter Fetchers"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="trump", pass_context=True)
    async def get_trump(self, ctx):
        """Gets a presidential tweet"""

        if common.twitter is None:
            await ctx.send("Twitter not activated.")
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
            await self.bot.say("Twitter is acting up, try again later.")

        if common.trump_chance_roll_rdy:
            await item_chance_roll(ctx, ctx.message.author.display_name)
            common.trump_chance_roll_rdy = False

    @commands.command(name='news', pass_context=True)
    async def get_news(self, ctx):
        """Get a news report"""
        if common.twitter is None:
            return

        shuffle(common.news_handles)
        found_art = False

        while not found_art:
            source = common.news_handles.pop(0)
            common.news_handles.append(source)
            tweet_text = "It looks like @" + source + " is reporting:"
            rt_text = "It looks like @" + source + " is retweeting:"

            try:
                await get_last_tweet(source, tweet_text, rt_text, ctx)
            except TwythonError:
                print("Error in get_news, trying another source")

            else:
                found_art = True

        return

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
    if common.twitter is None:
        await ctx.bot.say("Twitter not activated.")
        return

    try:
        last_tweet = common.twitter.get_user_timeline(screen_name=_id, count=1,
                                                      include_retweets=True)
    except TwythonError as e:
        raise e
    else:
        # if it's a retweet, send the original tweet
        if 'retweeted_status' in last_tweet[0]:
            if _id == 'realdonaldtrump':
                common.last_id = last_tweet[0]['id']
            rt_id = last_tweet[0]['retweeted_status']['id']
            rt_screen_name = last_tweet[0]['retweeted_status']['user'][
                    'screen_name']
            await ctx.bot.say('{}\n\nhttps://twitter.com/{}'
                                           '/status/{}'
                                           .format(rt_text, rt_screen_name,
                                                   str(rt_id)))
        # otherwise, send the tweet
        else:
            if _id == 'realdonaldtrump':
                common.last_id = last_tweet[0]['id']
            await ctx.bot.say('{}\n\nhttps://twitter.com/{}/status/{}'
                              .format(tweet_text, last_tweet[0]['user']
                                      ['screen_name'],
                                      str(last_tweet[0]['id'])))


def setup(bot):
    bot.add_cog(TwitterCog(bot))