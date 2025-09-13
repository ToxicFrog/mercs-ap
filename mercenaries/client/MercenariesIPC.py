'''
Low-level bit wiggling for Mercenaries.

This is responsible for:
- checking if the game is in a state where we can safely wiggle it;
- writing changes to game memory like money increases and shop unlocks;
- reading information from game memory like deck status and mission completion

Anything that needs to know specific memory addresses, data structures, etc should
go here or in one of our dependencies.

Note that it is possible for basically every call in this library to fail, even
if the game is running; when loading a game, transitioning between mission and
overworld states, etc the game is in a state where we can't safely modify it.

It is the responsibility of the caller to queue up changes and retry them on
failure; failures will throw, so they are hard to miss.
'''

'''
Useful but not yet usable addresses --
1A20A64 - free airstrike counter in the tutorial -- I suspect this is heap-allocated
1941060 - money counter in the tutorial
'''

from contextlib import contextmanager
from typing import List

from .deck import DeckOf52
from .lua import GCObject, Lua_TObject, LUA_TNUMBER, LUA_TSTRING, LUA_TBOOL
from .lopcode import LuaOpcode
from .patch import patch
from .pine import Pine
from .shop import MafiaShop
from .stats import PDAStats

class IPCError(RuntimeError):
  pass

class MercenariesIPC:
  pine: Pine
  shop: MafiaShop
  L_ptr: int = -1
  intel_total: Lua_TObject
  deck: DeckOf52
  stats: PDAStats
  latest_chapter: int = 0

  def __init__(self, pine_path: str) -> None:
    self.pine = Pine(pine_path)
    self.shop = MafiaShop(self.pine)
    self.deck = DeckOf52(self.pine)
    self.stats = PDAStats(self.pine)

  def validate(self):
    # We need to both probe the game to see if it's in a consistent state, and
    # if so, compare that state to our current state to see if they match.
    # If the former check fails, we can't do anything.
    # If the latter check fails, we need to reinitialize our pointers and code
    # injections.
    if self.pine.peek32(self.pine.peek32(0x005007f4) + 0x74) > 8:
      # Player model index. Only 0-8 are "normal" gameplay models.
      raise IPCError('Game is between scenes')
    if self.pine.peek32(0x005131e0) == 0:
      # Set to 1 in normal play, 0 in cutscenes.
      raise IPCError('Player is not in control')
    if self.pine.peek64(0x00558b10) == 0:
      # Two 4-byte flags, first is 1 if the player is on foot, second is 1 if
      # they're in a vehicle, if they're both 0 who knows what's happening?
      raise IPCError('Player is in an unknown state')
    if self.get_map() in {'menu', 'unknown'}:
      raise IPCError('Not in normal map')
    ptr = self.pine.peek32(0x00501a44)
    if ptr == 0x00501a44 or self.pine.peek32(ptr + 0x10) > 0:
      raise IPCError('Mystery Pointer has concerning value')

    L_ptr = self.pine.peek32(0x0056CBD0)
    if self.L_ptr != L_ptr:
      self.clear_handles()
      self.inject(L_ptr)

  def clear_handles(self):
    self.L_ptr = None
    self.intel_total = None
    self.shop_txn = 0

  def inject(self, L_ptr):
    print('Starting code injection.')
    # Initialize Lua.
    # Caller has already done consistency checks so hopefully we don't crash.
    L = GCObject(self.pine, L_ptr)

    # Grab all the things we want to modify *first*, so that if any of them are
    # nil we know the VM isn't done starting up yet and can retry later.
    # TODO: maybe getglobal and getnode should raise KeyError?
    try:
      globals = {
        'gameflow_GetIntelTotal': L.getglobal('gameflow_GetIntelTotal'),
        'gameflow_ShouldGameStateApply': L.getglobal('gameflow_ShouldGameStateApply'),
        'util_PrintDebugMsg': L.getglobal('util_PrintDebugMsg'),
        'Debug_Printf': L.getglobal('Debug_Printf'),
        'gameflow_AttemptAceMissionUnlock': L.getglobal('gameflow_AttemptAceMissionUnlock'),
        'AttemptFactionMoodClamp': L.getglobal('AttemptFactionMoodClamp'),
        # Stuff that we need to reference by name
        'bDebugOutput_name': L.getglobalnode('bDebugOutput').k,
        'gameflow_ShouldGameStateApply_name': L.getglobalnode('gameflow_ShouldGameStateApply').k,
        'gameflow_GetIntelTotal_name': L.getglobalnode('gameflow_GetIntelTotal').k,
        'gameflow_AttemptAceMissionUnlock_name': L.getglobalnode('gameflow_AttemptAceMissionUnlock').k,
        'Player_GetMoney_name': L.getglobalnode('Player_GetMoney').k,
        'Player_SetMoney_name': L.getglobalnode('Player_SetMoney').k,
        'Ui_PrintHudMessage_name': L.getglobalnode('Ui_PrintHudMessage').k,
        # Stuff we need to wiggle later
        'bDebugOutput': L.getglobal('bDebugOutput'),
      }
    except KeyError as e:
      raise IPCError(f'lua_State is still initializing: {e}')

    (
      self.intel_total,
      self.money_bonus,
      self.message_buffer,
      self.message_flag,
      self.reputation_floors,
    ) = patch(globals)
    self.debug_flag = globals['bDebugOutput']
    self.L_ptr = L_ptr
    print('Code injection complete.')


  #### Useful informational functions ####
  def get_map(self):
    # pointer to radar texture name buffer!
    # going to be a null-terminated string that is one of:
    # rdrNW rdrSW -- north or south world
    # rdraclubs, rdrAdmnd, rdrAHeart, rdrAspade -- ace missions
    # rdrSWN -- tutorial
    # rdrcddn -- credits/menu
    radar = self.pine.readmem(0x004a40e8, 8)
    match radar[:radar.find(0)]:
      case b'rdrcddn': return 'menu'
      case b'rdrSW': return 'SK'
      case b'rdrNW': return 'NK'
      case b'rdraclub': return 'clubs'
      case b'rdrAdmnd': return 'diamonds'
      case b'rdrAHear': return 'hearts'
      case b'rdrAspad': return 'spades'
    return 'unknown'

  def current_chapter(self):
    if self.is_card_verified('spades', 1):
      return 5 # victory!
    elif self.is_card_verified('hearts', 1):
      return 4
    elif self.is_card_verified('diamonds', 1):
      return 3
    elif self.is_card_verified('clubs', 1):
      return 2
    else:
      # We don't distinguish between the tutorial and chapter 1 at runtime
      return 1

  #### For checking locations ####
  @contextmanager
  def start_location_checks(self):
    '''
    Context manager for location checks.

    Checking a location requires talking to the game, and checking all the
    locations requires talking to the game a lot, which is very expensive. So
    we do the talking at the start of the location check block and cache the
    results.
    '''
    self.validate()
    self.doing_location_checks = True
    try:
      L = GCObject(self.pine, self.L_ptr)
      missions = L.getglobal('mission_accepted').val()
      self.mission_cache = {
        faction: missions.getfield(faction).val()
        for faction in ['allies', 'china', 'mafia', 'sk']
        if missions is not None
      }
    except KeyError:
      self.mission_cache = {}
    self.bounty_cache = self.stats.bounties_found()
    self.card_cache = self.deck.deck_status()
    self.latest_chapter = self.current_chapter()

    try:
      yield self
    finally:
      self.end_location_checks()

  def end_location_checks(self):
    self.doing_location_checks = False
    self.bounty_cache = None
    self.mission_cache = None
    self.card_cache = None

  def is_checked(self, location):
    assert self.doing_location_checks
    return location.is_checked(self)

  def is_card_verified(self, suit, rank):
    return self.card_cache[suit][rank-1] > 1

  def is_card_captured(self, suit, rank):
    return self.card_cache[suit][rank-1] > 2

  def is_mission_complete(self, faction: str, mission: int) -> bool:
    return mission < self.mission_cache.get(faction, 0)

  def is_bounty_collected(self, type: str, count: int) -> bool:
    return self.bounty_cache[type] >= count

  def send_once(self, money: int = 0, message: str = ''):
    '''
    Send things that should only be delivered to the player once. At the moment
    this means money and chat/info messages.

    Sent items are stored in the constant table of AttemptFactionMoodClamp. The
    presence of such items is signaled by setting bDebugOutput to true. The next
    time the function is called they are delivered and the flag reset to false.
    This function is then responsible for loading the constant table with new
    items and setting the flag again.
    '''
    self.validate()

    if not money and not message:
      return False

    if self.debug_flag.val():
      return False

    self.money_bonus.set(money)
    if message:
      # In practical terms, just by how much text we can fit on screen, this is
      # probably limited to about 50 cols.
      self.message_buffer.val().set_string(message)
      self.message_flag.set(True, tt=LUA_TBOOL)
    else:
      self.message_flag.set(False, tt=LUA_TBOOL)

    self.debug_flag.set(True)
    return True

  def set_unlocked_shop_items(self, items: List[List[int]], discounts: List, discount_factor: float):
    '''
    Sets the unlocked shop items to match the given list.

    The first element in each entry should be the item tag; the second should
    be the number of copies of that item (>= 1). Excess items are applied as
    discounts based on the discount_factor.

    Since this is potentially expensive (nearly 200 writes once everything is
    unlocked!) it does some simple checks first and skips updating if it doesn't
    need to.
    '''
    self.validate()

    # Number of distinct shop unlocks found in AP
    txn = sum(item[1] for item in items) + len(discounts)
    # Number of actual unlocks that turns into once duplicates are merged
    ap_count = len(items)
    # Number of unlocks the player has in-game.
    game_count = self.shop.unlock_count()

    if ap_count != game_count or self.shop_txn != txn:
      # Either:
      # - the player has found a new unlock in-game we need to re-lock;
      # - the player has received a new unlock through AP; or
      # - the player has received a duplicate unlock or coupon and we need to apply a discount
      print(f'Updating shop items (game: count={game_count}, txn={self.shop_txn}; ap: count={ap_count}, txn={txn})')
      self.shop.set_unlocks(items, discounts, discount_factor)
      self.shop_txn = txn

  def set_intel(self, amount, target):
    self.validate()
    self.intel_total.set((amount/target) * 80.0)

  def set_reputation_floor(self, faction, floor):
    self.validate()
    self.reputation_floors[faction].set(floor)
