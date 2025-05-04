import os.path

class Vardir():
  DIRECTORY_NAME = "var"

  def path(*s):
    return os.path.join(Vardir.DIRECTORY_NAME, *s)
