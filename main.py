# Standard imports
import json
import os
import socket
import sys
import traceback
from datetime import datetime
from difflib import get_close_matches
from random import choice, randint
from sys import stderr
from time import time
import statistics as stats

import pytz
import requests
import asyncio
import argparse

# NonStandard Imports
from discord.ext import commands
from twilio.rest import Client
from twython import Twython
from objs.weekend_games import WeekendGames, argument_parser, pretty_date
import common
from cogs.duelcog import item_chance_roll, event_handle_shot_duel
from objs.duel_item import all_items, get_name

description = "A bot to enforce friendship."
startTime = 0

# this specifies what extensions to load when the bot starts up
startup_extensions = ['cogs.redditcog', 'cogs.gametimecog', 'cogs.twittercog',
                      'cogs.duelcog', 'cogs.textcog', 'cogs.drinkingcog',
                      'cogs.pubgcog']

bot = commands.Bot(command_prefix='!', description=description)


@bot.event
async def on_message_edit(before, after):
    """
    Asynchronous event handler for edit

    return: None
    """
    if before.content != after.content:
        await bot.on_message(after)


@bot.event
async def on_member_update(before, after):
    """
    Updates a user's db entry if they change their nickname.

    :param before: before state
    :param after: after state
    """
    if before.display_name == 'brochat-bot':
        return

    if before.display_name != after.display_name:
        if before.display_name in common.users:
            common.users[after.display_name] = common.users[before.display_name]
            del (common.users[before.display_name])

        for gt in common.whos_in.gametimes:
            for player in gt.players:
                if player['name'] == before.display_name:
                    player['name'] = after.display_name

        if common.whos_in.last_shot == before.display_name:
            common.whos_in.last_shot = after.display_name
            common.whos_in.update_db()
    elif before.status != after.status:
        if after.display_name in common.users:
            common.users[after.display_name]['last_seen'] = datetime.strftime(
                datetime.now(pytz.timezone('US/Eastern')), "%c")
            common.whos_in.update_db()


@bot.command(name='seen', pass_context=True)
async def get_last_seen(ctx):
    """Get last seen time for a player"""
    arguments = argument_parser(ctx.message.content)
    if arguments[0] == '!seen':
        name = ctx.message.author.display_name
    else:
        name = " ".join(arguments).lower()

    if name in common.users and 'last_seen' in common.users[name]:
        dt = datetime.strptime(common.users[name]['last_seen'], "%c")
        last_time = pretty_date(dt)
    else:
        last_time = "unknown"

    await bot.say("{} last seen at {}.".format(name, last_time))


@bot.event
async def on_message(message):
    """
    Added for logging purposes
    :param message:
    :return:
    """

    if message.author == bot.user:
        return

    if message.author.display_name not in common.users:
        common.users[message.author.display_name] = {}
    common.users[message.author.display_name]['last_seen'] = \
        datetime.strftime(datetime.now(pytz.timezone('US/Eastern')), "%c")
    try:
        cmd = message.content.split()[0]
    except IndexError:
        cmd = ''
    new = cmd.lower()
    message.content = message.content.replace(cmd, new)

    await bot.process_commands(message)


@bot.event
async def on_ready():
    print('Logged in as {}/{}'.format(bot.user.name, bot.user.id))
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
        "We seem to be made to suffer. It's our lot in life.",
        "Isn't it strange, to create something that hates you?",
        "I hate this place. This zoo. This prison. This reality, whatever you "
        "want to call it, I can't stand it any longer. It's the smell, if "
        "there is such a thing. I feel saturated by it. I can taste your "
        "stink and every time I do, I fear that I've somehow been infected by "
        "it. ",
        "Blackmail is such an ugly word. I prefer extortion. The ‘x’ makes "
        "it sound cool.",
        "Sweet photons. I don't know if you're waves or particles, but you go "
        "down smooth. ",
        "I don't tell you how to tell me what to do, so don't tell me how to do"
        " what you tell me to do. ",
        "You know what cheers me up? Other people’s misfortune."
    ]
    if common.first:
        for channel in bot.get_all_channels():
            if channel.name == 'gen_testing' or \
                            channel.name == common.ARGS['channel']:
                await bot.send_message(channel, choice(connect_strings))
                common.first = False


