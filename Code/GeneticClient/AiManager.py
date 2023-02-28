# Imports
from ControlCenter import ControlCenter
from WeaponAI import WeaponAI
from PlannerProto_pb2 import ScenarioConcludedNotificationPb, \
    ScenarioInitializedNotificationPb  # Scenario start/end notifications
from PlannerProto_pb2 import ErrorPb  # Error messsage if scenario fails
from PlannerProto_pb2 import StatePb, AssetPb, TrackPb  # Simulation state information
from PlannerProto_pb2 import OutputPb, ShipActionPb, WeaponPb
from publisher import Publisher

"""
These libraries are not being used, since we pretty much have already implemented
everything so far througto take advantage of the functionality of these two libraries.

from pyharmonysearch import harmony_search
import pygad
"""

import random
import utils

"""
This class contains the basic genetic algorithm. Its has the required functionality 
# to receive data from the Planner and send actions back.

The word "receive" is protected in this class and should NOT be used in function names. 
"receive" is used to notify the subscriber that "this method wants to receive a proto message"

The second part of the function name is the type of proto message it wants to receive, thus proto
message names are also protected

Definitions/clarifications:

Threat: an incoming enemy missile starting from a random locations. There are no enemy ships. 
"""

WEAPON_TYPES = ["Cannon_System", "Chainshot_System"]
TRAINING = True
POPULATION_SIZE = 100


