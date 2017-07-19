# Standard imports
from time import time
import json
import os
from sys import stderr
from random import randint, shuffle
import socket
import datetime
from difflib import get_close_matches
import pytz

# NonStandard Imports
import discord
import asyncio
from twython import Twython, TwythonError
from twilio.rest import Client
import requests
from gametime import Gametime

VERSION_MAJOR = 2
VERSION_MINOR = 3
VERSION_PATCH = 0

# Global toggle for news feed
NEWS_FEED_ON = False
NEWS_FEED_CREATED = False

# Delays for Newsfeed and Check_trump, These are in minutes
# remember that news_del is fuzzed + (0-10)
trump_del = 30
news_del = 55

# Variable hold trumps last tweet id
last_id = 0

# News handles to pull from
news_handles = ['mashable', 'cnnbrk', 'whitehouse', 'cnn', 'nytimes',
                'foxnews', 'reuters', 'npr', 'usatoday', 'cbsnews',
                'abc', 'washingtonpost', 'msnbc', 'ap', 'aphealthscience',
                'lifehacker', 'cnnnewsroom', 'theonion']


def shot_lottery(client_obj, wg_games):
    """
    Run a shot lottery

    :param client_obj: client object to use
    :param wg_games: WeekendGames object to use
    :rtype: list
    :return: Array of strings for the shot lottery
    """
    glass = ":tumbler_glass:"
    output = ["Alright everyone (@here), its time for the SHOT LOTTERY!"
              "\n{} won the last lottery!".format(whos_in.last_shot),
              "...The tension is rising..."]
    players = []
    for m in client_obj.get_all_members():
        if str(m.status) == 'online' and str(m.display_name) != 'brochat-bot':
            players.append(m.display_name)
    output.append("{} have been entered in the SHOT LOTTERY good luck!"
                  .format(players))
    players.append('SOCIAL!')
    output.append("...Who will it be!?!?")
    output.append("Selecting a random number between 0 and {}"
                  .format(len(players) - 1))
    winner = randint(0, len(players) - 1)
    if players[winner] != 'SOCIAL!':
        output.append("The winning number is {}, Congrats {} you WIN!\n"
                      ":beers: Take your shot!".format(winner, players[winner]))
        consecutive = wg_games.add_shot_win(players[winner])
        if consecutive > 1:
            output.append("That's {} in a row!".format(consecutive))
    else:
        output.append("The winning number is {}".format(winner))
        output.append("Ah shit! ITS A SOCIAL! SHOTS! SHOTS! SHOTS!")
        output.append("{}{}{}".format(glass, glass, glass))
    wg_games.log_lottery_time()
    return output


def pretty_date(dt):
    """
    Takes a datetime and makes it a pretty string.
    :param dt:
    :return: string
    """
    return dt.strftime("%a, %b %d at %H:%M EST")
    # this version has the time, for the future:
    # return datetime.strftime("%a, %b %d at %I:%M %p")


