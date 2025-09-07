from itertools import chain
from math import ceil,floor
from typing import NamedTuple

from ..id import next_id

class BountyLocation(NamedTuple):
  id: int
  type: str
  count: int
  total: int

  def short_name(self):
    return f'{self.type}{self.count}'

  def name(self):
    verb = 'Find' if self.type in {'blueprint', 'treasure'} else 'Destroy'
    return f'{verb} {self.count} {self.type}{'s' if self.count > 1 else ''}'

  def should_include(self, options):
    if self.chapter() > options.goal:
      return False

    nrof_checks = options.bounty_checks[self.type]
    if nrof_checks == 'vanilla':
      return self.count in VANILLA_BOUNTY_THRESHOLDS[self.type]
    elif nrof_checks == 'all':
      return True
    else:
      assert nrof_checks <= self.total
      # We want an evenly distributed set of integers in the range [1..total]
      # that includes both the start and end of that range and has size nrof_checks.
      return self.count in {
        1 + floor(n/(nrof_checks-1)*(self.total-1))
        for n in range(nrof_checks)
      }

  def chapter(self):
    chapter = ceil(self.count/self.total*4)
    if self.count > SOUTH_BOUNTIES[self.type]:
      chapter = max(3, chapter)
    return chapter

  def groups(self):
    return {'bounties', f'{self.type}_bounties'}

  def is_checked(self, game):
    return game.is_bounty_collected(self.type, self.count)

  def is_hintable(self, found):
    # TODO: maybe the unused mission hints should provide hints for progression
    # items found in the bounty sequences?
    return False

  def access_rule(self, world):
    # There aren't really any hard limits on when the player can go out and find
    # these, except that the NK ones aren't accessible in the first half of the
    # game.
    # However, we don't want all of them to be in logic from the word go, because
    # that would be unbearably tedious when it decides that blueprint 50 contains
    # morph ball.
    # So instead we assign them to chapters, and further subdivide them using
    # the same combat logic as missions.
    rank = ceil(self.count/self.total*12)
    def rule(state):
      return world.has_combat_power_for_rank(state, rank)

    return rule


VANILLA_BOUNTY_THRESHOLDS = {
  'blueprint': {1, 5, 10, 15, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110},
  'treasure': {1, 5, 10, 15, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110},
  'monument': {10, 20},
  'listening post': {10, 20, 30, 40, 50, 55},
}

# How many of each you can find in SK in chapters 1/2.
SOUTH_BOUNTIES = {
  'blueprint': 59,
  'treasure': 53,
  'monument': 10,
  'listening post': 25,
}

BOUNTIES = {
  bounty.short_name(): bounty
  for bounty in chain(
    [BountyLocation(next_id(), 'blueprint', i, 110) for i in range(1, 110+1)],
    [BountyLocation(next_id(), 'treasure', i, 110) for i in range(1, 110+1)],
    [BountyLocation(next_id(), 'monument', i, 21) for i in range(1, 21+1)],
    [BountyLocation(next_id(), 'listening post', i, 56) for i in range(1, 56+1)],
  )
}
