# Imports
from Code.Planner.Example_Clients.MetaheuristicClient.ControlCenter import ControlCenter
from Code.Planner.Example_Clients.MetaheuristicClient.WeaponAI import WeaponAI
from PlannerProto_pb2 import ScenarioConcludedNotificationPb, \
    ScenarioInitializedNotificationPb  # Scenario start/end notifications
from PlannerProto_pb2 import ErrorPb  # Error messsage if scenario fails
from PlannerProto_pb2 import StatePb, AssetPb, TrackPb  # Simulation state information
from PlannerProto_pb2 import OutputPb, ShipActionPb, WeaponPb
from publisher import Publisher

import random
import utils

"""
This class contains the basic metaheuristic algorithm. Its has the required functionality 
# to receive data from the Planner and send actions back.

The word "receive" is protected in this class and should NOT be used in function names. 
"receive" is used to notify the subscriber that "this method wants to receive a proto message"

The second part of the function name is the type of proto message it wants to receive, thus proto
message names are also protected

Definitions/clarifications:

Threat: an incoming enemy missile starting from a random locations. There are no enemy ships. 
"""

WEAPON_TYPES = ["Cannon", "Chainshot"]
TRAINING = True


class AiManager:

    # Constructor
    def __init__(self, publisher: Publisher):
        print("Constructing AI Manager")
        self.ai_pub = publisher
        self.track_danger_levels = None
        self.blacklist = set()

        # make a new weapon A.I. object for each weapon_type
        # in this competition, WEAPON_TYPES = ["Cannon", "Chainshot"]
        self.weapon_AIs = dict()
        for weapon_type in WEAPON_TYPES:
            self.weapon_AIs[weapon_type] = WeaponAI(weapon_type)

        self.control_center = ControlCenter()

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
        print("Scenario run: " + str(msg.sessionId))

    # This method/message is used to nofify that a scenario/run has ended
    def receiveScenarioConcludedNotificationPb(self, msg: ScenarioConcludedNotificationPb):
        self.blacklist = set()
        print("Ended Run: " + str(msg.sessionId) + " with score: " + str(msg.score))

    def createActions(self, msg: StatePb):
        """
        Oversees the A.I. response and sends it back to the planner

        Parameters
        ----------
        msg: StatePb - data received from the planner, informing us of the state of the simulation
        
        Returns
        -------
        output_message: OutputPb with .actions: list[ShipAction] - list of A.I. actions from asset(s)
        """

        output_message: OutputPb = OutputPb()

        # As stated, shipActions go into the OutputPb as a list of ShipActionPbs
        # output_message.actions.append(ship_action)
        output_message.actions.extend(self.metaheuristic(msg))

        return output_message

    def metaheuristic(self, msg: StatePb):
        """
        This is the decision-making component of the meta-heuristic algorithm detailed in /Pseudocode/Algorithm.md
        """
        # create set of possible actions against target
        target_actions = list()

        for target in msg.Tracks:
            current_target_actions = set()
            for defense_ship in msg.assets:
                for weapon in defense_ship.weapons:
                    # get a set of proposed ( weapon, defense_ship, target ) tuples for the target
                    proposed_actions = self.weapon_AIs[weapon.SystemName].request(weapon, defense_ship, target)
                    target_actions.append(proposed_actions)
            target_actions.append(current_target_actions)

        # initialize and apply immune system dynamics to get the top Actions
        best_actions = ControlCenter.decide(target_actions)

        # execute the best actions to get a reward
        # reward = execute(best_actions)
        # TODO: execute the best actions, make it so this line is uncommented and implement the details

        if TRAINING:
            accuracy_sum = 0
            for action in best_actions:
                # accuracy_sum += action.update_predicted_values(reward)
                print("placeholder, uncomment the above line after finishing the above TODO")

            for action in best_actions:
                action.update_fitness(accuracy_sum)

            # do Genetic Algorithm OR Harmony Search here!
            # TODO: Implement GA, HS, or some other update to use here.

    # Helper methods for determining whether any weapons are left
    def weapons_are_available(self, assets: list[AssetPb]):
        for asset in assets:
            if self.weapons_in_asset(asset): return True
        return False

    def weapons_in_asset(self, asset: AssetPb):
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
