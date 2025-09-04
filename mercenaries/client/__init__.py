'''
Client entry point.

This just contains the startup code; the actual implementation is everywhere
else in this directory.
'''

import asyncio

import Utils
from CommonClient import get_base_parser, gui_enabled, logger, server_loop

from .MercenariesClient import MercenariesContext, tracker_loaded

def main(*args):
  Utils.init_logging('MercenariesClient')

  async def actual_main(args):
    ctx = MercenariesContext(args.connect, args.name, args.password, args.pcsx2)
    ctx.server_task = asyncio.create_task(server_loop(ctx), name='ServerLoop')
    if tracker_loaded:
      logger.info('Initializing tracker...')
      ctx.run_generator()
    if gui_enabled:
      ctx.run_gui()
    ctx.run_cli()

    await ctx.exit_event.wait()
    await ctx.shutdown()

  import colorama

  parser = get_base_parser()
  parser.add_argument('--pcsx2', default=None, help='Absolute path (unix) or host:port (windows) for PCSX2 PINE connection')
  parser.add_argument('--name', default=None, help='Slot name')

  colorama.init()
  args = parser.parse_args(args)
  asyncio.run(
    actual_main(args),
    debug=True)
  colorama.deinit()


if __name__ == '__main__':
  main()
