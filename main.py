import discord
import asyncio
from twython import Twython, TwythonError
from time import time
import json
import os
from sys import stderr
from random import randint
from twilio.rest import TwilioRestClient
import socket
import requests

VERSION_MAJOR = 0
VERSION_MINOR = 7


def shot_lottery():
    """
    Run a shot lottery

    :return: None
    """
    pass


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
        if 'last_lottery_time' in db:
            self.last_lottery = db['last_lottery_time']

        # non persistent variables
        self.wins = 0
        self.draws = 0
        self.losses = 0

    def whos_in(self):
        """
        Prints who is currently in for the weekend games.

        :rtype str
        :return: str: Formatted string for the list of people currently signed
        up for weekend games
        """

        if len(self.people) == 0:
            return 'Well that sucks, nobody is in...'
        elif len(self.people) == 1:
            return 'Good news: {} is in for this weekend.'.format(
                self.people[0])
        elif len(self.people) == 2:
            return 'Good news: {} and {} are in for this weekend.'.format(
                self.people[0], self.people[1])
        elif len(self.people) > 2:
            person_list = ', '.join(self.people[:-1])
            person_list += ', and %s' % self.people[-1]
            return 'Good news: {} are in for this weekend.'.format(person_list)

    def add(self, person):
        """
        Adds a person to the weekend games list
        :param person: Person to add
        :return: None
        """
        if type(person) is str:
            person_to_add = person
        else:
            person_to_add = str(person.display_name)

        if self.people.count(person_to_add) > 0:
            return
        else:
            self.people.append(person_to_add)
            self.update_db()

    def remove(self, person):
        """
        Removes a person from the weekend games list

        :param person: Person to remove
        :rtype str
        :return: str: Formatted string indicating whether a person was removed.
        """

        if type(person) is str:
            person_to_rem = person
        else:
            person_to_rem = str(person.display_name)

        if person_to_rem in self.people:
            self.people.remove(person_to_rem)
            self.update_db()
            return '{} is out for this weekend. What a ***REMOVED***.'.format(
                person_to_rem)
        else:
            return '{} was never in anyway. Deceptive!'.format(
                person_to_rem)

    def update_db(self):
        """
        Updates the database to disk

        :return: None
        """

        db['people'] = self.people
        db['last_shot'] = self.last_shot
        db['consecutive_shot_wins'] = self.consecutive_shot_wins
        db['last_lottery_time'] = self.last_lottery
        db['users'] = users
        with open(db_file, 'w') as datafile:
            json.dump(db, datafile, sort_keys=True, indent=4,
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

    def add_win(self):
        """
        Adds a win

        :return: None
        """

        self.wins += 1

    def add_loss(self):
        """
        Adds a loss

        :return: None
        """

        self.losses += 1

    def add_draw(self):
        """
        Adds a draw

        :return: None
        """

        self.draws += 1

    def clear_record(self):
        """
        Adds a draw

        :return: None
        """

        self.draws = 0
        self.wins = 0
        self.losses = 0

    def get_record(self):
        """
        Gets the record of a session

        :return: str: With record formatting
        """

        return "{0} - {1} - {2}".format(self.wins, self.losses, self.draws)

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

# Twilio Tokens
account_sid = tokens['twilio_account_sid']
auth_token = tokens['twilio_auth_token']
twilio_client = TwilioRestClient(account_sid, auth_token)


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
try:
    users = db['users']
except:
    users = {}

# Instantiate Discord client and Weekend Games
client = discord.Client()
whos_in = WeekendGames()


def argument_parser(input):
    """
    Returns a list of tokens for a given argument
    :param input: input string
    :return: argument list
    """

    arguments = input.split(' ')
    if len(arguments) > 1:
        return arguments[1:]
    else:
        return arguments


@client.event
async def on_ready():
    """
    Asynchronous event handler for logging in

    :return: None
    """
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    for channel in client.get_all_channels():
        print(channel)

    # await client.send_message('#general', 'Hi I\'m online :)')


def print_help():
    """
    Returns the help string

    :rtype str
    :return: str: Help Message
    """
    help_string = 'Here are some things I can help you with:\n\n' \
                  '**!ham:** I\'ll tell you what we\'re gonna get\n' \
                  '**!in:** Tell me you\'re in for the weekend\n' \
                  '**!whosin:** See who\'s in for the weekend\n' \
                  '**!out:** Tell me you\'re out for the weekend\n' \
                  '**!trump:** I\'ll show you Trump\'s latest Yuge ' \
                  'success!\n' \
                  '**!text <name>:** Get that fool in the loop\n' \
                  '**!shot-lottery:** Run a shot lottery.\n' \
                  '**!win/!loss/!draw:** Update session record ' \
                  'appropriately\n' \
                  '**!clear-record:** Clear the session record\n' \
                  '**!get-record:** Print the session record\n' \
                  '**!set:** Tell Brochat-Bot some info about you\n' \
                  '**!battletag:** I\'ll tell you your battletag\n' \
                  '**!whoami:** I\'ll tell you what I know about you\n' \
                  '**!version:** Print the version of brochat-bot\n'
    return help_string


def print_version():
    """
    Returns the version string

    :rtype str
    :return: str: Version string
    """
    version_string = "Version: {0}.{1}\n" \
                     "Running on: {2}".format(VERSION_MAJOR,
                                              VERSION_MINOR,
                                              socket.gethostname())
    return version_string


@client.event
async def on_message(message):
    """
    Asynchronous event handler for incoming message

    :return: None
    """

    global whos_in
    if message.content.startswith('!test'):
        counter = 0
        tmp = await client.send_message(message.channel,
                                        'Calculating messages...')
        async for log in client.logs_from(message.channel, limit=100):
            if log.author == message.author:
                counter += 1

        await client.edit_message(tmp, 'You have {} messages.'.format(counter))
    elif message.content.startswith('!sleep'):
        await asyncio.sleep(5)
        await client.send_message(message.channel, 'Done sleeping')

    elif message.content == '!ham':
        await client.send_message(message.channel,
                                  '@here Let\'s get retarded, {}'.format(
                                      message.author))

    elif message.content.startswith('!in'):
        arguments = message.content.split(' ')
        if len(arguments) > 1:
            arguments.remove('!in')
            for arg in arguments:
                whos_in.add(arg)
        else:
            whos_in.add(message.author)
            await client.send_message(message.channel,
                                      '{} is in for this weekend.'.format(
                                          message.author.display_name))
        await client.send_message(message.channel, whos_in.whos_in())

    elif message.content.startswith('!out'):
        person_is_out = whos_in.remove(message.author)
        await client.send_message(message.channel, person_is_out)
        await client.send_message(message.channel, whos_in.whos_in())

    elif message.content.startswith('!whosin'):
        await client.send_message(message.channel, whos_in.whos_in())

    elif message.content.startswith('@brochat-bot'):
        print(message)

    elif message.content.startswith('!text'):

        arguments = argument_parser(message.content)

        if len(arguments) != 1:
            await client.send_message(message.channel,
                                      'Just give me a name, I\'ll do the rest!')
        elif arguments[0] not in users:
            await client.send_message(message.channel,
                                      'That\'s not a real name...')
        elif 'mobile' not in users[arguments[0]]:
            await client.send_message(message.channel,
                                      'That person doesn\'t have a mobile. So poor!')
        else:
            try:
                twilio_message = twilio_client.messages.create(
                    to=users[arguments[0]]['mobile'], from_="+16088880320",
                    body="@brochat-bot is always watching you, {}. Just watching, waiting for games.".format(arguments[0]))
                await client.send_message(message.channel, 'Text message sent!')
            except:
                await client.send_message(message.channel,
                                          'Could not send text message!')

    elif message.content.startswith('!trump'):
        try:
            trumps_last_tweet = twitter.get_user_timeline(
                screen_name='realdonaldtrump', count=1, include_retweets=False)
        except TwythonError:
            await client.send_message(message.channel,
                                      "Twitter is acting up, try again later.")
        else:
            await client.send_message(
                message.channel,
                ':pen_ballpoint::monkey: Trump has been saying things, as usual...\n\n'
                'https://twitter.com/{}/status/{}'.format(
                    trumps_last_tweet[0]['user']['screen_name'],
                    str(trumps_last_tweet[0]['id'])))

    elif message.content.startswith('!help'):
        await client.send_message(message.channel, print_help())

    elif message.content.startswith('!shot-lottery'):
        if not whos_in.is_lottery_time():
            await client.send_message(message.channel, "Too soon for shots...")
        else:
            start_string = "Alright everyone, its time for the SHOT LOTTERY!" \
                           "\n{} won the last lottery!".format(
                            whos_in.last_shot)
            await client.send_message(message.channel, start_string)

            players = []
            for m in client.get_all_members():
                if str(m.status) == 'online' and \
                   str(m.display_name) != 'brochat-bot':
                    players.append(m.display_name)
            list_string = "{} have been entered in the SHOT LOTTERY " \
                          "good luck!".format(players)
            await asyncio.sleep(3)
            await client.send_message(message.channel, "...The tension is rising...")
            await asyncio.sleep(2)
            await client.send_message(message.channel, list_string)
            random_string = "Selecting a random number between 0 and {}".format(
                len(players)-1)
            await asyncio.sleep(4)
            await client.send_message(message.channel, "...Who will it be!?!?")
            await asyncio.sleep(4)
            await client.send_message(message.channel, random_string)
            winner = randint(0, len(players)-1)
            finish_string = "The winning number is {}, Congrats {} you WIN!\n" \
                            ":beers: Take your shot!".format(winner, players[winner])
            consecutive = whos_in.add_shot_win(players[winner])
            await client.send_message(message.channel, finish_string)
            if consecutive > 1:
                total_string = "That's {} in a row!".format(consecutive)
                await client.send_message(message.channel, total_string)
            whos_in.log_lottery_time()
    elif message.content.startswith('!win'):
        whos_in.add_win()
        await client.send_message(message.channel, "Congrats on the win!")
        record_string = "Current record: {}".format(whos_in.get_record())
        await client.send_message(message.channel, record_string)
    elif message.content.startswith('!loss'):
        whos_in.add_loss()
        await client.send_message(message.channel, "You guys are bad!")
        record_string = "Current record: {}".format(whos_in.get_record())
        await client.send_message(message.channel, record_string)
    elif message.content.startswith('!draw'):
        whos_in.add_draw()
        await client.send_message(message.channel, "What a waste!")
        record_string = "Current record: {}".format(whos_in.get_record())
        await client.send_message(message.channel, record_string)
    elif message.content.startswith('!clear-record'):
        record_string = "You went: {}".format(whos_in.get_record())
        await client.send_message(message.channel, record_string)
        whos_in.clear_record()
        await client.send_message(message.channel, "Record Cleared!")
    elif message.content.startswith('!get-record'):
        record_string = "Current record: {}".format(whos_in.get_record())
        await client.send_message(message.channel, record_string)
    elif message.content.startswith('!battletag'):
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
    elif message.content.startswith('!set'):
        author = str(message.author.display_name)
        arguments = argument_parser(message.content)

        if author not in users:
            users[author] = {}

        valid_arguments = {'name': "Okay, I'll call you {} now.",
                           'battletag':  "Okay, your battletag is {} from here"
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
            if arguments[0] == 'mobile' and (len(arguments[1]) != 12 or arguments[1][0] != '+'
                                             or not isinstance(int(arguments[1][1:]),int)):
                await client.send_message(message.channel,"You'll need to use the format **+14148888888**"
                                                          " for your mobile number.")
            else:
                users[author][arguments[0]] = arguments[1]
                await client.send_message(message.channel,
                                          valid_arguments[arguments[0]].format(
                                              users[author][arguments[0]]))
        # Update database
        whos_in.update_db()

    elif message.content.startswith('!whoami'):
        author = str(message.author.display_name)
        if author in users and users[author] != {}:
                await client.send_message(message.channel, "Well, I don't know you that well, but "
                                                           "from what I've been hearing on the streets...")
                for k,v in users[author].items():
                    await client.send_message(message.channel, "Your {} is {}.".format(k,v))
        else:
            await client.send_message(message.channel, "You're {}, but that all I know about you.".format(
                                                        author))

    elif message.content.startswith('!owstats'):
        author = str(message.author.display_name)
        if author in users and 'battletag' in users[author]:
            await client.send_message(message.channel, "Hold on, let me check the webs...")
            profile_url = 'https://api.lootbox.eu/pc/us/{}/profile'.format(users[author]['battletag'])
            heroes_url = 'https://api.lootbox.eu/pc/us/{}/competitive/allHeroes/'.format(users[author]['battletag'])
            headers = {'user-agent': 'brochat-bot/0.0.1'}
            response_profile = requests.get(profile_url)
            response_heroes = requests.get(heroes_url)
            print("Overwatch API returned a response code of {}".format(response_profile.status_code))
            if response_profile.status_code == 200:
                rating = response_profile.json()['data']['competitive']['rank']
                wins = response_heroes.json()['GamesWon']
                losses = response_heroes.json()['GamesLost']
                ties = response_heroes.json()['GamesTied']
                gold = int(response_heroes.json()['Medals-Gold'])
                silver = int(response_heroes.json()['Medals-Silver'])
                bronze = int(response_heroes.json()['Medals-Bronze'])
                await client.send_message(message.channel, "Here's the current outlook for {0}:\n\n"
                                                           "**Rating:** {1}\n"
                                                           "**Record:** {2} / {3} / {4}\n"
                                                           "**:first_place::** {5}\n"
                                                           "**:second_place::** {6}\n"
                                                           "**:third_place::** {7}".format(
                    author, rating, wins, losses, ties, gold, silver, bronze
                ))
            elif response_profile.status_code == 429:
                await client.send_message(message.channel, "You're being ratelimited, chill out bruh.")
            else:
                await client.send_message(message.channel, "Sorry, but the Overwatch API knows I did bad stuff...")
        else:
            await client.send_message(message.channel, "Sorry, but you didn't !set your battletag.")

    elif message.content.startswith('!version'):
        await client.send_message(message.channel, print_version())


client.run(token)


# TODO weekend gaming session management
# TODO !snapshot to get stats at the beginning of the session via OWAPI
# TODO command handler
