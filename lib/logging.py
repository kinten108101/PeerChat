# TODO(kinten): send helpppp
import sys
_stdlib_print = print
def print(s):
  _stdlib_print(f"app: {s}", file=sys.stderr)
