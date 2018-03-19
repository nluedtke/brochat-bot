import json

from objs.gametime import Gametime

import common
from objs.poll import Poll


class WeekendGames(object):
    """
    Defines the WeekendGames class
    """

    def __init__(self,):
        """
        WeekendGames constructor
        """

        db = common.db
        self.people = []
        if 'people' in db:
            self.people = db['people']
        self.day = 'Sunday'
        self.last_shot = "Unknown"
        if 'last_shot' in db:
            self.last_shot = db['last_shot']
        self.consecutive_shot_wins = 1
        if 'consecutive_shot_wins' in db:
            self.consecutive_shot_wins = db['consecutive_shot_wins']
        self.last_reddit_request = 0

        # store our games
        self.gametimes = []
        if 'gametimes' in db:
            for gt in db['gametimes']:
                self.gametimes.append(Gametime(json_create=gt))

        self.c_win = 0
        self.c_loss = 0
        self.c_draw = 0
        if 'c_win' in db:
            self.c_win = db['c_win']
        if 'c_loss' in db:
            self.c_loss = db['c_loss']
        if 'c_draw' in db:
            self.c_draw = db['c_draw']

        # non persistent variables
        self.wins = 0
        self.draws = 0
        self.losses = 0
        self.last = None
        self.consecutive = 0
        self.poll = None

    def get_gametimes(self):
        """
        Get upcoming gametimes.
        :return: string response to print to chat.
        """
        upcoming_days = "**Exciting f-ing news, boys:**\n\n"
        if len(self.gametimes) == 0:
            return "No games coming up, friendship outlook bleak."
        game_id = 0
        for gt in self.gametimes:
            game_id += 1
            upcoming_days += "{}: There is a gaming session coming up on " \
                             "**{}**\n".format(game_id,
                                               pretty_date(gt.get_date()))
            if len(gt.players) == 0:
                upcoming_days += "    Nobody's in for this day.\n"
            else:
                for player in gt.players:
                    status = gt.get_player_status(player['name'])
                    upcoming_days += "    - **{}** is *{}*.\n".format(
                        player['name'], status)
        return upcoming_days

    def gametime_actions(self, message):
        """
        Routes a gametime action, specified in the second
        argument, ex !gametime <add> Sunday
        :param message: Containing Arguments
        :return: string response to print to chat.
        """
        arguments = argument_parser(message)

        gametime_help_string = \
            "That's not a valid command for **!gametime**\n\n" \
            "Please use:\n" \
            "!gametime <add> <day of the week>" \
            "<_optional_: military time, HH:MM> to **add a gametime**\n" \
            "!gametime <remove> <index> to **delete a gametime**\n" \
            "!gametime <list> to **list current gametimes**\n" \
            "!gametime <set> <index> <time> to " \
            "**set the time of a gametime**"
        valid_commands = {
            "add": self.create_gametime,
            "remove": self.remove_gametime,
            "list": self.get_gametimes,
            "set": self.set_gametime
        }
        if arguments[0] in valid_commands:
            if len(arguments) == 3:
                try:
                    return valid_commands[arguments[0]](arguments[1],
                                                        arguments[2])
                except KeyError:
                    return gametime_help_string
            elif len(arguments) == 2:
                try:
                    return valid_commands[arguments[0]](arguments[1])
                except KeyError:
                    return gametime_help_string
            elif len(arguments) == 1:
                try:
                    return valid_commands[arguments[0]]()
                except KeyError:
                    return gametime_help_string
        return gametime_help_string

    def poll_actions(self, message):
        """
        Handles Poll creation/deletion

        :param message: Containing arguments
        :return: string response to print to chat.
        """
        arguments = argument_parser(message)

        poll_help_string = \
            "That's not a valid command for **!poll**\n\n" \
            "Please use:\n" \
            "!poll start \"option 1\" \"option 2\" etc... to **start a " \
            "poll**\n" \
            "!poll stop to **delete the current poll**"
        valid_commands = {
            "start": self.create_poll,
            "stop": self.stop_poll,
        }
        if arguments[0] in valid_commands:
            return valid_commands[arguments[0]](" ".join(arguments[1:]))
        return poll_help_string

    def create_poll(self, options):
        """
        Creates a poll if one is not already running

        :param options: Options for the poll
        """

        if self.poll is not None:
            return "Can't start poll, one is running try !poll stop first"
        try:
            self.poll = Poll(options)
        except SyntaxError:
            return "You probably want to start the poll correctly. Nice try."
        return self.poll.get_current_state()

    def stop_poll(self):
        """
        Stops a poll
        """

        if self.poll is None:
            return "No poll running"
        out_str = self.poll.get_final_state()
        self.poll = None
        return out_str

    def create_gametime(self, day, start_time=None):
        """
        Create a gametime, given a full name of a day of the week.
        :param start_time: Time of the game
        :param day: string of a proper case day of the week.
        :return: string response to send to chat.
        """
        day = day.capitalize()
        if day in Gametime.DAYS_IN_WEEK:
            new_gametime = Gametime(day=Gametime.DAYS_IN_WEEK.index(day),
                                    time=start_time)
            for game_session in self.gametimes:
                if new_gametime == game_session:
                    return "There is already a session that time."
            self.gametimes.append(new_gametime)
            self.gametimes.sort(key=lambda x: x.date)
            return "Gametime created for {}.".format(
                pretty_date(new_gametime.get_date()))
        else:
            return "Please use the full name of a day of the week."

    def remove_gametime(self, index):
        try:
            index = int(index)
        except ValueError:
            return "Your index should be a number, silly."
        if 0 < index <= len(self.gametimes):
            self.gametimes.pop(index - 1)
            return "Gametime removed."
        else:
            return "There's no gametime with that number."

    def set_gametime(self, index, new_time):
        try:
            index = int(index)
        except ValueError:
            return "Your index should be a number, silly."
        if 0 < index <= len(self.gametimes):
            output_string = ""
            output_string += self.gametimes[index - 1].set_time(new_time)
            return "{}\nGametime {} set to {}." \
                .format(output_string, index,
                        pretty_date(self.gametimes[index - 1].get_date()))
        else:
            return "There's no gametime with that number."

    def whos_in(self):
        """
        Depreciated function, now just calls get_gametimes()

        :rtype str
        :return: str: Formatted string for the list of people currently signed
        up for weekend games
        """

        return self.get_gametimes()

    def add(self, person, game_id, status):
        """
        Adds a person to the specified gametime

        :param status: Status to mark for player
        :param person: person to add
        :param game_id: list id of the gametime in gametimes
        :return: string to print to chat
        """
        try:
            game_id = int(game_id) - 1
        except ValueError:
            return "That's not a valid gametime."

        if game_id not in range(len(self.gametimes)):
            return "There's no gametime then."

        if type(person) is str:
            person_to_add = person
        else:
            person_to_add = str(person.display_name)

        game = self.gametimes[game_id]

        if game.find_player_by_name(person_to_add) and \
                status != game.get_player_status(person_to_add):
            game.unregister_player(person_to_add)

        if game.find_player_by_name(person_to_add):
            self.gametimes[game_id] = game
            return "You're already {} for that day.".format(
                game.get_player_status(person_to_add))
        else:
            game.register_player(person_to_add,
                                 status=status)
            self.gametimes[game_id] = game
            return '{} is {} for {}.'.format(person_to_add,
                                             game.get_player_status(
                                                 person_to_add),
                                             pretty_date(game.get_date()))

    def remove(self, person, game_id):
        """
        Removes a person from the weekend games list

        :param person: Person to remove
        :param game_id: The id of the game session
        :rtype str
        :return: str: Formatted string indicating whether a person was removed.
        """
        try:
            game_id = int(game_id) - 1
        except ValueError:
            return "That's not a valid gametime."

        if game_id not in range(len(self.gametimes)):
            return "There's no gametime then."

        if type(person) is str:
            person_to_remove = person
        else:
            person_to_remove = str(person.display_name)

        if self.gametimes[game_id].find_player_by_name(person_to_remove):
            self.gametimes[game_id].unregister_player(person_to_remove)
            return '{} is out for {}.' \
                .format(person_to_remove, pretty_date(self.gametimes[
                                                          game_id].get_date()))
        else:
            return '{} was never in for {}.' \
                .format(person_to_remove, pretty_date(self.gametimes[
                                                          game_id].get_date()))

    def update_db(self):
        """
        Updates the database to disk

        :return: None
        """

        common.db['people'] = self.people
        common.db['last_shot'] = self.last_shot
        common.db['consecutive_shot_wins'] = self.consecutive_shot_wins
        common.db['gametimes'] = []
        for gt in self.gametimes:
            common.db['gametimes'].append(gt.to_json())
        common.db['users'] = common.users
        common.db['c_win'] = self.c_win
        common.db['c_loss'] = self.c_loss
        common.db['c_draw'] = self.c_draw
        with open(common.db_file, 'w') as dbfile:
            json.dump(common.db, dbfile, sort_keys=True, indent=4,
                      ensure_ascii=False)

    def add_shot_win(self, name):
        """
        Adds a shot lottery win to the weekend games

        :param name: str Name of winner
        :rtype int
        :return: int: Number in a row
        """

        if self.last_shot == name:
            self.consecutive_shot_wins += 1
        else:
            self.last_shot = name
            self.consecutive_shot_wins = 1
        return self.consecutive_shot_wins

    def add_win(self):
        """
        Adds a win

        :return: None
        """

        self.wins += 1
        self.c_win += 1
        if self.last == "win":
            self.consecutive += 1
        else:
            self.last = "win"
            self.consecutive = 1

    def add_loss(self):
        """
        Adds a loss

        :return: None
        """

        self.losses += 1
        self.c_loss += 1
        if self.last == "loss":
            self.consecutive += 1
        else:
            self.last = "loss"
            self.consecutive = 1

    def add_draw(self):
        """
        Adds a draw

        :return: None
        """

        self.draws += 1
        self.c_draw += 1
        if self.last == "draw":
            self.consecutive += 1
        else:
            self.last = "draw"
            self.consecutive = 1

    def clear_record(self):
        """
        Adds a draw

        :return: None
        """

        self.draws = 0
        self.wins = 0
        self.losses = 0
        self.last = None
        self.consecutive = 0

    def get_record(self):
        """
        Gets the record of a session

        :return: str: With record formatting
        """

        return "{0} - {1} - {2}".format(self.wins, self.losses, self.draws)

    def get_c_record(self):
        """
        Gets the cumaltive record of a session

        :return: str: With record formatting
        """

        return "{0} - {1} - {2}".format(self.c_win, self.c_loss, self.c_draw)


def pretty_date(dt):
    """
    Takes a datetime and makes it a pretty string.
    :param dt:
    :return: string
    """
    return dt.strftime("%a, %b %d at %H:%M EST")
    # this version has the time, for the future:
    # return datetime.strftime("%a, %b %d at %I:%M %p")


def argument_parser(input_args):
    """
    Returns a list of tokens for a given argument
    :param input_args: input string
    :return: argument list
    """

    arguments = input_args.split(' ')
    if len(arguments) > 1:
        return arguments[1:]
    else:
        return arguments
