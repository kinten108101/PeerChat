class Watch():
  def __init__(self, filepath):
    self._filepath = filepath
    self._work = None

  def _work_listen(self, filepath, on_change, cancellable=None):
    while cancellable.is_set():
      message = None
      with open(filepath, mode="r+", encoding="utf8") as file:
        with mmap.mmap(file.fileno(), length=0, access=mmap.ACCESS_READ) as file:
          message = file.read().decode("utf8")
        file.close()

  def start(self, ):