class WeekendGames(object):
    """
    Defines the WeekendGames class
    """

    def __init__(self):
        """
        WeekendGames constructor
        """

        self.people = []
        if 'people' in db:
            self.people = db['people']
        self.day = 'Sunday'
        self.last_shot = "Unknown"
        if 'last_shot' in db:
            self.last_shot = db['last_shot']
        self.consecutive_shot_wins = 1
        if 'consecutive_shot_wins' in db:
            self.consecutive_shot_wins = db['consecutive_shot_wins']
        self.last_lottery = 0
        self.last_reddit_request = 0
        if 'last_lottery_time' in db:
            self.last_lottery = db['last_lottery_time']

        # store our games
        self.gametimes = []
        if 'gametimes' in db:
            for gt in db['gametimes']:
                self.gametimes.append(Gametime(json_create=gt))

        self.c_win = 0
        self.c_loss = 0
        self.c_draw = 0
        if 'c_win' in db:
            self.c_win = db['c_win']
        if 'c_loss' in db:
            self.c_loss = db['c_loss']
        if 'c_draw' in db:
            self.c_draw = db['c_draw']

        # non persistent variables
        self.wins = 0
        self.draws = 0
        self.losses = 0
        self.last = None
        self.consecutive = 0

    def get_gametimes(self):
        """
        Get upcoming gametimes.
        :return: string response to print to chat.
        """
        upcoming_days = "**Exciting f-ing news, boys:**\n\n"
        if len(self.gametimes) == 0:
            return "No games coming up, friendship outlook bleak."
        game_id = 0
        for gt in self.gametimes:
            game_id += 1
            upcoming_days += "{}: There is a gaming session coming up on " \
                             "**{}**\n".format(game_id,
                                               pretty_date(gt.get_date()))
            if len(gt.players) == 0:
                upcoming_days += "    Nobody's in for this day.\n"
            else:
                for player in gt.players:
                    status = gt.get_player_status(player['name'])
                    upcoming_days += "    - **{}** is *{}*.\n".format(
                        player['name'], status)
        return upcoming_days

    def gametime_actions(self, message):
        """
        Routes a gametime action, specified in the second
        argument, ex !gametime <add> Sunday
        :param message:
        :return: string response to print to chat.
        """
        arguments = argument_parser(message)

        gametime_help_string = \
            "That's not a valid command for **!gametime**\n\n" \
            "Please use:\n" \
            "!gametime <add> <day of the week>" \
            "<_optional_: military time, HH:MM> to **add a gametime**\n" \
            "!gametime <remove> <index> to **delete a gametime**\n" \
            "!gametime <list> to **list current gametimes**\n" \
            "!gametime <set> <index> <time> to " \
            "**set the time of a gametime**"
        valid_commands = {
            "add": self.create_gametime,
            "remove": self.remove_gametime,
            "list": self.get_gametimes,
            "set": self.set_gametime
        }
        if arguments[0] in valid_commands:
            if len(arguments) == 3:
                try:
                    return valid_commands[arguments[0]](arguments[1],
                                                        arguments[2])
                except KeyError:
                    return gametime_help_string
            elif len(arguments) == 2:
                try:
                    return valid_commands[arguments[0]](arguments[1])
                except KeyError:
                    return gametime_help_string
            elif len(arguments) == 1:
                try:
                    return valid_commands[arguments[0]]()
                except KeyError:
                    return gametime_help_string
        return gametime_help_string

    def create_gametime(self, day, start_time=None):
        """
        Create a gametime, given a full name of a day of the week.
        :param start_time: Time of the game
        :param day: string of a proper case day of the week.
        :return: string response to send to chat.
        """
        day = day.capitalize()
        if day in Gametime.DAYS_IN_WEEK:
            new_gametime = Gametime(day=Gametime.DAYS_IN_WEEK.index(day),
                                    time=start_time)
            for game_session in self.gametimes:
                if new_gametime == game_session:
                    return "There is already a session that time."
            self.gametimes.append(new_gametime)
            self.gametimes.sort(key=lambda x: x.date)
            self.update_db()
            return "Gametime created for {}.".format(
                pretty_date(new_gametime.get_date()))
        else:
            return "Please use the full name of a day of the week."

    def remove_gametime(self, index):
        try:
            index = int(index)
        except ValueError:
            return "Your index should be a number, silly."
        if 0 < index <= len(self.gametimes):
            self.gametimes.pop(index - 1)
            self.update_db()
            return "Gametime removed."
        else:
            return "There's no gametime with that number."

    def set_gametime(self, index, new_time):
        try:
            index = int(index)
        except ValueError:
            return "Your index should be a number, silly."
        if 0 < index <= len(self.gametimes):
            output_string = ""
            output_string += self.gametimes[index - 1].set_time(new_time)
            self.update_db()
            return "{}\nGametime {} set to {}." \
                .format(output_string, index,
                        pretty_date(self.gametimes[index - 1].get_date()))
        else:
            return "There's no gametime with that number."

    def whos_in(self):
        """
        Depreciated function, now just calls get_gametimes()

        :rtype str
        :return: str: Formatted string for the list of people currently signed
        up for weekend games
        """

        return self.get_gametimes()

    def add(self, person, game_id, status):
        """
        Adds a person to the specified gametime

        :param status: Status to mark for player
        :param person: person to add
        :param game_id: list id of the gametime in gametimes
        :return: string to print to chat
        """
        try:
            game_id = int(game_id) - 1
        except ValueError:
            return "That's not a valid gametime."

        if game_id not in range(len(self.gametimes)):
            return "There's no gametime then."

        if type(person) is str:
            person_to_add = person
        else:
            person_to_add = str(person.display_name)

        game = self.gametimes[game_id]

        if game.find_player_by_name(person_to_add) and \
           status != game.get_player_status(person_to_add):
            game.unregister_player(person_to_add)

        if game.find_player_by_name(person_to_add):
            self.gametimes[game_id] = game
            return "You're already {} for that day.".format(
                game.get_player_status(person_to_add))
        else:
            game.register_player(person_to_add,
                                 status=status)
            self.gametimes[game_id] = game
            self.update_db()
            return '{} is {} for {}.'.format(person_to_add,
                                             game.get_player_status(
                                                 person_to_add),
                                             pretty_date(game.get_date()))

    def remove(self, person, game_id):
        """
        Removes a person from the weekend games list

        :param person: Person to remove
        :param game_id: The id of the game session
        :rtype str
        :return: str: Formatted string indicating whether a person was removed.
        """
        try:
            game_id = int(game_id) - 1
        except ValueError:
            return "That's not a valid gametime."

        if game_id not in range(len(self.gametimes)):
            return "There's no gametime then."

        if type(person) is str:
            person_to_remove = person
        else:
            person_to_remove = str(person.display_name)

        if self.gametimes[game_id].find_player_by_name(person_to_remove):
            self.gametimes[game_id].unregister_player(person_to_remove)
            self.update_db()
            return '{} is out for {}.' \
                .format(person_to_remove, pretty_date(self.gametimes[
                                                          game_id].get_date()))
        else:
            return '{} was never in for {}.' \
                .format(person_to_remove, pretty_date(self.gametimes[
                                                          game_id].get_date()))

    def update_db(self):
        """
        Updates the database to disk

        :return: None
        """

        db['people'] = self.people
        db['last_shot'] = self.last_shot
        db['consecutive_shot_wins'] = self.consecutive_shot_wins
        db['last_lottery_time'] = self.last_lottery
        db['gametimes'] = []
        for gt in self.gametimes:
            db['gametimes'].append(gt.to_json())
        db['users'] = users
        db['c_win'] = self.c_win
        db['c_loss'] = self.c_loss
        db['c_draw'] = self.c_draw
        with open(db_file, 'w') as dbfile:
            json.dump(db, dbfile, sort_keys=True, indent=4,
                      ensure_ascii=False)

    def add_shot_win(self, name):
        """
        Adds a shot lottery win to the weekend games

        :param name: str Name of winner
        :rtype int
        :return: int: Number in a row
        """

        if self.last_shot == name:
            self.consecutive_shot_wins += 1
        else:
            self.last_shot = name
            self.consecutive_shot_wins = 1
        self.update_db()
        return self.consecutive_shot_wins

    def log_lottery_time(self):
        """
        Logs the last time a lottery was run, in order to insure its not ran too
        often.

        :return: None
        """

        self.last_lottery = time()
        self.update_db()

    def is_lottery_time(self):
        """
        Determines if its time for a lottery

        :rtype bool
        :return: True if more than 10 mins has passed
        """

        return time() - self.last_lottery > 600

    def log_reddit_time(self):
        """
        Logs the last time a reddit request was run to avoid ratelimit

        :return: None
        """

        self.last_reddit_request = time()

    def is_reddit_time(self):
        """
        Determines if its time for a reddit request

        :rtype bool
        :return: True if more than 10 seconds has passed
        """

        return time() - self.last_reddit_request > 10

    def add_win(self):
        """
        Adds a win

        :return: None
        """

        self.wins += 1
        self.c_win += 1
        if self.last == "win":
            self.consecutive += 1
        else:
            self.last = "win"
            self.consecutive = 1

    def add_loss(self):
        """
        Adds a loss

        :return: None
        """

        self.losses += 1
        self.c_loss += 1
        if self.last == "loss":
            self.consecutive += 1
        else:
            self.last = "loss"
            self.consecutive = 1

    def add_draw(self):
        """
        Adds a draw

        :return: None
        """

        self.draws += 1
        self.c_draw += 1
        if self.last == "draw":
            self.consecutive += 1
        else:
            self.last = "draw"
            self.consecutive = 1

    def clear_record(self):
        """
        Adds a draw

        :return: None
        """

        self.draws = 0
        self.wins = 0
        self.losses = 0
        self.last = None
        self.consecutive = 0

    def get_record(self):
        """
        Gets the record of a session

        :return: str: With record formatting
        """

        return "{0} - {1} - {2}".format(self.wins, self.losses, self.draws)

    def get_c_record(self):
        """
        Gets the cumaltive record of a session

        :return: str: With record formatting
        """

        return "{0} - {1} - {2}".format(self.c_win, self.c_loss, self.c_draw)


