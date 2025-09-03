from math import ceil,floor

from Options import PerGameCommonOptions, Toggle, DeathLink, StartInventoryPool, OptionSet, NamedRange, Range, OptionDict
from dataclasses import dataclass

'''
Options to implement:
- vanilla vs. fixed intel
- per-card vs. progressive intel
- missable location behaviour
- goal (how many chapters to play)

Options that will be useful once we have more features:
- whether to include collectibles
- whether to include collectible thresholds
- filler options: MOM discounts, faction bonuses, etc
'''

@dataclass
class MercenariesOptions(PerGameCommonOptions):
  pass
