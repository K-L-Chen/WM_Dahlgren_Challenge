#Imports
from PlannerProto_pb2 import ScenarioConcludedNotificationPb, ScenarioInitializedNotificationPb     #Scenario start/end notifications
from PlannerProto_pb2 import ErrorPb                                            #Error messsage if scenario fails
from PlannerProto_pb2 import StatePb, AssetPb, TrackPb                          #Simulation state information
from PlannerProto_pb2 import OutputPb, ShipActionPb,  WeaponPb
from publisher import Publisher

import random
import utils

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
        output_message.actions.extend(self.low_resources_strategy(msg))

        return output_message

    
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
    
        DISTANCE_THRESHOLD = 500000000
        CLOSEST_MISSILE = 500000000
        targets_list = []
        #Are there any valid targets (hostile, not in blacklist)?
        for track in msg.Tracks:
            if track.ThreatRelationship == "Hostile" and track.TrackId not in self.blacklist:
                targets_list.append(track)
                m_distance = utils.distance(0,0,0,track.PositionX,track.PositionY,track.PositionZ)
                if m_distance < CLOSEST_MISSILE:
                    CLOSEST_MISSILE = m_distance


        # if there are any threats and we have weapons and we are past the time threshold
        if self.weapons_are_available(msg.assets) and targets_list and CLOSEST_MISSILE < DISTANCE_THRESHOLD:
            
            # generate list of our defense ships that aren't targeting and have any weapons left
            unassigned_assets = []
            total_assets = [] # List of all of our ships
            for asset in msg.assets:
                if asset.AssetName != "Galleon_REFERENCE_SHIP":
                    total_assets.append(asset)
                    if self.weapons_in_asset(asset):
                        unassigned_assets.append(asset)

                    
            targeted_ships_dict = {} #Maps an asset to a list of the missiles targeting it
            #Calculate what ships every missile is targeting
            for enemy_missile in targets_list:
                utils.calculate_missile_target(enemy_missile,total_assets,targeted_ships_dict)
            
            #Calculate the most targeted ship
            most_targeted_ship = utils.find_most_targeted_ship(targeted_ships_dict)

            #Find the closest missile targeting the most-targeted ship
            missile_to_target = utils.find_closest_missile(most_targeted_ship, targeted_ships_dict[most_targeted_ship])

            #Find the closest ship available to attack the closest missle targeting the most targeted ship
            closest_ready_asset = utils.find_closest_ready_asset(missile_to_target,unassigned_assets)

            # send a response back to the planner
            
            ship_action: ShipActionPb = ShipActionPb()
            ship_action.TargetId = missile_to_target.TrackId    
            ship_action.AssetName = closest_ready_asset.AssetName

            self.blacklist.add(missile_to_target.TrackId)

            # random weapon selection, but it may not be ready or there may not be any left
            rand_weapon = random.choice(closest_ready_asset.weapons)

            # therefore, randomly scurry around until we have an immediate weapon to launch
            while rand_weapon.Quantity == 0 or rand_weapon.WeaponState != "Ready":
                rand_weapon = random.choice(closest_ready_asset.weapons)

            ship_action.weapon = rand_weapon.SystemName
        
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
