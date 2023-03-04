#Imports
from PlannerProto_pb2 import ScenarioConcludedNotificationPb, ScenarioInitializedNotificationPb     #Scenario start/end notifications
from PlannerProto_pb2 import ErrorPb                                            #Error messsage if scenario fails
from PlannerProto_pb2 import StatePb, AssetPb, TrackPb                          #Simulation state information
from PlannerProto_pb2 import OutputPb, ShipActionPb,  WeaponPb
from publisher import Publisher

import random
import utils

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

class AiManager:

    # Constructor
    def __init__(self, publisher:Publisher):
        print("Constructing AI Manager")
        self.ai_pub = publisher
        self.track_danger_levels = None
        self.blacklist = set()

        self.logfile = None

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
        #self.logfile = open('log{}_simple.txt'.format(msg.sessionId), 'w')

        
    # This method/message is used to nofify that a scenario/run has ended
    def receiveScenarioConcludedNotificationPb(self, msg:ScenarioConcludedNotificationPb):
        self.blacklist = set()
        if msg.score != 10000:
            print("Ended Run: " + str(msg.sessionId) + " with score: " + str(msg.score))
        #self.logfile.close()


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

        #hardcoded strategy selection, yes I know this is terrible but we have no time to think about anything non-essential
        #2 - full heuristic
        #1 - same as low_resources in GreedyClient, only here because I had no reason to remove it
        switch = 2

        if switch == 3:
            output_message.actions.extend(self.testing_strategy(msg))
        elif switch == 2:
            output_message.actions.extend(self.full_heuristic_strategy(msg))
        elif switch == 1:
            output_message.actions.extend(self.low_resources_strategy(msg))
        else:
            output_message.actions.extend(self.simple_greedy_strategy(msg))

        return output_message

    def testing_strategy(self, msg:StatePb):
        start = dt.now()
        # maps the index to the asset name
        #how the actual hell are we getting the ID?????? JOSEPH: this is how
        #GET ID BY ITS POSITION IN INITIAL INPUT
        asset_names = [None for _ in range(5)] #unordered list of assets (integer entries, correspond to elements in asset_info, asset_threats)
        asset_positions = [None] * 5  #len 5, bunch of tuple locations(x, y, z)
        asset_weapon_info = [None] * 5 # bunch of tuples (name, quantity, WeaponState)
        # asset_names = [asset.AssetName for asset in msg.assets if 'REFERENCE' not in asset.AssetName]          
        # self.populate_asset_names(assets)
        self.populate_asset_info(msg, asset_names, asset_positions, asset_weapon_info)
        #USE self.update_assets_trakcs(msg)


        # threats = [None] * 30 #unordered list of missiles, each entry is an int correstponding to the number of the missile

        # threat_info = [None] * 30 #len 30

        targetIds = [None] * 30 #len 30
        threat_trackIds = [None] * 30 # for our action outputPb
        threat_positions = [None] * 30
        threat_velocities = [None] * 30
        self.populate_threat_info(msg, targetIds, threat_trackIds, threat_positions, threat_velocities)
        # self.populate_threatIds(msg, targetIds, threatIds_to_trackIds)

        threat_secondaries = [None] * 5 #len 5

        threat_filtered = self.filter_targets(msg, threat_trackIds) #may/maynot need this
        
        #STUFF I NEED!!!!!!!!!!!!!!!!!!!

        # used to evaluate when something needs to go to its secondary target
        # list of list of weapons that are targeting the asset for each respective index?
        #NEEDS TO BE POPULATED WITH THE MISSILES FOR EACH ASSET THAT HAVE IT AS PRIMARY TARGET (asset identified by index)
        asset_threat_list = [None] * 5


        ammo = None

        delta = dt.now() - start
        print(f"Initialization time: {delta}")

        # utils.time_between_missile_and_ship()

        return []
    
    #Strategy based on the most exhaustive and complete set of heuristics we can apply in the time limit
    def full_heuristic_strategy(self, msg:StatePb):
        """
        Pre-implementation notes:
        
        - pivot to accounting for things at a given time, or with a given time difference.
          - the purpose of this is to allow us to make predictions about what will happen if we take certain actions
          - thus: we get to look at things like secondary targets and changes in missile speed after maneuvers (what beat us in round 2)
        
        - we need a better value system than we had before
          SPECIFICALLY, I think this means one of two things: 
          - 1: keeping track of an expected final score.
            - this may be impossibly slow unless we find a way to cull a TON of poential actions or use excessive simplification
          - 2: keep track of the maximum loss to score after n missiles are fired (for the highest n we can do)
            - one issue with this is that n must be high enough that SOME assets remain. 
            - it will not work if the best score is close to the minimum score, or if we have too few total missiles to handle unseen approaching missiles afterwards.
            - REMEMBER: we may not know if MORE missiles are outside of our view range

        - The general idea is to trade speed for accuracy for as long as we possibly can, and then find someting fast to finish off with when there's no time left.
          We can think of it as follows: we have ONE SECOND to find what the hell do do in the next second. 
          - If we have 30 targets to pick from for a first attack, we have 29 for the second. 30*29=870 - so if were looping through those, we'd need to do the inside in under 1ms.
          - I think this eliminates any possibiliy of doing brute force without some serious serious optimization.

         
        - Potential Strategies:
          - 1: GPU
            - I did some testing. I was able to do a billion simple operations that took 5 minutes on my CPU at home in well under a second on my 3080ti. We have 3090s in the laptops :) 
            - I really do want to play with this more. I did some testing for fun, it's very easy to set up I think.
            - we would need to design FOR this approach though, idk if we have time.
          - 2: Cull as many missiles as possible in the first loop and do a detailed search of the remaining choices
            - basically, the idea is to find out which missiles are the worst to shoot until we get to a space not much larger than our avaliable missiles
            - we're looking for the WORST missiles to shoot, not the best ones, because those should be ones that lack range to do much impact
            - this may be virually optimal if we have very few initial missiles and thee isn't something SUPER sneaky

        TODO: slightly modified, but simpler data structures filled out
        TODO: function that estimates, something reasonably fast, how long it 
        will take for a missile to reach a target (something Nick proposed: 2-line version)
        TODO: how exactly to make a decision 
        TODO: calculate the secondary targets


        Important variables: Time between enemy missile and ship (imperfect; straight line approx.)
        Find primary and secondary assets (second-closest ship to a missile)

        
        2ndary TODO: make a version of the secondary target that works with Nick's existing algorithm
        """

        start = dt.now()
        # maps the index to the asset name
        #how the actual hell are we getting the ID?????? JOSEPH: this is how
        #GET ID BY ITS POSITION IN INITIAL INPUT
        asset_names = [None for _ in range(5)] #unordered list of assets (integer entries, correspond to elements in asset_info, asset_threats)
        asset_positions = [None] * 5  #len 5, bunch of tuple locations(x, y, z)
        asset_weapon_info = [None] * 5 # bunch of tuples (name, quantity, WeaponState)
        # asset_names = [asset.AssetName for asset in msg.assets if 'REFERENCE' not in asset.AssetName]          
        # self.populate_asset_names(assets)
        self.populate_asset_info(msg, asset_names, asset_positions, asset_weapon_info)
        #USE self.update_assets_trakcs(msg)


        # threats = [None] * 30 #unordered list of missiles, each entry is an int correstponding to the number of the missile

        # threat_info = [None] * 30 #len 30


        targetIds = [None] * 30 #len 30
        threat_trackIds = [None] * 30 # for our action outputPb
        threat_positions = [None] * 30
        threat_velocities = [None] * 30
        self.populate_threat_info(msg, targetIds, threat_trackIds, threat_positions, threat_velocities)
        # self.populate_threatIds(msg, targetIds, threatIds_to_trackIds)

        threat_secondaries = [None] * 5 #len 5

        threat_filtered = self.filter_targets(msg, threat_trackIds) #may/maynot need this
        
        #STUFF I NEED!!!!!!!!!!!!!!!!!!!

        # used to evaluate when something needs to go to its secondary target
        # list of list of weapons that are targeting the asset for each respective index?
        #NEEDS TO BE POPULATED WITH THE MISSILES FOR EACH ASSET THAT HAVE IT AS PRIMARY TARGET (asset identified by index)
        asset_threat_list = [None] * 5


        ammo = None

        delta = dt.now() - start
        print(f"Initialization time: {delta}")


        '''
        ALGORITHM:

        For each missile:
            if it has time to get to its target and is NOT a current target, add to assets

        - each threat will have an expected penalty
          - want to minimize 
        - if >HP missiles targeting asset, the rest may as well be targeting 2ndary target UNLESS they can't make it
          - missiles slow down/can't retarget the later you shoot them, want to wait as long as possible
        
        FIRST - find current expected penalty of each missile
        - for each missile targeting ship after ship to dies, given based on 2ndary.

        - NOTE: tiebreakers should be resolved by time to target


        For n:

            For each remaining threat (missiles that are an actual threat):

                - want to pick the best one to shoot

                assume we destroy THIS one:
                
                    - want to see how this changes the situation

                    find new expected penalty of each missile 
            
            add most effective to targets, remove from threats

        '''

        n = 1 # depth of search

        curr_threats = [i for i in threat_filtered]
        future_score = 0
        shotsfired = 0

        for a in range(n): #a in range(threat_filtered) for ALL missiles considered
            curr_score = 0
            
            curr_target = None

            #inner pick-best-target
            for i in range(len(curr_threats)):

                threat = curr_threats[i]

                inner_threats = [i or i in curr_threats].remove[threat]
                
                for i in range(ammo-shotsfired):
                    pass
                
                #NOTE: PSEUDOCODE FOR FINAL STAGE EXPECTED VALUE GREEDY
                #   if there are missiles with HVU as target:
                #       remove the one that will hit HVU first
                #   elif there are missiles with HVU as 2ndary target AND primary target has more missiles inbound than HP:
                #       remove the one that will hit 2ndary target first
                #   else:
                #       remove missile that hits first

                total_score = 0
                
                #TODO keep track of final state

                for j in range(len(inner_threats)):

                    weapon_score = 0 #placeholder, see comments below

                    #sort inner threats

                    #add damage of the first target that hits, remove it from 

                    total_score + weapon_score
            

                

                    
                    


    # def populate_asset_names(self, msg: StatePb, init_lst: list):
    #     i = 0
    #     for asset in msg.assets:
    #         if 'REFERENCE' not in asset.AssetName:
    #             init_lst[i] = asset.AssetName
    #             i += 1
    
    def populate_asset_info(self, msg, names, positions, weapon_info):
        i = 0
        for asset in msg.assets:
            if 'REFERENCE' not in asset.AssetName:
                names[i] = asset.AssetName
                positions[i] = (asset.PositionX, asset.PositionY, asset.PositionZ)
                weapon_info[i] = []
                
                for w_data in asset.weapons:
                    weapon_info[i].append((w_data.SystemName, w_data.Quantity, w_data.WeaponState))
                i += 1
                


    def populate_threat_info(self, msg: StatePb, target_ids, threat_trackIds, threat_poss, threat_velos):
        """
        Get mappings from our programmatic threat index to its actual
        threatId and trackId through two different lists respectively
        """
        i = 0
        for track in msg.Tracks:
            if track.ThreatRelationship == "Hostile":
                target_ids[i] = track.ThreatId
                threat_trackIds[i] = track.TrackId
                threat_poss[i] = (track.PositionX, track.PositionY, track.PositionZ)
                threat_velos[i] = (track.VelocityX, track.VelocityY, track.VelocityZ)
                i += 1
    
    # def populate_threatIds_to_trackIds(self, msg: StatePb, init_lst: list):
    #     i = 0
    #     for track in msg.Tracks:
    #         init_lst[idx] = ((msg.Tracks[idx]).TrackID)

    def filter_targets(self, msg: StatePb, target_list: list):
        """
        Produces the final target space that we will work on.
        SHOVE MISSILES THAT CANNOT HIT ASSETS IN TIME TO BLACKLIST
        
        @param target_list: to be filtered. Is a list of length 30
        
        @return filtered_list
        """
        #300 seconds is max amount of time to do everything
        max_time = 300
        #get current time
        cur_time_remaining = max_time - msg.time
        
        idx = 0
        filtered_list = [None] * 30
        for target in target_list:
            if target is not None:
                time_to_target = utils.distance_between_missile_and_ship(msg.Tracks[target])
            
                if target not in self.blacklist and cur_time_remaining > time_to_target:
                    filtered_list[idx] = target
                    idx += 1
        
        return filtered_list

        
    
    def simple_greedy_strategy(self, msg:StatePb):
        """
        Greedy target selection based on distance of enemy missile to any asset

        Only one weapon is used per timestep.

        Parameters
        ----------
        msg: StatePb - received data from the planner

        Returns
        -------
        list[ShipAction], each ShipAction indicating a weapon-target assignment
        """

         # calculate danger levels
        DANGER_DISTANCE_SCALE = 10000000
        TARGETING_CUTOFF = 0.2
        MAX_DANGER = 100
           
        # list of (danger value, enemy missile info.) tuples
        self.track_danger_levels = []
        
        # assign a danger level for each incoming threat and have the threats sorted from most to least dangerous
        # Danger level is based on the summed distance to all of our assets
        print(msg.Tracks)
        for track in msg.Tracks:
            if track.ThreatRelationship == "Hostile" and track.TrackId not in self.blacklist:
                # calculate danger value for current track
                danger_metric = MAX_DANGER
                for asset in msg.assets:
                    danger_metric -= utils.distance(asset.PositionX, asset.PositionY, asset.PositionZ, track.PositionX, track.PositionY, track.PositionZ) / DANGER_DISTANCE_SCALE
                
                # insert in sorted order
                loc = 0
                while loc < len(self.track_danger_levels) - 1 and danger_metric < self.track_danger_levels[0][0]:
                    loc += 1
                self.track_danger_levels.insert(loc, (danger_metric, track)) if loc < len(self.track_danger_levels) - 1 else self.track_danger_levels.append((danger_metric, track))

        # print(self.track_danger_levels)
        
        # if there are any threat and we have weapons
        # and the most dangerous threat value > MAX_DANGER * TARGETING_CUTOFF
        if len(self.track_danger_levels) > 0  and self.weapons_are_available(msg.assets):
            
            # generate list of our defense ships that aren't targeting and have any weapons left
            unassigned_assets = []
            for asset in msg.assets:
                if asset.AssetName != "Galleon_REFERENCE_SHIP" and self.weapons_in_asset(asset):
                    unassigned_assets.append(asset)

                    
            # find closest (s_dist) asset (s_ass) to danger through comparisons
            
            # compare to the first asset
            s_ass = unassigned_assets[0]
            most_danger_threat = self.track_danger_levels[0][1]
            
            s_dist = utils.distance(s_ass.PositionX, s_ass.PositionY, s_ass.PositionZ, 
                                    most_danger_threat.PositionX, most_danger_threat.PositionY, most_danger_threat.PositionZ)
            
            # comparisons
            for asset in unassigned_assets:
                asset_dist = utils.distance(asset.PositionX, asset.PositionY, asset.PositionZ, 
                                        most_danger_threat.PositionX, most_danger_threat.PositionY, most_danger_threat.PositionZ)
                if asset_dist < s_dist:
                    s_dist = asset_dist
                    s_ass = asset

            # send a response back to the planner
            
            ship_action: ShipActionPb = ShipActionPb()
            ship_action.TargetId = most_danger_threat.TrackId       
            ship_action.AssetName = s_ass.AssetName

            self.blacklist.add(most_danger_threat.TrackId)

            # random weapon selection, but it may not be ready or there may not be any left
            rand_weapon = random.choice(s_ass.weapons)

            # therefore, randomly scurry around until we have an immediate weapon to launch
            while rand_weapon.Quantity == 0 or rand_weapon.WeaponState != "Ready":
                rand_weapon = random.choice(s_ass.weapons)

            ship_action.weapon = rand_weapon.SystemName
        
            return [ship_action]

        else:
            return []
        

    def low_resources_strategy(self, msg:StatePb):
        """
        Low resources strategy: goal is to preserve ships from dying

        Only one weapon is used per timestep.

        Strategy: wait for missiles to spawn, calculate number of missiles aimed at each ship, blow up
        closest missile targeting the most-targeted ship

        Parameters
        ----------
        msg: StatePb - received data from the planner

        Returns
        -------
        list[ShipAction], each ShipAction indicating a weapon-target assignment
        """
        #How long should we wait before acting? (Step 1: Wait before spawn)
    
        targets_list = []
        missile_dict = {}
        #Are there any valid targets (hostile, not in blacklist)?
        for track in msg.Tracks:
            if track.ThreatRelationship == "Hostile" and track.TrackId not in self.blacklist:
                targets_list.append(track)
                missile_dict[track.TrackId] = track


        # if there are any threats and we have weapons and we are past the time threshold
        if self.weapons_are_available(msg.assets) and targets_list:
            
            # generate list of our defense ships that aren't targeting and have any weapons left
            unassigned_assets = []
            total_assets = [] # List of all of our ships
            assets_dict = {} #Dictionary mapping asset names to the assets themselves
            for asset in msg.assets:
                if asset.AssetName != "Galleon_REFERENCE_SHIP":
                    total_assets.append(asset)
                    if self.weapons_in_asset(asset):
                        unassigned_assets.append(asset)
                    assets_dict[asset.AssetName] = asset

                    
            targeted_ships_dict = {} #Maps an asset to a list of the missiles targeting it
            missile_target_dict = {} #Maps a missile name to the ship it's attacking

            #Calculate what ships every missile is targeting
            for enemy_missile in targets_list:
                utils.smart_calculate_missile_target(enemy_missile,total_assets,targeted_ships_dict, missile_target_dict)
            
            expected_value_dict = {} # Maps missile name to expected value
            print(missile_target_dict)
            for missileName in missile_dict.keys():
                closest_ready_asset = utils.find_closest_ready_asset(missile_dict[missileName],unassigned_assets)
                for weapon in closest_ready_asset.weapons: 
                    if weapon.WeaponState == "Ready":
                        print(missileName,missile_target_dict.keys())
                        if utils.time_between_ships(closest_ready_asset, missile_target_dict[missileName], weapon) < utils.time_between_missile_and_ship(missile_dict[missileName], missile_target_dict[missileName]):
                            expected_value_dict[missileName] = utils.expected_value(missile_dict[missileName], targeted_ships_dict, missile_target_dict)
                    
            #find the missile with the highest expected value
            max_missile_id = max(expected_value_dict, key = expected_value_dict.get)
            closest_ready_asset = utils.find_closest_ready_asset(missile_dict[max_missile_id],unassigned_assets)
            # send a response back to the planner
            
            ship_action: ShipActionPb = ShipActionPb()
            ship_action.TargetId = max_missile_id
            ship_action.AssetName = closest_ready_asset.AssetName

            self.blacklist.add(max_missile_id)

            # random weapon selection, but it may not be ready or there may not be any left
            rand_weapon = random.choice(closest_ready_asset.weapons)

            # therefore, randomly scurry around until we have an immediate weapon to launch
            while rand_weapon.Quantity == 0 or rand_weapon.WeaponState != "Ready":
                rand_weapon = random.choice(closest_ready_asset.weapons)

            ship_action.weapon = rand_weapon.SystemName
            
            # self.saveStateInfoToFile(msg)

            return [ship_action]
        else:
            return []
        
    
    def random_WTA_strategy(self, msg:StatePb):
        """
        Random Weapon-Target assignments strategy

        Random target selection, asset to shoot from, and weapon type

        Only one weapon is used per timestep.

        Parameters
        ----------
        msg: StatePb - received data from the planner

        Returns
        -------
        list[ShipAction], each ShipAction indicating a weapon-target assignment
        """
        
        # if there are any enemy missiles and we have weapons
        if len(msg.Tracks) > 0 and self.weapons_are_available(msg.assets):
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
        
            return [ship_action]

        else:
            return []
        
    # Helper methods for determining whether any weapons are left 
    def weapons_are_available(self, assets:list[AssetPb]):
        for asset in assets:
            if self.weapons_in_asset(asset): return True
        return False 

    
    def weapons_in_asset(self, asset:AssetPb):
        for weapon in asset.weapons:
            if weapon.Quantity > 0: return True
        return False

    """
    def update_assets_tracks(self, state:StatePb, asset_list: list, track_list: list):
        '''
        take in StatePb to return a list of AssetNames, TrackIDs
        in the order they are in from the Pb we get initially
        
        IF ASSET IS HVU, then it is length of asset list - 1
            e.g. if we have 4 ships, then HVU value is 3
            since we have Galleon_0-2, HVU_Galleon_0
        Else, we just grab the index at the end of the string
        
        @param state: the Protocol Buffer we get from the calling function
        @return None
        '''
        
        for idx in len(state.assets):
            if((state.assets[idx]).AssetName != 'Galleon_REFERENCE_SHIP'):
                #mult = 1
                if((state.assets[idx]).isHVU):
                    asset_list[idx] = len(state.assets) - 1
                else:
                    asset_list[idx] = (int)((state.assets[idx]).AssetName[-1])
        
        for idx in len(state.tracks):
            track_list[idx] = ((state.tracks[idx]).TrackID)
        
        #return tempAssets, tempTracks
    """


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


    # def saveStateInfoToFile(self, msg: StatePb):
    #     self.logfile.write("Time: {}\nScore: {}\n------------------\nASSETS:\n".format(msg.time, msg.score))
        
    #     tempSIDHP = {}
    #     tempMissiles = []

    #     for asset in msg.assets:
    #         self.logfile.write("AssetName: {}\nHVU: {}\nHealth: {}\nPosX: {}\n".format(asset.AssetName, asset.isHVU, asset.health, asset.PositionX))
    #         self.logfile.write("PosY: {}\nPosZ: {}\nLong-Lat: {}\nWeapons: {}\n\n".format(asset.PositionY, asset.PositionZ, asset.Lle, asset.weapons))
    #         tempSIDHP[asset.AssetName] = asset.health

    #     self.logfile.write("------------------\nTRACKS:\n")

    #     for track in msg.Tracks:
    #         self.logfile.write("Track ID: {}\nThreat ID: {}\nThreat Relationship: {}\nLong-Lat: {}\n".format(track.TrackId, track.ThreatId, track.ThreatRelationship, track.Lle))
    #         self.logfile.write("PosX: {}\nPosY: {}\nPosZ: {}\n".format(track.PositionX, track.PositionY, track.PositionZ))
    #         self.logfile.write("VelX: {}\nVelY: {}\nVelZ: {}\n\n".format(track.VelocityX, track.VelocityY, track.VelocityZ))
            
    #         if track.ThreatRelationship == "Hostile":
    #             tempMissiles.append(track)
    
                

        '''if len(list(tempSIDHP.values())) > len(list(self.ship_idhp.values())):
            self.logfile.write("[READING NUMBER OF SHIPS, MISSILES...]")
            self.ship_idhp = tempSIDHP
            self.active_missiles = tempMissiles
            
        elif len(list(tempSIDHP.values())) < len(list(self.ship_idhp.values())):
            for ele in list(self.ship_idhp.keys()):
                if self.ship_idhp[ele] not in tempSIDHP:
                    #FIND THE MISSILE THAT KILLED IT AND PRINT ITS LAST POSZ, Z VEL
                    self.logfile.write(f"[SHIP LOST!{self.ship_idhp[ele]}]")
                    for missile in self.active_missiles:
                        if missile not in tempMissiles:
                            self.logfile.write(f"[MISSILE HIT POSITION Z, SPEED Z: {missile.PositionZ}, {missile.VelocityZ}]")
                elif self.ship_idhp[ele] != tempSIDHP[ele]:
                    #else, find any hits if the health doesn't match up
                    #this is a vey dumb way of doing it, but we can manually parse it
                    for missile in self.active_missiles:
                        if missile not in tempMissiles:
                            self.logfile.write(f"[MISSILE HIT POSITION Z, SPEED Z: {missile.PositionZ}, {missile.VelocityZ}]")
            self.ship_idhp = tempSIDHP
            self.active_missiles = tempMissiles'''
        
        # self.logfile.write("***************************\n\n")
