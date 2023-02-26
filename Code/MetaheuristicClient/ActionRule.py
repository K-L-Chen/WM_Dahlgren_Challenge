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

"""
@cvar BOUNDS
bounds for random initialization, 2D numpy array
order of bound values:
"distance_to_target", "target_speed", "target_heading", "target_height", "other_ship_priority", "num_weapons",
             "nearby_ship_health", "my_ship_health", "num_targets"
"""
BOUNDS = np.array([[0, 1000], # distance_to_target
                   [0, 1400], # target_speed
                   [0, 180], #  target_heading
                   [0, 2000], # target_height
                   [0, 25], #   other_ship_priority
                   [0, 100], #  num_weapons
                   [0, 100], #  nearby_ship_health
                   [0, 4], #    my_ship_health
                   ] 
                )

""" @cvar CONDITIONAL_ATTRIBUTE_COUNT — The number of conditional attributes that each ActionRule contains. """
CONDITIONAL_ATTRIBUTE_COUNT = 8


class ActionRule:
    # fields for updating ActionRule fitness
    predicted_value = 0.0
    predicted_val_error = 0.0
    fitness = 0.0
    accuracy = 0.0
    relative_accuracy = 0.0

    def __init__(self, attr:np.ndarray = None, cond_bits:int = None):
        """
        Constructor for ActionRule

        @param attr (): An optional parameter, if not None, are a 2D arr. of values used to initialize this ActionRule.
        @param cond_bits: An optional parameter, if not None, is an integer encoding the conditionals detailed below.
        """

        # make vectors for attr name, vec
        # think about making them into dataframes
        self.attr_name_vec = np.array(
            ["distance_to_target", "target_speed", "target_heading", "target_height", "ship_compassion",
             "num_weapons", "nearby_ship_health", "my_ship_health", "num_targets"])


        # manually specify attr_vec and conditional_bits
        if attr is not None and cond_bits is not None:
            self.attr_vec = attr
            self.conditional_bits = cond_bits

        # throw error if input is invalid
        elif attr is None or cond_bits is None:
            raise RuntimeError("Must specify both attr and cond_bits if manually instantiating!")

        # if nothing is passed, randomly initialize attr_vec and conditional_bits, based on BOUNDS
        else:
            self.attr_vec = np.random.uniform(BOUNDS[:, 0], BOUNDS[:, 1])
            # self.attr_vec = np.rand(CONDITIONAL_ATTRIBUTE_COUNT)
            # for idx in range(len(self.attr_vec)):
            #     # scales each attribute to the bounds specified
            #     self.attr_vec[idx] = self.attr_vec[idx] * \
            #         (BOUNDS[idx][1] - BOUNDS[idx][0]) + BOUNDS[idx][0]

            """
            Store all of our AND/OR, GE/LE decisions as 2 bit values in a long(?)
            start on the right hand side, so:
            distance_to_target is at bits 1 and 0
            target_speed is at bits 3 and 2, etc...
            odd num bits are AND/OR -> 0/1
            even num bits are LE/GE -> 0/1
            to change values, place all bits we want to flip into a number
            then XOR that number with conditional_bits
            e.g. we want to flip bit 3, then we XOR conditional_bits with 0x4
            """
            self.conditional_bits = np.random.randint(0, 2 ** (2 * CONDITIONAL_ATTRIBUTE_COUNT))

        # TODO maybe PCA it if we have time
        # TODO optimize if/else chains with lists, vectors, or other ways

    def update_predicted_values(self, reward, step):
        """
        Given the reward from an action, update predicted_value, predicted_val_error, and accuracy. Return accuracy.

        @param reward: The reward quantity from an action
        @param step: The step size for an update
        @return: NOTHING FOR NOW — later: (accuracy value for an action, as a double)
        """

        # right now, we are only updating predicted_value
        self.predicted_value = self.predicted_value + \
            step * (reward - self.predicted_value)

    def update_fitness(self, accuracy_sum):
        """
        Given the accuracy_sum, the sum of accuracy values for all other ActionRules that were executed at the
            same time step, update relative_accuracy and fitness.
        @param accuracy_sum: The sum of accuracy values for all other ActionRules that were executed at the
            same time step
        @return:
        """
        # TODO: Consider extra fitness parameters

    def get_fitness(self):
        """
        @return: The current fitness value for this ActionRule
        """
        return self.predicted_value

    def update_conditional_attributes(self, update_value):
        """
        Updates the attributes of the conditionals encoded within this ActionRule
        (e.g. (AND or OR) and (< or >))

        @param update_value: The update to the conditional bits that we want to carry out — an integer interpreted as
            a bitstring — use a 1 in the positions you want the bit to be flipped, and a 0 in the positions where you
            would not want a bit to be flipped.

            Example: If the conditional bits are 0101011, and the input value is 1001000, the updated conditional bits
                will be 1100011.
        @return: None
        """
        self.conditional_bits = self.conditional_bits ^ update_value

    def get_conditional_attributes(self):
        """
        @return: The conditional attributes bitstring
        """
        return self.conditional_bits

    def update_conditional_values(self, update_vec):
        """
        Updates the values encoded within the conditional.
        @param update_vec: New values to use in the conditional, as a numpy vector.
        @return: None
        """
        self.attr_vec = update_vec

    def get_conditional_values(self):
        """
        @return: The values encoded within the conditional.
        """
        return self.attr_vec
