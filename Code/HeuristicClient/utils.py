from PlannerProto_pb2 import _TRACKPB, _ASSETPB, _WEAPONPB
from random import choice
PI = 3.14159265
TURNING_SPEED = 25

def distance(x1, y1, z1, x2, y2, z2):
    return ((x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2) + (z1 - z2) * (z1 - z2)) ** (1/2)


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

#Arguments: a missile and its secondary target
#Returns if this secondary target is outside of the minimum retargeting radius
#Not sure how to calculate this
def can_reach_secondary_target(missile: _TRACKPB, secondary_target : _ASSETPB):
    missile_velocity = (missile.VelocityX ** 2 + missile.VelocityY ** 2 + missile.VelocityZ ** 2) ** (1/2)
    turning_radius = missile_velocity / (TURNING_SPEED * PI)
    return turning_radius < distance_between_missile_and_ship(missile,secondary_target)


#Arguments: the missile to be checked, a list of assets
#Returns the PRIMARY target of this missile (if it redirects)
def find_primary_target(missile: _TRACKPB, asset_list : list[_ASSETPB]):
    closest_asset = asset_list[0]
    dist = distance_between_missile_and_ship(missile, asset_list[0])
    for asset in asset_list:
        if distance_between_missile_and_ship(missile, asset) < dist:
            closest_asset = asset
    return closest_asset



#returns the DISTANCE between a given missile and a given ship
def distance_between_missile_and_ship(missile : _TRACKPB, ship : _ASSETPB):
    return distance(missile.PositionX, missile.PositionY, 0, ship.PositionX, ship.PositionY, 0)

#returns the time it takes for a weapon from one ship to reach another
def time_between_ships(defending_ship : _ASSETPB, target_ship : _ASSETPB, weapon_type : _WEAPONPB):
    distance_between_ships = distance(defending_ship.PositionX,defending_ship.PositionY,defending_ship.PositionZ, 
                                      target_ship.PositionX, target_ship.PositionY, target_ship.PositionZ)
    if weapon_type.SystemName == "Chainshot":
        weapon_speed = 1234
    else:
        weapon_speed = 3500
    return distance_between_ships / weapon_speed


#Arguments: firing ship, the missile it is targeting, and a List of assets 
#Returns the SLOWEST weapon on the ship that can reach the weapon in time
def slowest_available_ship_weapon(missile: _TRACKPB, asset_list, ship: _ASSETPB):
    for i in len(ship.weapons):
        weapon = ship.weapons[i]
        if weapon.WeaponState == "Ready" and can_reach_missile_in_time(missile,asset_list,ship,weapon):
            if weapon.SystemName == "Chainshot" or i == len(ship.weapons) - 1:
                return weapon



def can_reach_missile_in_time(missile:_TRACKPB, asset_list, defending_ship : _ASSETPB, weapon_type : _WEAPONPB):
    target_ship = find_primary_target(missile, asset_list)
    return time_between_ships(defending_ship, target_ship, weapon_type) < time_between_missile_and_ship(missile,target_ship)

#returns the time between a missile and its target
def time_between_missile_and_ship(missile : _TRACKPB, ship : _ASSETPB):
    missile_velocity = (missile.VelocityX ** 2 + missile.VelocityY ** 2 + missile.VelocityZ ** 2) ** (1/2)
    return distance_between_missile_and_ship(missile,ship) / missile_velocity

#Arguments: a missile, the dictionary mapping ships to missiles targeting them
#The dictionary mapping missiles to their targets
#Returns: the expected value of destroying this missile; want to use distance as a tiebreaker 
def expected_value(missile : _TRACKPB, target_dict, missile_target_dict):
    target = missile_target_dict[missile.TrackId] #What ship is being targeted
    m_with_same_t = len(target_dict[target.AssetName]) #How many missiles are targeting this target
    distance_between_missile_and_target = distance_between_missile_and_ship(missile,target)
    if target.isHVU and m_with_same_t >= 4:
        return 9000 + 10 / distance_between_missile_and_target
    elif target.isHVU:
        return 2000 + 10 / distance_between_missile_and_target
    elif m_with_same_t >= 4:
        return 5000 + 10 / distance_between_missile_and_target
    else:
        return 1000 + 10 / distance_between_missile_and_target


#Arguments: the most targeted ship and the list of missiles targeting it
#Returns the closest missile to that ship
def find_closest_missile(mts : _ASSETPB, missiles_list : list[_TRACKPB]):
    min_dist = 1000000
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



