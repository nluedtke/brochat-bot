whos_in = None
twitter = None
users = None

# Variable hold trumps last tweet id
last_id = 0
trump_chance_roll_rdy = False

items_awarded = 0

# News handles to pull from
news_handles = ['mashable', 'cnnbrk', 'whitehouse', 'cnn', 'nytimes',
                'foxnews', 'reuters', 'npr', 'usatoday', 'cbsnews',
                'abc', 'washingtonpost', 'msnbc', 'ap', 'aphealthscience',
                'lifehacker', 'cnnnewsroom', 'theonion']

async def trigger_social(ctx):
    """Triggers a social """
    glass = ":tumbler_glass:"
    await ctx.bot.say("Ah shit that's three in a row! ITS A SOCIAL! SHOTS! "
                      "SHOTS! SHOTS!\n{}{}{}".format(glass, glass, glass))
