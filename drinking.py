# some functions focused on drinking

def add_drink(user):
    """
    Adds a drink for the user.
    :param user:
    :return:
    """

    if "drinks_owed" in user:
        user['drinks_owed'] += 1
    else:
        user['drinks_owed'] = 1

    return user['drinks_owed']


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
