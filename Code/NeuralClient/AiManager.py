# Imports
from PlannerProto_pb2 import ScenarioConcludedNotificationPb, \
    ScenarioInitializedNotificationPb  # Scenario start/end notifications
from PlannerProto_pb2 import ErrorPb  # Error messsage if scenario fails
from PlannerProto_pb2 import StatePb, AssetPb, TrackPb  # Simulation state information
from PlannerProto_pb2 import OutputPb, ShipActionPb, WeaponPb
from scipy.special import softmax
from publisher import Publisher

import numpy as np
from numpy import ndarray
import torch
from collections import OrderedDict
# import random

from GeneticAlgorithmClass import GeneticAlgorithm
from GeneticAlgorithmClass import POPULATION_SIZE

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

THRESHOLD = .3
WEAPON_TYPES = ["Cannon_System", "Chainshot_System"]
GENERATION_SIZE = POPULATION_SIZE
FITNESS_SCALE = 1e-5

class AiManager:

    # Constructor
    def __init__(self, publisher: Publisher):
        #print("Constructing AI Manager")
        self.ai_pub = publisher
        self.track_danger_levels = None
        self.blacklist = set()
        self.simulation_count = 0
        self.generations_passed = 0

        # initialize GeneticAlgorithm
        self.GA = GeneticAlgorithm()
        self.currentNN = 0 # index of position in list of NeuralNets in GeneticAlgorithm

        # helper mapper for input of neural net in order for it to know
        # which ship is which in its input nodes;
        # by default, you may not be able to get the 
        # same ordering of assets each time you loop in msg.assets
        self.assetName_to_NNidx: dict[str, int] = {}
        self.setAssetName_to_NNidx = True 

        # serves same purpose as above but for threats
        self.threatTrackId_to_NNidx: OrderedDict = OrderedDict()
        self.ttId_to_NNidx_counter = 0

        self.training = True


    # Is passed StatePb from Planner
    def receiveStatePb(self, msg: StatePb):
        # self.printStateInfo(msg)

        # Call function to show example of building an action
        output_message = self.createActions(msg)
        # print(output_message)

        # To advance in step mode, its required to return an OutputPb
        self.ai_pub.publish(output_message)

    # This method/message is used to notify of new scenarios/runs
    def receiveScenarioInitializedNotificationPb(self, msg: ScenarioInitializedNotificationPb):
        """
        Each scenario should have its own GeneticAlgorithm. 
        """
        self.simulation_count += 1
        self.setAssetName_to_NNidx = True
        pass

    def save_population(self, filename:str):
        self.GA.save_population(filename)
        
    
    def load_population(self, filename):
        self.GA.set_population(filename)
    
    # ran at the first timestep for the entire simulation
    # to help the neural network preserve its ordering on
    # which ship is which
    def populate_assetName_to_NNidx(self, assets: list[AssetPb]):
        i = 0 
        for asset in assets:
            if 'REFERENCE' not in asset.AssetName:
                self.assetName_to_NNidx[asset.AssetName] = i
                i += 1

    # This method/message is used to nofify that a scenario/run has ended
    def receiveScenarioConcludedNotificationPb(self, msg: ScenarioConcludedNotificationPb):

        self.blacklist = set()
        
        self.currentNN += 1
        # empty blacklist
        if self.currentNN == GENERATION_SIZE:
            self.save_population("population.pt")
            self.GA.cull_and_rebuild() 
            self.generations_passed = self.generations_passed + 1
            print("Generations Passed: " + str(self.generations_passed))
            self.currentNN = 0
        else:
            self.GA.population[self.currentNN].set_fitness(self.GA.population[self.currentNN].get_fitness() + FITNESS_SCALE * msg.score)

        self.setAssetName_to_NNidx = True 
        self.assetName_to_NNidx: dict[str, int] = {}
        self.threatTrackId_to_NNidx: OrderedDict = OrderedDict()
        self.ttId_to_NNidx_counter = 0


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
        if self.setAssetName_to_NNidx:
            self.populate_assetName_to_NNidx(msg.assets)
            self.setAssetName_to_NNidx = False

        output_message: OutputPb = OutputPb()

        # As stated, shipActions go into the OutputPb as a list of ShipActionPbs
        # output_message.actions.append(ship_action)
        '''filedescriptor = open("log.txt", "w+")
        filedescriptor.write("createActions called\n")
        filedescriptor.close()'''

        output_message.actions.extend(self.engage_targets(msg))

        return output_message


    def engage_targets(self, msg: StatePb) -> list[ShipActionPb]:
        """
        This method uses forward prop in the current NeuralNetwork to make decisions. 

        @param msg: the current timestep situation containing info. about enemy missiles, ship assets, current time,
        and score

        @return: finalized_actions: list[ShipActionPb]
        """

        # evaluate neural net 
        """
        - We have up to 5 ships, each having:
                - Health (up to 4)
                - Ammo for Cannon_System
                - Ammo for Chainshot_System
                - x position
                - y position
                - whether ship is high value (HVU) or not
            - We have up to 30 missiles, each having:
                - x position
                - y position
                - z position
                - x velocity
                - y velocity
                - z velocity
        """

        # assemble input vector and indexed targets object
        input_vector = np.zeros(210)
        # dship_idx = 0

        ship_weaponType_to_ammo = OrderedDict()

        for weapon_system_name in WEAPON_TYPES:
            ship_weaponType_to_ammo[weapon_system_name] = 0

        for defense_ship in msg.assets:
            if 'REFERENCE' not in defense_ship.AssetName:
                # get the ammo for this specific ship
                for weapon in defense_ship.weapons:
                    ship_weaponType_to_ammo[weapon.SystemName] += 1
                
                # helps preserve order of ship nodes in input of neural net
                dship_idx = self.assetName_to_NNidx[defense_ship.AssetName]
                
                input_vector[6 * dship_idx:6 * (dship_idx + 1)] = [defense_ship.health, *list(ship_weaponType_to_ammo.values()), 
                                                                defense_ship.PositionX, defense_ship.PositionY, int(defense_ship.isHVU)]
                # clear out to properly count for the next ship
                for weapon_sys_name in ship_weaponType_to_ammo:
                    ship_weaponType_to_ammo[weapon_sys_name] = 0
                # dship_idx += 1
            
        # targets = []
        # target_idx = 0
        for target in msg.Tracks:
            if target.ThreatRelationship == "Hostile" and target.TrackId not in self.blacklist:
                # want to make one-to-one mapping between hostile TrackId and neural net idx
                if target.TrackId not in self.threatTrackId_to_NNidx:
                    self.threatTrackId_to_NNidx[target.TrackId] = self.ttId_to_NNidx_counter
                    self.ttId_to_NNidx_counter += 1

                target_idx = self.threatTrackId_to_NNidx[target.TrackId]
                input_vector[30 + 6 * target_idx: 30 + 6 * (1 + target_idx)] = [target.PositionX, target.PositionY, target.PositionZ, 
                                                                                target.VelocityX, target.VelocityY, target.VelocityZ]
                # target_idx += 1
                # targets.append(target)
        
        output = self.GA.population[self.currentNN].forward(torch.Tensor(input_vector))
        
        #Our output layer has 300 nodes
                # - 5 ships * 30 targets * 2 weapon types = 300
                # - Each node is the probability that ship x will target enemy y with weapon type z
        
        # map output to OutputPb
        final_output = []
        locations = torch.nonzero(output > THRESHOLD) # find all values that are larger than our specified threshold

        for loc in locations:
            # convert Tensor of one value to the integer it contains
            loc = int(loc)
            assignedWeaponType = loc % 2
            # mod 60 because 2 weapon types/enemy * 30 enemies; there are 60 total actions per ship
            # and we are stacking all the ships' actions sequentially
            # div 2 because node 0 and 1 are 1st target, node 2 and 3 are 2nd target, etc.
            assignedTarget = (loc % 60) // 2
            # read explanation above, mod 60 gets us to specific index of a target, and
            # div 60 gets us to identify the ship
            assignedShip = loc // 60

            # mask output of NeuralNet to filter out impossible outputs
            # if assignedTarget >= len(targets) or assignedShip > len(msg.assets):
            if assignedTarget not in self.threatTrackId_to_NNidx or \
                assignedShip not in self.assetName_to_NNidx:
                # TODO this
                continue

            # dont consider this action if testing or the target is already in the blacklist
            # if not self.training and targets[assignedTarget].TrackId in self.blacklist:
            if not self.training or assignedTarget in self.blacklist:
                continue

            # construct ship action
            ship_action: ShipActionPb = ShipActionPb()
            if assignedTarget in self.threatTrackId_to_NNidx and assignedShip in self.assetName_to_NNidx.values():
                ship_action.TargetId = assignedTarget
                # ship_action.TargetId = targets[assignedTarget].TrackId
                ship_action.AssetName = msg.assets[assignedShip + 1].AssetName # + 1 to ignore REFERENCE_SHIP
                ship_action.weapon = WEAPON_TYPES[assignedWeaponType]
            
                # add action to datasets
                final_output.append(ship_action)
                # self.blacklist.add(targets[assignedTarget].TrackId)
                self.blacklist.add(assignedTarget)
    
        return final_output
    
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