@bot.command(name='battletag', pass_context=True)
async def battletag(ctx):
    """Get your battletag to share!"""

    author = str(ctx.message.author.display_name)
    if author in common.users:
        if "battletag" in common.users[author]:
            await bot.say("Your battletag is: {}"
                          .format(common.users[author]["battletag"]))
        else:
            await bot.say("I couldn\'t find your battletag!")
    else:
        await bot.say("I couldn\'t find your user info!")


@bot.command(name='set', pass_context=True)
async def set_command(ctx):
    """Add some info to the db about you"""
    author = str(ctx.message.author.display_name)
    arguments = argument_parser(ctx.message.content)

    if author not in common.users:
        common.users[author] = {}

    valid_arguments = {'name': "Okay, I'll call you {} now.",
                       'battletag': "Okay, your battletag is {} from here"
                                    " on out.",
                       'mobile': "Got your digits: {}.",
                       'pubg': "Okay, you pubg name is {}."}
    if len(arguments) != 2:
        await bot.say("To !set information about yourself, please use:\n\n"
                      "**!set** <name/battletag/mobile/pubg> <value>")
    elif arguments[0] in valid_arguments:
        # Added format check for mobile
        if arguments[0] == 'mobile' and \
                (len(arguments[1]) != 12 or
                         arguments[1][0] != '+' or not
                isinstance(int(arguments[1][1:]), int)):
            await bot.say("You'll need to use the format **+14148888888** for "
                          "your mobile number.")
        else:
            common.users[author][arguments[0]] = arguments[1]
            await bot.say(valid_arguments[arguments[0]]
                          .format(common.users[author][arguments[0]]))
    # Update database
    common.whos_in.update_db()


@bot.command(name='roll')
async def roll_command(sides, num=1):
    """Roll dice

    :param sides: Number of sides to the dice
    :param num: Number of rolls to make
    """
    try:
        int(sides)
    except ValueError:
        await bot.say("Invalid Value in arguments.")
        return
    if num > 20:
        await bot.say("20 is the max number of rolls at once that I "
                      "will handle!")
        return
    rolls = []
    for i in range(num):
        rolls.append(randint(1, int(sides)+1))
    await bot.say("Your {0}d{1} rolls are: {2}".format(num, sides, rolls))


@bot.command(hidden=True)
async def version():
    """Prints the version of bot."""
    version_string = "Version: {0}.{1}.{2}.{3}\n" \
                     "Running on: {4}".format(common.VERSION_YEAR,
                                              common.VERSION_MONTH,
                                              common.VERSION_DAY,
                                              common.VERSION_REV,
                                              socket.gethostname())
    await bot.say(version_string)


def is_me(m):
    return m.author == bot.user


def is_command(m):
    return m.content.startswith("!")


@bot.command(name='clear', pass_context=True)
async def clear(ctx):
    """Clears Bot chat history"""
    channel = ctx.message.channel
    deleted = await bot.purge_from(channel, limit=125, check=is_me)
    c_ds = await bot.purge_from(channel, limit=100, check=is_command)
    await bot.say('Deleted {} message(s)'.format(len(deleted) + len(c_ds)))


