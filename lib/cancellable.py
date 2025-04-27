from threading import Event

class Cancellable():
  def __init__(self):
    self.event = Event()
    self.event.set()

  def unset(self):
    return self.event.unset()

  def is_set(self):
    return self.event.is_set()
