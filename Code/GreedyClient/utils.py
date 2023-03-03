from PlannerProto_pb2 import _TRACKPB, _ASSETPB
from random import choice

def distance(x1, y1, z1, x2, y2, z2):
    return (x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2) + (z1 - z2) * (z1 - z2)

#Arguments: missile and list of assets
#Adds a new entry to the target_dict mapping the asset to a list of the missiles targeting it
def calculate_missile_target(missile : _TRACKPB, asset_list : list[_ASSETPB], target_dict):
    missile_x = missile.PositionX
    missile_y = missile.PositionY
    missile_x_vel = missile.VelocityX
    missile_y_vel = missile.VelocityY
    missile_slope = missile_y_vel / missile_x_vel
    
    for asset in asset_list:
        asset_x = asset.PositionX
        asset_y = asset.PositionY

        expected_y = missile_slope * (asset_x - missile_x) + missile_y
        print("Asset X: {}\tAsset Y: {}\n Expected Y: {}\n".format(asset_x,asset_y,expected_y))
        print("Asset Y - Expected Y Squared: {}".format(str((asset_y - expected_y)**2)))
        if (asset_y - expected_y)**2 < 1e5: #This threshold may not be right. Will need empirical testing.
            if asset.AssetName in target_dict:
                target_dict[asset.AssetName].append(missile)
            else:
                target_dict[asset.AssetName] = [missile]

            return
    
    print("No target found. Choosing randomly.")
    asset = choice(asset_list)
    if asset.AssetName in target_dict:
        target_dict[asset.AssetName].append(missile)
    else:
        target_dict[asset.AssetName] = [missile]

#Argument: a dictionary mapping each asset to a list of missiles targeting it
#Returns the NAME of the most-targeted ship
def find_most_targeted_ship(target_dict: dict[str,list[_TRACKPB]]):
    max_targeting_missiles = 0
    most_targeted_ship = None
    for assetName in target_dict:
        if len(target_dict[assetName]) > max_targeting_missiles:
            max_targeting_missiles = len(target_dict[assetName])
            most_targeted_ship = assetName
    
    #most_targeted_ship = max(target_dict, key=len(target_dict.get()))
    return most_targeted_ship

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



