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

# NonStandard Imports
import discord
import asyncio
from twython import Twython, TwythonError
from twilio.rest import Client
import requests
from gametime import Gametime
from poll import Poll
from duel_item import DuelItem, common_items, rare_items, PoisonEffect










_client.loop.create_task(check_trumps_mouth())
_client.loop.create_task(print_at_midnight())
startTime = time()

if os.environ.get("TEST_TRAVIS_NL"):
    exit(0)
_client.run(token)


# TODO weekend gaming session management
