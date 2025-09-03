from itertools import chain
from typing import NamedTuple, Set

from BaseClasses import Region

from ..id import next_id

MISSIONS = {}

class MissionLocation(NamedTuple):
  id: int
  min_chapter: int
  max_chapter: int
  faction: str  # 'A', 'K', 'M', or 'C'
  rank: int  # 1..12
  title: str
  prereqs: Set[str] = frozenset()
  is_ace: bool = False

  def short_name(self):
    return f'{self.faction}{self.rank}'

  def name(self):
    return f'Complete Mission {self.short_name()}: {self.title}'

  def groups(self):
    if self.faction == 'A':
      return {'missions', 'an_missions'}
    elif self.faction == 'K':
      return {'missions', 'sk_missions'}
    elif self.faction == 'M':
      return {'missions', 'mafia_missions'}
    elif self.faction == 'C':
      return {'missions', 'prc_missions'}
    return {'missions'}

  def access_rule(self, world):
    prereqs = {
      MISSIONS[prereq].access_rule(world) for prereq in self.prereqs
    }

    def rule(state):
      for prereq in prereqs:
        if not prereq(state):
          return False

      if world.power_level(state) < (self.rank-1)*3:
        return False

      if self.is_ace:
        return world.has_intel_for_chapter(state, self.min_chapter)

      return True

    return rule

AN_MISSION_NAMES = [
  'Ante Up', 'Out of the Woodwork', 'Bringing Down the House',
  'Embedded', 'Downed Bird in Enemy Nest', 'The Guns of Kirin-Do',
  'Inspect and Verify', 'Reactor Retrieval', 'Gambit',
  'Humanitarian Efforts', 'The Ace of Spades'
]

SK_MISSION_NAMES = [
  'Stem the Tide', 'A Proper Function of Government', 'A Farewell to Kings',
  'A Hot Time in Nampo', 'First Principles', 'Master of None',
  'Repo Man', 'Clear Channel', 'The Acid Queen',
  'In and Out', 'BOOM!', 'Titular Regius'
]

MAFIA_MISSION_NAMES = [
  'Foothold', 'Gimme my Money', 'Bait and Switch',
  'Playing the Odds', 'Omertà', '...It\'s Who You Know',
  'In the Neighborhood', '106 Miles to Sinuiju', 'Raw Materials',
  'Escort Service (Mafia)', 'Housekeeping', 'Loose Ends'
]

PRC_MISSION_NAMES = [
  'Pest Control', 'No One Will Ever Know', 'Under New Management',
  'Escort Service (PRC)', 'Persuasion', 'Knock Knock',
  'Manipulate the Data', 'Exit Strategy', 'Chain Reaction',
  'An Eye for an Eye', 'Chokepoint', 'Two Degrees of Separation'
]

# Fields are: id, min_chapter, max_chapter, short_name, name, prerequisite missions if any
# We don't list cards here, the link from card to mission is sufficient.
MISSIONS = {
  mission.short_name(): mission
  for mission in chain(
    # AN missions
    # We list these out explicitly because AN missions include the tutorial and
    # ace missions, which require special handling
    [
      MissionLocation(next_id(), 0, 0, 'A', 1, AN_MISSION_NAMES[0]),
      MissionLocation(next_id(), 0, 0, 'A', 2, AN_MISSION_NAMES[1], {'A1', 'K1', 'M1', 'C1'}),
      MissionLocation(next_id(), 0, 0, 'A', 3, AN_MISSION_NAMES[2], {'A2'}, True),
      MissionLocation(next_id(), 0, 0, 'A', 4, AN_MISSION_NAMES[3], {'A3'}),
      MissionLocation(next_id(), 0, 0, 'A', 5, AN_MISSION_NAMES[4], {'A4'}),
      MissionLocation(next_id(), 0, 0, 'A', 6, AN_MISSION_NAMES[5], {'A5'}, True),
      MissionLocation(next_id(), 0, 0, 'A', 7, AN_MISSION_NAMES[6], {'A6'}),
      MissionLocation(next_id(), 0, 0, 'A', 8, AN_MISSION_NAMES[7], {'A7'}),
      MissionLocation(next_id(), 0, 0, 'A', 9, AN_MISSION_NAMES[8], {'A8'}, True),
      MissionLocation(next_id(), 0, 0, 'A', 10, AN_MISSION_NAMES[9], {'A9'}),
      MissionLocation(next_id(), 0, 0, 'A', 11, AN_MISSION_NAMES[10], {'A10'}, True),
    ],
    # SK missions
    # T1 and T2 missions for SK and Mafia are listed explicitly because they don't
    # unlock until you complete the A1->K1->M1->C1 introductory mission chain.
    [
      MissionLocation(next_id(), 1, 4, 'K', 1, SK_MISSION_NAMES[0], {'A1'}),
      MissionLocation(next_id(), 1, 4, 'K', 2, SK_MISSION_NAMES[1], {'K1', 'C1'}),
    ],
    [
      MissionLocation(next_id(), i//3+1, 4, 'K', i+1, SK_MISSION_NAMES[i], {f'K{i}'})
      for i in range(2,12)
    ],
    # Mafia missions
    [
      MissionLocation(next_id(), 1, 4, 'M', 1, MAFIA_MISSION_NAMES[0], {'K1'}),
      MissionLocation(next_id(), 1, 4, 'M', 2, MAFIA_MISSION_NAMES[1], {'M1', 'C1'}),
    ],
    [
      MissionLocation(next_id(), i//3+1, 4, 'M', i+1, MAFIA_MISSION_NAMES[i], {f'M{i}'})
      for i in range(2,12)
    ],
    # PRC missions
    [MissionLocation(next_id(), 1, 4, 'C', 1, PRC_MISSION_NAMES[0], {'M1'})],
    [
      MissionLocation(next_id(), i//3+1, 4, 'C', i+1, PRC_MISSION_NAMES[i], {f'C{i}'})
      for i in range(1,12)
    ],
  )
}
