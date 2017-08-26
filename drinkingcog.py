import common
from discord.ext import commands


class DrinkingCog:
    """Handles Dueling commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='drink', aliases=['bottomsup'], pass_context=True)
    async def drink(self, ctx):
        """Log a drink taken"""
        author = str(ctx.message.author.display_name)
        if author in common.users:
            output = "Bottoms up, {}.".format(author)
            result = common.consume_drink(common.users[author])
            if result < 0:
                output += " You're now banking **{}** dranks.".format(-result)
            else:
                output += " You now owe {} drinks.".format(result)
            await self.bot.say(output)

        else:
            await self.bot.say("I don't know you, man.")

        # update the db
        common.whos_in.update_db()

    @commands.command(name='drankbank', aliases=['dbank', 'drinkbank'])
    async def drankbank(self):
        """See how many drinks you owe."""

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


def setup(bot):
    bot.add_cog(DrinkingCog(bot))
