'''
This is the connector between the client (uses IDs, talks to the AP host via
TCP) and the game wiggler (uses memory addresses, talks to PCSX2 via PINE).

Checks are relatively straightforward: the client queries passing a set of
missing checks, and this library just forwards the request and converts the
response.

Items are harder because we are not guaranteed to be able to successfully send
them to the game (e.g. if it's in the middle of a scene transition). So we keep
track of which items the client has told us to send, and separately, which items
we have actually sent, and the client periodically asks us to converge those two.
Items are only added to the sent list once successfully sent.
'''

'''
Shop items: idempotent; send the whole list
Money: one-and-done, send it and record it as sent
Intel: sum up the total amount of intel we have
'''

from typing import Any, Dict, List, Set

from CommonClient import logger

from .MercenariesIPC import MercenariesIPC, IPCError
from ..items import item_by_id
from ..locations import location_by_id

class MercenariesConnector:
  client: Any # MercenariesClient, but circular dependency
  ipc: MercenariesIPC
  options: Dict[str, Any]

  sent_shop_items: List[Any] = []
  sent_money_items: List[Any] = []
  sent_intel_items: List[Any] = []

  all_shop_items: List[Any] = []
  all_money_items: List[Any] = []
  all_intel_items: List[Any] = []

  def __init__(self, client, game, options):
    self.client = client
    self.game = game
    self.options = options

  #### Readers ####
  def current_chapter(self):
    return self.game.current_chapter()

  def get_new_checks(self, missing: Set[int]):
    # TODO: this is where missable handling needs to go once it's implemented.
    # print('missing', missing)
    found = {
      id for id in missing
      if self.game.is_checked(location_by_id(id))
    }
    # if found:
    #   print('found', found)
    return found

  #### Writers ####
  def send_items(self, items: List[int]):
    '''
    Send the specified items to the game. This is the complete list of items the
    client knows we have received, which may include stuff we've already sent.
    '''
    items = [item_by_id(id) for id in items]
    self.all_shop_items = [item for item in items if 'shop' in item.groups()]
    self.all_money_items = [item for item in items if 'money' in item.groups()]
    self.all_intel_items = [item for item in items if 'intel' in item.groups()]
    self.converge()

  # Converge the game state with the rando state by sending any missing items.
  # Items are always sent from the host in the order they were discovered, so
  # any items at the end of all_foo_items that are not in sent_foo_items are
  # the missing ones.
  def converge(self):
    try:
      self.converge_shop_items()
      self.converge_money_items()
      self.converge_intel_items()
    except IPCError as e:
      logger.info(f'Error sending items to game, will retry later: {e}')

  def converge_shop_items(self):
    # We send this every time and trust the IPC library to not duplicate send
    # if unneeded.
    # This is idempotent, so we just send the whole set of unlocks each time.
    # We do this even if the set of unlocks hasn't changed, because the player
    # may have unlocked new items in-game and we need to override that!
    print(f'Unlocking items: {[item.name() for item in self.all_shop_items]}')
    unlock_list = []
    by_tag = {}
    for item in self.all_shop_items:
      if item.tag in by_tag:
        by_tag[item.tag][1] += 1
      else:
        unlock = [item.tag, 1]
        unlock_list.append(unlock)
        by_tag[item.tag] = unlock

    self.game.set_unlocked_shop_items(unlock_list, 1.0 - self.options['shop_discount_percent']/100)
    self.sent_shop_items = self.all_shop_items

  def converge_money_items(self):
    # This is not idempotent, so we send the missing items once each and
    # record them as send them.
    # If the send fails, adjust_money will throw and we don't do the append.
    # TODO: this ends up sending the money every time we connect, which is a
    # problem. We need to use the AP Set/Get API to record which ones have been
    # successfully sent.
    for item in self.all_money_items[len(self.sent_money_items):]:
      print(f'Sending money: {item.name()}')
      self.game.adjust_money(item.amount)
      self.sent_money_items.append(item)

  def converge_intel_items(self):
    # This is fully idempotent and is a single call to setk() in practice so we
    # just do it unconditionally each time.
    chapter = self.game.current_chapter()
    suit = ['clubs', 'diamonds', 'hearts', 'spades'][chapter-1]
    total_intel = sum(
      item.intel_amount() for item in self.all_intel_items
      if item.suit is None or item.suit == suit)

    # If progressive intel is on, excess intel "rolls over" from earlier
    # chapters to later ones.
    if self.options['vanilla_intel']:
      target_intel = self.options['vanilla_intel_target']
    else:
      target_intel = self.options['intel_target']
    if self.options['progressive_intel']:
      # This should never go negative, but weird things can happen...
      total_intel = max(0, total_intel - target_intel * (chapter-1))

    print(f'converge_intel: chapter={chapter} suit={suit} total={total_intel} target={target_intel}')
    self.game.set_intel(total_intel, target_intel)
    self.sent_intel_items = self.all_intel_items