class AiManager:

    # Constructor
    def __init__(self, publisher: Publisher):
        print("Constructing AI Manager")
        self.ai_pub = publisher
        self.track_danger_levels = None
        self.blacklist = set()

        # add swap var to let us swap from GA to HS
        self.swap = 0

        # make a new weapon A.I. object for each weapon_type
        # in this competition, WEAPON_TYPES = ["Cannon", "Chainshot"]
        self.weapon_AIs = dict()
        for weapon_type in WEAPON_TYPES:
            self.weapon_AIs[weapon_type] = WeaponAI(weapon_type=weapon_type, init_policy_population=POPULATION_SIZE)

        self.control_center = ControlCenter()

        # to keep track of all actions that were executed this round
        self.actions_executed_this_round = set()

    # Is passed StatePb from Planner
    def receiveStatePb(self, msg: StatePb):

        # Call function to print StatePb information
        # self.printStateInfo(msg)

        # Call function to show example of building an action
        output_message = self.createActions(msg)
        # print(output_message)

        # To advance in step mode, its required to return an OutputPb
        self.ai_pub.publish(output_message)
        # self.ai_pub.publish(OutputPb())

    # This method/message is used to notify of new scenarios/runs
    def receiveScenarioInitializedNotificationPb(self, msg: ScenarioInitializedNotificationPb):
        # empty the set of the weapons executed this round
        self.actions_executed_this_round = set()          

        print("Scenario run: " + str(msg.sessionId))


    # This method/message is used to nofify that a scenario/run has ended
    def receiveScenarioConcludedNotificationPb(self, msg: ScenarioConcludedNotificationPb):
        self.blacklist = set()
        self.training_update(msg.score)
        print("Ended Run: " + str(msg.sessionId) + " with score: " + str(msg.score))


    def createActions(self, msg: StatePb) -> OutputPb:
        """
        Oversees the A.I. response and sends it back to the planner

        Parameters
        ----------
        msg: StatePb - data received from the planner, informing us of the state of the simulation
        
        Returns
        -------
        output_message: OutputPb with actions: list[ShipAction] - list of A.I. actions from asset(s)
        """

        output_message: OutputPb = OutputPb()

        # As stated, shipActions go into the OutputPb as a list of ShipActionPbs
        # output_message.actions.append(ship_action)
        output_message.actions.extend(self.engage_targets(msg))

        return output_message


    def engage_targets(self, msg: StatePb) -> list[ShipActionPb]:
        """
        This method assigns weapons to all targets by:
        1. seeing which subset of potential weapon assignments apply to the situation at this timestep
        2. filtering out redundancies by choosing the best weapon assignment per target, based on genetic fitness
        3. sending an official assignment response back to the Planner

        @param msg: the current timestep situation containing info. about enemy missiles, ship assets, current time,
        and score

        @return: finalized_actions: list[ShipActionPb]
        """
        # let the WeaponAIs know what the current situation is
        for wai in self.weapon_AIs:
            self.weapon_AIs[wai].set_state_info(msg, self.blacklist)

        # create set of possible actions against target
        target_actions = dict()

        trackid_to_track = dict()

        for target in msg.Tracks:
            if target.ThreatRelationship == "Hostile" and target.TrackId not in self.blacklist:
                trackid_to_track[target.TrackId] = target
                current_target_actions = []

                for defense_ship in msg.assets:
                    for weapon in defense_ship.weapons:
                        # get a set of proposed ( weapon, defense_ship, action_rule_that_applies ) tuples for the target
                        proposed_actions = self.weapon_AIs[weapon.SystemName].request(weapon, defense_ship, target)
                        current_target_actions.extend(proposed_actions)

                target_actions[target.TrackId] = current_target_actions

        # initialize and apply immune system dynamics to get the top Actions
        self.control_center.decide_action_per_target(target_actions, trackid_to_track)

        # execute the best actions
        finalized_actions = []
        for target_id, target_action in target_actions.items():
            if target_action is not None:
                # add to the action rules executed this round
                self.actions_executed_this_round.add(target_action[2])

                # add track to blacklist so we don't consider it anymore
                self.blacklist.add(target_id)

                # construct a singular ship_action
                ship_action: ShipActionPb = ShipActionPb()
                ship_action.TargetId = target_id 
                ship_action.AssetName = target_action[1].AssetName
                ship_action.weapon = target_action[0].SystemName

                finalized_actions.append(ship_action)

        return finalized_actions


    def training_update(self, reward: int):
        """
        Updates ActionRule fitness values and does training/updates on the ActionRules using either GA or HS
        @param reward: the final score received after a scenario has concluded
        @return: None
        """

        # update fitness values

        # accuracy_sum = 0
        for action_rule in self.actions_executed_this_round:
            # accuracy_sum += action.update_predicted_values(reward)
            action_rule.update_predicted_values(reward, step = 1e-5)
            print("placeholder, uncomment the above line after finishing the above TODO")

        # for action in best_actions:
        #     action.update_fitness(accuracy_sum)

        # do Genetic Algorithm OR Harmony Search here!
        # TODO: Implement GA, HS, or some other update to use here.
        # we can read rate of change between our steps to swap between algorithms
        # or do a cutoff
        # use a global flag var? remember this code runs every step

        if self.swap:
            # TODO run harmony search
            pass
        else:
            # TODO run genetic algorithm
            pass

            cur_step, prev_step = 0, 0
            step_size = 1.0
            rate_of_change = (cur_step - prev_step) / step_size

            # swap flag based on genetic algorithm rate of change
            if rate_of_change < 5:
                # TODO set swap flag
                pass

    # Helper methods for determining whether any weapons are left
    def weapons_are_available(self, assets: list[AssetPb]) -> bool:
        for asset in assets:
            if self.weapons_in_asset(asset): return True
        return False

    def weapons_in_asset(self, asset: AssetPb) -> bool:
        for weapon in asset.weapons:
            if weapon.Quantity > 0: return True
        return False

    # Function to print state information and provide syntax examples for accessing protobuf messags
    def printStateInfo(self, msg: StatePb):
        print("Time: " + str(msg.time))
        print("Score: " + str(msg.score))

        # Accessing asset fields.  Notice that is is simply the exact name as seen 
        # In PlannerProto.proto
        print("Assets:")
        for asset in msg.assets:
            print("1: " + str(asset.AssetName))
            print("2: " + str(asset.isHVU))
            print("3: " + str(asset.health))
            print("4: " + str(asset.PositionX))
            print("5: " + str(asset.PositionY))
            print("6: " + str(asset.PositionZ))
            print("7: " + str(asset.Lle))
            print("8: " + str(asset.weapons))
        print("--------------------")

        # Accessing track information is done the same way.  
        print("Tracks:")
        for track in msg.Tracks:
            print("1: " + str(track.TrackId))
            print("2: " + str(track.ThreatId))
            print("3 " + str(track.ThreatRelationship))
            print("4: " + str(track.Lle))
            print("5: " + str(track.PositionX))
            print("6: " + str(track.PositionY))
            print("7: " + str(track.PositionZ))
            print("8: " + str(track.VelocityX))
            print("9 " + str(track.VelocityY))
            print("10: " + str(track.VelocityZ))
        print("**********************************")
