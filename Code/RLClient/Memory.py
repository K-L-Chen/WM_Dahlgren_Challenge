from __future__ import absolute_import
import random
from collections import deque, namedtuple

# don't encode inaction when weapon are unavailable, only explicit actions

Transition = namedtuple('Transition',
                        ('state', 'action', 'next_state', 'reward'))

class Memory(object):

    BATCH_SIZE = 25
    DIST_QUOTIENT = 3/5
    BACKFILL_LIMIT = 50
    def __init__(self, capacity):
        self.memory = deque([], maxlen=capacity)

    def push(self, transition):
        """Save a transition"""
        self.memory.append(transition)

    def sample(self):
        return random.sample(self.memory, min(self.BATCH_SIZE, len(self.memory)))

    def backfill_batch(self, score_mod):
        for idx in range(len(self.memory)):
            self.memory[idx][-1] += int(score_mod * (((1 - self.DIST_QUOTIENT) / len(self.memory)) * idx + self.DIST_QUOTIENT))

    def __len__(self):
        return len(self.memory)