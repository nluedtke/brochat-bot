# the gametime class, which represents an individual gaming session
import datetime
import pytz

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

    def __init__(self, day=None):
        """
        Creates a gametime on the next given day of the week.
        :param day:
        """
        self.timezone = pytz.timezone('US/Eastern')
        self.created = datetime.datetime.now(self.timezone)
        self.game = None
        """ Sets the time on the next available date for a given weekday. """
        self.time = self.next_date_for_day(self.created, day)
        self.snapshot = None
        self.players = []
        self.players_attended = []
        print("Gametime is: {}".format(self.time))

    class Player(object):
        """
        Defines the Gametime.Player class
        """

        def __init__(self, name=None, registered=None, arrived=None, record=None):
            """
            Gametime.Player constructor
            """
            self.name = name
            self.registered_time = registered
            self.arrived_time = arrived
            self.record = record

        def set_registered_time(self, time):
            self.registered_time = time

        def arrived(self, time):
            self.arrived_time = time

        def set_record(self, record):
            pass

    def next_date_for_day(self, created, day):
        """
        Finds the next datetime date for a given int day
        :param day:
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
        return self.time

    def start(self):
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
            if player.registered_time:
                output_string += "\n  {} shows up at {}"\
                                        .format(player.name,
                                                player.registered_time)
        output_string += "\n- Players Attended:"
        for player in self.players:
            if player.arrived_time:
                output_string += "\n  {} showed up at {}".format(player.name,
                                                                 player.arrived_time)
        output_string += "\n"
        for player in self.players:
            if player.registered_time and not player.arrived_time:
                output_string += "\nSorry, but it looks like {} lied about being here".format(player.name)

        return output_string

    def find_player_by_name(self, name):
        """
        Finds a player by name, if none found, returns None.
        :param name: string name
        :return: player or None
        """
        player_found = None
        for player in self.players:
            if player.name == name:
                player_found = player
        return player_found

    def register_player(self, name, time=None):
        """
        Registers a player, if applicable.
        :param name: string name
        :param time: datetime time of arrival, None is "sometime"
        :return: None
        """
        search_result = self.find_player_by_name(name)
        if not search_result:
            self.players.append(self.Player(name=name,registered=time))
        else:
            search_result.set_registered_time(time)

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
            search_result.arrived(arrival_time)

    pass

# Tests
if __name__ == "__main__":
    g = Gametime()
    print("Started: {}".format(g.created))
    #time.sleep(20)
    g.register_player("Jim", g.created)
    g.register_player("Nick", g.created)
    g.check_in_player("Nick")
    print("Status: {}".format(g.status()))
