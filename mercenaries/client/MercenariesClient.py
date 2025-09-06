import asyncio
import os

from CommonClient import logger

from .MercenariesIPC import MercenariesIPC, IPCError
from .MercenariesConnector import MercenariesConnector

_MERCS_DEBUG = 'MERCS_DEBUG' in os.environ

tracker_loaded = False
# try:
#   from worlds.tracker.TrackerClient import TrackerGameContext as SuperContext
#   self.debug('Universal Tracker detected, enabling tracker support.')
#   tracker_loaded = True
# except ModuleNotFoundError:
#   from CommonClient import CommonContext as SuperContext
#   self.debug('No Universal Tracker detected, running without tracker support.')

from CommonClient import CommonContext as SuperContext
class MercenariesContext(SuperContext):
  game = 'Mercenaries'
  items_handling = 0b111  # fully remote
  want_slot_data = True
  tags = {'AP'}
  ap_state = {}

  def __init__(self, server_address: str, slot_name: str, password: str, pine_path: str):
    super().__init__(server_address, password)
    self.auth = slot_name
    self.locations_checked = set()
    self.ipc = MercenariesIPC(pine_path)
    self.debug('Initialization complete.')

  def reset_server_state(self):
    self.debug('Resetting server state.')
    super().reset_server_state()
    self.connector = None
    self.ap_state = {}

  def make_gui(self):
    ui = super().make_gui()
    ui.base_title = 'Mercenaries Client'
    return ui

  def debug(self, *args):
    if _MERCS_DEBUG:
      logger.info(*args)
    else:
      logger.debug(*args)

  async def server_auth(self, password_requested: bool = False):
    if password_requested and not self.password:
      await super(SuperContext, self).server_auth(password_requested)
    await self.get_username()
    await self.send_connect()

  # We might need this later when testing UT integration.
  # async def server_auth(self, password_requested=False):
  #   '''
  #   Called automatically when the server connection is established.

  #   Must send the username (and password, if applicable) in a Connect message.
  #   '''
  #   # We can't safely call super().server_auth() to get the password here
  #   # because UT's server_auth will try to send its own Connect with the
  #   # wrong info, so instead we replicate the password prompt locally.
  #   if password_requested and not self.password:
  #     logger.info('Enter the password required to join this game:')
  #     self.password = await self.console_input()
  #   await self.get_username()
  #   await self.send_connect()

  def on_package(self, cmd: str, args: dict):
    if _MERCS_DEBUG:
      self.debug('on_package: %s %s', cmd, args)
    match cmd:
      case 'Connected':
        self.slot_data = args.get("slot_data", {})
        self.debug('Connected, slot data is: %s', self.slot_data)
        connector = MercenariesConnector(self, self.ipc, self.slot_data)
        asyncio.create_task(self.sync_with_game(connector))
      case 'SetReply':
        if 'key' in args and 'value' in args:
          self.ap_state[args['key']] = args['value']

  async def send_msgs(self, msgs):
    if _MERCS_DEBUG:
      for msg in msgs:
        self.debug('SEND: %s', msg)
    await super().send_msgs(msgs)

  async def sync_with_game(self, connector):
    self.debug('Game sync running.')
    await self.send_msgs([
      {'cmd': 'Set', 'key': 'items_synced', 'want_reply': True, 'default': 0,
        'operations': [{'operation': 'default', 'value': 0}]}
      ])
    while self.server:
      try:
        # self.debug('Starting sync iteration')
        if not self.ap_state:
          self.debug('Still waiting for state from server.')
          continue
        connector.send_items(
          [item.item for item in self.items_received],
          self.ap_state.get('items_synced', 0))
        await self.send_msgs([
          {'cmd': 'Set', 'key': 'items_synced', 'want_reply': True, 'default': 0,
           'operations': [{'operation': 'replace', 'value': len(self.items_received)}]}
          ])
        self.locations_checked |= connector.get_new_checks(self.missing_locations)
        await self.check_locations(self.locations_checked)
        if connector.current_chapter() > self.slot_data['goal']:
          self.finished_game = True
      except IPCError:
        # self.debug('IPC error, sleeping')
        pass
      finally:
        await asyncio.sleep(5)
    self.debug('Game sync exiting.')

