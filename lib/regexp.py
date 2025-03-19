class RegExpBuffer():
  def __init__(self):
    self._regexp_result = None

  def match(self, pattern, string):
    self._regexp_result = pattern.match(string)
    return self._regexp_result

  def group(self, num):
    return self._regexp_result.group(num)
