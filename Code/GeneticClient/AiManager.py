# Imports
from ControlCenter import ControlCenter
from WeaponAI import WeaponAI
from PlannerProto_pb2 import ScenarioConcludedNotificationPb, \
    ScenarioInitializedNotificationPb  # Scenario start/end notifications
from PlannerProto_pb2 import ErrorPb  # Error messsage if scenario fails
from PlannerProto_pb2 import StatePb, AssetPb, TrackPb  # Simulation state information
from PlannerProto_pb2 import OutputPb, ShipActionPb, WeaponPb
from ActionRuleClass import ActionRule
import ActionRuleClass
from publisher import Publisher

# import pygad as pga
# from pyharmonysearch import harmony_search
#from ObjectiveFunctionInterface import ObjectiveFunction as ofihs

"""
These libraries are not being used, since we pretty much have already implemented
everything so far to take advantage of the functionality of these two libraries.

from pyharmonysearch import harmony_search
import pygad
"""
import numpy as np
from numpy import ndarray

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
#switch to false once we start running for the competition
TRAINING = True
POPULATION_SIZE = 100
NUM_ELITES = 5
MUTATION_RATE_VALUES = 0.3 #How likely are individual cond_value entries to mutate
MUTATION_RATE_BITS = 0.05 #How likely are individual cond_bits to mutate
NUM_FEATURES = ActionRuleClass.CONDITIONAL_ATTRIBUTE_COUNT
PARENT_PERCENTAGE = 0.2 # how much of the population we want to sample from for parents to breed


