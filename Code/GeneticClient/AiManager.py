# Imports
from ControlCenter import ControlCenter
from WeaponAI import WeaponAI
from PlannerProto_pb2 import ScenarioConcludedNotificationPb, \
    ScenarioInitializedNotificationPb  # Scenario start/end notifications
from PlannerProto_pb2 import ErrorPb  # Error messsage if scenario fails
from PlannerProto_pb2 import StatePb, AssetPb, TrackPb  # Simulation state information
from PlannerProto_pb2 import OutputPb, ShipActionPb, WeaponPb
from publisher import Publisher

# import pygad as pga
# from pyharmonysearch import harmony_search
#from ObjectiveFunctionInterface import ObjectiveFunction as ofihs

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
#switch to false once we start running for the competition
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
        self.swap = False

        # make a new weapon A.I. object for each weapon_type
        # in this competition, WEAPON_TYPES = ["Cannon", "Chainshot"]
        self.weapon_AIs = dict()
        for weapon_type in WEAPON_TYPES:
            self.weapon_AIs[weapon_type] = WeaponAI(weapon_type=weapon_type, init_policy_population=POPULATION_SIZE)

        self.control_center = ControlCenter()

        # to keep track of all actions that were executed this round
        self.actions_executed_this_round = set()

        #algorithm vars
        '''
        KYLE: I'm going to be honest here, I think we just reinvented the wheel
              I'm also starting to think pygad loops once we start it...
              might have to write our own version of the algorithm and drop pygad
              This is legitimately painful

        Joseph: In response to Kyle, I would say even if we tried using PyGAD from the get-go, it would have been very hard
        to use it because, as the first step, we cannot really define an explicit fitness function we can evaluate in one-go
        for every single member of our population, which is an action rule. When we're running our simulations,
        all we have for feedback is the final score, and only a subset of our population can actually be updated
        with that score, since not every single action rule in our population will likely get executed.

        Also, the overall goal is not static, like in supervised learning where y = 44 in the PyGAD example. The maximum final
        score we can obtain in a given Planner simulation scenario will vary. 

        Personally, I was trusting Kevin when he said that he was having problems with using PyGAD, which is
        why I've been hammering out the original plan of implementing the genetic algorithm from scratch.

        pygad constructor vars we care about:
            - num_generations : number of generations
            - num_parents_mating : number of solutions to be selected as parents
            - fitness_func : function that acceses 2 parameters and return fitness value

            ^ I don't get what `solution_idx` is used for though
            ^ We can't really compute a fitness function directly until after running at least a simulation

            - fitness_batch_size (optional): calculates fitness function in batches
            - initial_population: defaults to None (is a list)
            - gene_type: data type of genes, defaults to float
            - init_range_low: lower bound of genes, defaults to -4
            - init_range_high: upper bound of genes, defaults to 4
            - parent_selection_type: how we select parents
                Choices:
                    sss - steady-state selection (default)
                    rws - roulette wheel selection
                    sus - stochastic universal selection
                    rank
                    random
                    tournament (what?)
            - keep_parents: keep parents in population.
                0 : do not keep any parents in next population
                i > 0 : keep i parents
                -1 : keep current number of parents (default)
            - keep_elitism: number of solutions we keep for next generation
                0 : no effect
                1 : keep only best solution (default)
                K > 1 : keep best K solutions

            - crossover_type: type of crossover operation
                single_point
                two_points
                scattered
                (we probably want to utilize all three of these types at once)

            - crossover_probability: probability for applying crossover operation to a parent
                value must be between 0.0 - 1.0 inclusive
            - mutation_type: type of mutation operation for creating children
                random (default)
                swap
                inversion
                scramble
                adaptive
            - mutation_percent_genes: percent of genes to mutate
                must be between 0 (exclusive) & 100 (inclusive)
                default is 10%
            - mutation_num_genes: raw number of genes to mutate
                default is nothing
            - on_start: accepts function to be called once GA starts (1 param)
            - on_fitness, on_parents, on_crossover, on_mutation: weird little functions called after respective functions
                take 2 params, read documentation for specifics
            - on_generation: accepts function to be called after each generation (1 param)
                if function returns 'stop', GA stops and doesn't complete other generations
            - on_stop: accepts function to be called before function stops, naturally or not (2 params)
                first param: instance of GA
                second param: list of fitness values of last population solutions
            - save_best_solutions: boolean to save best solutions to attribute best_solutions
                default False
            - save_solutions: boolean to save solutions to attribute solutions
                default False WHY ARE THERE SO MANY OF THESE VARIABLES????
            - allow_duplicate_genes: boolean to allow duplicate gene values
                default True (we probably want false)
            - parallel_processing: accepts process/thread variable and number of processes/threads
                default None
        '''
        # this is actually awful
        '''self.ga = pga(num_generations=1000, num_parents_mating=2, fitness_func=self.weapon_AIs['Cannon_System'].get_fitness_pga, \
                initial_population=list(0 for i in range(0, POPULATION_SIZE)), keep_elitism=1, crossover_type='single_point', \
                crossover_probability=1.0, mutation_type='adaptive', save_best_solutions=True, save_solutions=True, allow_duplicate_genes=False)
        self.hs_objfunc = ofihs()'''

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
        self.actions_executed_this_round = set()  # empty the set of the weapons executed this round
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
        for action_rule_executed in self.actions_executed_this_round:
            # accuracy_sum += action.update_predicted_values(reward)
            # I'm not sure why `step` was deleted earlier
            action_rule_executed.update_predicted_values(reward, step = 1e-5)
            print("placeholder, uncomment the above line after finishing the above TODO")

        # for action in best_actions:
        #     action.update_fitness(accuracy_sum)

        # do Genetic Algorithm OR Harmony Search here!
        # TODO: Implement GA, HS, or some other update to use here.
        # we can read rate of change between our steps to swap between algorithms
        # or do a cutoff
        # use a global flag var? remember this code runs every step
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
            count = 0

            for wai in self.weapon_AIs:
                self.control_center
                if(count % 10 == 0):
                    #TODO implement DBSCAN
                    pass

                proposed_actions = set(wai.request(WeaponPb, AssetPb, TrackPb))
                correct_actions = set()
                for action in wai.action_set:
                    ga_actions = wai.evaluate(WeaponPb, AssetPb, TrackPb, action)
                    if ga_actions:
                        correct_actions.update(action)

            cur_step, prev_step = 0, 0
            step_size = 1.0
            rate_of_change = (cur_step - prev_step) / step_size

            # swap flag based on genetic algorithm rate of change
            if rate_of_change < 5:
                self.swap = True

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
