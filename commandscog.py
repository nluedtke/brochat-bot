import discord
from discord.ext import commands


class CommandsCog:
    """Basic Commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='repeat', aliases=['copy', 'mimic'])
    async def do_repeat(self, *, our_input: str):
        """A simple command which repeats our input.
        In rewrite Context is automatically passed to our commands as the first
        argument after self."""

        await self.bot.say(our_input)

    @commands.command(name='add', aliases=['plus'])
    async def do_addition(self, first: int, second: int):
        """A simple command which does addition on two integer values."""

        total = first + second
        await self.bot.say('The sum of **{}** and **{}**  is  **{}**'.format(
            first, second, total))


def setup(bot):
    bot.add_cog(CommandsCog(bot))
