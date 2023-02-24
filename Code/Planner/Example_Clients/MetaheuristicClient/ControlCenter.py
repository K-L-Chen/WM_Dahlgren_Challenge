"""
The ControlCenter's role is to make overarching decisions, authorizing each weapon to fire at targets.
"""


class ControlCenter:
    def __init__(self):
        """
        Constructor for ControlCenter.
        """
        print("placeholder")

    def decide(self, proposed_actions):
        """
        This function takes a list of sets of all proposed (weapon_system, ship, target, ActionRule) tuples as an
        argument. Each element of the list will be a set of (weapon_system, ship, target, ActionRule) tuples that
        corresponds to a single target. Using this list, the ControlCenter decides on the best action to take for each
        target, and returns the selected actions as a list of (weapon_system, ship, target, ActionRule) tuples.

        @param proposed_actions: A list of sets of proposed (weapon_system, ship, target, ActionRule) tuples.
        @return: A list of accepted (weapon_system, ship, target, ActionRule) tuples.
        """
        return []