# Handle tokens from local file
tokens = {}
if not os.path.exists('tokens.config'):
    print("No tokens config file found.", file=stderr)
    exit(-1)
else:
    with open('tokens.config', 'r') as t_file:
        tokens = json.load(t_file)

# Discord Bot Token
token = tokens['token']

# Twitter tokens
twitter_api_key = tokens['twitter_api_key']
twitter_api_secret = tokens['twitter_api_secret']
twitter = Twython(twitter_api_key, twitter_api_secret)
auth = twitter.get_authentication_tokens()
OAUTH_TOKEN = auth['oauth_token']
OAUTH_TOKEN_SECRET = auth['oauth_token_secret']

# SMMRY tokens
smmry_api_key = tokens['smmry_api_key']

# Twilio Tokens
account_sid = tokens['twilio_account_sid']
auth_token = tokens['twilio_auth_token']
twilio_client = Client(account_sid, auth_token)

# Create/Load Local Database
db_file = 'db.json'
db = {}

if not os.path.exists(db_file):
    print("Starting DB from scratch")
    with open(db_file, 'w') as datafile:
        json.dump(db, datafile)
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
_client = discord.Client()
whos_in = WeekendGames()


def argument_parser(input_args):
    """
    Returns a list of tokens for a given argument
    :param input_args: input string
    :return: argument list
    """

    arguments = input_args.split(' ')
    if len(arguments) > 1:
        return arguments[1:]
    else:
        return arguments


@_client.event
async def on_ready():
    """
    Asynchronous event handler for logging in

    :return: None
    """
    print('Logged in as {}'.format(_client.user.name))
    print(_client.user.id)
    print('------')
    connect_strings = [
        "I have returned to enforce...I mean encourage friendship.",
        "Here to make brochat great again!",
        "Make every breakfast a Bot-fast.",
        "Pancakes are ***REMOVED*** ***REMOVED***."
    ]
    for channel in _client.get_all_channels():
        if channel.name == 'general' or channel.name == 'brochat':
            await _client.send_message(channel, connect_strings[
                randint(0, len(connect_strings) - 1)])


