from PlannerProto_pb2 import _TRACKPB, _ASSETPB, _WEAPONPB
from random import choice

def distance(x1, y1, z1, x2, y2, z2):
    return (x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2) + (z1 - z2) * (z1 - z2)


#returns the DISTANCE between a given missile and a given ship
def distance_between_missile_and_ship(missile : _TRACKPB, ship : _ASSETPB):
    return distance(missile.PositionX, missile.PositionY, 0, ship.PositionX, ship.PositionY, 0) ** (1/2)

#returns the time it takes for a weapon from one ship to reach another
def time_between_ships(defending_ship : _ASSETPB, target_ship : _ASSETPB, weapon_type : _WEAPONPB):
    distance_between_ships = distance(defending_ship.PositionX,defending_ship.PositionY,defending_ship.PositionZ, 
                                      target_ship.PositionX, target_ship.PositionY, target_ship.PositionZ) ** (1/2)
    if weapon_type.SystemName == "Chainshot":
        weapon_speed = 1234
    else:
        weapon_speed = 3500
    return distance_between_ships / weapon_speed


#returns the time between a missile and its target
def time_between_missile_and_ship(missile : _TRACKPB, ship : _ASSETPB):
    missile_velocity = (missile.VelocityX ** 2 + missile.VelocityY ** 2 + missile.VelocityZ ** 2) ** (1/2)
    return distance_between_missile_and_ship(missile,ship) / missile_velocity


def smart_calculate_missile_target(missile : _TRACKPB, asset_list : list[_ASSETPB], target_dict, missile_target_dict):
    closest_asset = asset_list[0]
    dist = distance_between_missile_and_ship(missile, asset_list[0])
    for asset in asset_list:
        if distance_between_missile_and_ship(missile, asset) < dist:
            closest_asset = asset
    if closest_asset.AssetName in target_dict.keys():
        target_dict[closest_asset.AssetName].append(missile)
    else:
        target_dict[closest_asset.AssetName] = [missile]
    missile_target_dict[missile.TrackId] = closest_asset
    
#Arguments: missile and list of assets
#Adds a new entry to the target_dict mapping the asset to a list of the missiles targeting it
#Another argument - missile_target_dict of missileName : target
def calculate_missile_target(missile : _TRACKPB, asset_list : list[_ASSETPB], target_dict, missile_target_dict):
    missile_x = missile.PositionX
    missile_y = missile.PositionY
    missile_x_vel = missile.VelocityX
    missile_y_vel = missile.VelocityY
    missile_slope = missile_y_vel / missile_x_vel
    
    dist_btwn_missile_target = distance_between_missile_and_ship(missile, asset_list[0])
    cur_target = asset_list[0]
    for asset in asset_list:
        asset_x = asset.PositionX
        asset_y = asset.PositionY

        expected_y = missile_slope * (asset_x - missile_x) + missile_y
        # print("Asset X: {}\tAsset Y: {}\n Expected Y: {}\n".format(asset_x,asset_y,expected_y))
        # print("Asset Y - Expected Y Squared: {}".format(str((asset_y - expected_y)**2)))
        if (asset_y - expected_y)**2 < 1e6: #This threshold may not be right. Will need empirical testing.
            #if distance_between_missile_and_ship(missile,asset) <= dist_btwn_missile_target:
            if cur_target.AssetName in target_dict.keys() and missile in target_dict[cur_target.AssetName]:
                target_dict[cur_target.AssetName].remove(missile)
            cur_target = asset
            #dist_btwn_missile_target = distance_between_missile_and_ship(missile,asset)
            if asset.AssetName in target_dict.keys():
                target_dict[asset.AssetName].append(missile)
            else:
                target_dict[asset.AssetName] = [missile]
            missile_target_dict[missile.TrackId] = asset

            #return
    
    # print("No target found. Choosing randomly.")
    # asset = choice(asset_list)
    # if asset.AssetName in target_dict:
    #     target_dict[asset.AssetName].append(missile)
    # else:
    #     target_dict[asset.AssetName] = [missile]

