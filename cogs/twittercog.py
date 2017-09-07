import asyncio
from datetime import datetime
from random import shuffle, randint

from discord.ext import commands
from twython import TwythonError

import common
from cogs.duelcog import item_chance_roll


class Twitter:
    """ Twitter Fetchers"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="trump", pass_context=True)
    async def get_trump(self, ctx):
        """Get Trump's latest Yuge success!"""

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
            await item_chance_roll(ctx.bot, ctx.message.author.display_name,
                                   ctx.message.channel)
            common.trump_chance_roll_rdy = False

    @commands.command(name='news', pass_context=True)
    async def get_news(self, ctx):
        """Grab a news story"""
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

    @commands.command(name='toggle-news', pass_context=True, hidden=True)
    async def toggle_news(self, ctx):
        """Toggle the news feed on and off"""

        if common.NEWS_FEED_ON:
            common.NEWS_FEED_ON = False
            await self.bot.say("News Feed turned off.")
        else:
            if not common.NEWS_FEED_CREATED:
                self.bot.loop.create_task(handle_news(ctx))
                common.NEWS_FEED_CREATED = True
            common.NEWS_FEED_ON = True
            await self.bot.say("News Feed turned on.")

async def get_last_tweet(_id, tweet_text, rt_text, ctx):
    """
    Gets the last tweet for id.
    :param _id: Twitter id
    :param tweet_text: flavor text for tweets
    :param rt_text: flavor text for retweets
    :param ctx: Context
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
            if _id == 'realdonaldtrump'and \
                            common.last_id != last_tweet[0]['id']:
                await item_chance_roll(ctx.bot, ctx.message.author.display_name,
                                       ctx.message.channel)
                common.last_id = last_tweet[0]['id']
            rt_id = last_tweet[0]['retweeted_status']['id']
            rt_screen_name = last_tweet[0]['retweeted_status']['user'][
                    'screen_name']
            await ctx.bot.say('{}\n\nhttps://twitter.com/{}/status/{}'
                              .format(rt_text, rt_screen_name, str(rt_id)))
        # otherwise, send the tweet
        else:
            if _id == 'realdonaldtrump':
                common.last_id = last_tweet[0]['id']
            await ctx.bot.say('{}\n\nhttps://twitter.com/{}/status/{}'
                              .format(tweet_text, last_tweet[0]['user']
                                      ['screen_name'],
                                      str(last_tweet[0]['id'])))

async def check_trumps_mouth(bot):
    """
    Waits for an update from the prez
    :return: None
    """
    c_to_send = None

    await bot.wait_until_ready()
    for channel in bot.get_all_channels():
        if channel.name == 'gen_testing' \
                or channel.name == common.ARGS['channel']:
            c_to_send = channel
            break

    if common.twitter is None:
        await bot.say("Twitter not activated.")
        return

    common.last_id = common.twitter.get_user_timeline(
        screen_name='realdonaldtrump', count=1, include_retweets=False)[0]['id']

    delay = common.trump_del * 60

    while not bot.is_closed:
        await asyncio.sleep(delay)
        print("Checked trump at {}".format(datetime.now()))
        try:
            trumps_lt_id = common.twitter.get_user_timeline(
                screen_name='realdonaldtrump', count=1,
                include_retweets=False)[0]['id']
        except:
            print("Error caught in check_trump, shortening delay")
            delay = 10 * 60
        else:
            delay = common.trump_del * 60
            if trumps_lt_id != common.last_id:
                common.trump_tweets_seen += 1
                await bot.send_message(c_to_send, "New Message from the prez! "
                                                  "Try !trump")
                common.last_id = trumps_lt_id
                common.trump_chance_roll_rdy = True

async def handle_news(ctx):
    """
    Handles the news feed
    :return:
    """

    c_to_send = ctx.message.channel
    shuffle(common.news_handles)

    await ctx.bot.wait_until_ready()
    for channel in ctx.bot.get_all_channels():
        if channel.name == 'gen_testing' or channel.name == 'newsfeed':
            c_to_send = channel
            break

    if common.twitter is None:
        await ctx.bot.say("Twitter not activated.")
        return

    delay = (common.news_del * 60) + (randint(0, 10) * 60)
    while not ctx.bot.is_closed:
        next_source = common.news_handles.pop(0)
        common.news_handles.append(next_source)
        print("Next news source will be {}".format(next_source))
        await asyncio.sleep(delay)
        if common.NEWS_FEED_ON:
            try:
                news = common.twitter.get_user_timeline(
                    screen_name=next_source, count=1,
                    include_retweets=False)
            except:
                print("Error caught in news, shortening delay")
                delay = 30
            else:
                delay = (common.news_del * 60) + (randint(0, 10) * 60)
                await ctx.bot.send_message(
                    c_to_send, "https://twitter.com/{0}/status/{1}"
                               .format(news[0]['user']['screen_name'],
                                       str(news[0]['id'])))
        else:
            common.NEWS_FEED_CREATED = False
            print("Destroying News Feed Task")
            return


def setup(bot):
    bot.add_cog(Twitter(bot))
    bot.loop.create_task(check_trumps_mouth(bot))