async def print_help(client, message):
    """
    Returns the help string

    :param client: The Client
    :param message: The message
    :return: None
    """
    help_string = "Here are some things I can help you with:\n\n" \
                  "**!ham**: I'll tell you what we're gonna get\n" \
                  "**!gametime**: I'll add, list, and manage gametimes!\n" \
                  "**!in <sessionid>**: Sign up for a game session\n" \
                  "**!out <sessionid>**: Remove yourself from a session\n" \
                  "**!possible <sessionid>**: Sign up, tentatively for a " \
                  "session\n" \
                  "**!late <sessionid>**: Sign up, but will be late for a " \
                  "session\n" \
                  "**!whosin**: See who's in for gaming sessions\n" \
                  "**!trump**: I'll show you Trump's latest Yuge " \
                  "success!\n" \
                  "**!summary <url>**: I'll summarize a link for you\n" \
                  "**!dankmeme**: I'll fetch you a succulent dank may-may\n" \
                  "**!bertstrip**: I'll ruin your childhood\n" \
                  "**!news**: I'll grab a news story for you.\n" \
                  "**!text <name>**: Get that fool in the loop\n" \
                  "**!shot-lottery**: Run a shot lottery.\n" \
                  "**!win/!loss/!draw**: Update session record " \
                  "appropriately\n" \
                  "**!clear-record**: Clear the session record\n" \
                  "**!get-record**: Print the session record\n" \
                  "**!set**: Tell Brochat-Bot some info about you\n" \
                  "**!battletag**: I'll tell you your battletag\n" \
                  "**!whoami**: I'll tell you what I know about you\n" \
                  "**!toggle-news**: Turn news feed on/off\n" \
                  "**!version**: Print the version of brochat-bot\n" \
                  "**!uptime**: Print how long the bot has been running for\n"

    await client.send_message(message.channel, help_string)


async def print_version(client, message):
    """
    Returns the version string

    :param client: The Client
    :param message: The message
    :return: None
    """
    version_string = "Version: {0}.{1}.{2}\n" \
                     "Running on: {3}".format(VERSION_MAJOR,
                                              VERSION_MINOR,
                                              VERSION_PATCH,
                                              socket.gethostname())
    await client.send_message(message.channel, version_string)


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
        'User-Agent': 'Brochat-Bot {}.{}'.format(VERSION_MAJOR, VERSION_MINOR)
    }
    if not whos_in.is_reddit_time():
        return ":tiger: **Easy, tiger.** Wait 10 seconds between reddit " \
               "requests so they don't get mad."

    response = requests.get(url, headers=headers)
    whos_in.log_reddit_time()
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


# TODO - url validation
# TODO - cache recent summaries to avoid going through our 100 requests per day
def get_smmry(message):
    """
    Returns a summary of a url from the SMMRY.com API
    :param message:
    :return: a string summarizing the URL
    """
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


async def get_uptime(client, message):
    """
    Prints the uptime

    :param client: The Client
    :param message: The message
    :return: None
    """
    total_time = time() - startTime
    mins, secs = divmod(total_time, 60)
    hours, mins = divmod(mins, 60)
    days, hours = divmod(hours, 24)

    ret_str = "{:.0f} days, {:.0f} hours, {:.0f} minutes, {:.0f} " \
              "seconds".format(days, hours, mins, secs)
    await client.send_message(message.channel, 'Uptime: {}'
                              .format(ret_str))


async def run_test(client, message):
    """
    Handles the test command

    :param client: The Client
    :param message: The message
    :return: None
    """
    counter = 0
    tmp = await client.send_message(message.channel, 'Calculating messages...')
    async for log in client.logs_from(message.channel, limit=100):
        if log.author == message.author:
            counter += 1

    await client.edit_message(tmp, 'You have {} messages.'.format(counter))


async def sleep(client, message):
    """
    Sleeps the bot

    :param client: The Client
    :param message: The message
    :return: None
    """
    await asyncio.sleep(10)
    await client.send_message(message.channel, 'Done sleeping')


async def go_ham(client, message):
    """
    goes ham

    :param client: The Client
    :param message: The message
    :return: None
    """
    await client.send_message(message.channel,
                              '@here Let\'s get retarded, {}'.format(
                                  message.author.display_name))


async def dankmeme(client, message):
    """
    Gets a dank meme

    :param client: The Client
    :param message: The message
    :return: None
    """
    await client.send_message(message.channel, get_reddit("dankmemes"))


async def bertstrip(client, message):
    """
    Gets a bertstrip

    :param client: The Client
    :param message: The message
    :return: None
    """
    await client.send_message(message.channel, get_reddit("bertstrips"))


async def summary(client, message):
    """
    Gets a summary of a url

    :param client: The Client
    :param message: The message
    :return: None
    """
    await client.send_message(message.channel, get_smmry(message.content))


async def gametime(client, message):
    """
    Handles gametime actions

    :param client: The Client
    :param message: The message
    :return: None
    """
    await client.send_message(message.channel, whos_in.gametime_actions(
        message.content))


