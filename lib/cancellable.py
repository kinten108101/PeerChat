from threading import Event

class Cancellable():
  def __init__(self):
    self.event = Event()
    self.event.set()

  def clear(self):
    return self.event.clear()

  def is_set(self):
    return self.event.is_set()
