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

from typing import List

from .pine import Pine
from .shop import MafiaShop
from .lua import GCObject, Lua_TObject, LUA_TNUMBER, LUA_TSTRING
from .lopcode import LuaOpcode
from .deck import DeckOf52
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
      self.clear_handles()
      self.inject(L_ptr)

  def clear_handles(self):
    self.L_ptr = None
    self.intel_total = None
    self.missions = None
    self.shop_txn = 0

  def inject(self, L_ptr):
    print('Starting code injection.')
    # Initialize Lua.
    # Caller has already done consistency checks so hopefully we don't crash.
    L = GCObject(self.pine, L_ptr)

    # Grab all the things we want to modify *first*, so that if any of them are
    # nil we know the VM isn't done starting up yet and can retry later.
    # TODO: maybe getglobal and getnode should raise KeyError?
    GetIntelTotal = L.getglobal('gameflow_GetIntelTotal')
    ShouldGameStateApply = L.getglobal('gameflow_ShouldGameStateApply')
    PrintDebugMsg = L.getglobal('util_PrintDebugMsg')
    Debug_Printf = L.getglobal('Debug_Printf')
    AttemptAceMissionUnlockNode = L._G.val().getnode('gameflow_AttemptAceMissionUnlock')

    if not (GetIntelTotal and ShouldGameStateApply and PrintDebugMsg
            and Debug_Printf and AttemptAceMissionUnlockNode):
      raise IPCError('lua_State is still initializing')

    # Hook GetIntelTotal to return a value of our choice.
    # Grab a handle to constant 0 so we can adjust it at our leisure.
    self.intel_total = GetIntelTotal.val().getk(0)
    self.intel_total.set(0.0)

    # Replace the function body with an immediate return.
    # code[0] is already LOADK r1, 0 -- i.e. exactly what we want -- so we just
    # replace code[1] with a return.
    with GetIntelTotal.val().lock():
      GetIntelTotal.val().patch(1, [LuaOpcode('RETURN', A=1, B=2)])

    # Modify gameflow_ShouldGameStateApply to exfiltrate information about
    # mission completion state (and exit early if called without arguments).
    with ShouldGameStateApply.val().lock():
      ShouldGameStateApply.val().patch(24, [
        LuaOpcode('SETGLOBAL', A=5, Bx=1), # set _G.mission_accepted to r5, which is the info table
        LuaOpcode('TEST', A=0, B=0, C=0), # test if r0 is nil, and if so
        LuaOpcode('JMP', sBx=50), # jump to the end of the function
      ])

    # Hook the debug output function to call stuff we designate instead.
    with PrintDebugMsg.val().lock():
      # Replace its constant table with the names of the functions we want to call
      PrintDebugMsg.val().setk(0, L._G.val().getnode('gameflow_ShouldGameStateApply').k)
      PrintDebugMsg.val().setk(1, AttemptAceMissionUnlockNode.k)

      # Replace the function body with calls to those functions.
      PrintDebugMsg.val().patch(0, [
        LuaOpcode('GETGLOBAL', A=0, Bx=0),
        LuaOpcode('CALL', A=0, B=1, C=1),
        LuaOpcode('GETGLOBAL', A=0, Bx=1),
        LuaOpcode('CALL', A=0, B=1, C=1),
        LuaOpcode('RETURN', A=0, B=1),
      ])

    # Now redirect Debug_Printf to alias util_PrintDebugMsg.
    Debug_Printf.set(PrintDebugMsg)

    # For a larger hook, we can use AttemptFactionMoodClamp.
    # 25 constants, 77 free instructions, and most of what it does we can replace,
    # if we're going to be managing faction mood floors from AP -- we need 6
    # constants and 16 instructions to call Faction_SetMinimumRelation repeatedly,
    # and then after that we've got loads of time to call ShouldGameStateApply,
    # PrintHudMessage, AdjustMoney, etc

    # 4 constants, 5 instructions
    #   Faction_ModifyRelation(faction, 'prokat', amount)

    # 3 constants, 4 instructions, not sure what other stuff it might do though
    #   Player_AdjustMoney(delta, 'interface.economyevent.challenge')
    # Have also seen money adjustment done with
    #   Player_SetMoney(Player_GetMoney()+delta)
    # which is 6 instructions but still only 3 constants and might be safer

    # 2 constants, 3 instructions
    #   Ui_PrintHudMessage(msg)

    # Also need a few instructions at the end to clear the global "we did this" flag.


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
  def is_checked(self, location):
    self.validate()
    return location.is_checked(self)

  def is_card_verified(self, suit, rank):
    return self.deck.is_verified(suit, rank)

  def refresh_mission_list(self):
    if not self.missions:
      L = GCObject(self.pine, self.L_ptr)
      self.missions = L.getglobal('mission_accepted')
    if self.missions:
      return self.missions.val()
    else:
      return None

  def is_mission_complete(self, faction: str, mission) -> bool:
    self.validate()
    missions = self.refresh_mission_list()
    if not missions:
      return False
    return mission < missions.getfield(faction).val()

  def is_bounty_collected(self, type: str, count: int) -> bool:
    return self.stats.bounties_found()[type] >= count

  #### For sending things to the game ####
  def adjust_money(self, delta: int):
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

  def set_unlocked_shop_items(self, items: List[List[int]], discount_factor: float):
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
    txn = sum(item[1] for item in items)
    # Number of actual unlocks that turns into once duplicates are merged
    ap_count = len(items)
    # Number of unlocks the player has in-game.
    game_count = self.shop.unlock_count()

    if ap_count != game_count or self.shop_txn != txn:
      # Either:
      # - the player has found a new unlock in-game we need to re-lock;
      # - the player has received a new unlock through AP; or
      # - the player has received a duplicate unlock and we need to apply a discount
      print(f'Updating shop items (game: count={game_count}, txn={self.shop_txn}; ap: count={ap_count}, txn={txn})')
      self.shop.set_unlocks(items, discount_factor)
      self.shop_txn = txn

  def set_intel(self, amount, target):
    self.validate()
    self.intel_total.set((amount/target) * 80.0)