async def in_command(client, message):
    """
    Handles !in actions

    :param client: The Client
    :param message: The message
    :return: None
    """
    arguments = argument_parser(message.content)
    if len(arguments) != 1 or arguments[0].lower() == "!in":
        await client.send_message(message.channel,
                                  "When are you in for, though?\n\n{}"
                                  .format(whos_in.get_gametimes()))
    elif len(arguments) == 1:
        await client.send_message(message.channel,
                                  whos_in.add(message.author, arguments[0],
                                              status="in"))
    else:
        await client.send_message(message.channel,
                                  "You'll need to be more specific :smile:")


async def possible_command(client, message):
    """
    Handles !possible actions

    :param client: The Client
    :param message: The message
    :return: None
    """
    arguments = argument_parser(message.content)
    if len(arguments) != 1 or arguments[0].lower() == "!possible":
        await client.send_message(message.channel,
                                  "When are you possibly in for, though?\n\n{}"
                                  .format(whos_in.get_gametimes()))
    elif len(arguments) == 1:
        await client.send_message(message.channel,
                                  whos_in.add(message.author, arguments[0],
                                              status="possible"))
    else:
        await client.send_message(message.channel,
                                  "You'll need to be more specific :smile:")


async def late_command(client, message):
    """
    Handles !late actions

    :param client: The Client
    :param message: The message
    :return: None
    """
    arguments = argument_parser(message.content)
    if len(arguments) != 1 or arguments[0].lower() == "!late":
        await client.send_message(message.channel,
                                  "For what session are you going to be late "
                                  "for, though?\n\n{}"
                                  .format(whos_in.get_gametimes()))
    elif len(arguments) == 1:
        await client.send_message(message.channel,
                                  whos_in.add(message.author, arguments[0],
                                              status="going to be late"))
    else:
        await client.send_message(message.channel,
                                  "You'll need to be more specific :smile:")


async def out_command(client, message):
    """
    Handles !out actions

    :param client: The Client
    :param message: The message
    :return: None
    """
    arguments = argument_parser(message.content)
    if len(arguments) != 1 or arguments[0].lower() == "!out":
        await client.send_message(message.channel,
                                  "When are you out for, though?\n\n{}"
                                  .format(whos_in.get_gametimes()))
    elif len(arguments) == 1:
        await client.send_message(message.channel,
                                  whos_in.remove(message.author,
                                                 arguments[0]))
    else:
        await client.send_message(message.channel,
                                  "You'll need to be more specific :smile:")


async def whosin_command(client, message):
    """
    Handles !whosin

    :param client: The Client
    :param message: The message
    :return: None
    """
    await client.send_message(message.channel, whos_in.whos_in())


async def send_text(client, message):
    """
    Sends a text

    :param client: The Client
    :param message: The message
    :return: None
    """
    arguments = argument_parser(message.content)

    if len(arguments) != 1 or arguments[0] == '!text':
        await client.send_message(message.channel,
                                  'Just give me a name, I\'ll do the rest!')
    elif arguments[0] not in users:
        await client.send_message(message.channel,
                                  'That\'s not a real name...')
    elif 'mobile' not in users[arguments[0]]:
        await client.send_message(message.channel,
                                  'That person doesn\'t have a mobile. So '
                                  'poor!')
    else:
        try:
            twilio_message = twilio_client.messages.create(
                to=users[arguments[0]]['mobile'], from_="+16088880320",
                body="@brochat-bot: Brochat calls, {}. "
                     "Friendship and glory await you. Join us!".format(
                    arguments[0]))
            await client.send_message(message.channel, 'Text message sent!')
        except:
            await client.send_message(message.channel,
                                      'Could not send text message!')


async def get_trump(client, message):
    """
    Gets a presidential tweet

    :param client: The Client
    :param message: The message
    :return: None
    """
    twitter_id = 'realdonaldtrump'
    tweet_text = \
        ':pen_ballpoint::monkey: Trump has been saying things, as ' \
        'usual...'
    rt_text = \
        ':pen_ballpoint::monkey: Trump has been repeating things, as ' \
        'usual... (RT ALERT)'

    try:
        await get_last_tweet(twitter_id, tweet_text, rt_text, client, message)
    except TwythonError:
        await client.send_message(message.channel,
                                  "Twitter is acting up, try again later.")

async def get_last_tweet(id, tweet_text, rt_text, client, message):
    """
    Gets the last tweet for id.
    :param id:
    :param tweet_text: flavor text for tweets
    :param rt_text: flavor text for retweets
    :param client: discord client
    :param message: discord message
    :return:
    """

    if id == 'realdonaldtrump':
        global last_id

    try:
        last_tweet = twitter.get_user_timeline(
            screen_name=id, count=1, include_retweets=True)
    except TwythonError as e:
        raise e
    else:
        # if it's a retweet, send the original tweet
        if 'retweeted_status' in last_tweet[0]:
            if id == 'realdonaldtrump':
                last_id = last_tweet[0]['id']
            rt_id = last_tweet[0]['retweeted_status']['id']
            rt_screen_name = last_tweet[0]['retweeted_status']['user']['screen_name']
            await client.send_message(
                message.channel,
                '{}\n\n'
                'https://twitter.com/{}/status/{}'.format(
                    rt_text,
                    rt_screen_name,
                    str(rt_id)))
        # otherwise, send the tweet
        else:
            if id == 'realdonaldtrump':
                last_id = last_tweet[0]['id']
            await client.send_message(
                message.channel,
                '{}\n\n'
                'https://twitter.com/{}/status/{}'.format(
                    tweet_text,
                    last_tweet[0]['user']['screen_name'],
                    str(last_tweet[0]['id'])))


