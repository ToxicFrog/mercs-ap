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

class ProgressiveIntel(Toggle):
  '''
  If enabled, intel items will be progressive: all intel items you collect will
  count towards your next Ace until that Ace is unlocked, then the Ace after
  that, etc.

  If disabled, intel items are specific to a suit and collecting items for a
  later Ace doesn't help you unlock earlier ones.
  '''
  default: False

class IntelAmount(NamedRange):
  '''
  This many intel items will be added to the pool for each Ace in the game.
  With default settings, this results in 3 per Ace, for a total of 12. Setting
  this higher than intel_target_per_ace will result in extra intel items in the
  pool (and thus generally a faster game).

  Setting it to 0 enables vanilla behaviour: each Ace gets 3 "face card" intel
  items worth 30 points, and 9 "number card" intel items worth [2..10] points,
  and you need a total of 80 points to unlock each Ace.
  '''
  display_name = 'Intel Items per Ace'
  range_start = 0
  range_end = 12
  default = 3
  special_range_names = {
    'vanilla': 0
  }

class IntelTarget(Range):
  '''
  Number of intel items needed to unlock each Ace. Has no effect if
  intel_in_pool_per_ace is set to 0 (vanilla).
  '''
  display_name = 'Intel Required per Ace'
  range_start = 1
  range_end = 12
  default = 3

@dataclass
class MercenariesOptions(PerGameCommonOptions):
  goal: Goal
  progressive_intel: ProgressiveIntel
  intel_in_pool_per_ace: IntelAmount
  intel_target_per_ace: IntelTarget
