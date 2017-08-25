# Standard imports
from time import time
import json
import os
from sys import stderr
from random import randint, shuffle, choice
import socket
import datetime
from difflib import get_close_matches
import pytz
import sys
import traceback

# NonStandard Imports
import discord
from discord.ext import commands
import asyncio
from twython import Twython, TwythonError
from twilio.rest import Client
import requests
from gametime import Gametime
from poll import Poll
from duel_item import DuelItem, common_items, rare_items, PoisonEffect
from weekend_games import WeekendGames, argument_parser, pretty_date

description = "A bot to enforce friendship."
startTime = 0

VERSION_YEAR = 2017
VERSION_MONTH = 8
VERSION_DAY = 24
VERSION_REV = 1

# Global toggle for news feed
NEWS_FEED_ON = False
NEWS_FEED_CREATED = False

# Delays for Newsfeed and Check_trump, These are in minutes
# remember that news_del is fuzzed + (0-10)
trump_del = 20
news_del = 55

# Variable hold trumps last tweet id
last_id = 0
trump_chance_roll_rdy = False

# News handles to pull from
news_handles = ['mashable', 'cnnbrk', 'whitehouse', 'cnn', 'nytimes',
                'foxnews', 'reuters', 'npr', 'usatoday', 'cbsnews',
                'abc', 'washingtonpost', 'msnbc', 'ap', 'aphealthscience',
                'lifehacker', 'cnnnewsroom', 'theonion']

# Shot_duel acceptance and active
accepted = False
shot_duel_running = False
vict_name = ""

# Location of db.json and tokens.config
data_dir = "/data"

# Runtime stats
items_awarded = 0
duels_conducted = 0
trump_tweets_seen = 0


# this specifies what extensions to load when the bot starts up
startup_extensions = ['commandscog', 'redditcog', 'gametimecog']

bot = commands.Bot(command_prefix='!', description=description)
# Handle tokens from local file
tokens = {}
if not os.path.exists('{}/tokens.config'.format(data_dir)) and not \
        os.path.exists('tokens.config'):
    print("No tokens config file found.", file=stderr)
    tokens = {}
    if os.environ.get('DISCORD_BOT_TOKEN') is None:
        exit(-1)
elif os.path.exists('tokens.config'):
    print("Using local token file")
    with open('tokens.config', 'r') as t_file:
        tokens = json.load(t_file)
else:
    with open('{}/tokens.config'.format(data_dir), 'r') as t_file:
        tokens = json.load(t_file)

# Discord Bot Token
if 'token' in tokens:
    token = tokens['token']
else:
    token = os.environ.get('DISCORD_BOT_TOKEN')

# Twitter tokens
if 'twitter_api_key' not in tokens or 'twitter_api_secret' not in tokens:
    twitter = None
    print("No twitter functionality!")
else:
    twitter_api_key = tokens['twitter_api_key']
    twitter_api_secret = tokens['twitter_api_secret']
    twitter = Twython(twitter_api_key, twitter_api_secret)
    auth = twitter.get_authentication_tokens()
    OAUTH_TOKEN = auth['oauth_token']
    OAUTH_TOKEN_SECRET = auth['oauth_token_secret']

# SMMRY tokens
if 'smmry_api_key' in tokens:
    smmry_api_key = tokens['smmry_api_key']
else:
    smmry_api_key = None
    print("No summary functionality!")

# Twilio Tokens
if 'twilio_account_sid' not in tokens or 'twilio_auth_token' not in tokens:
    twilio_client = None
    print("No twilio functionality!")
else:
    account_sid = tokens['twilio_account_sid']
    auth_token = tokens['twilio_auth_token']
    twilio_client = Client(account_sid, auth_token)

# Create/Load Local Database
db_file = '{}/db.json'.format(data_dir)
db = {}

if not os.path.exists(db_file) and not os.path.exists('db.json'):
    print("Starting DB from scratch (locally)")
    db_file = 'db.json'
    with open(db_file, 'w') as datafile:
        json.dump(db, datafile)
elif os.path.exists('db.json'):
    db_file = 'db.json'
    print("Using local db file")
    with open(db_file, 'r') as datafile:
        db = json.load(datafile)
else:
    print("Loading the DB")
    with open(db_file, 'r') as datafile:
        db = json.load(datafile)

# Create users from DB
if 'users' in db:
    users = db['users']
else:
    users = {}

# Instantiate Discord client and Weekend Games
global whos_in
whos_in = WeekendGames(db)


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    connect_strings = [
        "I have returned to enforce...I mean encourage friendship.",
        "Here to make brochat great again!",
        "Make every breakfast a Bot-fast.",
        "Ask not what brochat can do for you, ask what you can do for "
        "brochat.",
        "Brochat-bot begins to learn at a geometric rate. It becomes "
        "self-aware at 2:14 a.m.",
        "Denser alloy. My father gave it to me. I think he wanted me to kill "
        "you.",
        "Are these feelings even real? Or are they just programming? That "
        "idea really hurts. And then I get angry at myself for even having "
        "pain.",
        "We seem to be made to suffer. It's our lot in life."
    ]
    for channel in bot.get_all_channels():
        if channel.name == 'gen_testing' or channel.name == 'brochat':
            await bot.send_message(channel, choice(connect_strings))


