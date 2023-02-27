"""
The Weapon_AI class handles decision-making for a specific type of weapon. For example, since we have Chainshot
and Cannonball as the two types of weapon systems at our disposal, we would have a Weapon_AI object in charge of
Chainshot logic, and another in charge of Cannonball logic.

This class is analogous to the B-cell from the immunized classifier paper.
"""
from ActionRule import ActionRule, CONDITIONAL_NAMES, CONDITIONAL_ATTRIBUTE_COUNT
from PlannerProto_pb2 import AssetPb, TrackPb, WeaponPb, StatePb
import utils
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

        self.current_statePb = None
        self.blacklist = None
        # self.trackID_to_track = {}

        if filename:
            self.action_df = pd.read_csv(filename)
            self.action_set = set(ActionRule(bounds) for bounds in self.action_df.to_numpy())

        else:
            if init_policy_population is None:
                raise RuntimeError("Must specify `init_policy_population` parameter for WeaponAI constructor")

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
            Kevin: Aren't we returning a set of tuples here?
        (hostile TrackId and in ShipActionPb)
        """
        # if target not in self.trackID_to_track:
        #     self.trackID_to_track[target.TrackID] = target

        proposed_actions = []
        for action_rule in self.action_set:
            if self.evaluate(weapon, ship, target, action_rule):
                proposed_actions.append((weapon, ship, action_rule))
        return proposed_actions

    #
    # def get_trackID_to_track(self):
    #     """
    #     @return: trackID_to_track: dict[int]: TrackPb to map each TrackId to its corresponding TrackPb object
    #     """
    #     return self.trackID_to_track
    #
    # def clear_trackID_to_track(self):
    #     """
    #     Resets the class variable trackID_to_track
    #
    #     @return: None
    #     """
    #     self.trackID_to_track = {}

    def evaluate(self, weapon: WeaponPb, ship: AssetPb, target: TrackPb, action_rule: ActionRule) -> bool:
        """
        Given an input situation and an ActionRule, evaluates the ActionRule to see if it fits the scenario.

        @param weapon: The weapon requesting analysis
        @param ship: The ship that the weapon is on.
        @param target: The target (missile) that the weapon is currently considering.
        @param action_rule: The ActionRule we are considering for this situation

        @return: The evaluated boolean truth value of the ActionRule, given the scenario
        """
        calculated_conditional_list = [self.calc_distance_to_target(ship, target),
                                       self.calc_target_speed(target),
                                       self.calc_target_heading(ship, target),
                                       self.calc_target_height(target),
                                       self.calc_ship_compassion(target),
                                       self.ammo_on_ship(weapon),
                                       self.calc_nearby_ship_health(ship),
                                       self.calc_my_ship_health(ship),
                                       self.calc_number_of_targets()]
        conditional_bits = action_rule.get_conditional_attributes()
        conditional_cutoffs = action_rule.get_conditional_values()

        return_val = True
        for idx in range(CONDITIONAL_ATTRIBUTE_COUNT):
            and_or_or = conditional_bits & 1
            conditional_bits = conditional_bits >> 1
            le_or_ge = conditional_bits & 1
            conditional_bits = conditional_bits >> 1

            current_truth = False
            if le_or_ge:
                current_truth = (calculated_conditional_list[idx] > conditional_cutoffs[idx])
            else:
                current_truth = (calculated_conditional_list[idx] <= conditional_cutoffs[idx])

            if and_or_or:
                return_val = return_val or current_truth
            else:
                return_val = return_val and current_truth

        return return_val

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

    def set_state_info(self, state_pb: StatePb, blacklist: set) -> None:
        """
        Use this function to give this WeaponAI access to the current StatePb and blacklist.

        @param state_pb: The StatePb at the current timestep
        @param blacklist: The blacklist at the current timestep

        @return: None
        """
        self.current_statePb = state_pb
        self.blacklist = blacklist

    def calc_distance_to_target(self, ship: AssetPb, target: TrackPb) -> float:
        """
        Calculates the squared distance from a ship to a target
        @param ship: The ship
        @param target: The target
        @return: the distance from a ship to a target
        """
        return utils.distance(ship.PositionX, ship.PositionY, ship.PositionZ, target.PositionX, target.PositionY,
                              target.PositionZ)

    def calc_target_speed(self, target: TrackPb) -> float:
        """
        Returns the target's squared speed
        @param target: The target
        @return: Squared speed of the target
        """
        return utils.magnitude(target.VelocityX, target.VelocityY, target.VelocityZ)

    def calc_target_heading(self, ship: AssetPb, target: TrackPb) -> float:
        """
        Given the ship and the target, returns the difference between the target's heading and the ship's heading,
        in radians.

        @param ship: The ship
        @param target: The target

        @return: The difference between the target's heading and the ship's heading, in radians.
        """
        return np.arccos(utils.dot(ship.PositionX, ship.PositionY, ship.PositionZ, target.PositionX, target.PositionY,
                                   target.PositionZ) / (utils.magnitude(target.VelocityX, target.VelocityY,
                                                                        target.VelocityZ) * utils.magnitude(
            ship.PositionX - target.PositionX, ship.PositionY - target.PositionY, ship.PositionZ - target
            .PositionZ)))

    def calc_ship_compassion(self, target: TrackPb) -> float:
        """
        Given the target, and the current state, computes the ship compassion for the target

        Ship compassion = {sum over all ships} (max distance - distance to ship) (4 if HVU 1 if NU)

        @param ship: The ship
        @param target: The target
        @return: The ship compassion for this current weapon
        """
        ship_compassion = 0
        for asset in self.current_statePb.assets:
            ship_compassion += utils.DISTANCE_SCALE * (
                    utils.MAX_DISTANCE - utils.distance(target.PositionX, target.PositionY, target.PositionZ,
                                                        asset.PositionX, asset.PositionY, asset.PositionZ)) * (
                                   4 if asset.isHVU else 1)
        return ship_compassion

    def calc_target_height(self, target: TrackPb) -> float:
        """
        Given the target, returns its height above the water.

        @param target: The target
        @return: The height of the target above the water.
        """
        return target.PositionZ

    def calc_nearby_ship_health(self, ship: AssetPb) -> float:
        """
        Calculates a sum of the health values of nearby ships to the weapon, weighted by distance.

        @param ship: The ship

        @return: sum of the health values of nearby ships, weighted by distance.
        """
        w_ship_health = 0
        for asset in self.current_statePb.assets:
            w_ship_health += utils.DISTANCE_SCALE * (
                    utils.MAX_DISTANCE - utils.distance(ship.PositionX, ship.PositionY, ship.PositionZ,
                                                        asset.PositionX, asset.PositionY, asset.PositionZ)) * (
                                 asset.health)
        return w_ship_health

    def calc_my_ship_health(self, ship: AssetPb) -> int:
        """
        Returns this ship's health

        @param ship: The ship

        @return: returns this ship's health
        """
        return ship.health

    def calc_number_of_targets(self) -> int:
        """
        Calculates the number of enemy missiles in StatePb

        @return: the number of enemy missiles in StatePb
        """
        count = 0
        for track in self.current_statePb.Tracks:
            if track.ThreatRelationship == "Hostile" and track.TrackId not in self.blacklist:
                count += 1
        return count

    def ammo_on_ship(self, weapon: WeaponPb) -> int:
        """
        Returns the quantity of ammunition remaining for this weapon type on the ship

        @param weapon:
        @param ship:
        @return: the amount of ammunition remaining for this weapon type on this ship
        """
        return weapon.Quantity
