# the duel_item class, which represents an item to help one duel

from random import choice

# Define a common item here.
# Current guidelines for rarity are:
#   Any item with more than 4 duels in duration is RARE.
#   Any item with a modifier greater than 2 damage or 4 life is RARE.
# The key is the id of the item
# The item is a dictionary with two key:value pairs
#   1) type: effect_type
#   2) prop: strength or effect descriptor
#   3) uses: amount of uses, measured in duels
#   4) text: text description of item
#   5) name: name of item
# effect_type: effect
# Currently these effect_types are implemented:
#   1) roll_effect = This effect modifies a roll
#   2) life_effect = This effect modifies a life total at the start of a duel
#   3) disarm_effect = This effect disarms the opponent's item provided its not
#   a disarm_effect itself.
common_items = {
    "0": {"name": "Copper Ring of One Better",
          "type": "roll_effect",
          "prop": 1,
          "uses": 1,
          "text": "This ring adds +1 to all damage for the user for one duel."},
    "1": {"name": "Bronze Ring of One Better",
          "type": "roll_effect",
          "prop": 1,
          "uses": 2,
          "text": "This ring adds +1 to all damage for the user for two "
                  "duels."},
    "2": {"name": "Steel Ring of One Better",
          "type": "roll_effect",
          "prop": 1,
          "uses": 4,
          "text": "This ring adds +1 to all damage for the user for four "
                  "duels."},
    "3": {"name": "Cloth Vest",
          "type": "life_effect",
          "prop": 2,
          "uses": 1,
          "text": "This armor adds +2 life for the wearer for one duel."},
    "4": {"name": "Leather Vest",
          "type": "life_effect",
          "prop": 2,
          "uses": 2,
          "text": "This armor adds +2 life for the wearer for two duels."},
    "5": {"name": "Reinforced Leather Vest",
          "type": "life_effect",
          "prop": 2,
          "uses": 4,
          "text": "This armor adds +2 life for the wearer for four duels."},
    "6": {"name": "Copper Plate Armor",
          "type": "life_effect",
          "prop": 4,
          "uses": 1,
          "text": "This armor adds +4 life for the wearer for one duel."},
    "7": {"name": "Bronze Plate Armor",
          "type": "life_effect",
          "prop": 4,
          "uses": 2,
          "text": "This armor adds +4 life for the wearer for two duels."},
    "8": {"name": "Steel Plate Armor",
          "type": "life_effect",
          "prop": 4,
          "uses": 4,
          "text": "This armor adds +4 life for the wearer for four duels."},
    "9": {"name": "Leotard",
          "type": "life_effect",
          "prop": 1,
          "uses": 1,
          "text": "This armor adds +1 life for the wearer for one duel."},
    "10": {"name": "Broadsword",
           "type": "roll_effect",
           "prop": 2,
           "uses": 1,
           "text": "This sword adds +2 to all damage for the user for one "
                   "duel."},
    "11": {"name": "Disarming Hook",
           "type": "disarm_effect",
           "prop": 0,
           "uses": 1,
           "text": "This item will remove your opponent's item. Note: This "
                   "simply unequips the item, it does not destroy it.",
           "spec_text": "The opponent's item will be removed if there is one "
                        "equiped."}

}

# Rare items go here and generally considered be more powerful either in
# strength or duration
rare_items = {
    "100": {"name": "Gold Ring of One Better",
            "type": "roll_effect",
            "prop": 1,
            "uses": 10,
            "text": "This ring adds +1 to all damage for the user for ten "
                    "duels."},

    "101": {"name": "Heavy Steel Plate Armor",
            "type": "life_effect",
            "prop": 4,
            "uses": 10,
            "text": "This armor adds +4 life for the wearer for ten duels."}
}


class DuelItem(object):
    """
    Defines the Duel_Item Class
    """

    def __init__(self, item_roll, _id=None):
        """
        :param item_roll: Int representing the roll value used to determine
        :param _id: Create item from id number if an item should be reward
        and what type of item
        """

        self.item_id = None
        self.name = None
        self.prop = None
        self.uses = None
        self.type = None

        if _id is not None:
            self.item_id = str(_id)
        else:
            if 9 >= item_roll > 1:
                item = choice(list(common_items.keys()))
                self.item_id = item
            elif item_roll == 1:
                item = choice(list(rare_items.keys()))
                self.item_id = item

        if self.item_id is not None:
            if int(self.item_id) < 100:
                items = common_items
            else:
                items = rare_items
            self.name = items[self.item_id]['name']
            self.prop = items[self.item_id]['prop']
            self.type = items[self.item_id]['type']
            self.uses = items[self.item_id]['uses']
            if 'spec_text' in items[self.item_id]:
                self.spec_text = items[self.item_id]['spec_text']


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

    i = DuelItem(11, 11)
    print(i.name)
    print(i.prop)
    print(i.uses)
    print(i.spec_text)

    i = DuelItem(99)
    if i.name is None:
        print("True")
