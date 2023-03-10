from PlannerProto_pb2 import _TRACKPB, _ASSETPB, _WEAPONPB
from random import choice
from math import sqrt
PI = 3.14159265
TURNING_SPEED = 25

def distance(x1, y1, z1, x2, y2, z2):
    return ((x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2) + (z1 - z2) * (z1 - z2)) ** (1/2)


#Finds WHEN a given missile will reach its SECONDARY target if it exists
#Returns a number of seconds in the future
def time_to_reach_secondary(missile: _TRACKPB, targeting_missiles, asset_list : list[_ASSETPB] ):
    #Calculate WHEN the primary target will be destroyed
    primary_target = find_primary_target(missile,asset_list)
    #time to destruction
    ttd = when_ship_will_be_destroyed(primary_target,targeting_missiles)
    #Estimate WHERE our missile will be at this time
    est_x = missile.PositionX + missile.VelocityX * ttd
    est_y = missile.PositionY + missile.VelocityY * ttd
    est_z = missile.PositionZ + missile.VelocityZ * ttd
    #Calculate WHEN missile will reach secondary target FROM this position IF it can reach it
    secondary_target  = find_secondary_target(missile,asset_list)
    if secondary_target is None or not can_reach_secondary_target(missile,secondary_target):
        return 301
    missile_velocity = (missile.VelocityX ** 2 + missile.VelocityY ** 2 + missile.VelocityZ ** 2) ** (1/2)
    return missile_velocity / distance(est_x,est_y,est_z, secondary_target.PositionX,secondary_target.PositionY,secondary_target.PositionY)

#ship is the ship that will be destroyed
#targeting_missiles is a list of the missiles that are targeting a given ship
def when_ship_will_be_destroyed(ship, targeting_missiles):
    def ttd(tm):
        return time_between_missile_and_ship(tm,ship)
    targeting_missiles.sort(reverse = True, key=ttd)
    killing_missile = targeting_missiles[ship.health - 1]
    return time_between_missile_and_ship(killing_missile,ship)
    
#Returns the TOTAL remaining ammo for our entire fleet
#Argument: a list of our assets
#def total_remaining_ammo(asset_list : list[_ASSETPB]):
#    remaining_ammo = 0
#    for asset in asset_list:
#        for weapon in asset.weapons:
#            remaining_ammo = remaining_ammo + weapon.Quantity
#    return remaining_ammo

# UPDATED version of above function
def total_remaining_ammo(wep_info):
    total = 0
    for ship in wep_info:
        for weapon in ship:
            total += weapon[1]
    return total
        

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

def findSecondaryTarget_with_tuples(missile_pos: tuple[int], asset_pos_list : list[tuple[int]]):
    if len(asset_pos_list) < 2:
        return None
    primary_asset = find_primary_asset_of_enemy(missile_pos, asset_pos_list)
    primary_asset_pos = asset_pos_list[primary_asset]
    temp2 = primary_asset_pos[-1]

    secondary_target = None
    cur_dist = 1e10
    for asset in asset_pos_list:
        if asset != primary_asset:
            curr_asset_pos = asset_pos_list[asset]
            temp1 = curr_asset_pos[-1]
            curr_asset_pos[-1] = 0 
            # dist_btwn_ships = distance(primary_target.PositionX,primary_target.PositionY,0,asset.PositionX,asset.PositionY,0)
            dist_btwn_ships = distance(*primary_asset_pos, *curr_asset_pos)
            curr_asset_pos[-1] = temp1

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
#def slowest_available_ship_weapon(missile: _TRACKPB, asset_list, ship: _ASSETPB):
#   for i in len(ship.weapons):
#        weapon = ship.weapons[i]
#        if weapon.WeaponState == "Ready" and can_reach_missile_in_time(missile,asset_list,ship,weapon):
#            if weapon.SystemName == "Chainshot" or i == len(ship.weapons) - 1:
#                return weapon

#ARGUMENTS:
#   target: missile ID
#   wep_info: the whole list
#   ship: ship index
#
#RETURNS: 
#   (shipIndex, weaponIndex)
def slowest_avaliable_ship_weapon(target, wep_info, target_pos, target_vel, ship_pos, def_ship_pos):
    shipID, wepID = None, None
    
    best_time = 301

    for ship in wep_info:
        for i in range(2):
            if ship[i][1] > 0 and ship[i][2] == True:
                new_time, possible = missile_to_ship_info(target, target_pos, target_vel, wep_info[shipID][0], shipID, def_ship_pos)
                if possible and new_time > best_time:
                    best_time = new_time
                    shipID = ship
                    wepID = i
    
    return (shipID, wepID)
        
        

