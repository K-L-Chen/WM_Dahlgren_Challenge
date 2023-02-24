

class ActionRule:
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

    predicted_value = 0.0
    predicted_val_error = 0.0
    fitness = 0.0
    accuracy = 0.0
    relative_accuracy = 0.0

    def __init__(self):
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