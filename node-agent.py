#!/usr/bin/env python3
from os import getenv
import lib.dotenv as dotenv
from lib.server import listen
from lib.fetch import fetch
from lib.cancellable import Cancellable

NODE_ADDRESS = ("127.0.0.1", 7230)

def peer_connect(address):
  pass

def work_submit_info():
  def on_response(response):
    print(f"agent: tracker responsed: \"{response}\"")
  body = {}
  body["address"] = NODE_ADDRESS
  print(f"agent: submitting info to tracker")
  return fetch(TRACKER_ADDRESS, "submit_info", body).then(on_response)

def on_connection(request, response):
  pass

if __name__ == "__main__":
  dotenv.source(prefix="node-agent")
  trackaddr = getenv("TRACKER_ADDRESS")
  if trackaddr is None:
    raise Exception("wtf")
  trackaddr = trackaddr.split(":")
  global TRACKER_ADDRESS
  TRACKER_ADDRESS = trackaddr[0], int(trackaddr[1])
  work_submit_info().start()
  cancellable = Cancellable()
  listen(TRACKER_ADDRESS, on_connection, cancellable)