#Arguments: a ship and a list of missiles targeting it
#Returns true if the number of active missiles targeting it is greater than its health
def will_be_destroyed(ship: _ASSETPB, targeting_list):
    return targeting_list >= ship.health
    # num_threats = 0
    # for missile in missile_list:
    #     if find_primary_target(missile,asset_list) == ship:
    #         num_threats = num_threats + 1
    # return num_threats >= ship.health

#Returns true if weapon_type from defending_ship will reach missile before missile reaches its primary target
#Requires missile, asset_list, defending_ship, weapon_type
def can_reach_missile_in_time(missile:_TRACKPB, asset_list, defending_ship : _ASSETPB, weapon_type : _WEAPONPB):
    target_ship = find_primary_target(missile, asset_list)
    return time_between_ships(defending_ship, target_ship, weapon_type) < time_between_missile_and_ship(missile,target_ship)

#returns the time between a missile and its target
def time_between_missile_and_ship(missile : _TRACKPB, ship : _ASSETPB):
    missile_speed = (missile.VelocityX * missile.VelocityX + missile.VelocityY * missile.VelocityY + missile.VelocityZ * missile.VelocityZ) ** (1/2)
    return distance_between_missile_and_ship(missile,ship) / missile_speed

#updated time for weapon to missile
def missile_to_ship_info(target, target_pos, target_vel, wep_type, ship_pos, def_ship_pos):
    
    target_speed = sqrt(target_vel(0)**2, target_vel(1), (target_vel(2)*-1)**2)

    weapon_speed = 3500
    if wep_type == "Chainshot":
        weapon_speed = 1234

    wep_to_def = distance(*ship_pos, *def_ship_pos) / weapon_speed
    missile_to_def = distance(*target_pos, *def_ship_pos) / target_speed

    return (wep_to_def+missile_to_def)/2, (wep_to_def < missile_to_def)

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

def expected_value_new(primary_HVU, secondary_HVU, kill_1st, kill_2nd, reach_2nd):
    score = 0
    if not kill_1st:
        score = 1000
        if primary_HVU:
            score = 2000
    else:
        score = 5000
        if primary_HVU: 
            score = 9000
        if reach_2nd:
            if not kill_2nd:
                score += 500
                if secondary_HVU:
                    score += 500
            else:
                score += 2500
                if secondary_HVU:
                    score += 2000

    return score
    
        


    
            



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


def find_primary_asset_of_enemy(missile_pos: tuple[int], asset_pos_list : list[tuple[int]]):
    # z-coordiante does not matter
    preserved_missileZPos = missile_pos[-1]
    missile_pos[-1] = 0

    # find max. by comparisons with distance between first ship in the list 
    closest_asset = 0
    dist = distBtwnMissileAndShip_with_tuples(missile_pos, asset_pos_list[0])

    for asset_pos_idx in range(len(asset_pos_list)):
        # z-coordinate does not matter
        preserved_assetZPos = asset_pos_list[asset_pos_idx][-1]
        asset_pos_list[asset_pos_idx][-1] = 0 

        if distBtwnMissileAndShip_with_tuples(missile_pos, asset_pos_list[asset_pos_idx]) < dist:
            closest_asset = asset_pos_idx

        asset_pos_list[asset_pos_idx][-1] = preserved_assetZPos

    missile_pos[-1] = preserved_missileZPos
    return closest_asset

#returns the DISTANCE between a given missile and a given ship
def distBtwnMissileAndShip_with_tuples(missile_pos: tuple[int], ship_pos: tuple[int]):
    # return distance(missile.PositionX, missile.PositionY, 0, ship.PositionX, ship.PositionY, 0)
    return distance(*missile_pos, *ship_pos)



#returns the time between a missile and its target
def timeBtwnEnemyAndShip_with_tuples(enemy_velos: tuple[int], enemy_pos: tuple[int], ship_pos: tuple[int]):
    missile_speed = (enemy_velos[0] * enemy_velos[0] + enemy_velos[1] * enemy_velos[2] + enemy_velos[2] * enemy_velos[2]) ** 0.5
    return distBtwnMissileAndShip_with_tuples(enemy_pos, ship_pos) / missile_speed