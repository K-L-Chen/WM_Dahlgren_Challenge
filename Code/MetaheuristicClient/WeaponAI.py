"""
The Weapon_AI class handles decision-making for a specific type of weapon. For example, since we have Chainshot
and Cannonball as the two types of weapon systems at our disposal, we would have a Weapon_AI object in charge of
Chainshot logic, and another in charge of Cannonball logic.

This class is analogous to the B-cell from the immunized classifier paper.
"""
import ActionRule
import pandas as pd


class WeaponAI:
    def __init__(self, weapon_type, filename=None):
        """
        The constructor for this class initializes action_set, defaulting to randomly generating the ActionRule objects
        contained within, but if a file is specified, it will fetch the information from a file and initialize them
        that way.

        @param weapon_type: The weapon type that this WeaponAI object is for (e.g. Chainshot or Cannonball), as a string.
        @param filename: Optional parameter for training with GA — the file where trained ActionRule are stored.
        """
        # TODO implement pandas csv create and parse

        self.type = weapon_type
        self.action_set = set()
        self.df = None

        if filename:
            self.df = pd.read_csv(filename)

        else:
            #self.my_actionrule = ActionRule()
            self.action_set.add(ActionRule())

    def request(self, weapon, ship, target):
        """
        Generates a strategy for a specific weapon, ship and target.

        Through this function, each weapon can make a request to the Weapon_AI object that corresponds to its
        weapon type. From its parameters, the request() function has access to the location, direction, threat-level,
        and type of target and the location/capabilities of the specific weapon, and will choose an appropriate subset
        of its ActionRule objects having conditionals that match the situation. It will return a set of tuples of the
        following format: ( weapon_system, ship, target, ActionRule ).

        @param weapon: The weapon requesting analysis
        @param ship: The ship that the weapon is on.
        @param target: The target (missile) that the weapon is currently considering.
        @return: set(( weapon_system, ship, target, ActionRule ))
        """

        print('requested')

    def save_rules(self, filename):
        """
        This function saves all ActionRules to a file named filename, overwriting that file if it already exists, and
        creating it if it does not.

        @param filename: The filename, as a string, where this function will save the ActionRules to.
        @return: None
        """

        # TODO Figure out the formatting for the file output
        self.df.to_csv(filename, sep='\n')
