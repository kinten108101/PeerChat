import os
from lib.promise import Promise 
from pathlib import Path
import time
from lib.cancellable import Cancellable
import mmap

DELAY_WAIT_CLI = 0.05

def mkdir_relaxed(s):
  try:
    os.mkdir(s)
  except FileExistsError:
    pass

class MessageRegion():
  def __init__(self, filepath):
    self._filepath = filepath
    self._work = None

  def _work_listen(self, cancellable, on_received_message):
    filepath = self._filepath
    mkdir_relaxed(os.path.dirname(filepath))
    with open(filepath, mode="w+", encoding="utf8") as file:
      file.truncate(100)
      file.close()
    while cancellable.is_set():
      message = None
      with open(filepath, mode="r+", encoding="utf8") as file:
        with mmap.mmap(file.fileno(), length=0, access=mmap.ACCESS_READ) as file:
          message = file.read().decode("utf8")
        file.close()
      message = message.strip()
      if "done" in message: # what the fuck
        pass
      elif len(message) == 100 and ord(message[0]) == 0:
        pass
      else:
        on_received_message(message, cancellable)
      with open(filepath, mode="w+", encoding="utf8") as file:
        file.truncate(100)
        with mmap.mmap(file.fileno(), length=0, access=mmap.ACCESS_WRITE) as file:
          file.write("done".encode("utf8"))
        file.close()
      time.sleep(DELAY_WAIT_CLI)
    Path.unlink(filepath)

  def watch_async(self, cancellable):
    self._work = Promise(target=self._work_listen, args=[cancellable])
    return self._work
