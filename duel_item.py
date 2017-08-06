# the duel_item class, which represents an item to help one duel

from random import choice

# Define a common item here.
# The key is the name of the item
# The item is a dictionary with two key:value pairs
#   1) type: effect_type
#   2) prop: strength or effect discripter
#   3) uses: amount of uses, measured in duels
# effect_type: effect
# Currently there are three effect_types:
#   1) roll_effect = This effect modifies a roll
#   2) life_effect = This effect modifies a life total at the start of a duel
#   3) spec_effect = This effect does something different other than the two
#           above and takes places after rolls go into effect.
common_items = {
    "Copper Ring of One Better": {"type": "roll_effect",
                                  "prop": 1,
                                  "uses": 1},
    "Bronze Ring of One Better": {"type": "roll_effect",
                                  "prop": 1,
                                  "uses": 2},
    "Steel Ring of One Better": {"type": "roll_effect",
                                 "prop": 1,
                                 "uses": 4}
}

# Rare items go here and generally considered be more powerful either in
# strength or duration
rare_items = {
    "Gold Ring of One Better": {"type": "roll_effect",
                                "prop": 1,
                                "uses": 10}
}


class Duel_Item(object):
    """
    Defines the Duel_Item Class
    """

    def __init__(self, item_roll):
        """
        :param item_roll: Int representing the roll value used to determine
        if an item should be reward and what type of item
        """

        self.name = None
        self.prop = None
        self.uses = None
        self.type = None

        if 5 >= item_roll > 1:
            item = choice(list(common_items.keys()))
            self.name = item
            self.prop = common_items[item]['prop']
            self.type = common_items[item]['type']
            self.uses = common_items[item]['uses']
        elif item_roll == 1:
            item = choice(list(rare_items.keys()))
            self.name = item
            self.prop = rare_items[item]['prop']
            self.type = rare_items[item]['type']
            self.uses = rare_items[item]['uses']


if __name__ == "__main__":
    """
    For testing
    """
    i = Duel_Item(3)
    print(i.name)
    print(i.prop)
    print(i.uses)

    i = Duel_Item(1)
    print(i.name)
    print(i.prop)
    print(i.uses)

    i = Duel_Item(99)
    if i.name is None:
        print("True")