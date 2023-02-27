"""
The ControlCenter's role is to make overarching decisions, authorizing each weapon to fire at targets.
"""
import random
from PlannerProto_pb2 import WeaponPb, AssetPb, TrackPb
from ActionRule import ActionRule


class ControlCenter:
    def __init__(self):
        """
        Constructor for ControlCenter.
        """
        print("placeholder")

    def decide_action_per_target(self, proposed_actions: dict[int, set[tuple[WeaponPb, AssetPb, ActionRule]]],
                                 trackid_to_track: dict[int, TrackPb]):
        """
        This function takes as input a dictionary, mapping each target to
        a set of all proposed weapon assignment tuples for that target. 
        The function aims to choose the best action of the set for each target. It therefore filters out redundant
        actions and ensures every weapon assigned has a unique target.

        @param proposed_actions: A dictionary of sets of proposed (weapon_system, ship, ActionRule) tuples.
            - format: {track_id: {(weapon, ship, action_rule_that_applies)}}
        @param trackid_to_track: A dictionary with track IDs as keys and tracks as objects
        """
        # TODO: implement immune system dynamics (system of ODEs)
        # TODO: simple greedy strategy (see below)

        # finalized_action_list = []

        # for each target, find the best action from its set in proposed_actions
        for track_id in proposed_actions:
            best_action = None # will remain as None when there is no applicable action rule or when
            # all actions have the same fitness

            # find best action for this target
            for action in proposed_actions[track_id]:
                # if best_action is None:
                #     best_action = action
                if action[2].get_fitness() > action[2].get_fitness():
                    best_action = action

            # don't forget that it's possible that no proposed action might exist
            if best_action is not None:
                # replace list of potential actions with the action we'll take for this target
                best_weapon = best_action[0]

                if best_weapon.Quantity > 0 and best_weapon.WeaponState == "Ready":
                    proposed_actions[track_id] = best_action
                else:
                    proposed_actions[track_id] = None

            else:
                # TODO: revise this to a simple greedy strategy for this target
                proposed_actions[track_id] = self.backup_action_for_target(
                    trackid_to_track[track_id], proposed_actions[track_id])


    def backup_action_for_target(self, target: TrackPb, 
                                 proposed_target_actions: set[tuple[WeaponPb, AssetPb, ActionRule]]):
        """Backup in there is no best action (either because of uniform fitness or there is no applicable action rule)"""
        if not proposed_target_actions:
            return

        else: # TODO: replace with greedy strategy, or some strategy that utilizes
              # info. about the impending target
            return random.choice(list(proposed_target_actions))
