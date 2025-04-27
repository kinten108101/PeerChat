#!/usr/bin/env python3
import re
import json
from lib.cancellable import Cancellable
from lib.server import listen
from lib.regexp import RegExpBuffer
from threading import Lock

mutex = Lock()
re_submit_info = re.compile(r"^submit_info:(.+)$")
re_get_list = re.compile(r"^get_list$")

class User():
  pass

ADDRESS = ("127.0.0.1", 7090)

TRACKING = {}

def add_list(body):
  global TRACKING, mutex
  with mutex:
    TRACKING[f"{body["address"][0]}:{body["address"][1]}"] = "test"

def get_list():
  return json.dumps(TRACKING)

def on_connection(request, response):
  print(f"tracker: received from client: \"{request.message}\"")
  regexp = RegExpBuffer()
  if regexp.match(re_submit_info, request.message):
    print(f"tracker: request is submit_info")
    body = regexp.group(1)
    body = json.loads(body)
    print(f"tracker: submit_info: address {body["address"][0]}")
    add_list(body)
    response.write(get_list())
  elif regexp.match(re_get_list, request.message):
    print(f"tracker: request is get_list")
    response.write(get_list())
  else:
    raise OSError("wtf")
  response.close()

if __name__ == "__main__":
  cancellable = Cancellable()
  listen(ADDRESS, on_connection, cancellable)