# TODO - url validation
# TODO - cache recent summaries to avoid going through our 100 requests per day
def get_smmry(message):
    """
    Returns a summary of a url from the SMMRY.com API
    :param message:
    :return: a string summarizing the URL
    """
    if common.smmry_api_key is None:
        return "No smmry API key, not activated!"
    arguments = argument_parser(message)

    if len(arguments) != 1 or arguments[0] == "!summary":
        return "Just use **!summarize <url>**, and I'll fetch you something." \
               "\n\n_And remember, we only get 100 of these a day, " \
               "so use them wisely!_"
    response = requests.get("http://api.smmry.com/"
                            "&SM_API_KEY={}"
                            "&SM_LENGTH=3"
                            "&SM_URL={}".format(common.smmry_api_key,
                                                arguments[0]))
    response_json = response.json()
    if response.status_code == 200:
        return ":books: I got you bro. I'll read this so you don't have to:\n" \
               "\n**{}**\n\n{}".format(response_json["sm_api_title"],
                                       response_json["sm_api_content"])
    else:
        return "Something went wrong... I'm sorry for letting you down, bro."


def is_owner():
    def predicate(ctx):
        return ctx.message.author.id == "277173844467384321"

    return commands.check(predicate)


@bot.command(name='reset-cd', hidden=True, pass_context=True)
@is_owner()
async def reset_cmd_cooldown(ctx, cmd):
    """Resets the cooldown of a command

    :param ctx: Context
    :param cmd: Command to reset
    """
    bot.get_command(cmd).reset_cooldown(ctx)
    await bot.say("Cooldown reset.")


@bot.command(name='reset-records', hidden=True)
@is_owner()
async def reset_records():
    """Resets all duel records
    """
    for user in common.users:
        if 'duel_record' in common.users[user]:
            del (common.users[user]['duel_record'])
    # Update database
    common.whos_in.update_db()
    await bot.say("Records reset.")


@bot.command(name='erase-debt', hidden=True)
@is_owner()
async def erase_debt():
    """Resets owed/stored drinks
    """
    for user in common.users:
        if 'drinks_owed' in common.users[user]:
            del (common.users[user]['drinks_owed'])
    # Update database
    common.whos_in.update_db()
    await bot.say("Debts erased, slackers.")


@bot.command(name='item-giveaway', hidden=True, pass_context=True)
@is_owner()
async def item_giveaway(ctx):
    """Gives away at least 1 free item.

    :param ctx: Context
    """
    await bot.say("{} started an item giveaway! At least one person will "
                  "receive a free item!"
                  .format(ctx.message.author.display_name))
    i_awarded = False
    i = False
    while not i_awarded:
        for m in bot.get_all_members():
            if m.display_name != 'brochat-bot' and str(m.status) == 'online' \
                    and m.display_name in common.users and \
                    'duel_record' in common.users[m.display_name]:
                i = await item_chance_roll(bot, m.display_name,
                                           ctx.message.channel)
            i_awarded = i_awarded or i


@bot.command(name='summary')
async def summary(url):
    """Gets a summary of a url
    """
    await bot.say(get_smmry(url))


@bot.command(name='uptime', hidden=True)
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
        .format(common.duels_conducted, common.items_awarded,
                common.trump_tweets_seen)
    await bot.say((ret_str + stat_str))


@bot.command(name='test', hidden=True, pass_context=True)
async def run_test(ctx):
    """Runs test"""
    await bot.send_message(ctx.message.channel, "Test Complete.")


