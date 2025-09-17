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
import random
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

      # Locations that the player did not but which are now uncollectable due
      # to being removed from the map after finishing a chapter.
      # TODO: is there some way we can force them to respawn? A lot of that
      # seems to be controlled from lua...
      missed = {
        id for id in missing
        if id not in found
        and ipc.is_missed(location_by_id(id))
      }

      hints = set()
      suits = ['clubs', 'diamonds', 'hearts', 'spades']
      for i in range(3):
        for rank in range(1, 14):
          if ipc.is_card_captured(suits[i], rank):
            hints.add(tuple(available_hints[i*13 + rank-1]))

      return (found | missed, hints)

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
      self.send_shop_items(self.item_group('shop', items))
      self.send_intel_items(self.item_group('intel', items))
      self.send_reputation_items(self.item_group('reputation', items))
      sent_items += self.send_once(items)
    except IPCError as e:
      logger.info(f'Error sending items to game, will retry later: {e}')

    return sent_items

  def queue_message(self, msg):
    self.messages.append(msg)

  def send_shop_items(self, items):
    # This is idempotent, so we just send the whole set of unlocks each time.
    # We do this even if the set of unlocks hasn't changed, because the player
    # may have unlocked new items in-game and we need to override that!
    unlocks = {}
    discount_factor = 1.0 - self.options['shop_discount_percent']/100

    unlock_items = self.item_group('shop-unlock', items)
    if not unlock_items:
      self.game.set_unlocked_shop_items([], 0)
      return

    for item in unlock_items:
      if item.tag in unlocks:
        unlocks[item.tag] = item.discount(discount_factor)
      else:
        unlocks[item.tag] = item

    discount_items = sorted(self.item_group('shop-discount', items), key=lambda x: x.discount, reverse=True)
    for discount in discount_items:
      item = max(unlocks.values(), key=lambda x: x.price)
      unlocks[item.tag] = item.discount(1.0 - discount.discount/100)

    self.game.set_unlocked_shop_items(sorted(unlocks.values(), key=lambda x: x.title), len(items))

  def send_intel_items(self, items):
    # This is fully idempotent and is a single call to setk() in practice so we
    # just do it unconditionally each time.
    chapter = self.current_chapter()
    if chapter < 1:
      # Haven't figured out what chapter the player is in yet, can't usefully
      # assign intel.
      return

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

    self.game.set_intel(total_intel, target_intel)

  def send_reputation_items(self, items):
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
    if not self.messages:
      message = ''
    else:
      message = self.messages[0]

    money = self.item_group('money', items)
    money_total = sum(item.amount for item in money)
    sent = Counter(item.id for item in money)

    support_template = ''
    unlocks = self.item_group('shop-unlock', items)
    support = self.item_group('shop-coupon', items)
    for coupon in support:
      matches = [item for item in unlocks if coupon.applies_to(item)]
      if len(matches) < 3:
        continue
      support_item = random.choice(matches)
      support_template = support_item.template
      sent += Counter([coupon.id])
      break

    if self.game.send_once(money=money_total, message=message, support_item=support_template):
      if support_template:
        print(f'Reified {coupon} as {support_template} from choices {[i.title for i in matches]}')
      print(f'Successfully dispatched ${money_total:,d} + support {support_template} + message {message}')
      if self.messages:
        self.messages.popleft()
      return sent
    else:
      return Counter()
