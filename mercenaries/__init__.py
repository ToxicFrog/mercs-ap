import logging
import random
from typing import Dict, FrozenSet

from BaseClasses import CollectionState, Item, ItemClassification, Location, MultiWorld, Region, Tutorial, LocationProgressType
from worlds.AutoWorld import WebWorld, World
import worlds.LauncherComponents as LauncherComponents

from . import items
from . import locations
from .options import MercenariesOptions

logger = logging.getLogger('Mercenaries')

def launch_client(*args) -> None:
  from .client import main
  # TODO: use launch() here once it's in main
  LauncherComponents.launch_subprocess(main, name='MercenariesClient', args=args)

LauncherComponents.components.append(
  LauncherComponents.Component(
  'Mercenaries Client',
  func=launch_client,
  component_type=LauncherComponents.Type.CLIENT,
  )
)

class MercenariesItem(Item):
  game = 'Mercenaries'
  def __init__(self, world, item):
    super().__init__(
      player=world.player,
      name=item.name(),
      code=item.id,
      classification=item.classification())

class MercenariesLocation(Location):
  game = 'Mercenaries'
  def __init__(self, world, location, region):
    super().__init__(
      player=world.player,
      name=location.name(),
      address=location.id,
      parent=region)
    self.access_rule = location.access_rule(world)
    self.progress_type = location.progress_type(world.options)

class MercenariesEventToken(Item):
  game = 'Mercenaries'
  def __init__(self, world, name):
    super().__init__(
      player=world.player,
      name=name,
      code=None,
      classification=ItemClassification.progression)

class MercenariesEvent(Location):
  game = 'Mercenaries'
  def __init__(self, world, event_name, token_name, region, rule):
    super().__init__(
      player=world.player,
      name=event_name,
      address=None,
      parent=region)
    self.access_rule = rule
    self.place_locked_item(MercenariesEventToken(world, token_name))


