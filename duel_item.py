# the duel_item class, which represents an item to help one duel

from random import choice

# Define a common item here.
# The key is the id of the item
# The item is a dictionary with two key:value pairs
#   1) type: effect_type
#   2) prop: strength or effect discripter
#   3) uses: amount of uses, measured in duels
#   4) text: text description of item
#   5) name: name of item
# effect_type: effect
# Currently there are three effect_types:
#   1) roll_effect = This effect modifies a roll
#   2) life_effect = This effect modifies a life total at the start of a duel
#   3) spec_effect = This effect does something different other than the two
#           above and takes places after rolls go into effect.
common_items = {
    "0": {"name": "Copper Ring of One Better",
          "type": "roll_effect",
          "prop": 1,
          "uses": 1,
          "text": "This ring adds +1 to all damage "
                  "for the user for one duel."},
    "1": {"name": "Bronze Ring of One Better",
          "type": "roll_effect",
          "prop": 1,
          "uses": 2,
          "text": "This ring adds +1 to all damage "
                  "for the user for two duels."},
    "2": {"name": "Steel Ring of One Better",
          "type": "roll_effect",
          "prop": 1,
          "uses": 4,
          "text": "This ring adds +1 to all damage "
                  "for the user for four duels."}
}

# Rare items go here and generally considered be more powerful either in
# strength or duration
rare_items = {
    "100": {"name": "Gold Ring of One Better",
            "type": "roll_effect",
            "prop": 1,
            "uses": 10,
            "text": "This ring adds +1 to all damage "
                    "for the user for ten duels."}
}


class DuelItem(object):
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
            print("Created " + item)
            self.name = common_items[item]['name']
            self.prop = common_items[item]['prop']
            self.type = common_items[item]['type']
            self.uses = common_items[item]['uses']
        elif item_roll == 1:
            item = choice(list(rare_items.keys()))
            print("Created " + item)
            self.name = rare_items[item]['name']
            self.prop = rare_items[item]['prop']
            self.type = rare_items[item]['type']
            self.uses = rare_items[item]['uses']


if __name__ == "__main__":
    """
    For testing
    """
    i = DuelItem(3)
    print(i.name)
    print(i.prop)
    print(i.uses)

    i = DuelItem(1)
    print(i.name)
    print(i.prop)
    print(i.uses)

    i = DuelItem(99)
    if i.name is None:
        print("True")
