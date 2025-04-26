import subprocess
import os
import re

regexp_envpair = re.compile("(.*?)\\=(.*)")

def source(prefix=None):
  filename = "" if prefix is None else "." + str(prefix)
  filename = f"{filename}.env"
  with open(filename, "r") as f:
    for line in f:
      res = re.match(regexp_envpair, line)
      envvarkey = res.group(1)
      envvarvalue = res.group(2)
      os.environ[envvarkey] = envvarvalue.strip("\"")