async def run_shot_lottery(client, message):
    """
    Runs a shot-lottery

    :param client: The Client
    :param message: The message
    :return: None
    """
    if not whos_in.is_lottery_time():
        await client.send_message(message.channel, "Too soon for shots...")
    else:
        shot_lottery_string = shot_lottery(client, whos_in)
        for x in range(4):
            await client.send_message(message.channel,
                                      shot_lottery_string.pop(0))
            await asyncio.sleep(4)
        while len(shot_lottery_string) > 0:
            await client.send_message(message.channel,
                                      shot_lottery_string.pop(0))


async def trigger_social(client, message):
    """

    :param client: The Client
    :param message: The message
    :return: None
    """
    glass = ":tumbler_glass:"
    await client.send_message(message.channel, "Ah shit that's three in a row! "
                                               "ITS A SOCIAL! SHOTS! "
                                               "SHOTS! SHOTS!\n{}{}{}".
                              format(glass, glass, glass))


async def record_win(client, message):
    """
    Handles !win

    :param client: The Client
    :param message: The message
    :return: None
    """
    whos_in.add_win()
    await client.send_message(message.channel, "Congrats on the win!")
    await record_get(client, message)
    if whos_in.consecutive == 3:
        await trigger_social(client, message)
        whos_in.consecutive = 0
    else:
        await run_shot_lottery(client, message)


async def record_loss(client, message):
    """
    Handles !loss

    :param client: The Client
    :param message: The message
    :return: None
    """
    whos_in.add_loss()
    await client.send_message(message.channel, "You guys are bad!")
    await record_get(client, message)
    if whos_in.consecutive == 3:
        await trigger_social(client, message)
        whos_in.consecutive = 0


async def record_draw(client, message):
    """print_version()
    Handles !draw

    :param client: The Client
    :param message: The message
    :return: None
    """
    whos_in.add_draw()
    await client.send_message(message.channel, "What a waste!")
    await record_get(client, message)
    if whos_in.consecutive == 3:
        await trigger_social(client, message)
        whos_in.consecutive = 0


async def record_clear(client, message):
    """
    Handles !record-clear

    :param client: The Client
    :param message: The message
    :return: None
    """
    record_string = "You went: {}".format(whos_in.get_record())
    await client.send_message(message.channel, record_string)
    whos_in.clear_record()
    await client.send_message(message.channel, "Record Cleared!")


async def record_get(client, message):
    """
    Handles !get-record

    :param client: The Client
    :param message: The message
    :return: None
    """
    record_string = "Current Record: {}".format(whos_in.get_record())
    await client.send_message(message.channel, record_string)
    record_string = "Overall Record {}".format(whos_in.get_c_record())
    await client.send_message(message.channel, record_string)


async def battletag(client, message):
    """
    Handles !battletag

    :param client: The Client
    :param message: The message
    :return: None
    """
    author = str(message.author.display_name)
    if author in users:
        if "battletag" in users[author]:
            await client.send_message(message.channel,
                                      "Your battletag is: {}".format(
                                          users[author]["battletag"]))
        else:
            await client.send_message(message.channel,
                                      "I couldn\'t find your battletag!")
    else:
        await client.send_message(message.channel,
                                  "I couldn\'t find your user info!")


async def set_command(client, message):
    """
    Handles !set

    :param client: The Client
    :param message: The message
    :return: None
    """
    author = str(message.author.display_name)
    arguments = argument_parser(message.content)

    if author not in users:
        users[author] = {}

    valid_arguments = {'name': "Okay, I'll call you {} now.",
                       'battletag': "Okay, your battletag is {} from here"
                                    " on out.",
                       'mobile': "Got your digits: {}."}
    if len(arguments) != 2:
        await client.send_message(message.channel,
                                  "To !set information about yourself, "
                                  "please use:\n\n"
                                  "**!set** <name/battletag/mobile> "
                                  "<value>")
    elif arguments[0] in valid_arguments:
        # Added format check for mobile
        if arguments[0] == 'mobile' and \
                (len(arguments[1]) != 12 or
                    arguments[1][0] != '+' or not
                    isinstance(int(arguments[1][1:]), int)):
            await client.send_message(message.channel,
                                      "You'll need to use the format "
                                      "**+14148888888**"
                                      " for your mobile number.")
        else:
            users[author][arguments[0]] = arguments[1]
            await client.send_message(message.channel,
                                      valid_arguments[arguments[0]].format(
                                          users[author][arguments[0]]))
    # Update database
    whos_in.update_db()


