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

from .pine import Pine
from .shop import MafiaShop
from .lua import GCObject, Lua_Number, LUA_TNUMBER
from .lopcode import LuaOpcode
from .deck import DeckOf52

class IPCError(RuntimeError):
  pass

class MercenariesIPC:
  pine: Pine
  shop: MafiaShop
  L_ptr: int = -1
  intel_total: Lua_Number
  deck: DeckOf52

  def __init__(self, pine_path: str) -> None:
    self.pine = Pine(pine_path)
    self.shop = MafiaShop(self.pine)
    self.deck = DeckOf52(self.pine)

  def validate(self):
    # We need to both probe the game to see if it's in a consistent state, and
    # if so, compare that state to our current state to see if they match.
    # If the former check fails, we can't do anything.
    # If the latter check fails, we need to reinitialize our pointers and code
    # injections.
    if self.pine.peek32(self.pine.peek32(0x005007f4) + 0x74) > 8:
      raise IPCError('Game is between scenes')
    if self.pine.peek32(0x005131e0) == 0:
      raise IPCError('Player is not in control')
    if self.get_map() in {'menu', 'unknown'}:
      raise IPCError('Not in normal map')
    ptr = self.pine.peek32(0x00501a44)
    if ptr == 0x00501a44 or self.pine.peek32(ptr + 0x10) > 0:
      raise IPCError('Mystery Pointer has concerning value')

    L_ptr = self.pine.peek32(0x0056CBD0)
    if self.L_ptr != L_ptr:
      self.inject(L_ptr)

  def inject(self, L_ptr):
    print('Starting code injection.')
    # Initialize Lua.
    # Caller has already done consistency checks so hopefully we don't crash.
    self.L_ptr = L_ptr
    L = GCObject(self.pine, L_ptr)

    # Hook GetIntelTotal to return a value of our choice.
    # Grab a handle to constant 0 so we can adjust it at our leisure.
    gameflow_GetIntelTotal = L.getglobal('gameflow_GetIntelTotal').val
    self.intel_total = gameflow_GetIntelTotal.getk(0)
    self.intel_total.setval(0.0)

    # Replace the function body with an immediate return.
    # code[0] is already LOADK r1, 0 -- i.e. exactly what we want -- so we just
    # replace code[1] with a return.
    gameflow_GetIntelTotal.patch(1, [LuaOpcode('RETURN', A=1, B=3)])

    # Redirect frequently-called debug output functions to instead re-evaluate
    # the intel situation (and use our modified GetIntelTotal in the process).
    gameflow_AttemptAceMissionUnlock = L.getglobal('gameflow_AttemptAceMissionUnlock').val.addr
    L.getglobal('util_PrintDebugMsg').setval(gameflow_AttemptAceMissionUnlock)
    L.getglobal('Debug_Printf').setval(gameflow_AttemptAceMissionUnlock)
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
  def is_checked(self, location):
    self.validate()
    return location.is_checked(self)

  def is_card_verified(self, suit, rank):
    return self.deck.is_verified(suit, rank)

  def is_mission_complete(self, mission):
    return False

  #### For sending things to the game ####
  def adjust_money(self, delta):
    '''
    Add (or subtract) the given amount of money from the player's account.

    Due to difficulty in finding reliable pointers to the player structure,
    this will only send if the player is on foot.
    '''
    self.validate()
    # See NOTES for the ongoing quest to find a stable player/money pointer. :<
    on_foot = self.pine.peek32(0x00558B10) > 0
    if not on_foot:
      raise IPCError('Player is not on foot.')
    player_ptr = self.pine.peek32(0x00558B4C)
    money_ptr = player_ptr + 0xB60
    self.pine.pokef32(money_ptr, self.pine.peekf32(money_ptr) + delta)
    pass

  def set_unlocked_shop_items(self, items):
    '''
    Set the unlocked shop items to the given list. Removes excess items from the
    game and appends new items.

    Since this is potentially expensive (nearly 200 writes once everything is
    unlocked!) it does some simple checks first and skips updating if it doesn't
    need to.
    '''
    self.validate()
    game_count = self.shop.unlock_count()
    ap_count = len(items)
    if ap_count == 0:
      self.shop.update_unlocks([])
    elif game_count == ap_count and self.shop.unlocks[-1].tag() == items[-1]:
      # Same number of unlocked items in-game as in AP, and the most recently
      # unlocked item has the same ID as the most recently unlocked AP item,
      # so we assume we've neither received a new item from AP nor has the player
      # unlocked something new.
      return
    elif game_count > ap_count:
      # Player has unlocked something new in-game. Roll it back.
      self.shop.unlock_count(ap_count)
    elif ap_count > game_count:
      # Player has received new unlocks in AP. Grant them.
      self.shop.update_unlocks(items)

  def set_intel(self, amount, target):
    self.validate()
    self.intel_total.setval((amount/target) * 80.0)
