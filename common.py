VERSION_YEAR = 2017
VERSION_MONTH = 9
VERSION_DAY = 15
VERSION_REV = 0

whos_in = None
twitter = None
users = {}
twilio_client = None
ARGS = {}
smmry_api_key = None

# Variable hold trumps last tweet id
last_id = 0
trump_chance_roll_rdy = False

# Runtime stats
duels_conducted = 0
items_awarded = 0
trump_tweets_seen = 0

# Shot_duel acceptance and active
accepted = False
shot_duel_running = False
vict_name = ""

# News handles to pull from
news_handles = ['mashable', 'cnnbrk', 'whitehouse', 'cnn', 'nytimes',
                'foxnews', 'reuters', 'npr', 'usatoday', 'cbsnews',
                'abc', 'washingtonpost', 'msnbc', 'ap', 'aphealthscience',
                'lifehacker', 'cnnnewsroom', 'theonion']

# Delays for Newsfeed and Check_trump, These are in minutes
# remember that news_del is fuzzed + (0-10)
trump_del = 15
news_del = 55

# Location of db.json and tokens.config
data_dir = "/data"

# Create/Load Local Database
db_file = '{}/db.json'.format(data_dir)
db = {}

# Global toggle for news feed
NEWS_FEED_ON = False
NEWS_FEED_CREATED = False

async def trigger_social(ctx):
    """Triggers a social """
    for m in ctx.bot.get_all_members():
        if m.display_name != 'brochat-bot':
            add_drink(m.display_name)
    glass = ":tumbler_glass:"
    await ctx.bot.say("Ah shit that's three in a row! ITS A SOCIAL! SHOTS! "
                      "SHOTS! SHOTS!\n{}{}{}".format(glass, glass, glass))


def add_drink(user):
    """
    Adds a drink for the user.
    :param user: users display name
    :return:
    """

    if "drinks_owed" in users[user]:
        users[user]['drinks_owed'] += 1
    else:
        users[user]['drinks_owed'] = 1

    return users[user]['drinks_owed']
