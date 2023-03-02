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

import random

import GeneticAlgorithm

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

class AiManager:

    # Constructor
    def __init__(self, publisher: Publisher):
        #print("Constructing AI Manager")
        self.ai_pub = publisher
        self.track_danger_levels = None
        self.blacklist = set()
        self.simulation_count = 0

        # initialize GeneticAlgorithm
        self.GA = GeneticAlgorithm()
        self.currentNN = 0 # index of position in list of NeuralNets in GeneticAlgorithm 

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

        pass

    #This method is responsible for training our genetic algorithm. It runs every NN in the population
    #Through some number of simulations, then calls cull(). 
    def train(self):
        self.GA.cull()

    def save_population(self):
        return None
    
    def load_population(self, filename):
        return None

    # This method/message is used to nofify that a scenario/run has ended
    def receiveScenarioConcludedNotificationPb(self, msg: ScenarioConcludedNotificationPb):
        # empty blacklist
        self.blacklist = set()
        self.GA.POPULATION[self.currentNN].setFitness(self.GA.POPULATION[self.currentNN].getFitness() + msg.score)
        self.currentNN += 1

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
        dship_idx = 0
        for defense_ship in msg.assets:
            input_vector[6 * dship_idx:6 * (dship_idx + 1)] = [defense_ship.health, defense_ship.weapons[0].Quantity, defense_ship.weapons[1].Quantity, 
                                                               defense_ship.PositionX, defense_ship.PositionY, int(defense_ship.isHVU)]
            dship_idx += 1
        
        targets = []
        target_idx = 0
        for target in msg.Tracks:
            if target.ThreatRelationship == "Hostile" and target.TrackId not in self.blacklist:
                input_vector[30 + 6 * target_idx: 30 + 6 * (1 + target_idx)] = [target.PositionX, target.PositionY, target.PositionZ, 
                                                                                target.VelocityX, target.VelocityY, target.VelocityZ]
                target_idx += 1
                targets.append(target)
        
        output = self.GA.POPULATION[self.currentNN].forward(input_vector)
        
        #Our output layer has 300 nodes
                # - 5 ships * 30 targets * 2 weapon types = 300
                # - Each node is the probability that ship x will target enemy y with weapon type z
        
        # map output to OutputPb
        final_output = []
        locations = torch.where(output > THRESHOLD) # find all values that are larger than our specified threshold
        for loc in locations:
            assignedWeaponType = loc % 2
            assignedTarget = (loc % 60) // 2
            assignedShip = (loc // 60)

            # mask output of NeuralNet to filter out impossible outputs
            if assignedTarget >= len(targets) or assignedShip > len(msg.assets):
                pass

            # dont consider this action if testing and the target is already in the blacklist
            if not self.training and targets[assignedTarget].TrackId in self.blacklist:
                pass

            # construct ship action
            ship_action: ShipActionPb = ShipActionPb()
            ship_action.TargetId = targets[assignedTarget].TrackId
            ship_action.AssetName = msg.assets[assignedShip + 1].AssetName # + 1 to ignore REFERENCE_SHIP
            ship_action.weapon = WEAPON_TYPES[assignedWeaponType]
            
            # add action to datasets
            final_output.append(ship_action)
            self.blacklist.add(targets[assignedTarget].TrackId)
    
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
