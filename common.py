whos_in = None
twitter = None
users = None

# Variable hold trumps last tweet id
last_id = 0
trump_chance_roll_rdy = False

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
trump_del = 20
news_del = 55

async def trigger_social(ctx):
    """Triggers a social """
    glass = ":tumbler_glass:"
    await ctx.bot.say("Ah shit that's three in a row! ITS A SOCIAL! SHOTS! "
                      "SHOTS! SHOTS!\n{}{}{}".format(glass, glass, glass))