class MercenariesWorld(World):
  '''
  Mercenaries: Playground of Destruction is a 2005 PS2 game by Pandemic Studios. You play as a mercenary operating in
  a present-day warzone. Your objective: to capture or kill 52 high-value targets -- and get rich in the process.
  '''
  game = 'Mercenaries'
  options_dataclass = MercenariesOptions
  options: MercenariesOptions
  topology_present = True
  required_client_version = (0, 6, 2)
  included_item_categories = {}

  # Used by the AP core.
  # Map from canonical name to internal ID.
  item_name_to_id: Dict[str, int] = items.name_to_id_map()
  location_name_to_id: Dict[str, int] = locations.name_to_id_map()
  # Map from group name to set of canonical names.
  item_name_groups: Dict[str,FrozenSet[str]] = items.group_to_names_map()
  location_name_groups: Dict[str,FrozenSet[str]] = locations.group_to_names_map()

  # Universal Tracker integration
  ut_can_gen_without_yaml = True

  # Internal bookkeeping
  location_count: int = 0


  def __init__(self, multiworld: MultiWorld, player: int):
    super().__init__(multiworld, player)

  def create_item(self, name: str) -> MercenariesItem:
    return MercenariesItem(self, items.item_by_name(name))

  def get_filler_item_name(self):
    return self.create_filler(1).name

  def create_filler(self, amount):
    weights = {
      name: items.item_by_name(name).count(None)
      for name in self.item_name_groups['filler']
    }
    return [
      self.create_item(name)
      for name in random.choices(
        population=list(weights.keys()),
        weights=list(weights.values()),
        k=amount)
    ]

  def generate_early(self) -> None:
    # Option consistency checks
    if not self.options.vanilla_intel and not self.options.progressive_intel:
      assert self.options.intel_in_pool % 4 == 0, 'When not using progressive intel, intel_in_pool must be a multiple of 4'
    # Universal Tracker yaml-less generation support
    ut_config = getattr(self.multiworld, 're_gen_passthrough', {}).get(self.game, None)
    if ut_config:
      print('Doing Universal Tracker worldgen with settings:', ut_config)
      for opt in ut_config:
        getattr(self.options, opt).value = ut_config[opt]

  def connect_chapters(self, first, second, mission):
    mission = locations.mission(mission)
    token = f'{first.name} Complete'
    first.locations.append(MercenariesEvent(
      world=self,
      event_name=f'Finish {first.name} via {mission.short_name()}',
      token_name=token,
      region=first,
      rule=mission.access_rule(self)))

    first.connect(
      connecting_region=second,
      name=f'"{mission.name()} Clear',
      rule=lambda state: state.has(token, self.player))

  def create_regions(self) -> None:
    menu_region = Region('Menu', self.player, self.multiworld)
    credits_region = Region('Credits', self.player, self.multiworld)
    chapters = [
      Region('Tutorial', self.player, self.multiworld),
      Region('Chapter 1', self.player, self.multiworld),
      Region('Chapter 2', self.player, self.multiworld),
      Region('Chapter 3', self.player, self.multiworld),
      Region('Chapter 4', self.player, self.multiworld),
    ]
    self.multiworld.regions.extend([menu_region, credits_region] + chapters)

    menu_region.connect(
      connecting_region=chapters[0],
      name='New Game',
      rule=lambda _: True)

    self.connect_chapters(chapters[0], chapters[1], 'A1')
    self.connect_chapters(chapters[1], chapters[2], 'A3')
    if self.options.goal > 1:
      self.connect_chapters(chapters[2], chapters[3], 'A6')
    if self.options.goal > 2:
      self.connect_chapters(chapters[3], chapters[4], 'A9')
    if self.options.goal > 3:
      self.connect_chapters(chapters[4], credits_region, 'A11')

    for location in locations.all_locations():
      if not location.should_include(self.options):
        continue
      chapter = chapters[location.chapter(self.options)]
      print(f'Including location "{location.name()}" in {chapter} ({location.progress_type(self.options)})')
      chapter.locations.append(MercenariesLocation(self, location, chapter))
      self.location_count += 1

  def create_items(self) -> None:
    slots_left = self.location_count

    print('Including progression items:')
    for item in items.all_progression_items():
      if item.count(self.options) > 0:
        print(f'{item.count(self.options):4d} {item.name()}')
      for _ in range(item.count(self.options)):
        self.multiworld.itempool.append(self.create_item(item.name()))
        slots_left -= 1

    assert slots_left >= 0, f'Tried to place more items ({self.location_count - slots_left}) than we have checks ({self.location_count}), giving up'

    print(f'Remaining {slots_left} slots will be populated with filler.')
    for item in self.create_filler(slots_left):
      self.multiworld.itempool.append(item)

  def set_rules(self):
    # All region and location access rules were defined in create_regions, so we just need the
    # overall victory condition here.
    def goal(state):
      return state.has(f'Chapter {self.options.goal} Complete', self.player)
    self.multiworld.completion_condition[self.player] = goal

  def get_progression_hints(self):
    '''
    Get a list of up to 52 locations that we will provide hints for in exchange
    for capturing members of the Deck alive.

    We can only hint our own items, or other people's items in our own locations.
    So our priority for this is something like:
    - our own intel items;
    - other people's progression items in our world;
    - the rest of our progression items.
    '''
    # Initially populate with our intel items
    hintables = [
      item for item in self.multiworld.get_items()
      if item.player == self.player
      and item.code is not None
      and 'intel' in items.item_by_id(item.code).groups()
    ]
    # If that's not enough add everyone else's progression items in our world
    if len(hintables) < 52:
      extras = [
        item for item in self.multiworld.get_items()
        if item.player != self.player
        and item.advancement
        and item.code
        and item.location.player == self.player
      ]
      self.random.shuffle(extras)
      hintables += extras[0:52-len(hintables)]
    # If that's still not enough, add the rest of our progression items, which
    # includes all shop items and is definitely enough.
    if len(hintables) < 52:
      extras = [
        item for item in self.multiworld.get_items()
        if item.player == self.player
        and item.advancement
        and item.code
        and 'intel' not in items.item_by_id(item.code).groups()
      ]
      self.random.shuffle(extras)
      hintables += extras[0:52-len(hintables)]

    return self.random.sample(hintables, k=52)

  def fill_slot_data(self):
    return self.options.as_dict(
      'goal',
      'vanilla_intel', 'vanilla_intel_target',
      'intel_in_pool', 'intel_target', 'progressive_intel',
      'shop_discount_percent',
      toggles_as_bools=True
    ) | {
      'hints_from_cards': [
        (item.location.address, item.location.player)
        for item in self.get_progression_hints()
      ],
    }

  # Called by UT on connection. In UT mode all configuration will come from
  # slot_data rather than via the YAML.
  @staticmethod
  def interpret_slot_data(slot_data):
    print('interpret_slot_data', slot_data)
    return slot_data

  def has_combat_power_for_rank(self, state, rank):
    '''
    Figure out if the player has enough combat power for missions of the given
    rank. We base this entirely on shop unlocks, on the assumption that if the
    player needs more money they can do challenges or collect NK vehicle bounties.

    R1 missions are free, every rank after that increases the number of shop items
    needed by 3, capping at 36 at R12, or about half of the total unlocks and a
    bit less than what you'd have at that point in normal play if you missed
    every optional objective.

    From R3 onwards we additionally require that the player have a balanced
    amount of vehicles, supplies, and airstrikes, scaling from 1 of each at
    R3 to 7 of each at R12, to prevent this from saying things are a-ok if (e.g.)
    the player has lots of supplies available but no vehicles or airstrikes.
    '''
    vehicles = sum(
      1 for item in items.all_items_in_groups({'shop', 'vehicle'})
      if state.has(item.name(), self.player))
    supplies = sum(
      1 for item in items.all_items_in_groups({'shop', 'supplies'})
      if state.has(item.name(), self.player))
    airstrikes = sum(
      1 for item in items.all_items_in_groups({'shop', 'airstrike'})
      if state.has(item.name(), self.player))
    shop = vehicles + supplies + airstrikes
    target = (rank-1)*3

    return (
      shop >= (rank-1)*3
      and (vehicles >= target//5)
      and (supplies >= target//5)
      and (airstrikes >= target//5))

  def current_chapter(self, state):
    if state.has('Chapter 4 Complete', self.player):
      return 5
    elif state.has('Chapter 3 Complete', self.player):
      return 4
    elif state.has('Chapter 2 Complete', self.player):
      return 3
    elif state.has('Chapter 1 Complete', self.player):
      return 2
    else:
      return 1

  def has_intel_for_chapter(self, state, chapter):
    '''
    Figure out if the player has enough intel for the given chapter, based on
    the yaml options.
    '''
    if self.options.vanilla_intel:
      target = self.options.vanilla_intel_target
    else:
      target = self.options.intel_target

    if self.options.progressive_intel:
      suit = None
      target *= chapter
    else:
      suit = ['clubs', 'diamonds', 'hearts', 'spades'][chapter-1]

    intel = sum(
      item.intel_amount() * state.count(item.name(), self.player)
      for item in items.all_items_in_groups({'intel'})
      if item.suit == suit)

    return intel >= target
