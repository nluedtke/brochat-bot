# the gametime class, which represents an individual gaming session
import datetime
import pytz
import re


class Gametime(object):
    """
    Defines the Gametime class
    """

    DAYS_IN_WEEK = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday"
    ]

    DEFAULT_GAMETIME = "12:00"

    def __init__(self, day=None, time=DEFAULT_GAMETIME, json_create=None):
        """
        Creates a gametime on the next given day of the week.

        :param json_create
        :param time:
        :param day:
        """
        if json_create:
            self.timezone = pytz.timezone(json_create['timezone'])
            self.created = datetime.datetime.strptime(json_create['created'],
                                                      "%c")
            self.game = json_create['game']
            self.date = datetime.datetime.strptime(json_create['date'], "%c")
            self.date = self.date.replace(tzinfo=self.timezone)
            self.time = json_create['time']
            self.snapshot = json_create['snapshot']
            self.players = json_create['players']
        else:
            self.timezone = pytz.timezone('US/Eastern')
            self.created = datetime.datetime.now(self.timezone)
            self.game = None
            # Sets the time on the next available date for a given weekday.
            self.date = self.next_date_for_day(self.created, day)
            """ Sets the """
            if time:
                self.time = self.set_time(time)
            else:
                self.time = self.set_time(Gametime.DEFAULT_GAMETIME)
            self.snapshot = None
            self.players = []
        print("Gametime is: {}".format(self.date))

    def to_json(self):
        """
        Dumps the class contents to json.

        :return:
        """
        json_info = {
            "timezone": str(self.timezone),
            "created": datetime.datetime.strftime(self.created, "%c"),
            "game": self.game,
            "date": datetime.datetime.strftime(self.date, "%c"),
            "time": self.time,
            "snapshot": self.snapshot,
            "players": self.players
        }
        return json_info

    def next_date_for_day(self, created, day):
        """
        Finds the next datetime date for a given int day

        :param day:
        :param created:
        :return: datetime
        """
        for increment in range(7):
            if created.weekday() == int(day):
                return created
            created += datetime.timedelta(days=1)

    def get_date(self):
        """
        Gets time of a gametime.

        :return: datetime object
        """
        return self.date

    def set_time(self, time_string):
        """
        Sets the time of day of a gametime.

        :param time_string: A string representation of HH:MM or H:MM
        :return: String of result.
        """
        """ Regex match for H:MM or HH:MM time formats. """
        date_format = re.compile("^\d?\d:\d\d$")
        if date_format.match(time_string):
            time_list = time_string.split(":")
        else:
            return "Sorry, that's not a valid time format!"

        hour = int(time_list[0])
        minute = int(time_list[1])

        if hour not in range(24) or minute not in range(60):
            return "Please use a valid military time, to keep things simple."

        self.date = self.date.replace(hour=hour, minute=minute)
        return "Time set"

    def start(self):
        """

        :return:
        """
        pass

    def status(self):
        """
        Returns the status of the Gametime object

        :return: A status string
        """
        now = datetime.datetime.now(self.timezone)
        time_elapsed = now - self.created

        output_string = "\n- Session Length: {}".format(time_elapsed)

        output_string += "\n- Players Registered:"
        for player in self.players:
            if player['time']:
                output_string += "\n  {} shows up at {}"\
                                        .format(player['name'],
                                                player['time'])
        output_string += "\n- Players Attended:"
        for player in self.players:
            if player['arrived_time']:
                output_string += "\n  {} showed up at {}".\
                    format(player['name'], player['arrived_time'])
        output_string += "\n"
        for player in self.players:
            if player['time'] and not player['arrived_time']:
                output_string += "\nSorry, but it looks like {} lied about " \
                                 "being here".format(player['name'])

        return output_string

    def find_player_by_name(self, name):
        """
        Finds a player by name, if none found, returns None.

        :param name: string name
        :return: player or None
        """
        for player in self.players:
            if name == player['name']:
                return player
        return None

    def register_player(self, name, time=None, status=None):
        """
        Registers a player, if applicable.
        :param status:
        :param name: string name
        :param time: datetime time of arrival, None is "sometime"
        :return: None
        """
        search_result = self.find_player_by_name(name)
        if not search_result:
            self.players.append({"name": name,
                                 "time": time,
                                 "arrived_time": None,
                                 "status": status})
        else:
            for player in self.players:
                if name in player:
                    player["time"] = time

    def get_player_status(self, name):
        """
        Returns a players status for this gametime.
        :param name:
        :return: status string, default to "in"
        """

        search_result = self.find_player_by_name(name)
        if not search_result:
            raise Exception("Player not found!")
        else:
            try:
                return search_result["status"]
            except KeyError:
                return "in"

    def unregister_player(self, name):
        """
        Unregisters a player

        :param name: string name
        :return: None
        """
        search_result = self.find_player_by_name(name)
        if search_result:
            self.players.remove(search_result)

    def check_in_player(self, name):
        """
        Checks in a player

        :param name: string name
        :return: None
        """
        search_result = self.find_player_by_name(name)
        arrival_time = datetime.datetime.now(self.timezone)
        if not search_result:
            print("player not found")
        else:
            for player in self.players:
                if player['name'] == name:
                    player['arrived_time'] = arrival_time

    def __eq__(self, other):
        """
        Equal to override
        NOTE: This override == to compare value not pointers.
        :param other: Right hand side comparison
        :return: bool indicating whether self equal to other (In value)
        """

        if self.date.weekday() == other.date.weekday() and \
           self.time == other.time:
            return True
        else:
            return False

# Tests
if __name__ == "__main__":
    g = Gametime(3)
    print("Started: {}".format(g.created))
    # time.sleep(20)
    g.register_player("Jim", g.created)
    g.register_player("Jim", g.created)
    g.register_player("Nick", g.created)
    g.check_in_player("Nick")
    print("Status: {}".format(g.status()))

    g.set_time("12:00")
    g.set_time("taco")

    print(g.to_json())
