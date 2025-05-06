from threading import Thread

class Promise():
  """
API is a mix between JavaScript's Promise and Python's Thread
  """
  def __init__(self, target=None, args=None):
    self.target = target
    self.args   = args
    self.on_response = None

  def then(self, on_response):
    self.on_response = on_response
    return self

  def start(self):
    if self.on_response is None:
      raise Exception("promise was not bound with a then clause")
    Thread(target=self.target, args=(*self.args, self.on_response)).start()
    return self

