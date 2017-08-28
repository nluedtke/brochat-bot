# The poll class handling poll functions/objects

import re

option_re = re.compile("\"(.*?)\"")


class Poll(object):
    """
    Defines the Poll Class

    """

    def __init__(self, options):
        """
        Constructor for a Poll object

        :param options: String of complete options
        """

        self.choices = option_re.findall(options)
        self.voters = list()

        if len(self.choices) < 2:
            raise SyntaxError

        self.choice_count = {}

        for ind, opt in enumerate(self.choices):
            self.choice_count[ind] = 0

    def add_vote(self, choice, user):
        """
        Adds a vote to the choice

        :param choice: Choice to add the vote to
        :param user: User that is voting
        """
        choice = int(choice)

        if choice > len(self.choices):
            raise IndexError

        if user in self.voters:
            return "You already voted! That doesn't count!"
        else:
            self.voters.append(user)

        if choice not in self.choice_count:
            self.choice_count[choice] = 0

        self.choice_count[choice] += 1

        out_string = "Vote added!"
        out_string += self.get_current_state()
        return out_string

    def get_current_state(self):
        """
        Returns of string of the current results
        """

        out_string = "\nIndex: Option (total votes)\n"
        for ind, opt in enumerate(self.choices):
            out_string += "**{0}**: {1} (**{2}**)\n"\
                          .format(ind, opt, self.choice_count[ind])

        return out_string

    def get_final_state(self):
        """
        Returns of string of the final results

        """

        out_string = ":scales: Poll. *Freaking.* Over. :scales:\n\n"
        for ind, opt in enumerate(self.choices):
            out_string += "**{0}**: {1} (**{2}**)\n"\
                          .format(ind, opt, self.choice_count[ind])

        winner = []
        vote_count = 0

        for item, name in enumerate(self.choices):
            if self.choice_count[item] > vote_count:
                winner = [name]
                vote_count = self.choice_count[item]
            elif self.choice_count[item] == vote_count:
                winner.append(name)

        if len(winner) == 1:
            out_string += "\nVoting has concluded, the winner is " \
                          "**{}** with **{}** votes!"\
                          .format(winner[0], vote_count)
        else:
            out_string += "Gross, it was a tie, between: "
            out_string += ", ".join(winner)
            out_string += "."

        return out_string
