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

        if len(self.choices) < 2:
            raise SyntaxError

        self.choice_count = {}

        print("Choices are:")
        ind = 0
        for opt in self.choices:
            print(opt)
            self.choice_count[ind] = 0
            ind += 1

    def add_vote(self, choice):
        """
        Adds a vote to the choice

        :param choice: Choice to add the vote to
        """
        choice = int(choice)

        if choice > len(self.choices):
            raise IndexError

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
            out_string += "{0}: {1} ({2})\n".format(ind, opt,
                                                  self.choice_count[ind])
        return out_string
