#Imports
from PlannerProto_pb2 import ScenarioConcludedNotificationPb, ScenarioInitializedNotificationPb     #Scenario start/end notifications
from PlannerProto_pb2 import ErrorPb                                            #Error messsage if scenario fails
from PlannerProto_pb2 import StatePb, AssetPb, TrackPb                          #Simulation state information
from PlannerProto_pb2 import OutputPb, ShipActionPb,  WeaponPb
from publisher import Publisher

import random
import utils
import torch
import torch.optim as optim
import torch.nn as nn
import math  
import numpy as np

from DQN import DQN
from Memory import Memory
import Environment
from Environment import Environment

# This class is the center of action for this example client.  Its has the required functionality 
# to receive data from the Planner and send actions back.  Developed AIs can be written directly in here or
# this class could be used toolbox that a more complex AI classes reference.

# The word "receive" is protected in this class and should NOT be used in function names
# "receive" is used to notify the subscriber that "this method wants to receive a proto message"

# The second part of the function name is the type of proto message it wants to receive, thus proto
# message names are also protected


"""
Definitions/clarifications:

Threat: an incoming enemy missile starting from a random locations. There are no enemy ships. 
"""

# BATCH_SIZE is the number of transitions sampled from the replay buffer
# GAMMA is the discount factor as mentioned in the previous section
# EPS_START is the starting value of epsilon
# EPS_END is the final value of epsilon
# EPS_DECAY controls the rate of exponential decay of epsilon, higher means a slower decay
# TAU is the update rate of the target network
# LR is the learning rate of the AdamW optimizer
BATCH_SIZE = 128
GAMMA = 0.99
EPS_START = 0.9
EPS_END = 0.05
EPS_DECAY = 1000
TAU = 0.005
LR = 1e-4
WEAPON_TYPES = ["Cannon_System", "Chainshot_System"]