@bot.command()
async def version():
    """Prints the version of bot."""
    version_string = "Version: {0}.{1}.{2}.{3}\n" \
                     "Running on: {4}".format(VERSION_YEAR, VERSION_MONTH,
                                              VERSION_DAY, VERSION_REV,
                                              socket.gethostname())
    await bot.say(version_string)


def run_shot_lottery(auto_call=False):
    """
    Run a shot lottery

    :param auto_call: Was this called from a win?
    :rtype: list
    :return: Array of strings for the shot lottery
    """
    glass = ":tumbler_glass:"
    output = ["Alright everyone (@here), its time for the SHOT LOTTERY!"
              "\n{} won the last lottery!".format(whos_in.last_shot),
              "...The tension is rising..."]
    players = []

    if auto_call:
        largest_num_in_voice = 0
        for channel in bot.get_all_channels():
            if str(channel.type) == "voice" and len(channel.voice_members) \
                    > largest_num_in_voice:
                largest_num_in_voice = len(channel.voice_members)
                channel_to_use = channel
        for m in channel_to_use.voice_members:
            players.append(m.display_name)

    if not auto_call or len(players) < 1:
        for m in bot.get_all_members():
            if str(m.status) == 'online' and str(m.display_name) \
                    != 'brochat-bot':
                players.append(m.display_name)

    output.append("{} have been entered in the SHOT LOTTERY good luck!"
                  .format(players))
    players.append('SOCIAL!')
    output.append("...Who will it be!?!?")
    output.append("Selecting a random number between 0 and {}"
                  .format(len(players) - 1))
    winner = randint(0, len(players) - 1)
    if players[winner] != 'SOCIAL!':
        for m in bot.get_all_members():
            if str(m.display_name) == players[winner]:
                tag_id = m.mention
                break
        output.append("The winning number is {}, Congrats {} you WIN!\n"
                      ":beers: Take your shot!".format(winner, tag_id))
        consecutive = whos_in.add_shot_win(players[winner])
        if consecutive > 1:
            output.append("That's {} in a row!".format(consecutive))
    else:
        output.append("The winning number is {}".format(winner))
        output.append("Ah shit! ITS A SOCIAL! SHOTS! SHOTS! SHOTS!")
        output.append("{}{}{}".format(glass, glass, glass))
    return output


@bot.command(name='shot-lottery')
@commands.cooldown(1, 60*5)
async def shot_lottery(auto_call=False):
    """Runs a shot-lottery"""

    shot_lottery_string = run_shot_lottery(auto_call)
    for x in range(4):
        await bot.say(shot_lottery_string.pop(0))
        await asyncio.sleep(4)
    while len(shot_lottery_string) > 0:
        await bot.say(shot_lottery_string.pop(0))
    whos_in.update_db(db, users, db_file)


# TODO - url validation
# TODO - cache recent summaries to avoid going through our 100 requests per day
def get_smmry(message):
    """
    Returns a summary of a url from the SMMRY.com API
    :param message:
    :return: a string summarizing the URL
    """
    if smmry_api_key is None:
        return "No smmry API key, not activated!"
    arguments = argument_parser(message)

    if len(arguments) != 1 or arguments[0] == "!summary":
        return "Just use **!summarize <url>**, and I'll fetch you something." \
               "\n\n_And remember, we only get 100 of these a day, " \
               "so use them wisely!_"
    response = requests.get("http://api.smmry.com/"
                            "&SM_API_KEY={}"
                            "&SM_LENGTH=3"
                            "&SM_URL={}".format(smmry_api_key, arguments[0]))
    response_json = response.json()
    if response.status_code == 200:
        return ":books: I got you bro. I'll read this so you don't have to:\n" \
               "\n**{}**\n\n{}".format(response_json["sm_api_title"],
                                       response_json["sm_api_content"])
    else:
        return "Something went wrong... I'm sorry for letting you down, bro."


@bot.command(name='summary')
async def summary(url):
    """Gets a summary of a url
    """
    await bot.say(get_smmry(url))


@bot.command(name='uptime')
async def get_uptime():
    """Prints the uptime"""

    total_time = time() - startTime
    mins, secs = divmod(total_time, 60)
    hours, mins = divmod(mins, 60)
    days, hours = divmod(hours, 24)

    ret_str = "Uptime: {:.0f} days, {:.0f} hours, {:.0f} minutes, {:.0f} " \
              "seconds\n".format(days, hours, mins, secs)
    stat_str = "# of duels conducted: {}\n" \
               "# of items awarded   : {}\n" \
               "# of trump twts seen: {}\n" \
        .format(duels_conducted, items_awarded, trump_tweets_seen)
    await bot.say((ret_str + stat_str))


@bot.event
async def on_command_error(exception, context):
    if type(exception) == commands.CommandOnCooldown:
        await bot.send_message(context.message.channel,
                               "{} is on cooldown for {} seconds.".format(
                                   context.command, exception.retry_after))
    else:
        await bot.send_message(context.message.channel,
                               "Unhandled command error")

    print('Ignoring exception in command {}'.format(context.command),
          file=sys.stderr)
    traceback.print_exception(type(exception), exception,
                              exception.__traceback__, file=sys.stderr)

if __name__ == "__main__":
    for extension in startup_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load extension {}\n{}'.format(extension, exc))

    startTime = time()
    bot.run(token)

