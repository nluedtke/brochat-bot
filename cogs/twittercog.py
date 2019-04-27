import asyncio
from datetime import datetime
from random import randint, shuffle

import common
from cogs.duelcog import item_chance_roll
from discord.ext import commands
from twython import TwythonError


class Twitter(commands.Cog):
    """ Twitter Fetchers"""


    @commands.command(name="trump")
    async def get_trump(ctx):
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
            await get_last_tweet(twitter_id, tweet_text,
                                 rt_text, ctx, max(1, common.missed_trumps))
        except TwythonError:
            await ctx.send("Twitter is acting up, try again later.")
        else:
            if common.trump_chance_roll_rdy:
                await item_chance_roll(ctx.message.author.display_name,
                                       ctx.message.channel,
                                       92 - (common.missed_trumps * 2))
                common.trump_chance_roll_rdy = False
            common.missed_trumps = 0

    @commands.command(name='news')
    async def get_news(ctx):
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

    @commands.command(name='toggle-news', hidden=True)
    async def toggle_news(ctx):
        """Toggle the news feed on and off"""

        if common.NEWS_FEED_ON:
            common.NEWS_FEED_ON = False
            await ctx.send("News Feed turned off.")
        else:
            if not common.NEWS_FEED_CREATED:
                ctx.loop.create_task(handle_news(ctx))
                common.NEWS_FEED_CREATED = True
            common.NEWS_FEED_ON = True
            await ctx.send("News Feed turned on.")


async def get_last_tweet(_id, tweet_text, rt_text, ctx, c=1):
    """
    Gets the last tweet for id.
    :param _id: Twitter id
    :param tweet_text: flavor text for tweets
    :param rt_text: flavor text for retweets
    :param ctx: Context
    :param c: number of tweets to get
    :return:
    """
    if common.twitter is None:
        await ctx.send("Twitter not activated.")
        return

    try:
        last_tweet = common.twitter.get_user_timeline(screen_name=_id, count=c,
                                                      include_retweets=True)
    except TwythonError as e:
        raise e
    else:
        for i in range(c):
            # if it's a retweet, send the original tweet
            if 'retweeted_status' in last_tweet[i]:
                rt_id = last_tweet[i]['retweeted_status']['id']
                rt_screen_name = last_tweet[i]['retweeted_status']['user'][
                        'screen_name']
                await ctx.send('{}\n\nhttps://twitter.com/{}/status/{}'
                                  .format(rt_text, rt_screen_name, str(rt_id)))
            # otherwise, send the tweet
            else:
                await ctx.send('{}\n\nhttps://twitter.com/{}/status/{}'
                                  .format(tweet_text, last_tweet[i]['user']
                                          ['screen_name'],
                                          str(last_tweet[i]['id'])))


async def check_trumps_mouth(ctx):
    """
    Waits for an update from the prez
    :return: None
    """
    c_to_send = None
    decay = 0

    await ctx.wait_until_ready()
    for channel in ctx.get_all_channels():
        if channel.name == 'gen_testing' \
                or channel.name == common.ARGS['channel']:
            c_to_send = channel
            break

    if common.twitter is None:
        return

    common.last_id = common.twitter.get_user_timeline(
        screen_name='realdonaldtrump', count=1, include_retweets=False)[0]['id']

    delay = common.trump_del * 60

    while not ctx.is_closed:
        await asyncio.sleep(delay)
        print("Checked trump at {}".format(datetime.now()))
        try:
            trumps_lt_id = common.twitter.get_user_timeline(
                screen_name='realdonaldtrump', count=1,
                include_retweets=False)[0]['id']
        except:
            print("Error caught in check_trump, shortening delay")
            delay = 60
        else:
            if decay > 0:
                delay = (common.trump_del - decay) * 60
                decay -= 1
            else:
                delay = common.trump_del * 60
            if trumps_lt_id != common.last_id:
                common.trump_tweets_seen += 1
                await c_to_send.send("New Message from the prez! Try !trump")
                decay = common.trump_del - 1
                delay = (common.trump_del - decay) * 60
                common.last_id = trumps_lt_id
                common.trump_chance_roll_rdy = True
                common.missed_trumps += 1


async def handle_news(ctx):
    """
    Handles the news feed
    :return:
    """

    c_to_send = ctx.message.channel
    shuffle(common.news_handles)

    await ctx.wait_until_ready()
    for channel in ctx.get_all_channels():
        if channel.name == 'gen_testing' or channel.name == 'newsfeed':
            c_to_send = channel
            break

    if common.twitter is None:
        await ctx.send("Twitter not activated.")
        return

    delay = (common.news_del * 60) + (randint(0, 10) * 60)
    while not ctx.is_closed:
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
                await c_to_send.send("https://twitter.com/{0}/status/{1}"
                               .format(news[0]['user']['screen_name'],
                                       str(news[0]['id'])))
        else:
            common.NEWS_FEED_CREATED = False
            print("Destroying News Feed Task")
            return


def setup(bot):
    bot.add_cog(Twitter(bot))
    bot.loop.create_task(check_trumps_mouth(bot))
