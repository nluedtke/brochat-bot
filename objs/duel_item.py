# the duel_item class, which represents an item to help one duel

from random import choice

# Define a common item here.
# Current guidelines for rarity are:
#   Any item with more than 4 duels in duration is RARE.
#   Any item with a modifier greater than 2 damage or 4 life is RARE.
#   Any item with life_regen greater than 2 is RARE.
# The key is the id of the item
# The item is a dictionary with two key:value pairs
#   1) type: effect types SEE NOTE BELOW
#   2) prop: strength or effect descriptor, this is a dictionary with "eff: str"
#   3) uses: amount of uses, measured in duels
#   4) text: text description of item
#   5) name: name of item
#   6) slot: Where the item sits either armor, weapon, or other
# effect_type: effect
# Currently these effect_types are implemented:
#   1) roll_effect = This effect modifies a roll
#   2) life_effect = This effect modifies a life total at the start of a duel
#   3) disarm_effect = This effect disarms the opponent's item provided its not
#   a disarm_effect itself. CAN ONLY BE ON WEAPONS
#   4) regen_effect = The effect adds life at the end of the round, this
#   happens after the death check goes into effect.
#   5) luck_effect = This modifies the item chance roll at the start of the
#   duel, this does not effect the other random luck effects that happen with
#   other bot interactions.,
#   6) poison_effect = Should only be on weapons and defines two items in the
#   prop list. 'poison' which is the amount the poison actually does right
#   round and 'duration' the amount of rounds it hits for following a
#   successful strike. Poison damage does not stack, but the duration does.
#   deadly = 3 duration, moderate = 2 duration, irritating/oily = 1 duration.
common_items = {
    "0": {"name": "Copper Ring of One Better",
          "type": ["roll_effect"],
          "prop": {'roll': 1},
          "uses": 1,
          "slot": "other",
          "text": "This ring adds +1 to all damage for the user for one duel."},
    "1": {"name": "Bronze Ring of One Better",
          "type": ["roll_effect"],
          "prop": {'roll': 1},
          "uses": 2,
          "slot": "other",
          "text": "This ring adds +1 to all damage for the user for two "
                  "duels."},
    "2": {"name": "Steel Ring of One Better",
          "type": ["roll_effect"],
          "prop": {'roll': 1},
          "uses": 4,
          "slot": "other",
          "text": "This ring adds +1 to all damage for the user for four "
                  "duels."},
    "3": {"name": "Cloth Vest",
          "type": ["life_effect"],
          "prop": {'life': 2},
          "uses": 1,
          "slot": "weapon",
          "text": "This armor adds +2 life for the wearer for one duel."},
    "4": {"name": "Leather Vest",
          "type": ["life_effect"],
          "prop": {'life': 2},
          "uses": 2,
          "slot": "armor",
          "text": "This armor adds +2 life for the wearer for two duels."},
    "5": {"name": "Reinforced Leather Vest",
          "type": ["life_effect"],
          "prop": {'life': 2},
          "uses": 4,
          "slot": "armor",
          "text": "This armor adds +2 life for the wearer for four duels."},
    "6": {"name": "Copper Plate Armor",
          "type": ["life_effect"],
          "prop": {'life': 4},
          "uses": 1,
          "slot": "armor",
          "text": "This armor adds +4 life for the wearer for one duel."},
    "7": {"name": "Bronze Plate Armor",
          "type": ["life_effect"],
          "prop": {'life': 4},
          "uses": 2,
          "slot": "armor",
          "text": "This armor adds +4 life for the wearer for two duels."},
    "8": {"name": "Steel Plate Armor",
          "type": ["life_effect"],
          "prop": {'life': 4},
          "uses": 4,
          "slot": "armor",
          "text": "This armor adds +4 life for the wearer for four duels."},
    "9": {"name": "Leotard",
          "type": ["life_effect"],
          "prop": {'life': 1},
          "uses": 1,
          "slot": "armor",
          "text": "This armor adds +1 life for the wearer for one duel."},
    "10": {"name": "Broadsword",
           "type": ["roll_effect"],
           "prop": {'roll': 2},
           "uses": 1,
           "slot": "weapon",
           "text": "This sword adds +2 to all damage for the user for one "
                   "duel."},
    "11": {"name": "Disarming Hook",
           "type": ["disarm_effect"],
           "prop": {},
           "uses": 1,
           "slot": "weapon",
           "text": "This item will remove your opponent's item."},
    "12": {"name": "Copper Pendant of Regeneration",
           "type": ["regen_effect"],
           "prop": {'regen': 1},
           "uses": 1,
           "slot": "other",
           "text": "This item allows the wearer to regenerate 1 life at the "
                   "end of each round for one duel."},
    "13": {"name": "Metal Detector",
           "type": ["luck_effect"],
           "prop": {'luck': 50},
           "uses": 4,
           "slot": "weapon",
           "text": "This item greatly increases the chance the user will "
                   "receive an item at the start of a duel for four duels."
           },
    "14": {"name": "Hook Sword",
           "type": ["roll_effect", "disarm_effect"],
           "prop": {"roll": 2},
           "uses": 2,
           "slot": "weapon",
           "text": "This sword adds +2 to all damage for the user and disarms "
                   "the opponent's item for two duels."
           },
    "15": {"name": "Glistening Leather Vest",
           "type": ["life_effect", "luck_effect"],
           "prop": {'life': 2, "luck": 20},
           "uses": 2,
           "slot": "armor",
           "text": "This armor adds +2 life for the wearer and moderately "
                   "increases chance for an item for two duels."},
    "16": {"name": "Oily Hook",
           "type": ["poison_effect", "disarm_effect"],
           "prop": {'poison': 1, 'duration': 1},
           "uses": 2,
           "slot": "weapon",
           "text": "This hook disarms the opponent for two duels. The hook "
                   "seems coated in an oily residue."},
    "17": {"name": "Bronze Pendant of Regeneration",
           "type": ["regen_effect"],
           "prop": {'regen': 1},
           "uses": 2,
           "slot": "other",
           "text": "This item allows the wearer to regenerate 1 life at the "
                   "end of each round for two duels."},
    "18": {"name": "Steel Pendant of Regeneration",
           "type": ["regen_effect"],
           "prop": {'regen': 1},
           "uses": 4,
           "slot": "other",
           "text": "This item allows the wearer to regenerate 1 life at the "
                   "end of each round for four duels."},
    "19": {"name": "Xiphos",
           "type": ["roll_effect"],
           "prop": {'roll': 1},
           "uses": 2,
           "slot": "weapon",
           "text": "This sword adds +1 to all damage for the user for two "
                   "duels."},
    "20": {"name": "Lucky Xiphos",
           "type": ["roll_effect", "luck_effect"],
           "prop": {'roll': 1, "luck": 10},
           "uses": 2,
           "slot": "weapon",
           "text": "This sword adds +1 to all damage for the user and slightly "
                   "increases item chance for two duels."},
    "21": {"name": "Bastard sword",
           "type": ["roll_effect"],
           "prop": {'roll': 3},
           "uses": 1,
           "slot": "weapon",
           "text": "This sword adds +3 to all damage for the user for one "
                   "duel."}
}

