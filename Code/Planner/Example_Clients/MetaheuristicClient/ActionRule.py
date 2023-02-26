"""
    The ActionRule class encodes logic for a decision to fire. Each ActionRule object is a wrapper around a specialized
    if-then statement. It has a set of conditionals describing the state of units and ships. It is also the candidate
    that the genetic algorithm will evolve over time, and also contains pertinent variables.

    An ActionRule object could look like this:
        "IF distance from target IS low AND velocity IS medium AND heading IS high THEN fire".

    Since any one weapon could only fire or not fire at any time step, the consequent of this conditional is
    always fire.

    This is analogous to the classifier from the immunized classifier paper.
"""
import numpy as np

class ActionRule:
    # fields for updating ActionRule fitness
    predicted_value = 0.0
    predicted_val_error = 0.0
    fitness = 0.0
    accuracy = 0.0
    relative_accuracy = 0.0

    def __init__(self):
        #decision variables
        self.distance_to_target = 0
        self.target_speed = 0
        self.target_heading = 0 #abs value of angle
        self.target_height = 0
        
        #most important decision vars
        self.nearby_ships = 0
        self.nearby_weapons = 0
        self.nearby_ship_health = 0
        self.my_ship_health = 0

        #make vectors for attr name, vec
        #think about making them into dataframes
        self.attr_name_vec = np.array(["distance_to_target", "target_speed", "target_heading", "target_height", "nearby_ships", "nearby_weapons", "nearby_ship_health", "my_ship_health"])
        self.attr_vec = np.zeros(8)

        # TODO consider AND vs OR style of policy, use greater than or less than
        # store all of our AND/OR, GE/LE decisions as 2 bit values in a long(?)
        # start at the right hand side, so:
        # distance_to_target is at bits 1 and 0
        # target_speed is at bits 3 and 2, etc...
        # odd num bits are AND/OR -> 0/1
        # even num bits are GE/LE -> 0/1
        # to change values, place all bits we want to flip into a number
        # then XOR that number with conditional_bits
        # e.g. we want to flip bit 3, then we XOR conditional_bits with 0x4
        self.conditional_bits = 0

        # TODO maybe PCA it if we have time
        # TODO optimize if/else chains with lists, vectors, or other ways

        print("placeholder")

    def update_predicted_values(self, reward):
        """
        Given the reward from an action, update predicted_value, predicted_val_error, and accuracy. Return accuracy.

        @param reward: The reward quantity from an action
        @return: accuracy value for an action, as a double
        """

    def update_fitness(self, accuracy_sum):
        """
        Given the accuracy_sum, the sum of accuracy values for all other ActionRules that were executed at the
            same time step, update relative_accuracy and fitness.
        @param accuracy_sum: The sum of accuracy values for all other ActionRules that were executed at the
            same time step
        @return:
        """
