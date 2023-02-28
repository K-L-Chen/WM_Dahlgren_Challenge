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
from numpy import ndarray

"""
@cvar BOUNDS
bounds for random initialization, 2D numpy array

TODO: investigate target_height, since the cruising attitude
is either 20 meters or 1000 meters according to slide #10 on
the Planner Instruction Manual
"""
BOUNDS = np.array([[0, 1000],  # distance_to_target
                   [0, 1400],  # target_speed
                   [0, 180],  # target_heading
                   [0, 2000],  # target_height
                   [0, 8],  # other_ship_priority
                   [0, 100],  # num_weapons
                   [0, 100],  # nearby_ship_health
                   [0, 4],  # my_ship_health
                   [0, 30],  # num_targets
                   ]
                  )

""" @cvar CONDITIONAL_ATTRIBUTE_COUNT — The number of conditional attributes that each ActionRule contains. """
CONDITIONAL_ATTRIBUTE_COUNT = 9
"""@cvar CONDITIONAL_NAMES - identifiers to the conditional attributes"""
CONDITIONAL_NAMES = ["distance_to_target", "target_speed", "target_heading", "target_height", "other_ship_priority",
                     "num_weapons", "nearby_ship_health", "my_ship_health", "num_targets"]

if len(CONDITIONAL_NAMES) != CONDITIONAL_ATTRIBUTE_COUNT:
    raise RuntimeError("CONDITIONAL_ATTRIBUTE_COUNT must match with length of CONDITIONAL_NAMES")


class ActionRule:
    def __init__(self, conditional_vals: np.ndarray = None, cond_bits: int = None):
        # fields for updating ActionRule fitness
        self.predicted_value = 0.0
        self.predicted_val_error = 0.0
        self.fitness = 0.0
        self.accuracy = 0.0
        self.relative_accuracy = 0.0

        """
        Constructor for ActionRule

        An ActionRule is essentially a list of conditionals, or a policy for short
        - These conditionals can be combined with either AND or OR
            (e.g. if dist_to_target < 500 AND target_speed > 686 OR ... AND num_targets < 4)

        @param (optional) conditional_vals: an arr. of values to compare against for the policy
            - each val. is either a lower bound ("greater than", >) or an upper bound ("lesser than", <)

        @param (optional) cond_bits: an integer encoding additional info. of the policy detailed below.
        """

        # self.conditional_vals_names = np.array(
        #     ["distance_to_target", "target_speed", "target_heading", "target_height", "other_ship_priority",
        #      "num_weapons", "nearby_ship_health", "my_ship_health", "num_targets"]
        #      )

        # manually specify conditional_vals and conditional_bits
        if conditional_vals is not None and cond_bits is not None:
            self.conditional_vals = conditional_vals
            self.conditional_bits = cond_bits

        # throw error if input is invalid
        elif (conditional_vals is None and cond_bits is not None) or \
                (conditional_vals is not None and cond_bits is None):
            raise RuntimeError("Must specify both conditional values and cond_bits if manually instantiating!")

        # if nothing is passed, randomly initialize lower_upper_bounds_vec and conditional_bits, based on BOUNDS
        else:
            self.conditional_vals = np.random.randint(low=BOUNDS[:, 0], high=BOUNDS[:, 1] + 1)
            # self.lower_upper_bounds_vec = np.rand(CONDITIONAL_ATTRIBUTE_COUNT)
            # for idx in range(len(self.lower_upper_bounds_vec)):
            #     # scales each lower_upper_boundsibute to the bounds specified
            #     self.lower_upper_bounds_vec[idx] = self.attr_vec[idx] * \
            #         (BOUNDS[idx][1] - BOUNDS[idx][0]) + BOUNDS[idx][0]

            """
            `conditional_bits` definition

            Store all of our AND/OR, greater than/less than decisions as 2 bit values in a long(?)
            start on the right hand side, so:
            distance_to_target is at bits 1 and 0
            target_speed is at bits 3 and 2, etc...
            EVEN indexed bits are AND/OR -> 0/1
            ODD indexed bits are LE/GE -> 0/1
            to change values, place all bits we want to flip into a number
            then XOR that number with conditional_bits
            e.g. we want to flip bit 3, then we XOR conditional_bits with 0x4
            """
            self.conditional_bits = np.random.randint(0, 2 ** (2 * CONDITIONAL_ATTRIBUTE_COUNT))

        # TODO maybe PCA it if we have time
        # TODO optimize if/else chains with lists, vectors, or other ways

    def update_predicted_values(self, reward: int, step: float):
        """
        Given the reward from an action, update predicted_value, predicted_val_error, and accuracy. Return accuracy.

        @param reward: The reward quantity from an action
        @param step: The step size for an update
        @return: NOTHING FOR NOW — later: (accuracy value for an action, as a double)
        """

        # right now, we are only updating predicted_value
        # self.predicted_value += step * (reward - self.predicted_value)
        self.predicted_value += step * reward
                               

    def update_fitness(self, accuracy_sum: float):
        """
        Given the accuracy_sum, the sum of accuracy values for all other ActionRules that were executed at the
            same time step, update relative_accuracy and fitness.
        @param accuracy_sum: The sum of accuracy values for all other ActionRules that were executed at the
            same time step
        @return:
        """
        # TODO: Consider extra fitness parameters
        pass

    def get_fitness(self):
        """
        @return: The current fitness value for this ActionRule
        """
        return self.predicted_value

    def update_conditional_attributes(self, update_value: int):
        """
        Updates the attributes of the conditionals encoded within this ActionRule
        (e.g. (AND or OR) and (< or >))

        @param update_value: The update to the conditional bits that we want to carry out — an integer interpreted as
            a bitstring — use a 1 in the positions you want the bit to be flipped, and a 0 in the positions where you
            would not want a bit to be flipped.

        - Useful Python syntax: you can pass in update_value as the bitstring directly with 0b1010... 
        for example, and Python will automatically convert that into its respective integer to 
        perform the XOR (^) bitwise operation
        - Python will not use leading 0s in its binary representation if it doesn't have to, which
         means that the representation's length is not always 2 * CONDITIONAL_ATTRIBUTE_COUNT,
        but this is not an issue as when we want to change any of these leadings 0s to 1s

        Example: If the conditional bits are 0101011, and the input value is 1001000, the updated conditional bits
            will be 1100011.
        @return: None
        """
        self.conditional_bits = self.conditional_bits ^ update_value

    def get_cond_bitstr(self):
        """
        @return: The conditional attributes bitstring
        """
        return self.conditional_bits

    def update_conditional_values(self, update_vec: ndarray[float]):
        """
        Updates the values encoded within the conditional.
        @param update_vec: New values to use in the conditional, as a numpy vector.
        @return: None
        """
        self.conditional_vals = update_vec

    def get_conditional_values(self) -> ndarray[int]:
        """
        @return: The values encoded within the conditional.
        """
        return self.conditional_vals
