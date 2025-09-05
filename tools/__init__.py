import sys

match sys.argv[1]:
  case 'test':
    from . import test
  case 'inspect':
    from . import inspect

sys.exit(0)
