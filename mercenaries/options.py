from math import ceil,floor

from Options import PerGameCommonOptions, Toggle, DeathLink, StartInventoryPool, OptionSet, NamedRange, Range, OptionDict
from dataclasses import dataclass

'''
Options to implement:
- vanilla vs. fixed intel
- per-card vs. progressive intel
- missable location behaviour

Options that will be useful once we have more features:
- whether to include collectibles
- whether to include collectible thresholds
- filler options: MOM discounts, faction bonuses, etc
'''

class Goal(NamedRange):
  '''
  Select a win condition. The default is to complete chapter 4 by verifying the
  Ace of Spades, but if you want a shorter game you can select an earlier chapter
  as your goal.
  '''
  display_name = 'Win Condition'
  range_start = 1
  range_end = 4
  default = 4
  special_range_names = {
    'chapter1': 1,
    'chapter2': 2,
    'chapter3': 3,
    'chapter4': 4,
  }

@dataclass
class MercenariesOptions(PerGameCommonOptions):
  goal: Goal
