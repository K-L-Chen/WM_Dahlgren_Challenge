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
from Memory import Transition
from collections import OrderedDict
from datetime import datetime as dt

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

# GAMMA is the discount factor
# EPS_START is the starting value of epsilon
# EPS_END is the final value of epsilon
# EPS_DECAY controls the rate of exponential decay of epsilon, higher means a slower decay
# TAU is the update rate of the target network
# LR is the learning rate of the AdamW optimizer
GAMMA = 0.99 # 0.99
EPS_START = 0.9
EPS_END = 0
EPS_DECAY = 1000
TAU = 0.025
LR = 1e-4
WEAPON_TYPES = ["Cannon_System", "Chainshot_System"]
WEAPON_TO_IDX = {
    "Cannon_System": 0,
    "Chainshot_System": 1
}
THRESHOLD = 0.6
BASE_REWARD = 0.0

POLICY_FILE = "policy"
TARGET_FILE = "target"

FROM_FILE = False
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
        
        if FROM_FILE:
            print("Loading from File")
            self.load(POLICY_FILE, TARGET_FILE)
            self.target_net.load_state_dict(self.policy_net.state_dict())
        else:
            print("Initializing randomly")
            self.policy_net = DQN(Environment.N_OBSERVATIONS, Environment.N_ACTIONS).to(self.device)
            self.target_net = DQN(Environment.N_OBSERVATIONS, Environment.N_ACTIONS).to(self.device)
            self.target_net.load_state_dict(self.policy_net.state_dict())

        self.optimizer = optim.AdamW(self.policy_net.parameters(), lr=LR, amsgrad=True)
        self.memory = Memory(10000) # use some arbitrary buffer size

        self.steps_done = 0
        self.training = True
        self.start = dt.now()
        self.current_score = 0

        self.currentTransition = None

        # helper mapper for input of neural net in order for it to know
        # which ship is which in its input nodes;
        # by default, you may not be able to get the 
        # same ordering of assets each time you loop in msg.assets
        self.assetName_to_NNidx: dict[str, int] = {}
        self.setAssetName_to_NNidx = True 

        # we need the trackId of the enemy missile for the output
        self.threatId_to_trackId: dict[int, int] = {}
        # self.threatTrackId_to_NNidx: OrderedDict = OrderedDict()
        # self.ttId_to_NNidx_counter = 0
   
   # ran at the first timestep for the entire simulation
    # to help the neural network preserve its ordering on
    # which ship is which
    def populate_assetName_to_NNidx(self, assets: list[AssetPb]):
        i = 0 
        for asset in assets:
            if 'REFERENCE' not in asset.AssetName:
                self.assetName_to_NNidx[asset.AssetName] = i
                i += 1

    # Is passed StatePb from Planner
    def receiveStatePb(self, msg:StatePb):

        # Call function to print StatePb information
        # self.printStateInfo(msg)

        # Call function to show example of building an action
        output_message, action_vector, state_vector = self.createActions(msg)
        # print(output_message)

        # To advance in step mode, its required to return an OutputPb
        self.ai_pub.publish(output_message)
        #self.ai_pub.publish(OutputPb())

        # update memory
        if state_vector is not None:
            if self.currentTransition != None: # update currentTransition with the next state
                if len(self.currentTransition) > 1:
                    for idx in range(len(self.currentTransition[1])):
                        self.memory.push([self.currentTransition[0], self.currentTransition[1][idx].unsqueeze(1), state_vector, self.currentTransition[3]])
                else: 
                    self.currentTransition[2] = state_vector
                    self.memory.push(self.currentTransition)
            
            self.currentTransition = [state_vector, action_vector, None, torch.tensor([BASE_REWARD], device=self.device, dtype=torch.float32)]


        
        if self.current_score != msg.score:
            diff = msg.score - self.current_score
            print(f"diff: {diff}")
            if diff > 0: # larger than
                self.memory.backfill_batch(diff * 10)
            elif diff <= -200 and diff > -1000:
                self.memory.backfill_batch(-diff * 10)
            else:
                self.memory.backfill_batch(diff * 0.1)

            if len(self.memory) > 2: 
                self.rl_update()
            self.current_score = msg.score

        target_net_state_dict = self.target_net.state_dict()
        policy_net_state_dict = self.policy_net.state_dict()
        for key in policy_net_state_dict:
            target_net_state_dict[key] = policy_net_state_dict[key]*TAU + target_net_state_dict[key]*(1-TAU)
        self.target_net.load_state_dict(target_net_state_dict)

        
    # This method/message is used to notify of new scenarios/runs
    def receiveScenarioInitializedNotificationPb(self, msg:ScenarioInitializedNotificationPb):
        # print("Scenario run: " + str(msg.sessionId))
        self.current_score = 0

        
    # This method/message is used to nofify that a scenario/run has ended
    def receiveScenarioConcludedNotificationPb(self, msg:ScenarioConcludedNotificationPb):
        delta = dt.now() - self.start
        print(f"Run {msg.sessionId} — Score: {msg.score}, time: {delta}")
        self.blacklist = set()
        self.assetName_to_NNidx: dict[str, int] = {}
        self.setAssetName_to_NNidx = True
        self.save(POLICY_FILE, TARGET_FILE)
        self.start = dt.now()


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

        if self.setAssetName_to_NNidx:
            self.populate_assetName_to_NNidx(msg.assets)
            self.setAssetName_to_NNidx = False

        output_message: OutputPb = OutputPb()

        # As stated, shipActions go into the OutputPb as a list of ShipActionPbs
        # output_message.actions.append(ship_action)
        ship_actions, action_tensor, state_vector = self.reinforcement_strategy(msg)

        output_message.actions.extend(ship_actions)

        return output_message, action_tensor, state_vector


    def reinforcement_strategy(self, msg:StatePb):
        """
        Epsilon Greedy Strategy 

        TODO 
        """

        # calculate epsilon threshold
        global steps_done
        sample = random.random()
        eps_threshold = EPS_END + (EPS_START - EPS_END) * \
            math.exp(-1. * self.steps_done / EPS_DECAY) # calculate epsilon threshold
        self.steps_done += 1 # update steps done


        if len(msg.Tracks) > 0 and self.weapons_are_available(msg.assets):
            input_vector = np.zeros(210)
            # dship_idx = 0

            ship_weaponType_to_ammo = OrderedDict()

            assets_remaining = set()
            for defense_ship in msg.assets:
                if 'REFERENCE' not in defense_ship.AssetName:
                    # default is zero in case info. from one weapon type isn't provided
                    for weapon_type in WEAPON_TYPES:
                        ship_weaponType_to_ammo[weapon_type] = 0
                    
                    assets_remaining.add(defense_ship.AssetName)

                    # get the ammo for this specific ship
                    for weapon in defense_ship.weapons:
                        ship_weaponType_to_ammo[weapon.SystemName] = weapon.Quantity
                    
                    assert len(ship_weaponType_to_ammo) == len(WEAPON_TYPES)
                    
                    # helps preserve order of ship nodes in input of neural net
                    dship_idx = self.assetName_to_NNidx[defense_ship.AssetName]
                    
                    input_vector[6 * dship_idx:6 * (dship_idx + 1)] = [defense_ship.health, *list(ship_weaponType_to_ammo.values()), 
                                                                    defense_ship.PositionX, defense_ship.PositionY, int(defense_ship.isHVU)]


            # forces a copy of the original keys
            keys_to_keep = list(self.assetName_to_NNidx)
            # remove the assets that are now gone
            for asset_name in keys_to_keep:
                if asset_name not in assets_remaining:
                    del self.assetName_to_NNidx[asset_name]


            for track in msg.Tracks:
                # focus on only the enemy missiles
                if track.ThreatRelationship == "Hostile" and track.TrackId not in self.blacklist:
                    try:
                        target_threatId = int(track.ThreatId.split("_")[-1])
                    # i.e. ValueError happens with the MIN_RAID Planner simulation case where
                    # track.ThreatId = "ENEMY MISSILE"
                    except ValueError:
                        assert track.ThreatId == "ENEMY MISSILE"
                        target_threatId = 0

                    self.threatId_to_trackId[target_threatId] = track.TrackId

                    input_vector[30 + 6 * target_threatId: 30 + 6 * (1 + target_threatId)] = [track.PositionX, track.PositionY, track.PositionZ, 
                                                                                    track.VelocityX, track.VelocityY, track.VelocityZ]
            
            input_vector = torch.tensor(input_vector, device=self.device, dtype=torch.float32)
            output_vector = input_vector.unsqueeze(0)
            if sample > eps_threshold: # pick the best reward
                with torch.no_grad():

                    output = self.policy_net(input_vector)
                    # map output to OutputPb
                    final_output = []
                    locations = torch.nonzero(output > THRESHOLD) # find all values that are larger than our specified threshold

                    ship_weaponType_blacklist = set()
                    
                    executedActionIdxes = []

                    if 300 in locations:
                        return [], torch.tensor([[300]], device=self.device), output_vector

                    for loc in locations:
                        # convert Tensor of one value to the integer it contains
                        loc = int(loc)
                        assignedWeaponType = (loc // 10) % 2
                        # mod 60 because 2 weapon types/enemy * 30 enemies; there are 60 total actions per ship
                        # and we are stacking all the ships' actions sequentially
                        # div 2 because node 0 and 1 are 1st target, node 2 and 3 are 2nd target, etc.
                        assignedTarget = loc % 30
                        # read explanation above, mod 60 gets us to specific index of a target, and
                        # div 60 gets us to identify the ship
                        assignedShip = loc // 5

                        # mask output of NeuralNet to filter out impossible outputs
                        # if assignedTarget >= len(targets) or assignedShip > len(msg.assets):
                        if assignedTarget not in self.threatId_to_trackId or \
                            assignedShip not in self.assetName_to_NNidx.values():
                            continue

                        # dont consider this action if testing or the target is already in the blacklist
                        # if not self.training and targets[assignedTarget].TrackId in self.blacklist:
                        if not self.training or assignedTarget in self.blacklist:
                            continue

                        # construct ship action
                        ship_action: ShipActionPb = ShipActionPb()

                        # if assignedTarget in self.threatTrackId_to_NNidx and assignedShip in self.assetName_to_NNidx.values():
                        ship_action.TargetId = self.threatId_to_trackId[assignedTarget]

                        nnIdx_to_assetName = {v:k for k, v in self.assetName_to_NNidx.items()}
                        # reject if asset is dead
                        if assignedShip not in nnIdx_to_assetName:
                            continue 
                        # at this point, we know that the asset does exist
                        ship_action.AssetName = nnIdx_to_assetName[assignedShip]

                        ship_action.weapon = WEAPON_TYPES[assignedWeaponType]

                        selectedShip_weaponType_to_info = {}
                        for asset in msg.assets:
                            if asset.AssetName == ship_action.AssetName:
                                for weapon in asset.weapons:
                                    selectedShip_weaponType_to_info[weapon.SystemName] = [weapon.WeaponState, weapon.Quantity]

                        # selectedShip_weaponType_to_info = {weapon.SystemName:[weapon.WeaponState, weapon.Quantity] for \
                        #                                     weapon in msg.assets[assignedShip+1].weapons}
                        
                        # reject if weapon state is not ready or is out of ammo:
                        if ship_action.weapon not in selectedShip_weaponType_to_info or \
                            f"{ship_action.AssetName}_{ship_action.weapon}" in ship_weaponType_blacklist:
                            continue 
                        else:
                            weapon_info = selectedShip_weaponType_to_info[ship_action.weapon]
                            if weapon_info[0] != "Ready" or weapon_info[1] == 0:
                                continue
                    
                        # add action to datasets
                        final_output.append(ship_action)
                        # print(f"appended loc: {loc}")
                        executedActionIdxes.append(loc)
                        # self.blacklist.add(targets[assignedTarget].TrackId)
                        self.blacklist.add(assignedTarget)

                    # if len(final_output) > 0:
                        # print(f"Number of actions taken: {len(final_output)}")
                        # print(final_output)

                    if len(executedActionIdxes) == 0:
                        # print("action idx empty")
                        return final_output, torch.tensor([[300]], device=self.device), output_vector
                    else:
                        # print(f"{executedActionIdxes}")
                        return final_output, torch.tensor(executedActionIdxes, device=self.device).unsqueeze(1), output_vector
            else: # random
                return *self.generate_random_action(msg), output_vector
        return [], None, None

    def generate_random_action(self, msg: StatePb):
        """
        Given a StatePb, generates a random ShipActionPb

        @param msg: The StatePb argument

        @return ship_action: A randomly generated, valid ShipActionPb object to be executed. 
        """
        # set up a data response to send later
        ship_action: ShipActionPb = ShipActionPb()

        # random target selection
        random_loc = random.randint(0, len(msg.Tracks)-1)
        start = random_loc - 1
        track_choice = msg.Tracks[random_loc]
        while track_choice.ThreatRelationship != "Hostile" and random_loc != start:
            track_choice = msg.Tracks[random_loc]
            random_loc = (random_loc + 1) % len(msg.Tracks)
        ship_action.TargetId = track_choice.TrackId

        if ship_action.TargetId in self.blacklist or track_choice.ThreatRelationship != "Hostile":
            # print("random in blacklist")
            return [],  torch.tensor([[300]], device=self.device)
        else:
            self.blacklist.add(ship_action.TargetId)             

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

        try:
            target_threatId = int(track_choice.ThreatId.split("_")[-1])
        # i.e. ValueError happens with the MIN_RAID Planner simulation case where
        # track.ThreatId = "ENEMY MISSILE"
        except ValueError:
            assert track_choice.ThreatId == "ENEMY MISSILE"
            target_threatId = 0
        
        reversed_NN_idx = 60 * self.assetName_to_NNidx[rand_asset.AssetName] + WEAPON_TO_IDX[ship_action.weapon] * 30 + target_threatId

        # print(f"random {reversed_NN_idx}")
        return [ship_action], torch.tensor([[reversed_NN_idx]], device=self.device)

    def rl_update(self):
        """
        Run this function when the score gets updated (we get feedback)
        """
        # backfill reward values over a sample

        sample = self.memory.sample()
        transitions = []
        for trans in sample:
            transitions.append(Transition(*trans))

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
        action_batch = torch.cat(batch.action).type(torch.int64) 
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
        next_state_values = torch.zeros(len(non_final_mask), device=self.device)
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


    #Sets an entirely new population. Only called when loading an old population from a file.
    def load(self, policy_file, target_file):
        self.policy_net = torch.load(policy_file).to(self.device)
        self.target_net = torch.load(target_file).to(self.device)

    def save(self, policy_file, target_file):
        torch.save(self.policy_net, policy_file)
        torch.save(self.target_net, target_file)
    
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
