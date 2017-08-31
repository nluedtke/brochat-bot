import common
from discord.ext import commands
from random import randint
import asyncio


class DrinkBank:
    """Handles the DrankBank and registering drinks."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='drink', aliases=['bottomsup'], pass_context=True)
    @commands.cooldown(1, 60, type=commands.BucketType.user)
    async def drink(self, ctx):
        """Log a drink taken"""
        author = str(ctx.message.author.display_name)
        if author in common.users:
            output = "Bottoms up, {}. ".format(author)
            result = consume_drink(common.users[author])

            if result < -5:
                output += "Whoa there buddy, drinking around here is a " \
                          "friendship activity. For your sake, I'll go ahead " \
                          "forget about that one."
                common.users[author]["drinks_owed"] = -5
            elif result < 0:
                output += "You're now banking **{}** dranks.".format(-result)
            else:
                output += "You now owe {} drinks.".format(result)
            await self.bot.say(output)

        else:
            await self.bot.say("I don't know you, man.")

        # update the db
        common.whos_in.update_db()

    @commands.command(name='drankbank', aliases=['dbank', 'drinkbank'])
    async def drankbank(self):
        """See your *assets and liabilities* with the bank of drank"""

        output = ":moneybag: The **drankbank** is now open for business " \
                 ":moneybag:\n"
        for name, user in common.users.items():
            if "drinks_owed" in user:
                if user["drinks_owed"] > 0:
                    output += "\n**{}** owes **{}** :tumbler_glass: to the " \
                              "**drankbank**.".format(name, user['drinks_owed'])
                elif user['drinks_owed'] < 0:
                    output += "\n**{}** has **{}** dranks in their ledger. " \
                              "*In the black!*".format(name,
                                                       -user['drinks_owed'])
                else:
                    output += "\n**{}** is in clear and good standing with " \
                              "the **drankbank**.".format(name)
        await self.bot.say(output)

    @commands.command(name='shot-lottery', pass_context=True)
    @commands.cooldown(1, 60 * 5)
    async def shot_lottery(self, ctx, auto_call=False):
        """Runs a shot-lottery"""

        shot_lottery_string = run_shot_lottery(ctx, auto_call)
        for x in range(4):
            await self.bot.say(shot_lottery_string.pop(0))
            ctx.bot.send_typing(ctx.message.channel)
            await asyncio.sleep(4)
        while len(shot_lottery_string) > 0:
            await self.bot.say(shot_lottery_string.pop(0))
        common.whos_in.update_db()


def run_shot_lottery(ctx, auto_call=False):
    """
    Run a shot lottery
    :param ctx: Context
    :param auto_call: Was this called from a win?
    :rtype: list
    :return: Array of strings for the shot lottery
    """
    glass = ":tumbler_glass:"
    output = ["Alright everyone (@here), its time for the SHOT LOTTERY!"
              "\n{} won the last lottery!".format(common.whos_in.last_shot),
              "...The tension is rising..."]
    players = []

    if auto_call:
        largest_num_in_voice = 0
        for channel in ctx.bot.get_all_channels():
            if str(channel.type) == "voice" and len(channel.voice_members) \
                    >= largest_num_in_voice:
                largest_num_in_voice = len(channel.voice_members)
                channel_to_use = channel
        for m in channel_to_use.voice_members:
            players.append(m.display_name)

    if not auto_call or len(players) < 1:
        for m in ctx.bot.get_all_members():
            if str(m.status) == 'online' and str(m.display_name) \
                    != 'brochat-bot':
                players.append(m.display_name)

    output.append("{} entered in the SHOT LOTTERY good luck!"
                  .format(", ".join(players)))
    players.append('SOCIAL!')
    output.append("...Who will it be!?!?")
    output.append("Selecting a random number between 0 and {}"
                  .format(len(players) - 1))
    winner = randint(0, len(players) - 1)
    if players[winner] != 'SOCIAL!':
        common.add_drink(common.users[players[winner]])
        for m in ctx.bot.get_all_members():
            if str(m.display_name) == players[winner]:
                tag_id = m.mention
                break
        output.append("The winning number is {}, Congrats {} you WIN!\n"
                      ":beers: Take your shot!".format(winner, tag_id))
        consecutive = common.whos_in.add_shot_win(players[winner])
        if consecutive > 1:
            output.append("That's {} in a row!".format(consecutive))
    else:
        output.append("The winning number is {}".format(winner))
        output.append("Ah shit! ITS A SOCIAL! SHOTS! SHOTS! SHOTS!")
        output.append("{}{}{}".format(glass, glass, glass))
        players.pop(winner)
        for player in players:
            common.add_drink(common.users[player])
    return output


def consume_drink(user):
    """
    Consumes a drink for the user.

    :param user:
    :return:
    """

    if "drinks_owed" in user:
        user['drinks_owed'] -= 1
    else:
        user['drinks_owed'] = -1

    return user['drinks_owed']


def setup(bot):
    bot.add_cog(DrinkBank(bot))