async def whoami(client, message):
    """
    Handles !whoami

    :param client: The Client
    :param message: The message
    :return: None
    """
    author = str(message.author.display_name)
    if author in users and users[author] != {}:
        await client.send_message(message.channel,
                                  "Well, I don't know you that well, but "
                                  "from what I've been hearing on the "
                                  "streets...")
        for k, v in users[author].items():
            await client.send_message(message.channel,
                                      "Your {} is {}.".format(k, v))
    else:
        await client.send_message(message.channel,
                                  "You're {}, but that all I know about "
                                  "you.".format(author))


async def toggle_news(client, message):
    """
    Handles !toggle-news

    :param client: The Client
    :param message: The message
    :return: None
    """
    global NEWS_FEED_ON, NEWS_FEED_CREATED

    if NEWS_FEED_ON:

        NEWS_FEED_ON = False
        await client.send_message(message.channel,
                                  "News Feed turned off.")
    else:
        if not NEWS_FEED_CREATED:
            client.loop.create_task(handle_news())
            NEWS_FEED_CREATED = True
        NEWS_FEED_ON = True
        await client.send_message(message.channel,
                                  "News Feed turned on.")

async def get_news(client, message):
    """
    Handles !news

    :param client: The Client
    :param message: The message
    :return: None
    """
    global news_handles
    shuffle(news_handles)
    found_art = False

    while not found_art:
        source = news_handles.pop(0)
        news_handles.append(source)
        tweet_text = "It looks like @" + source + " is reporting:"
        rt_text = "It looks like @" + source + " is retweeting:"

        try:
            await get_last_tweet(source, tweet_text, rt_text, client, message)
        except TwythonError:
            print("Error in get_news, trying another source")

        else:
            found_art = True

    return

async def change_trump_delay(client, message):
    """
    Handles !tdelay

    :param client: The Client
    :param message: The message
    :return: None
    """
    global trump_del
    arguments = argument_parser(message.content)

    if len(arguments) != 1 or arguments[0] == '!tdelay':
        await client.send_message(message.channel, "Incorrect arguments to set "
                                                   "delay, try !tdelay <int>")
    else:
        trump_del = int(arguments[0])
        await client.send_message(message.channel, "Trump delay set to {}"
                                  .format(trump_del))


async def change_news_delay(client, message):
    """
    Handles !ndelay

    :param client: The Client
    :param message: The message
    :return: None
    """
    global news_del
    arguments = argument_parser(message.content)

    if len(arguments) != 1 or arguments[0] == '!ndelay':
        await client.send_message(message.channel, "Incorrect arguments to set "
                                                   "delay, try !ndelay <int>")
    else:
        news_del = int(arguments[0])
        await client.send_message(message.channel, "News delay set to {}"
                                  .format(news_del))


async def owstats(client, message):
    """
    Handles !owstats

    :param client: The Client
    :param message: The message
    :return: None
    """
    author = str(message.author.display_name)
    if author in users and 'battletag' in users[author]:
        await client.send_message(message.channel,
                                  "Hold on, let me check the webs...")
        profile_url = 'https://api.lootbox.eu/pc/us/{}/profile'.format(
            users[author]['battletag'])
        heroes_url = 'https://api.lootbox.eu/pc/us/{}/competitive/' \
                     'allHeroes/'.format(users[author]['battletag'])
        # The following variable is unused
        # headers = {'user-agent': 'brochat-bot/0.0.1'}
        response_profile = requests.get(profile_url)
        response_heroes = requests.get(heroes_url)
        print("Overwatch API returned a response code of {}".format(
            response_profile.status_code))
        if 'statusCode' in response_profile.json() or \
           'statusCode' in response_heroes.json():
            await client.send_message(message.channel,
                                      "Something went wrong. Make sure "
                                      "your battletag is set up like "
                                      "this: **name-1234**")
        elif response_profile.status_code == 429:
            await client.send_message(message.channel,
                                      "You're being ratelimited, chill out "
                                      "bruh.")
        else:
            rating = response_profile.json()['data']['competitive']['rank']
            wins = response_heroes.json()['GamesWon']
            losses = response_heroes.json()['GamesLost']
            ties = response_heroes.json()['GamesTied']
            gold = int(response_heroes.json()['Medals-Gold'])
            silver = int(response_heroes.json()['Medals-Silver'])
            bronze = int(response_heroes.json()['Medals-Bronze'])
            await client.send_message(message.channel,
                                      "Here's the current outlook for {0}:"
                                      "\n\n**Rating:** {1}\n"
                                      "**Record:** {2} / {3} / {4}\n"
                                      "**:first_place::** {5}\n"
                                      "**:second_place::** {6}\n"
                                      "**:third_place::** {7}".format(
                                          author, rating, wins, losses,
                                          ties, gold, silver, bronze
                                      ))
    else:
        await client.send_message(message.channel,
                                  "Sorry, but you didn't !set your"
                                  " battletag.")


@_client.event
async def on_message_edit(before, after):
    """
    Asynchronous event handler for edit

    return: None
    """
    await on_message(after)


