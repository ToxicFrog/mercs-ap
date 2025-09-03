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
  In normal play, all intel items are specific to a suit, and collecting intel
  for one Ace doesn't help you unlock any of the others. Enabling this will
  replace all suited intel items with progressive intel items, that provide
  intel towards whatever your next Ace is.
  '''
  display_name = 'Progressive Intel'
  default: False

class VanillaIntel(Toggle):
  '''
  Enables the vanilla intel behaviour.

  If turned on, intel_in_pool is ignored; instead the 48 intel items from the
  vanilla game are shuffled into the pool. Each suit gets 3 "face" intel items
  worth 30 points, and 9 "number" intel items worth 2-10 points.

  To change how many you need, use vanilla_intel_target instead of intel_target.
  '''
  display_name = 'Vanilla Intel'
  default: False

class VanillaIntelTarget(Range):
  '''
  Number of intel points needed to unlock each Ace when vanilla_intel is on.

  The default is 80, which means each Ace needs either all three face cards, or
  any two face cards + 3-6 number cards.

  The maximum value of 144 requires you to collect every single intel item in
  the game.
  '''
  display_name = 'Vanilla Intel Target'
  range_start = 5
  range_end = 144
  default = 80

class IntelAmount(Range):
  '''
  Number of intel items added to the pool. You will need to collect intel_target
  of these *per Ace* to unlock the Ace missions. You can add more to the pool
  than you actually need if you want a faster game.

  If progressive_intel is off, this must be a multiple of the number of chapters
  you've selected, and it will be evenly split between the suits for those
  chapters. If it's on you can choose any amount you want.

  If vanilla_intel is enabled, this option is ignored.
  '''
  display_name = 'Intel in Pool'
  range_start = 4
  range_end = 48
  default = 12  # 3 per Ace

class IntelTarget(Range):
  '''
  Number of intel items needed to unlock each Ace. You will require a total of
  goal * intel_target items to complete the game.

  If vanilla_intel is enabled, this option is ignored.
  '''
  display_name = 'Intel Target'
  range_start = 1
  range_end = 12
  default = 3

@dataclass
class MercenariesOptions(PerGameCommonOptions):
  goal: Goal
  progressive_intel: ProgressiveIntel
  vanilla_intel: VanillaIntel
  vanilla_intel_target: VanillaIntelTarget
  intel_in_pool: IntelAmount
  intel_target: IntelTarget
