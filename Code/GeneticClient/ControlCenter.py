"""
The ControlCenter's role is to make overarching decisions, authorizing each weapon to fire at targets.
"""
from PlannerProto_pb2 import TrackPb


class ControlCenter:
    def __init__(self):
        """
        Constructor for ControlCenter.
        """
        print("placeholder")

    def decide(self, proposed_actions, trackId_to_track: dict[int, TrackPb]):
        """
        This function takes a list of sets of all proposed (weapon_system, ship, target, ActionRule) tuples as an
        argument. Each element of the list will be a set of (weapon_system, ship, target, ActionRule) tuples that
        corresponds to a single target. Using this list, the ControlCenter decides on the best action to take for each
        target, and returns the selected actions as a list of (weapon_system, ship, target, ActionRule) tuples.

        TODO: make sure the same weapon is not selected twice — if the same weapon is optimal for two different
              targets, the current selection algorithm will use that same weapon. This is not possible in-simulation,
              and will cause problems.

        @param proposed_actions: A dictionary of sets of proposed (weapon_system, ship, ActionRule) tuples.
        @param trackid_to_track: A dictionary with track IDs as keys and tracks as objects

        @return: A list of accepted (weapon_system, ship, target, ActionRule) tuples.
        """

        # TODO: implement immune system dynamics (system of ODEs)

        finalized_action_list = []

        # for each target, find the best action from its set in proposed_actions
        for track_id in proposed_actions:
            best_action = None

            # find best action for this target
            for action in proposed_actions[track_id]:
                if best_action is None:
                    best_action = action
                elif action[2].get_fitness() > best_action[2].get_fitness():
                    best_action = action

            # put best action in the final action list
            finalized_action_list.append((best_action[0], best_action[1], trackId_to_track[track_id], best_action[2]))

        return finalized_action_list
