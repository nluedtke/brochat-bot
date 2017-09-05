# Standard imports
import json
import os
import socket
import sys
import traceback
from datetime import datetime
from difflib import get_close_matches
from random import choice
from sys import stderr
from time import time
import pytz
import requests
import asyncio

# NonStandard Imports
from discord.ext import commands
from twilio.rest import Client
from twython import Twython
from objs.weekend_games import WeekendGames, argument_parser, pretty_date
import common
from cogs.duelcog import item_chance_roll, event_handle_shot_duel
from objs.duel_item import DuelItem, all_items

description = "A bot to enforce friendship."
startTime = 0

# this specifies what extensions to load when the bot starts up
startup_extensions = ['cogs.redditcog', 'cogs.gametimecog', 'cogs.twittercog',
                      'cogs.duelcog', 'cogs.textcog', 'cogs.drinkingcog']

bot = commands.Bot(command_prefix='!', description=description)
# Handle tokens from local file
tokens = {}
if not os.path.exists('{}/tokens.config'.format(common.data_dir)) and not \
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
    with open('{}/tokens.config'.format(common.data_dir), 'r') as t_file:
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
    smmry_api_key = tokens['smmry_api_key']
else:
    smmry_api_key = None
    print("No summary functionality!")

# Twilio Tokens
if 'twilio_account_sid' not in tokens or 'twilio_auth_token' not in tokens:
    common.twilio_client = None
    print("No twilio functionality!")
else:
    account_sid = tokens['twilio_account_sid']
    auth_token = tokens['twilio_auth_token']
    common.twilio_client = Client(account_sid, auth_token)


if not os.path.exists(common.db_file) and not os.path.exists('db.json'):
    print("Starting DB from scratch (locally)")
    common.db_file = 'db.json'
    with open(common.db_file, 'w') as datafile:
        json.dump(common.db, datafile)
elif os.path.exists('db.json'):
    common.db_file = 'db.json'
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
            del(common.users[before.display_name])

        for gt in common.whos_in.gametimes:
            for player in gt.players:
                if player['name'] == before.display_name:
                    player['name'] = after.display_name

        if common.whos_in.last_shot == before.display_name:
            common.whos_in.last_shot = after.display_name
            common.whos_in.update_db()
    elif before.status != after.status:
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
    cmd = message.content.split()[0]
    new = cmd.lower()
    message.content = message.content.replace(cmd, new)
    await bot.process_commands(message)


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
        "We seem to be made to suffer. It's our lot in life.",
        "Isn't it strange, to create something that hates you?",
        "I hate this place. This zoo. This prison. This reality, whatever you "
        "want to call it, I can't stand it any longer. It's the smell, if "
        "there is such a thing. I feel saturated by it. I can taste your "
        "stink and every time I do, I fear that I've somehow been infected by "
        "it. "
    ]
    for channel in bot.get_all_channels():
        if channel.name == 'gen_testing' or channel.name == 'brochat':
            await bot.send_message(channel, choice(connect_strings))


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
                       'mobile': "Got your digits: {}."}
    if len(arguments) != 2:
        await bot.say("To !set information about yourself, please use:\n\n"
                      "**!set** <name/battletag/mobile> <value>")
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
            if m.display_name != 'brochat-bot' and str(m.status) == 'online':
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

    if ctx.message.channel.name == 'gen_testing':
        arguments = argument_parser(ctx.message.content)
        if arguments[0] == 'all':
            await bot.send_message(ctx.message.channel, "Starting Automated "
                                                        "Tests.")
            ctx.message.content = "!version"
            await bot.process_commands(ctx.message)
            await asyncio.sleep(5)
            await bot.send_message(ctx.message.channel, "Printing help.")
            ctx.message.content = "!help"
            await bot.process_commands(ctx.message)
            await asyncio.sleep(5)
            await bot.send_message(ctx.message.channel, "Populating inventory.")
            await item_chance_roll(bot, ctx.message.author.display_name,
                                   ctx.message.channel, 10)
            await item_chance_roll(bot, ctx.message.author.display_name,
                                   ctx.message.channel, 10)
            await item_chance_roll(bot, ctx.message.author.display_name,
                                   ctx.message.channel, 10)
            await asyncio.sleep(5)
            await bot.send_message(ctx.message.channel, "Calling !use")
            ctx.message.content = "!use"
            await bot.process_commands(ctx.message)
            await asyncio.sleep(5)
            await bot.send_message(ctx.message.channel, "Equiping first item")
            inv = common.users[ctx.message.author.display_name]['inventory']
            ctx.message.content = "!use {}".format(str(list(inv)[0]))
            await bot.process_commands(ctx.message)
            await asyncio.sleep(5)
            await bot.send_message(ctx.message.channel, "Simulating Trump Call")
            ctx.message.content = "!trump"
            await bot.process_commands(ctx.message)
            await asyncio.sleep(10)
            await bot.send_message(ctx.message.channel,
                                   "Simulating Bertstrip Call")
            ctx.message.content = "!bertstrip"
            await bot.process_commands(ctx.message)
            await asyncio.sleep(10)
        await bot.send_message(ctx.message.channel, "Setting test duel")
        test_inv1 = {}
        for i in range(3):
            test_inv1[choice(list(all_items.keys()))] = 0
        test_inv2 = {}
        for i in range(3):
            test_inv2[choice(list(all_items.keys()))] = 0
        common.users['palu']['inventory'] = test_inv1
        common.users['csh']['inventory'] = test_inv2
        common.users['palu']['equip'] = {}
        common.users['csh']['equip'] = {}
        common.whos_in.update_db()

        await asyncio.sleep(5)
        for p in bot.get_all_members():
            if p.display_name == 'palu':
                player2 = p
            elif p.display_name == 'csh':
                player1 = p
        for i in range(3):
            inv = common.users[player1.display_name]['inventory']
            if len(inv) >= i:
                ctx.message.content = "!use {}".format(str(list(inv)[i]))
                ctx.message.author = player1
                await bot.process_commands(ctx.message)
            inv = common.users[player2.display_name]['inventory']
            if len(inv) >= i:
                ctx.message.content = "!use {}".format(str(list(inv)[i]))
                ctx.message.author = player2
                await bot.process_commands(ctx.message)
        ctx.message.author = player1
        common.accepted = True
        await event_handle_shot_duel(ctx, player2)
        await asyncio.sleep(20)
        while common.shot_duel_running:
            await asyncio.sleep(10)
        common.users['palu']['inventory'] = {}
        common.users['csh']['inventory'] = {}
        common.users['palu']['equip'] = {}
        common.users['csh']['equip'] = {}
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
                if v[0] < 10:
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
                    output = "You have **{}** equipped."\
                        .format(DuelItem(0, v).name)
            elif k == "inventory":
                if v == {}:
                    output = "You don't have an inventory for dueling items."
                else:
                    output = "Your inventory of dueling items:"
                    for item, count in v.items():
                        output += "\n    - {}".format(DuelItem(0, item).name)
            else:
                output = "Your {} is **{}**.".format(k, v)

            message_output += "\n" + output
        await bot.say(message_output)

    else:
        await bot.say("You're {}, but that's all I know about you."
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
    else:
        await bot.send_message(context.message.channel, "Unhandled command "
                                                        "error")

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
            exit(1)

    startTime = time()
    if os.environ.get("TEST_TRAVIS_NL"):
        exit(0)
    bot.run(token)
