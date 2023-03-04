from PlannerProto_pb2 import StatePb, ShipActionPb
from random import random


class Environment:
    """       
    output_size:
        Our output layer has 301 nodes
            - 5 ships * 30 targets * 2 weapon types = 300
            - Each node is the probability that ship x will target enemy y with weapon type z
            - plus a node that tells you to do nothing
    """
    N_ACTIONS = 301
    """
    input_size: number of input nodes
        Our specific setup is 220 input nodes:
        - We have up to 5 ships, each having:
            - Health (up to 4)
            - Ammo for Cannon_System
            - Ammo for Chainshot_System
            - Cannon_System Ready or not Ready
            - Chainshot_System Ready or not Ready
            - x position
            - y position
            - whether ship is high value (HVU) or not
        - We have up to 30 missiles, each having:
            - x position
            - y position
            - z position
            - x velocity
            - y velocity
            - z velocity
        - We have up to 30 friendly missles, each having:
            - x position
            - y position
            - z position
            - x velocity
            - y velocity
            - z velocity
            - target
        - Therefore, 5 ships * 8 attributes/ship + 30 missiles * 6 attributes/missile = 220 total attributes
        - Less than five ships or 30 missiles means we'll zero out the corresponding input nodes 
    """
    N_OBSERVATIONS = 210
    def __init__():
        pass

    