class AiManager:

    # Constructor
    def __init__(self, publisher:Publisher):
        print("Constructing AI Manager")
        self.ai_pub = publisher
        self.track_danger_levels = None
        self.blacklist = set()

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Get number of actions from current action space (n_actions)
        # Get the number of state observations (n_observations)

        # TODO — figure out what this means, implement it

        self.policy_net = DQN(Environment.N_OBSERVATIONS, Environment.N_ACTIONS).to(self.device)
        self.target_net = DQN(Environment.N_OBSERVATIONS, Environment.N_ACTIONS).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())

        self.optimizer = optim.AdamW(self.policy_net.parameters(), lr=LR, amsgrad=True)
        self.memory = Memory(10000) # use some arbitrary buffer size

        self.steps_done = 0

        self.asset_mapper = {}
   

    # Is passed StatePb from Planner
    def receiveStatePb(self, msg:StatePb):

        # Call function to print StatePb information
        # self.printStateInfo(msg)

        # Call function to show example of building an action
        output_message = self.createActions(msg)
        # print(output_message)

        # To advance in step mode, its required to return an OutputPb
        self.ai_pub.publish(output_message)
        #self.ai_pub.publish(OutputPb())

        
    # This method/message is used to notify of new scenarios/runs
    def receiveScenarioInitializedNotificationPb(self, msg:ScenarioInitializedNotificationPb):
        print("Scenario run: " + str(msg.sessionId))

        
    # This method/message is used to nofify that a scenario/run has ended
    def receiveScenarioConcludedNotificationPb(self, msg:ScenarioConcludedNotificationPb):
        self.blacklist = set()
        if msg.score != 10000:
            print("Ended Run: " + str(msg.sessionId) + " with score: " + str(msg.score))


    def createActions(self, msg:StatePb):
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
        output_message.actions.extend(self.reinforcement_strategy(msg))

        return output_message


    def reinforcement_strategy(self, msg:StatePb):
        """
        Epsilon Greedy Strategy 
        """
        global steps_done
        sample = random.random()
        eps_threshold = EPS_END + (EPS_START - EPS_END) * \
            math.exp(-1. * self.steps_done / EPS_DECAY) # calculate epsilon threshold
        self.steps_done += 1 # update steps done

        if sample > eps_threshold: # pick the best reward
            with torch.no_grad():
                # create state input vector to pass to policy_net
                input_vector = torch.Tensor(np.zeros(220))
                for defense_ship in msg.assets: # add defense ships to input_vector
                    if defense_ship.AssetName not in self.asset_mapper:
                        # asset_mapper guarantees that our assets appear in the same locations consistently
                        self.asset_mapper[defense_ship.AssetName] = len(self.asset_mapper) 
                    input_vector[6 * self.asset_mapper[defense_ship.AssetName]:6 * (self.asset_mapper[defense_ship.AssetName] + 1)] = [defense_ship.health, 
                                                                    defense_ship.weapons[0].Quantity, defense_ship.weapons[1].Quantity, 
                                                                    defense_ship.PositionX, defense_ship.PositionY, int(defense_ship.isHVU)]
                
                # missles need not appear in the same location every time, they just need to be considered. 
                enemy_targets = []
                etarget_idx = 0
                for target in msg.Tracks: # add targets to input_vector
                    if target.ThreatRelationship == "Hostile": #and target.TrackId not in self.blacklist:
                        input_vector[40 + 6 * etarget_idx: 40 + 6 * (1 + etarget_idx)] = [target.PositionX, target.PositionY, target.PositionZ, 
                                                                                        target.VelocityX, target.VelocityY, target.VelocityZ]
                        etarget_idx += 1
                        enemy_targets.append(target)

                # feed our input_vector into policy_net, then get the action with the largest value 
                max = self.policy_net(input_vector).max(1)[1].view(1, 1)

                assignedWeaponType = max % 2
                # mod 60 because 2 weapon types/enemy * 30 enemies; there are 60 total actions per ship
                # and we are stacking all the ships' actions sequentially
                # div 2 because node 0 and 1 are 1st target, node 2 and 3 are 2nd target, etc.
                assignedTarget = (max % 60) // 2
                # read explanation above, mod 60 gets us to specific index of a target, and
                # div 60 gets us to identify the ship
                assignedShip = max // 60

                # mask output of NeuralNet to filter out impossible outputs
                if assignedTarget >= len(enemy_targets) or assignedShip > len(msg.assets):
                    pass

                # dont consider this action if testing and the target is already in the blacklist
                if not self.training and enemy_targets[assignedTarget].TrackId in self.blacklist:
                    pass

                # construct ship action
                ship_action: ShipActionPb = ShipActionPb()
                ship_action.TargetId = assignedTarget
                # ship_action.TargetId = targets[assignedTarget].TrackId
                ship_action.AssetName = msg.assets[assignedShip + 1].AssetName # + 1 to ignore REFERENCE_SHIP
                ship_action.weapon = WEAPON_TYPES[assignedWeaponType]
                
                return [ship_action]
            
        else: # random
            return [self.generate_random_action(msg)]

    def generate_random_action(self, msg: StatePb):
        """
        Given a StatePb, generates a random ShipActionPb

        @param msg: The StatePb argument

        @return ship_action: A randomly generated, valid ShipActionPb object to be executed. 
        """
        # set up a data response to send later
        ship_action: ShipActionPb = ShipActionPb()

        # random target selection
        ship_action.TargetId = random.choice(msg.Tracks).TrackId             

        # random asset to launch weapon from
        rand_asset = random.choice(msg.assets)

        # reference ship does not count; it has no weapons anyway
        # our ship must also have at least one weapon available
        while rand_asset.AssetName == "Galleon_REFERENCE_SHIP" or \
            not self.weapons_in_asset(rand_asset):
            rand_asset = random.choice(msg.assets)

        ship_action.AssetName = rand_asset.AssetName

        # random weapon selection
        rand_weapon = random.choice(rand_asset.weapons)

        # randomly scurry around until we have an immediate weapon to launch
        while rand_weapon.Quantity == 0 or rand_weapon.WeaponState != "Ready":
            rand_weapon = random.choice(rand_asset.weapons)

        ship_action.weapon = rand_weapon.SystemName
        return ship_action

    def rl_update(self):
        """
        Run this function when the score gets updated (we get feedback)
        TODO — this entire function is sus....
        """

        # fetch memory values since last score update TODO — nail down format for this batch object
        batch = self.memory.sample()

        # Transpose the batch (see https://stackoverflow.com/a/19343/3343043 for
        # detailed explanation). This converts batch-array of Transitions
        # to Transition of batch-arrays.
        batch = Transition(*zip(*transitions))

        # Compute a mask of non-final states and concatenate the batch elements
        # (a final state would've been the one after which simulation ended)
        non_final_mask = torch.tensor(tuple(map(lambda s: s is not None,
                                            batch.next_state)), device=self.device, dtype=torch.bool)
        non_final_next_states = torch.cat([s for s in batch.next_state
                                                    if s is not None])
        state_batch = torch.cat(batch.state)
        action_batch = torch.cat(batch.action)
        reward_batch = torch.cat(batch.reward)

        # Compute Q(s_t, a) - the model computes Q(s_t), then we select the
        # columns of actions taken. These are the actions which would've been taken
        # for each batch state according to policy_net
        state_action_values = self.policy_net(state_batch).gather(1, action_batch)

        # Compute V(s_{t+1}) for all next states.
        # Expected values of actions for non_final_next_states are computed based
        # on the "older" target_net; selecting their best reward with max(1)[0].
        # This is merged based on the mask, such that we'll have either the expected
        # state value or 0 in case the state was final.
        next_state_values = torch.zeros(BATCH_SIZE, device=self.device)
        with torch.no_grad():
            next_state_values[non_final_mask] = self.target_net(non_final_next_states).max(1)[0]
        # Compute the expected Q values
        expected_state_action_values = (next_state_values * GAMMA) + reward_batch

        # Compute Huber loss
        criterion = nn.SmoothL1Loss()
        loss = criterion(state_action_values, expected_state_action_values.unsqueeze(1))

        # Optimize the model
        self.optimizer.zero_grad()
        loss.backward()
        # In-place gradient clipping
        torch.nn.utils.clip_grad_value_(self.policy_net.parameters(), 100)
        self.optimizer.step()
        
        
    # Helper methods for determining whether any weapons are left 
    def weapons_are_available(self, assets:list[AssetPb]):
        for asset in assets:
            if self.weapons_in_asset(asset): return True
        return False 

    
    def weapons_in_asset(self, asset:AssetPb):
        for weapon in asset.weapons:
            if weapon.Quantity > 0: return True
        return False

    
    # Function to print state information and provide syntax examples for accessing protobuf messags
    def printStateInfo(self, msg:StatePb):
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
