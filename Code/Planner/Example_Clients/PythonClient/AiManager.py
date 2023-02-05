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
        output_message.actions.extend(self.random_WTA_strategy(msg))

        return output_message

    def simple_greedy_strategy(self, msg:StatePb):
         # calculate danger levels
        DANGER_DISTANCE_SCALE = 10000000
        TARGETING_CUTOFF = 0.2
        MAX_DANGER = 100

        self.track_danger_levels = []
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
        # if there are any enemy missiles and we have weapons
        # and self.track_danger_levels[0][0] > MAX_DANGER * TARGETING_CUTOFF
        if len(self.track_danger_levels) > 0  and self.weapons_are_available(msg.assets):

            # generate list of unassigned assets
            unassigned_assets = []
            for ass in msg.assets:
                if ass.AssetName != "Galleon_REFERENCE_SHIP" and self.weapons_in_asset(ass):
                    unassigned_assets.append(ass)

            # find closest asset to danger 
            s_dist = utils.distance(unassigned_assets[0].PositionX, unassigned_assets[0].PositionY,
                    unassigned_assets[0].PositionZ, self.track_danger_levels[0][1].PositionX, self.track_danger_levels[0][1].PositionY,
                    self.track_danger_levels[0][1].PositionZ)
            s_ass = unassigned_assets[0]
            for ass in unassigned_assets:
                c_dist = utils.distance(ass.PositionX, ass.PositionY,
                    ass.PositionZ, self.track_danger_levels[0][1].PositionX, self.track_danger_levels[0][1].PositionY,
                    self.track_danger_levels[0][1].PositionZ)
                if c_dist < s_dist:
                    s_dist = c_dist
                    s_ass = ass

            # set up a data response to send later
            ship_action: ShipActionPb = ShipActionPb()

            # select the target with the highest danger level
            ship_action.TargetId = self.track_danger_levels[0][1].TrackId       

            # set assetname 
            ship_action.AssetName = s_ass.AssetName

            self.blacklist.add(self.track_danger_levels[0][1].TrackId)

            print(self.blacklist)

            # random weapon selection
            rand_weapon = random.choice(s_ass.weapons)

            # randomly scurry around until we have an immediate weapon to launch
            while rand_weapon.Quantity == 0 or rand_weapon.WeaponState != "Ready":
                rand_weapon = random.choice(s_ass.weapons)

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