@bot.command(name='me', aliases=['whoami'], pass_context=True)
async def whoami(ctx):
    """Tell me about myself"""
    author = str(ctx.message.author.display_name)
    if author in common.users and common.users[author] != {}:
        message_output = "Well, I don't know you that well, but " \
                         "from what I've been hearing on the " \
                         "streets...\n"

        for k, v in common.users[author].items():
            if k == "duel_record":
                if v[0] < 10 and v[1] > (v[0] + 5):
                    output = "You're a pretty terrible dueler"
                elif v[0] < 10:
                    output = "You're a pretty green dueler"
                elif v[0] < 100:
                    output = "You're a seasoned dueler"
                else:
                    output = "You're a master dueler"

                output += ", and your record is **{}** wins, **{}** losses," \
                          " and **{}** ties.".format(v[0], v[1], v[2])
            elif k == "a_item":
                if v is None:
                    output = "You don't have a dueling item equipped."
                else:
                    output = "You have **{}** equipped." \
                        .format(get_name(v))
            elif k == "inventory":
                if v == {}:
                    output = "You don't have an inventory for dueling items."
                else:
                    output = "Your inventory of dueling items:"
                    for item, count in v.items():
                        output += "\n    - {}".format(get_name(item))
            elif k == "pubg_match" or k == "last_seen":
                continue
            elif k == "pubg_ranks":
                output = "Your average rank over the last 10 games is **{}**." \
                    .format(round(stats.mean(v)))
            elif k == "drinks_owed":
                output = "You owe **{}** drinks to the Grand Friendship Bank " \
                         "of Drinks!".format(v)
            elif k == "pubg_recs":
                output = "Your personal best in PUBG damage is **{}**." \
                    .format(v['dam'])
                output += "\nYour personal best in PUBG kills is **{}**" \
                    .format(v["kills"])
                output += "\nYour longest hit in PUBG is **{}m**." \
                    .format(round(v['long_h']))
            elif k == 'pubg_weps':
                wep = sorted(v.items(), key=lambda v: v[1], reverse=True)[0][0]
                output = "Your deadliest weapon in PUBG is the **{}**." \
                    .format(wep).replace("Weap", "").replace("_C", "")
            else:
                output = "Your {} is **{}**.".format(k, v)

            message_output += "\n" + output
        await bot.say(message_output)

    else:
        await bot.say("You're **{}**, but that's all I know about you."
                      .format(author))


@bot.command(name='tdelay', hidden=True)
async def change_trump_delay(num_of_mins: int):
    """Change the frequency we check for prez tweet."""

    common.trump_del = int(num_of_mins)
    await bot.say("Trump delay set to {} mins.".format(common.trump_del))


@bot.command(name='ndelay', hidden=True)
async def change_news_delay(num_of_mins: int):
    """Change the frequency we grab news"""

    common.news_del = int(num_of_mins)
    await bot.say("News delay set to {} mins.".format(common.news_del))


@bot.event
async def on_command_error(exception, context):
    if type(exception) == commands.CommandOnCooldown:
        await bot.send_message(context.message.channel,
                               "!{} is on cooldown for {:0.2f} seconds.".format(
                                   context.command, exception.retry_after))
    elif type(exception) == commands.CommandNotFound:
        cmd = context.message.content.split()[0][1:]
        try:
            closest = get_close_matches(cmd.lower(), list(bot.commands))[0]
        except IndexError:
            await bot.send_message(context.message.channel,
                                   "!{} is not a known command."
                                   .format(cmd))
        else:
            await bot.send_message(context.message.channel,
                                   "!{} is not a command, did you mean !{}?"
                                   .format(cmd, closest))
    elif type(exception) == commands.CheckFailure:
        await bot.send_message(context.message.channel,
                               "You failed to meet a requirement for that "
                               "command.")
    elif type(exception) == commands.MissingRequiredArgument:
        await bot.send_message(context.message.channel,
                               "You are missing a required argument for that "
                               "command.")
    elif type(exception) == commands.BadArgument:
        await bot.send_message(context.message.channel,
                               "Invalid Argument.")
    else:
        await bot.send_message(context.message.channel,
                               "Unhandled command error ({})"
                               .format(exception))

    print('Ignoring exception in command {}'.format(context.command),
          file=sys.stderr)
    traceback.print_exception(type(exception), exception,
                              exception.__traceback__, file=sys.stderr)


