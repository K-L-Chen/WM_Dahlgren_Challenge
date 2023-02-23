# PROTOCOL BUFFER NOTES
The purpose of this file is to understand what each specific protocol buffer is within the `PlannerProto_pb2.py`.

## General Ideas
Our code: gets a state protocol-buffer (StatePb) from the JCore env;  
returns an output protocol-buffer (OutputPb)  

## StatePb
- assets : our weapons & ships -> assetPb
- tracks : in what way are assets moving -> trackPb

## AssetPb
- AssetName
- isHVU : is High Value Unit
- health
- PositionX
- PositionY
- PositionZ
- VelocityX
- VelocityY
- VelocityZ

## TrackPb
- TrackID
- ThreatID
- ThreatRelationship
- Lle : we have no idea what this is
- PositionX
- PositionY
- PositionZ
- VelocityX
- VelocityY
- VelocityZ

## OutputPb
- Just a field descriptor!
- actions : ShipActionPb

## ShipActionPb
- TargetID
- AssetName
- Weapon : WeaponPb

## WeaponPb
- SystemName
- Quantity
- WeaponState