# Rare items go here and generally considered be more powerful either in
# strength or duration
rare_items = {
    "100": {"name": "Gold Ring of One Better",
            "type": ["roll_effect"],
            "prop": {'roll': 1},
            "uses": 10,
            "slot": "other",
            "text": "This ring adds +1 to all damage for the user for ten "
                    "duels."},
    "101": {"name": "Heavy Steel Plate Armor",
            "type": ["life_effect"],
            "prop": {'life': 4},
            "uses": 10,
            "slot": "armor",
            "text": "This armor adds +4 life for the wearer for ten duels."},
    "102": {"name": "Exceptional Broadsword",
            "type": ["roll_effect"],
            "prop": {'roll': 2},
            "uses": 5,
            "slot": "weapon",
            "text": "This sword adds +2 to all damage for the user for five "
                    "duels."},
    "103": {"name": "Stinger",
            "type": ["poison_effect", "roll_effect"],
            "prop": {'roll': 1, 'poison': 1, 'duration': 3},
            "uses": 5,
            "slot": "weapon",
            "text": "This dagger adds +1 to all damage for the user for five "
                    "duels. The dagger is coated in deadly poison."},
    "104": {"name": "Gold Pendant of Regeneration",
            "type": ["regen_effect"],
            "prop": {'regen': 1},
            "uses": 10,
            "slot": "other",
            "text": "This item allows the wearer to regenerate 1 life at the "
                    "end of each round for ten duels."},
    "105": {"name": "Exceptional Bastard sword",
            "type": ["roll_effect"],
            "prop": {'roll': 3},
            "uses": 3,
            "slot": "weapon",
            "text": "This sword adds +3 to all damage for the user for three "
                    "duels."}
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
        self.slot = None

        if _id is not None:
            self.item_id = str(_id)
        else:
            if 10 >= item_roll > 1:
                _item = choice(list(common_items.keys()))
                self.item_id = _item
            elif item_roll == 1:
                _item = choice(list(rare_items.keys()))
                self.item_id = _item

        if self.item_id is not None:
            if int(self.item_id) < 100:
                items = common_items
            else:
                items = rare_items
            self.name = items[self.item_id]['name']
            self.prop = items[self.item_id]['prop']
            self.type = items[self.item_id]['type']
            self.uses = items[self.item_id]['uses']
            self.text = items[self.item_id]['text']
            self.slot = items[self.item_id]['slot']
            if 'spec_text' in items[self.item_id]:
                self.spec_text = items[self.item_id]['spec_text']

    def __iadd__(self, other):
        """
        Override the +=

        :param other: Item effect to add
        :return:
        """
        self.name = "Combined item"
        self.item_id = None

        if self.type is None:
            self.type = other.type
        else:
            self.type += other.type
        for p in other.prop:
            if self.prop is None:
                self.prop = {}
            if p in self.prop:
                self.prop[p] += other.prop[p]
            else:
                self.prop[p] = other.prop[p]

        return self

    def __eq__(self, other):
        """
        Override the equal operator

        :param other: Second item to compare
        :return: True if the same, false otherwise
        """

        return self.item_id == other.item_id


class PoisonEffect(object):
    """
    Defines a PoisonEffect object
    """

    def __init__(self, _item, p_source):
        """
        Constructor for a PoisonEffect

        :param _item: Item causing the PoisonEffect
        :param p_source: Person Causing the poison
        """

        self.p_id = "{}_{}".format(_item.item_id, p_source)
        self.dam = _item.prop['poison']
        self.dur = _item.prop['duration']

    def __eq__(self, other):
        """
        Override the equal operator

        :param other: Second item to compare
        :return: True if the same, false otherwise
        """

        return self.p_id == other.p_id

    def __iadd__(self, other):
        """
        Override the +=

        :param other: Item effect to add
        :return:
        """
        if type(other) == int:
            self.dur += other
        else:
            self.dur += other.dur

        return self

    def __isub__(self, other):
        """
        Override the -=

        :param other: Item effect to sub
        :return:
        """
        if type(other) == int:
            self.dur -= other
        else:
            self.dur -= other.dur

        return self

    def ended(self):
        """
        Returns if the effect is ended
        :return:
        """
        return self.dur <= 0

if __name__ == "__main__":
    """
    For testing
    """
    i = DuelItem(3)
    print(i.name)
    print(i.prop)
    print(i.uses)
    print(i.text)

    i = DuelItem(1)
    print(i.name)
    print(i.prop)
    print(i.uses)
    print(i.text)

    i = DuelItem(99)
    if i.name is None:
        print("True")
    else:
        print("Item roll of 99 returned an item.")
        exit(1)

    for item in rare_items:
        i = DuelItem(0, item)
        if not hasattr(i, 'item_id') or i.item_id is None:
            print("{} has no item_id")
            exit(1)
        if not hasattr(i, 'name')or i.name is None:
            print("{} has no name")
            exit(1)
        if not hasattr(i, 'prop')or i.prop is None:
            print("{} has no prop")
            exit(1)
        if not hasattr(i, 'uses')or i.uses is None:
            print("{} has no uses")
            exit(1)
        if not hasattr(i, 'type') or i.type is None:
            print("{} has no type")
            exit(1)
        if not hasattr(i, 'slot') or i.slot is None:
            print("{} has no slot")
            exit(1)

    for item in common_items:
        i = DuelItem(0, item)
        if not hasattr(i, 'item_id') or i.item_id is None:
            print("{} has no item_id")
            exit(1)
        if not hasattr(i, 'name')or i.name is None:
            print("{} has no name")
            exit(1)
        if not hasattr(i, 'prop')or i.prop is None:
            print("{} has no prop")
            exit(1)
        if not hasattr(i, 'uses')or i.uses is None:
            print("{} has no uses")
            exit(1)
        if not hasattr(i, 'type') or i.type is None:
            print("{} has no type")
            exit(1)
        if not hasattr(i, 'slot') or i.slot is None:
            print("{} has no slot")
            exit(1)