class AiManager:

    # Constructor
    def __init__(self, publisher: Publisher):
        print("Constructing AI Manager")
        self.ai_pub = publisher
        self.track_danger_levels = None
        self.blacklist = set()
        self.simulation_count = 0

        # add swap var to let us swap from GA to HS
        self.swap = False

        # make a new weapon A.I. object for each weapon_type
        # in this competition, WEAPON_TYPES = ["Cannon", "Chainshot"]
        self.weapon_AIs = dict()
        for weapon_type in WEAPON_TYPES:
            self.weapon_AIs[weapon_type] = WeaponAI(weapon_type=weapon_type, init_policy_population=POPULATION_SIZE)

        self.control_center = ControlCenter()

        # to keep track of all actions that were executed this round
        # to sample without replacement, we need this to be a list instead of a set
        self.actRules_executed_this_round = []


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
        self.actRules_executed_this_round = []  # empty the list of the weapons executed this round
        self.simulation_count += 1
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
                # add action rules executed this round to update their fitness
                self.actRules_executed_this_round.append(target_action[2])

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
        #setup step size
        step = 1e-5

        # update fitness values
        
        # accuracy_sum = 0
        for action_rule_executed in self.actRules_executed_this_round:
            # accuracy_sum += action.update_predicted_values(reward)
            # I'm not sure why `step` was deleted earlier
            action_rule_executed.update_predicted_values(reward, step)
            #print("placeholder, uncomment the above line after finishing the above TODO")

        # for action in best_actions:
        #     action.update_fitness(accuracy_sum)

        # do Genetic Algorithm OR Harmony Search here!
        # TODO: Implement GA, HS, or some other update to use here.
        # we can read rate of change between our steps to swap between algorithms
        # or do a cutoff
        # use a global flag var? remember this code runs every step

        #this is to judge what our current slope is going to be
        prev_step = 0

        if self.swap:
            # TODO run harmony search
            pass
        else:
            # TODO run genetic algorithm
            """
            for each WeaponAI object in self.weaponAIs:
                - Sample the top k (k is even) policies
                    by normalizing the set of fitness/prediction values -> prob. distribution
                - Randomly assign pairings for the k policies

                - For each pair:
                    -  Perform crossover + mutation in multiple different ways --> new action rules
                        - crossover methods: averaging or taking subsets of attributes from both parents
                        - mutation method: perturbation, small to big
                    - Add the resulting action rule to this WeaponAI object
            
            Every 10 or so runs ...
            - (DBSCAN) Cluster similar action rules together to avoid redundancies
            - Now just replace the population with the means of these clusters
            - ^^ but be careful: keep track if a small perturbation results in a huge different in fitness value
                ^ unlikely to be the case, but just an edge case I wanted to throw out there
                ^ instead of replacing with the mean, we could replace with the action rule with the highest fitness
            """
            # for _ in range(100):
            for weapon_name in self.weapon_AIs:
                #self.control_center
                if(self.simulation_count % 10 == 0):
                    #TODO implement DBSCAN
                    pass
                
                weaponType_actRules = self.weapon_AIs[weapon_name].action_set

                # Beginning the breeding process
                # parent_actRules = set()
                children_actRules = []

                # Calculating the prob. distribution of the fitness values to help with random
                # sampling of the parents
                fitness_values = np.array([rule.get_fitness() for rule in weaponType_actRules])
                fitness_values = np.where(fitness_values == 0, 1 / len(fitness_values), fitness_values)
                fitness_values = np.where(fitness_values < 0, -fitness_values, fitness_values)
                fitness_based_probs = fitness_values / np.sum(fitness_values)

                # rounds to the nearest even number
                num_parents = int(PARENT_PERCENTAGE*len(weaponType_actRules) + 0.5) & ~1

                sample_action_rules = np.random.choice(weaponType_actRules, 
                                                        size = num_parents, 
                                                        replace = False,
                                                        p = fitness_based_probs)
                



                # for action in self.weapon_AIs[weapon_name].action_set:
                #     ga_actions = self.weapon_AIs[weapon_name].evaluate(WeaponPb, AssetPb, TrackPb, action)
                #     if ga_actions:
                #         action.update_predicted_values(reward + 1, step)
                #         correct_actions.update(action)

                # length = len(correct_actions)
                # for _ in range(NUM_ELITES):
                #     a = (int)(random.random() * length)
                #     b = (int)(random.random() * length * length + 1) % length
                #     children_actRules.add(self.breed(correct_actions[a], correct_actions[b]))

                for i in range(len(sample_action_rules) - 1):
                    children_actRules.append(self.breed(sample_action_rules[i], sample_action_rules[i + 1]))
                    
                self.weapon_AIs[weapon_name].update_action_set(children_actRules)

                # proposed_actions_dict = {}
                # proposed_actions_dict[count] = set(self.weapon_AIs[weapon_name].request(WeaponPb, AssetPb, TrackPb))


            # cur_step, prev_step = 0, 0
            # rate_of_change = (cur_step - prev_step) / step

            # # swap flag based on genetic algorithm rate of change
            # if rate_of_change < 5:
            #     self.swap = True
            #     break

    # Helper methods for determining whether any weapons are left
    def weapons_are_available(self, assets: list[AssetPb]) -> bool:
        for asset in assets:
            if self.weapons_in_asset(asset): return True
        return False

    def weapons_in_asset(self, asset: AssetPb) -> bool:
        for weapon in asset.weapons:
            if weapon.Quantity > 0: return True
        return False
    
    #Takes two ActionRules and produces a third ActionRule
    def breed(self, action_rule_1 : ActionRule, action_rule_2 : ActionRule):
        '''
        gets the breeded average value for our correct solutions

        @param action_rule_1: good rule 1
        @param action_rule_2: good rule 2

        @return:
        '''
        #Combine the two conditional_vals arrays
        new_conditional_vals = (action_rule_1.get_conditional_values() + action_rule_2.get_conditional_values())//2
        
        #Combine the two bitsets
        new_bitset = 0
        
        conditional_bits_1 = action_rule_1.get_cond_bitstr()
        conditional_bits_1b = action_rule_1.get_cond_bitstr()
        conditional_bits_2 = action_rule_2.get_cond_bitstr()
        conditional_bits_2b = action_rule_2.get_cond_bitstr()

        new_cond_bits = 0
        
        lena = conditional_bits_1b.bit_length()
        lenb = conditional_bits_2b.bit_length()
        bitlen = 0
        
        for _ in range(NUM_FEATURES):
            tempA = conditional_bits_1b % 2
            tempB = conditional_bits_2b % 2
            new_cond_bits = new_cond_bits + (((tempA) & (tempB)) | ((tempA) ^ (tempB)))
            new_cond_bits = new_cond_bits * 2

            conditional_bits_1b = conditional_bits_1b // 2
            conditional_bits_2b = conditional_bits_2b // 2
            print(format(new_cond_bits,'b'))
        print("*********")
        # grab AND/OR, LE/GE bits for each element in our calculated conditional list
        # starting at the rightmost side of the integer
        # EVEN indexed bits are AND/OR -> 0/1
        # ODD indexed bits are LE/GE -> 0/1
        # KYLE : maybe we might want a separate grabber method for individual bit pairs?

        """Crossover by obtainig LE/GE bit from 1st parent and the AND/OR bit from 2nd parent"""
        for _ in range(NUM_FEATURES):
            # and_or_or_1 = conditional_bits_1 % 2
            conditional_bits_1 = conditional_bits_1 // 2 # >> 1
            le_or_ge_1 = conditional_bits_1 % 2 # & 1
            conditional_bits_1 = conditional_bits_1 // 2 # >> 1
            
            and_or_or_2 = conditional_bits_2 % 2 # & 1
            conditional_bits_2 = conditional_bits_2 // 2 # >> 1
            # le_or_ge_2 = conditional_bits_2 % 2 # & 1
            conditional_bits_2 = conditional_bits_2 // 2 # >> 1

            
            # add less than/greater than bit from first parent
            new_bitset *= 2 # << 1
            new_bitset += le_or_ge_1   
            

            #add and/or bit from second parent
            new_bitset *= 2 # << 1
            new_bitset += and_or_or_2

            print(format(new_bitset,'b'))
            
        """Mutation"""
        for i in range(NUM_FEATURES):
            random_sample_prob = random.random()
            if random_sample_prob < MUTATION_RATE_VALUES:
                #This is dumb, should be range not current value
                new_conditional_vals[i] += (random.random() - 0.5) * new_conditional_vals[i]
            if random_sample_prob < MUTATION_RATE_BITS:
                new_bit_mask = 0
                new_bit_mask << random.randint(0,18)
                new_bit_mask = new_bit_mask + 1
        
        return ActionRule(conditional_vals = new_conditional_vals, cond_bits= new_bitset)
    

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
