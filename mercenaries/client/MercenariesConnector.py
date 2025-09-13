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

from collections import Counter, deque
from typing import Any, Dict, List, Set

from CommonClient import logger

from .MercenariesIPC import MercenariesIPC, IPCError
from ..items import item_by_id
from ..locations import location_by_id

class MercenariesConnector:
  client: Any # MercenariesClient, but circular dependency
  game: MercenariesIPC
  options: Dict[str, Any]
  messages: deque[str]

  def __init__(self, client, game, options):
    self.client = client
    self.game = game
    self.options = options
    self.messages = deque()

  #### Readers ####
  def current_chapter(self):
    return self.game.latest_chapter

  def get_checks_and_hints(self, missing: Set[int], available_hints: List[List[int]]):
    # TODO: this is where missable handling needs to go once it's implemented.
    with self.game.start_location_checks() as ipc:
      found = {
        id for id in missing
        if ipc.is_checked(location_by_id(id))
      }

      hints = set()
      suits = ['clubs', 'diamonds', 'hearts', 'spades']
      for i in range(3):
        for rank in range(1, 14):
          if ipc.is_card_captured(suits[i], rank):
            hints.add(tuple(available_hints[i*13 + rank-1]))

      return (found, hints)

  def get_hintable_checks(self, found: Set[int], missing: Set[int]):
    found = { location_by_id(id).short_name() for id in found }
    return {
      id for id in missing
      if location_by_id(id).is_hintable(found)
    }

  #### Writers ####
  def item_group(self, group: str, items: List[int]) -> List[int]:
    return [item for item in items if group in item.groups()]

  def send_items(self, items: List[int]) -> Set[int]:
    '''
    Send the specified items to the game. This is the complete list of items the
    client knows we have received, minus any items we told it not to re-send (by
    returning them in sent_items). The do-not-send list is remembered across
    runs by the host.

    We have, broadly speaking, two kinds of items we care about: idempotent
    items, which can be re-sent without ill effects, and non-idempotent items,
    which must only be sent once. The latter are added to sent_items and
    returned to tell the client layer not to re-send them.
    '''
    items = [item_by_id(id) for id in items]
    sent_items = Counter()
    try:
      self.converge_shop_items(self.item_group('shop', items))
      self.converge_intel_items(self.item_group('intel', items))
      self.converge_reputation_items(self.item_group('reputation', items))
      sent_items += self.send_once(self.item_group('money', items))
    except IPCError as e:
      logger.info(f'Error sending items to game, will retry later: {e}')

    return sent_items

  def queue_message(self, msg):
    self.messages.append(msg)

  def converge_shop_items(self, items):
    # This is idempotent, so we just send the whole set of unlocks each time.
    # We do this even if the set of unlocks hasn't changed, because the player
    # may have unlocked new items in-game and we need to override that!
    unlock_list = []
    by_tag = {}
    for item in (i for i in items if 'progression' in i.groups()):
      if item.tag in by_tag:
        by_tag[item.tag][1] += 1
      else:
        unlock = [item.tag, 1]
        unlock_list.append(unlock)
        by_tag[item.tag] = unlock

    self.game.set_unlocked_shop_items(
      unlock_list, [i for i in items if 'filler' in i.groups()],
      1.0 - self.options['shop_discount_percent']/100)

  def converge_intel_items(self, items):
    # This is fully idempotent and is a single call to setk() in practice so we
    # just do it unconditionally each time.
    chapter = self.current_chapter()
    suit = ['clubs', 'diamonds', 'hearts', 'spades'][chapter-1]
    total_intel = sum(
      item.intel_amount() for item in items
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

    # print(f'converge_intel: chapter={chapter} suit={suit} total={total_intel} target={target_intel}')
    self.game.set_intel(total_intel, target_intel)

  def converge_reputation_items(self, items):
    factions = Counter()
    for item in items:
      factions[item.faction()] += 1
    for faction, count in factions.items():
      if count <= 2:
        floor = -100 + (50*count)
      else:
        floor = 100 - (100 * 0.9 ** (count-2))
      self.game.set_reputation_floor(faction, floor)

  def send_once(self, items):
    '''
    Send things that need to only be delivered once.

    At the moment this means money (in the items array) and messages (in the
    sendq). We don't care so much about losing messages (they're in the text
    client, displaying them in-game is only useful if they're delivered
    promptly) but we do care about losing money, so the latter gets returned
    to the caller so it can be recorded server-side as having been delivered.
    '''
    total = sum([item.amount for item in items])
    if not self.messages:
      message = ''
    else:
      message = self.messages[0]

    if self.game.send_once(money=total, message=message):
      print(f'Successfully dispatched ${total:,d} and message {message}')
      if self.messages:
        self.messages.popleft()
      return Counter(item.id for item in items)
    else:
      return Counter()
