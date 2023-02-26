"""
The Weapon_AI class handles decision-making for a specific type of weapon. For example, since we have Chainshot
and Cannonball as the two types of weapon systems at our disposal, we would have a Weapon_AI object in charge of
Chainshot logic, and another in charge of Cannonball logic.

This class is analogous to the B-cell from the immunized classifier paper.
"""
from ActionRule import ActionRule, CONDITIONAL_NAMES
from PlannerProto_pb2 import AssetPb, TrackPb, WeaponPb
import pandas as pd
import numpy as np


class WeaponAI:
    def __init__(self, weapon_type: str, filename: str = None, init_policy_population: int = None):
        """
        The constructor for this class initializes action_set, defaulting to randomly generating the ActionRule objects
        contained within, but if a file is specified, it will fetch the information from a file and initialize them
        that way.

        @param weapon_type: The weapon type that this WeaponAI object is for (e.g. Chainshot or Cannonball)
        @param filename: Optional parameter for training with GA — the file where trained ActionRule are stored.
        @param init_policy_population: if no filename, then the starting number of action rules
        """
        # TODO implement pandas csv create and parse

        self.type = weapon_type
        self.action_set = None  # set[ActionRule]
        self.action_df = None  # Pandas dataframe representing action set

        if filename:
            self.action_df = pd.read_csv(filename)
            self.action_set = set(ActionRule(bounds) for bounds in self.action_df.to_numpy())

        else:
            self.action_set = set(ActionRule() for _ in range(init_policy_population))
            self.action_df = pd.DataFrame(
                data=[np.append(a.conditional_vals, a.conditional_bits) for a in self.action_set],
                columns=CONDITIONAL_NAMES + ['cond_bits']
            )

    def request(self, weapon: WeaponPb, ship: AssetPb, target: TrackPb):
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

        @return: 
        1. proposed_actions: list[ set[ tuple[weapon_system, ship, ActionRule] ] ]
        2. idx_to_targetId: list[int] to map each idx. of proposed_actions to its TargetId 
        (hostile TrackId and in ShipActionPb)
        """

        print('requested')

    def save_rules(self, filename):
        # Joseph: Hmmm I have questions about this method being here
        # because we should be updating the set of rules during the genetic update;
        # this class only exists to select the best actions and does not perform mutation/crossover
        # to produce a new set of rules.
        """
        This function saves all ActionRules to a file named filename, overwriting that file if it already exists, and
        creating it if it does not.

        @param filename: The filename, as a string, where this function will save the ActionRules to.
        @return: None
        """

        # TODO Figure out the formatting for the file output
        self.action_df.to_csv(filename, sep='\n')