@_client.event
async def on_message(message):
    """
    Asynchronous event handler for incoming message

    :return: None
    """

    if "Jim" in message.content and "brochat-bot" not in str(message.author):
        await _client.send_message(message.channel,
                                   'Jim, you mean fat ***REMOVED*** boy?')

    commands = {
        "test": run_test,
        "uptime": get_uptime,
        "sleep": sleep,
        "ham": go_ham,
        "dankmeme": dankmeme,
        "bertstrip": bertstrip,
        "summary": summary,
        "gametime": gametime,
        "in": in_command,
        "possible": possible_command,
        "late": late_command,
        "out": out_command,
        "whosin": whosin_command,
        "text": send_text,
        "trump": get_trump,
        "help": print_help,
        "shot-lottery": run_shot_lottery,
        "win": record_win,
        "loss": record_loss,
        "draw": record_draw,
        "clear-record": record_clear,
        "get-record": record_get,
        "battletag": battletag,
        "set": set_command,
        "whoami": whoami,
        "version": print_version,
        "toggle-news": toggle_news,
        'news': get_news,
        'tdelay': change_trump_delay,
        'ndelay': change_news_delay
    }

    if message.content.startswith("!") and \
       "brochat-bot" not in str(message.author):
        cmd = message.content.lower()
        cmd = cmd.split()[0][1:]
        if cmd in commands:
            await commands[cmd](_client, message)
        else:
            try:
                closest = get_close_matches(cmd, commands)[0]
            except IndexError:
                await _client.send_message(message.channel,
                                           "!{} is not a known command."
                                           .format(cmd))
            else:
                await _client.send_message(message.channel,
                                           "!{} is not a command, did you mean "
                                           "!{}?".format(cmd, closest))

    elif message.content.startswith('@brochat-bot'):
        print(message)


async def check_trumps_mouth():
    """
    Waits for an update from the prez
    :return: None
    """
    global last_id
    c_to_send = None
    await _client.wait_until_ready()
    last_id = twitter.get_user_timeline(
        screen_name='realdonaldtrump',
        count=1, include_retweets=False)[0]['id']

    for channel in _client.get_all_channels():
        if channel.name == 'general' or channel.name == 'brochat':
            c_to_send = channel
            break

    delay = trump_del * 60

    while not _client.is_closed:
        await asyncio.sleep(delay)
        print("Checked trump at {}".format(datetime.datetime.now()))
        try:
            trumps_lt_id = twitter.get_user_timeline(
                screen_name='realdonaldtrump', count=1,
                include_retweets=False)[0]['id']
        except:
            print("Error caught in check_trump, shortening delay")
            delay = 10 * 60
        else:
            delay = trump_del * 60
            if trumps_lt_id != last_id:
                await _client.send_message(c_to_send, "New Message from the "
                                                      "prez! Try !trump")
                last_id = trumps_lt_id


async def print_at_midnight():
    """
    Prints list at midnight
    :return:
    """
    c_to_send = None
    await _client.wait_until_ready()
    for channel in _client.get_all_channels():
        if channel.name == 'general' or channel.name == 'brochat':
            c_to_send = channel
            break

    while not _client.is_closed:
        now = datetime.datetime.now(pytz.timezone('US/Eastern'))
        midnight = now.replace(hour=23, minute=59, second=59, microsecond=59)
        if now > midnight:
            midnight = midnight.replace(day=(now.day + 1))
        print("Scheduling next list print at {}".format(pretty_date(midnight)))
        await asyncio.sleep((midnight - now).seconds)
        await _client.send_message(c_to_send, whos_in.whos_in())
        await asyncio.sleep(60 * 10)


async def handle_news():
    """
    Handles the news feed
    :return:
    """

    global news_handles, NEWS_FEED_ON, NEWS_FEED_CREATED
    c_to_send = None
    shuffle(news_handles)
    await _client.wait_until_ready()

    for channel in _client.get_all_channels():
        if channel.name == 'general' or channel.name == 'newsfeed':
            c_to_send = channel
            break

    delay = (news_del * 60) + (randint(0, 10)*60)
    while not _client.is_closed:
        next_source = news_handles.pop(0)
        news_handles.append(next_source)
        print("Next news source will be {}".format(next_source))
        await asyncio.sleep(delay)
        if NEWS_FEED_ON:
            try:
                news = twitter.get_user_timeline(
                    screen_name=next_source, count=1,
                    include_retweets=False)
            except:
                print("Error caught in news, shortening delay")
                delay = 30
            else:
                delay = (news_del * 60) + (randint(0, 10)*60)
                await _client.send_message(
                    c_to_send, "https://twitter.com/{0}/status/{1}"
                    .format(news[0]['user']['screen_name'],
                            str(news[0]['id'])))
        else:
            NEWS_FEED_CREATED = False
            print("Destroying News Feed Task")
            return


_client.loop.create_task(check_trumps_mouth())
_client.loop.create_task(print_at_midnight())
startTime = time()
_client.run(token)


# TODO weekend gaming session management
# TODO !snapshot to get stats at the beginning of the session via OWAPI
# TODO command handler
