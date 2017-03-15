import discord
import asyncio
from twython import Twython
from time import time
import json
import os
from sys import stderr
from random import randint
from twilio.rest import TwilioRestClient

tokens = {}
db_file = 'db.json'

if not os.path.exists('tokens.config'):
    print("No config file found.", file=stderr)
    exit(-1)
else:
    with open('tokens.config', 'r') as t_file:
        tokens = json.load(t_file)

token = tokens['token']
twitter_api_key = tokens['twitter_api_key']
twitter_api_secret = tokens['twitter_api_secret']

account_sid = tokens['twilio_account_sid']
auth_token = tokens['twilio_auth_token']
twilio_client = TwilioRestClient(account_sid, auth_token)

db = {}

if not os.path.exists(db_file):
    print("Starting DB from scratch")
    with open(db_file, 'w') as datafile:
        json.dump(db, datafile)
else:
    print("Loading the DB")
    with open(db_file, 'r') as datafile:
        db = json.load(datafile)

twitter = Twython(twitter_api_key, twitter_api_secret)
auth = twitter.get_authentication_tokens()

OAUTH_TOKEN = auth['oauth_token']
OAUTH_TOKEN_SECRET = auth['oauth_token_secret']

client = discord.Client()


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

        if self.people.count(remove_formatting(person)) > 0:
            return
        else:
            self.people.append(remove_formatting(person))
            self.update_db()

    def remove(self, person):
        """
        Removes a person from the weekend games list

        :param person: Person to remove
        :rtype str
        :return: str: Formatted string indicating whether a person was removed.
        """

        if remove_formatting(person) in self.people:
            self.people.remove(remove_formatting(person))
            self.update_db()
            return '{} is out for this weekend. What a ***REMOVED***.'.format(
                remove_formatting(person))
        else:
            return '{} was never in anyway. Deceptive!'.format(
                remove_formatting(person))

    def update_db(self):
        """
        Updates the database to disk

        :return: None
        """

        db['people'] = self.people
        db['last_shot'] = self.last_shot
        db['consecutive_shot_wins'] = self.consecutive_shot_wins
        db['last_lottery_time'] = self.last_lottery
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

whos_in = WeekendGames()


def remove_formatting(username):
    """
    Removes the hashtag id from a person's discord name, this is for
    readability.

    :param username: Full username to clean
    :rtype str
    :return: str: Clean user name (striped # from username)
    """

    if '#' in str(username):
        return str(username)[:str(username).index('#')]
    else:
        return str(username)


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
                                          remove_formatting(message.author)))
        await client.send_message(message.channel, whos_in.whos_in())

    elif message.content.startswith('!out'):
        person_is_out = whos_in.remove(message.author)
        await client.send_message(message.channel,person_is_out)
        await client.send_message(message.channel, whos_in.whos_in())

    elif message.content.startswith('!whosin'):
        await client.send_message(message.channel,whos_in.whos_in())

    elif message.content.startswith('@brochat-bot'):
        print(message)

    elif message.content.startswith('!text-brandon'):
        await client.send_message(message.channel, '#TODO: Twilio integration')
        message = twilio_client.messages.create(to="+12174155978", from_="+16088880320",
                                     body="Hello there! Wait, you're not Brandon...")
        message = twilio_client.messages.create(to="+16082173743", from_="+16088880320",
                                     body="Hello there!")

    elif message.content.startswith('!trump'):
        trumps_last_tweet = twitter.get_user_timeline(
            screen_name='realdonaldtrump', count=1, include_retweets=False)
        await client.send_message(
            message.channel,
            'Trump has been saying things, as usual...\n\n'
            'https://twitter.com/{}/status/{}'.format(
                trumps_last_tweet[0]['user']['screen_name'],
                str(trumps_last_tweet[0]['id'])))

    elif message.content.startswith('!help'):
        help_string = 'Here are some things I can help you with:\n\n' \
                      '**!ham:** I\'ll tell you what we\'re gonna get\n' \
                      '**!in:** Tell me you\'re in for the weekend\n' \
                      '**!whosin:** See who\'s in for the weekend\n' \
                      '**!out:** Tell me you\'re out for the weekend\n' \
                      '**!trump:** I\'ll show you Trump\'s latest Yuge ' \
                      'success!\n' \
                      '**!text-brandon:** Tempt fate\n' \
                      '**!shot-lottery:** Run a shot lottery.'

        await client.send_message(message.channel, help_string)

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
            await client.send_message(message.channel, list_string)
            random_string = "Selecting a random number between 0 and {}".format(
                len(players)-1)
            await client.send_message(message.channel, random_string)
            winner = randint(0, len(players)-1)
            finish_string = "The winning number is {}, Congrats {} you WIN!\n" \
                            " Take your shot!".format(winner, players[winner])
            consecutive = whos_in.add_shot_win(players[winner])
            await client.send_message(message.channel, finish_string)
            if consecutive > 1:
                total_string = "Thats {} in a row!".format(consecutive)
                await client.send_message(message.channel, total_string)
            whos_in.log_lottery_time()


client.run(token)


#TODO weekend gaming session management
#TODO !shots
#TODO !in