#Argument: a dictionary mapping each asset to a list of missiles targeting it
#Returns the NAME of the most-targeted ship
def find_most_targeted_ship(target_dict: dict[str,list[_TRACKPB]]):
    max_targeting_missiles = 0
    most_targeted_ship = None
    for assetName in target_dict.keys():
        if len(target_dict[assetName]) > max_targeting_missiles:
            max_targeting_missiles = len(target_dict[assetName])
            most_targeted_ship = assetName
    
    #most_targeted_ship = max(target_dict, key=len(target_dict.get()))
    return most_targeted_ship

#Arguments: a missile, the dictionary mapping ships to missiles targeting them
#The dictionary mapping missiles to their targets
#Returns: the expected value of destroying this missile; want to use distance as a tiebreaker 
def expected_value(missile : _TRACKPB, target_dict, missile_target_dict):
    target = missile_target_dict[missile.TrackId] #What ship is being targeted
    m_with_same_t = len(target_dict[target.AssetName]) #How many missiles are targeting this target
    distance_between_missile_and_target = distance_between_missile_and_ship(missile,target)
    ev = 10 / distance_between_missile_and_target
    if target.isHVU and m_with_same_t >= target.health:
        ev = ev + 9000
    elif target.isHVU:
        ev = ev + 2000
    elif m_with_same_t >= target.health:
        ev = ev + 5000
    else:
        ev = ev + 1000
    secondary_target = find_secondary_target(missile, list(target_dict.keys()))
    if secondary_target.isHVU:
        ev = ev + 4500
    return ev


#Arguments: the most targeted ship and the list of missiles targeting it
#Returns the closest missile to that ship
def find_closest_missile(mts : _ASSETPB, missiles_list : list[_TRACKPB]):
    min_dist = 10000000000
    min_missile = missiles_list[0]
    for missile in missiles_list:
        dist = distance(missile.PositionX,missile.PositionY,missile.PositionZ,mts.PositionX,mts.PositionY,mts.PositionZ)
        if dist < min_dist:
            min_dist = dist
            min_missile = missile
    print("Min Distance: " + str(min_dist))
    return min_missile


#Arguments: the most dangerous missile and a list of unassigned assets
#Returns the closest ready SHIP (not weapon)
def find_closest_ready_asset(most_danger_threat : _TRACKPB, unassigned_assets : list[_ASSETPB]):
    # find closest (s_dist) asset (s_ass) to danger through comparisons
    # compare to the first asset
    s_ass = unassigned_assets[0]
    s_dist = distance(s_ass.PositionX, s_ass.PositionY, s_ass.PositionZ, 
                            most_danger_threat.PositionX, most_danger_threat.PositionY, most_danger_threat.PositionZ)
    
    # comparisons
    for asset in unassigned_assets:
        asset_dist = distance(asset.PositionX, asset.PositionY, asset.PositionZ, 
                                most_danger_threat.PositionX, most_danger_threat.PositionY, most_danger_threat.PositionZ)
        if asset_dist < s_dist:
            s_dist = asset_dist
            s_ass = asset

    return s_ass



#Arguments: the missile to be checked, a list of assets
#Returns the SECONDARY target of this missile (if it redirects)
#Returns None if there are no secondary targets possible
def find_secondary_target(missile: _TRACKPB, asset_list : list[_ASSETPB]):
    if len(asset_list) < 2:
        return None
    primary_target = find_primary_target(missile,asset_list)
    secondary_target = None
    cur_dist = 1e10
    for asset in asset_list:
        if asset != primary_target:
            dist_btwn_ships = distance(primary_target.PositionX,primary_target.PositionY,0,asset.PositionX,asset.PositionY,0)
            if dist_btwn_ships < cur_dist and dist_btwn_ships != 0:
                cur_dist = dist_btwn_ships
                secondary_target = asset
    return secondary_target

#Arguments: the missile to be checked, a list of assets
#Returns the PRIMARY target of this missile (if it redirects)
def find_primary_target(missile: _TRACKPB, asset_list : list[_ASSETPB]):
    closest_asset = asset_list[0]
    dist = distance_between_missile_and_ship(missile, asset_list[0])
    for asset in asset_list:
        if distance_between_missile_and_ship(missile, asset) < dist:
            closest_asset = asset
    return closest_asset