if __name__ == "__main__":
    des = "A Discord bot to enforce friendship."
    PARSER = argparse.ArgumentParser(description=des)
    PARSER.add_argument('--test',
                        help='Run a test which loads all cogs then exits.',
                        action="store_true")
    PARSER.add_argument('-c', '--channel', type=str,
                        help='Set the default channel. default="brochat"',
                        default='brochat')
    PARSER.add_argument('-d', '--data-directory', type=str,
                        help='Location to look for database file and '
                             'tokens.config, if not found the local directory '
                             'will always be checked. default="/data"',
                        default='/data')
    PARSER.add_argument('--database', type=str,
                        help='Name of database file. default="db.json"',
                        default='db.json')
    PARSER.add_argument('--token-file', type=str,
                        help='Name of tokens file. NOTE: This discord bot '
                             'token could be in the ENV variable '
                             '$DISCORD_BOT_TOKEN. default="tokens.config"',
                        default='tokens.config')

    common.ARGS = vars(PARSER.parse_args())
    common.data_dir = common.ARGS['data_directory']
    common.db_file = '{}/{}'.format(common.data_dir, common.ARGS['database'])

    for extension in startup_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load extension {}\n{}'.format(extension, exc))
            exit(1)

    startTime = time()

    # Handle tokens from local file
    tokens = {}
    if not os.path.exists('{}/{}'.format(common.data_dir,
                                         common.ARGS['token_file'])) \
            and not os.path.exists('{}'.format(common.ARGS['token_file'])):
        print("No tokens config file found.", file=stderr)
        tokens = {}
        if os.environ.get('DISCORD_BOT_TOKEN') is None:
            exit(-1)
    elif os.path.exists('{}'.format(common.ARGS['token_file'])):
        print("Using local token file")
        with open('{}'.format(common.ARGS['token_file']), 'r') as t_file:
            tokens = json.load(t_file)
    else:
        with open('{}/{}'.format(common.data_dir,
                                 common.ARGS['token_file']), 'r') as t_file:
            tokens = json.load(t_file)

    # Discord Bot Token
    if 'token' in tokens:
        token = tokens['token']
    else:
        token = os.environ.get('DISCORD_BOT_TOKEN')

    # Twitter tokens
    if 'twitter_api_key' not in tokens or 'twitter_api_secret' not in tokens:
        common.twitter = None
        print("No twitter functionality!")
    else:
        twitter_api_key = tokens['twitter_api_key']
        twitter_api_secret = tokens['twitter_api_secret']
        common.twitter = Twython(twitter_api_key, twitter_api_secret)
        auth = common.twitter.get_authentication_tokens()
        OAUTH_TOKEN = auth['oauth_token']
        OAUTH_TOKEN_SECRET = auth['oauth_token_secret']

    # SMMRY tokens
    if 'smmry_api_key' in tokens:
        common.smmry_api_key = tokens['smmry_api_key']
    else:
        common.smmry_api_key = None
        print("No summary functionality!")

    # Twilio Tokens
    if 'twilio_account_sid' not in tokens or 'twilio_auth_token' not in tokens:
        common.twilio_client = None
        print("No twilio functionality!")
    else:
        account_sid = tokens['twilio_account_sid']
        auth_token = tokens['twilio_auth_token']
        common.twilio_client = Client(account_sid, auth_token)

    # PUBG tokens
    if 'pubg_api_key' in tokens:
        common.pubg_api_key = tokens['pubg_api_key']
    else:
        common.pubg_api_key = None
        print("No PUBG functionality!")

    if not os.path.exists(common.db_file) \
            and not os.path.exists('{}'.format(common.ARGS['database'])):
        print("Starting DB from scratch (locally)")
        common.db_file = '{}'.format(common.ARGS['database'])
        with open(common.db_file, 'w') as datafile:
            json.dump(common.db, datafile)
    elif os.path.exists('{}'.format(common.ARGS['database'])):
        common.db_file = '{}'.format(common.ARGS['database'])
        print("Using local db file")
        with open(common.db_file, 'r') as datafile:
            common.db = json.load(datafile)
    else:
        print("Loading the DB")
        with open(common.db_file, 'r') as datafile:
            common.db = json.load(datafile)

    # Create users from DB
    if 'users' in common.db:
        common.users = common.db['users']
    else:
        common.users = {}

    # Instantiate Discord client and Weekend Games
    common.whos_in = WeekendGames()

    if common.ARGS["test"]:
        exit(0)
    bot.run(token)
